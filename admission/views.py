import calendar
import csv
import hashlib
import hmac
import json
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from io import BytesIO
from urllib.parse import urlencode
from dateutil.relativedelta import relativedelta

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

import openpyxl
import razorpay
from calendar import monthrange
from weasyprint import CSS, HTML

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import FieldDoesNotExist
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db import models
from django.db.models import (
    Q,
    Count,
    Case,
    When,
    Value,
    CharField,
    DecimalField,
    F,
    Sum,
)
from django.forms import formset_factory, inlineformset_factory

from django.forms.widgets import static
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.timezone import now
from django.views import View
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_GET, require_POST

from admission.forms import (
    AdmissionEnquiryForm,
    AttendanceForm,
    AttendanceUpdateForm,
    FeeReceiptForm,
    FeeReceiptFormSet,
)
from admission.models import (
    Admission,
    AdmissionEnquiry,
    Attendance,
    AttendanceRegister,
    FeeReceipt,
    FeeStructure,
    StudentStageStatusHistory,
    generate_receipt_no,
)
from admission.services.fee_refresh import refresh_fee_structure_queryset

from admission.utils import send_sms

from core.choices import ENQUIRY_STATUS, ENQUIRY_TYPE_CHOICES

from branches.models import Branch
from core import choices, mixins
from core.pdfview import PDFView
from core.utils import build_url

from employees.models import Employee
from masters.forms import BatchForm
from masters.models import Batch, Course, Holiday, LeaveRequest

from . import forms, tables

logger = logging.getLogger(__name__)

User = get_user_model()


@login_required
def create_razorpay_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            fee_structure_id = data.get('fee_structure_id')
            amount = float(data.get('amount'))
            
            # Validate amount
            if amount <= 0:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid amount'
                })
            
            # Get keys from settings
            key_id = getattr(settings, 'RAZORPAY_KEY_ID', '').strip()
            key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '').strip()
            
            # Check if keys are properly configured
            if not key_id or not key_secret:
                logger.error("Razorpay keys not configured")
                return JsonResponse({
                    'success': False,
                    'message': 'Payment gateway not configured'
                })
            
            # Validate key format
            if not key_id.startswith('rzp_'):
                logger.error(f"Invalid Razorpay Key ID format")
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid payment gateway configuration'
                })
            
            # Get fee structure
            try:
                fee_structure = FeeStructure.objects.get(id=fee_structure_id)
            except FeeStructure.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Fee structure not found'
                })
            
            # Initialize Razorpay client
            try:
                client = razorpay.Client(auth=(key_id, key_secret))
                logger.info("Razorpay client initialized successfully")
            except Exception as e:
                logger.error(f"Razorpay client initialization failed: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'message': f'Payment gateway error: {str(e)}'
                })
            
            # Create order with proper amount (minimum ₹1)
            amount_in_paise = int(amount * 100)
            
            # Razorpay requires minimum amount of 100 paise (₹1)
            if amount_in_paise < 100:
                return JsonResponse({
                    'success': False,
                    'message': 'Minimum payment amount is ₹1'
                })
            
            order_data = {
                'amount': amount_in_paise,
                'currency': 'INR',
                'payment_capture': 1,  # Auto capture
                'notes': {
                    'student_id': str(fee_structure.student.id),
                    'student_name': fee_structure.student.fullname(),
                    'admission_number': fee_structure.student.admission_number or '',
                    'fee_structure_id': str(fee_structure_id),
                    'installment_name': fee_structure.name,
                    'installment_no': str(fee_structure.installment_no),
                }
            }
            
            try:
                order = client.order.create(data=order_data)
                logger.info(f"Razorpay order created: {order['id']} for ₹{amount}")
                
                return JsonResponse({
                    'success': True,
                    'order_id': order['id'],
                    'amount': order['amount'],
                    'currency': order['currency'],
                    'key_id': key_id,
                    'description': f"{fee_structure.name} - {fee_structure.student.fullname()}"
                })
                
            except razorpay.errors.BadRequestError as e:
                error_msg = str(e)
                logger.error(f"Razorpay BadRequestError: {error_msg}")
                
                # Handle specific error cases
                if 'api key' in error_msg.lower() or 'authentication' in error_msg.lower():
                    return JsonResponse({
                        'success': False,
                        'message': 'Payment gateway authentication failed. Please contact support.'
                    })
                elif 'amount' in error_msg.lower():
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid payment amount. Please check and try again.'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': f'Payment gateway error: {error_msg}'
                    })
                    
            except razorpay.errors.ServerError as e:
                logger.error(f"Razorpay ServerError: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'message': 'Payment gateway temporarily unavailable. Please try again in a few moments.'
                })
            except Exception as e:
                logger.error(f"Error creating Razorpay order: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'message': f'Unable to create payment order. Please try again.'
                })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid request data'
            })
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': 'An unexpected error occurred. Please try again.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def verify_razorpay_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            razorpay_payment_id = data.get('razorpay_payment_id')
            razorpay_order_id = data.get('razorpay_order_id')
            razorpay_signature = data.get('razorpay_signature')
            fee_structure_id = data.get('fee_structure_id')
            
            logger.info(f"Verifying payment: {razorpay_payment_id}")
            
            # Validate required fields
            if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature, fee_structure_id]):
                return JsonResponse({
                    'success': False,
                    'message': 'Missing required payment information'
                })
            
            # Get keys from settings
            key_id = getattr(settings, 'RAZORPAY_KEY_ID', '').strip()
            key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '').strip()
            
            if not key_id or not key_secret:
                logger.error("Razorpay keys not configured")
                return JsonResponse({
                    'success': False,
                    'message': 'Payment gateway not configured'
                })
            
            # Get fee structure
            try:
                fee_structure = FeeStructure.objects.get(id=fee_structure_id)
            except FeeStructure.DoesNotExist:
                logger.error(f"Fee structure not found: {fee_structure_id}")
                return JsonResponse({
                    'success': False,
                    'message': 'Fee structure not found'
                })
            
            # Verify signature manually
            try:
                message = f"{razorpay_order_id}|{razorpay_payment_id}"
                
                generated_signature = hmac.new(
                    key_secret.encode('utf-8'),
                    message.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                if generated_signature != razorpay_signature:
                    logger.error("Signature mismatch - possible fraud attempt")
                    return JsonResponse({
                        'success': False,
                        'message': 'Payment verification failed. Please contact support.'
                    })
                
                logger.info("Signature verified successfully")
                
            except Exception as e:
                logger.error(f"Signature verification error: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'message': 'Payment verification failed'
                })
            
            # Initialize Razorpay client to fetch payment details
            try:
                client = razorpay.Client(auth=(key_id, key_secret))
                payment_details = client.payment.fetch(razorpay_payment_id)
                
                amount_paise = payment_details.get('amount', 0)
                amount = Decimal(amount_paise) / 100
                payment_status = payment_details.get('status', '')
                
                logger.info(f"Payment amount: ₹{amount}, Status: {payment_status}")
                
                # Check payment status
                if payment_status not in ['captured', 'authorized']:
                    logger.warning(f"Payment not successful. Status: {payment_status}")
                    return JsonResponse({
                        'success': False,
                        'message': f'Payment was not successful. Status: {payment_status}'
                    })
                
            except razorpay.errors.BadRequestError as e:
                logger.error(f"Invalid payment ID: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid payment information'
                })
            except Exception as e:
                logger.error(f"Error fetching payment details: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'message': 'Unable to verify payment. Please contact support.'
                })
            
            # Check if payment already recorded
            existing_receipt = FeeReceipt.objects.filter(
                razorpay_payment_id=razorpay_payment_id
            ).first()
            
            if existing_receipt:
                logger.warning(f"Payment already recorded: {razorpay_payment_id}")
                return JsonResponse({
                    'success': True,
                    'message': 'Payment already recorded',
                    'receipt_id': existing_receipt.id,
                    'receipt_no': existing_receipt.receipt_no
                })
            
            # Record payment in database
            try:
                with transaction.atomic():
                    receipt_count = FeeReceipt.objects.count()
                    receipt = FeeReceipt.objects.create(
                        student=fee_structure.student,
                        receipt_no=f"RZP{receipt_count + 1:06d}",
                        date=timezone.now().date(),
                        note=f"{fee_structure.name} - Online Payment",
                        payment_type='Razorpay',
                        amount=amount,
                        razorpay_payment_id=razorpay_payment_id,
                        razorpay_signature=razorpay_signature,
                        status='paid'
                    )
                    
                    logger.info(f"Receipt created: {receipt.receipt_no}")
                    
                    # Update fee structure
                    fee_structure.paid_amount = (fee_structure.paid_amount or Decimal(0)) + amount
                    
                    if fee_structure.paid_amount >= fee_structure.amount:
                        fee_structure.is_paid = True
                        logger.info(f"Fee structure {fee_structure.id} marked as fully paid")
                    
                    fee_structure.razorpay_payment_id = razorpay_payment_id
                    fee_structure.razorpay_status = 'paid'
                    fee_structure.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Payment successful',
                        'receipt_id': receipt.id,
                        'receipt_no': receipt.receipt_no,
                        'amount_paid': float(amount),
                        'total_paid': float(fee_structure.paid_amount),
                        'remaining': float(fee_structure.get_due_amount()),
                        'is_fully_paid': fee_structure.is_paid
                    })
                    
            except Exception as e:
                logger.error(f"Database error: {str(e)}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'message': 'Payment received but failed to record. Please contact support.'
                })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid request data'
            })
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': 'An unexpected error occurred'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def verify_razorpay_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            razorpay_payment_id = data.get('razorpay_payment_id')
            razorpay_order_id = data.get('razorpay_order_id')
            razorpay_signature = data.get('razorpay_signature')
            fee_structure_id = data.get('fee_structure_id')
            
            logger.info(f"Verifying payment: {razorpay_payment_id}")
            
            # Validate required fields
            if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature, fee_structure_id]):
                return JsonResponse({
                    'success': False,
                    'message': 'Missing required payment information'
                })
            
            # Get keys from settings
            key_id = getattr(settings, 'RAZORPAY_KEY_ID', '').strip()
            key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '').strip()
            
            if not key_id or not key_secret:
                logger.error("Razorpay keys not configured")
                return JsonResponse({
                    'success': False,
                    'message': 'Payment gateway not configured'
                })
            
            # Get fee structure
            try:
                fee_structure = FeeStructure.objects.get(id=fee_structure_id)
            except FeeStructure.DoesNotExist:
                logger.error(f"Fee structure not found: {fee_structure_id}")
                return JsonResponse({
                    'success': False,
                    'message': 'Fee structure not found'
                })
            
            # Verify signature manually
            try:
                # Create the signature string
                message = f"{razorpay_order_id}|{razorpay_payment_id}"
                
                # Generate HMAC signature
                generated_signature = hmac.new(
                    key_secret.encode('utf-8'),
                    message.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                # Compare signatures
                if generated_signature != razorpay_signature:
                    logger.error("Signature mismatch")
                    logger.error(f"Expected: {generated_signature}")
                    logger.error(f"Received: {razorpay_signature}")
                    return JsonResponse({
                        'success': False,
                        'message': 'Payment signature verification failed. Please contact support.'
                    })
                
                logger.info("Signature verified successfully")
                
            except Exception as e:
                logger.error(f"Signature verification error: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'message': f'Signature verification error: {str(e)}'
                })
            
            # Initialize Razorpay client to fetch payment details
            try:
                client = razorpay.Client(auth=(key_id, key_secret))
                payment_details = client.payment.fetch(razorpay_payment_id)
                
                logger.info(f"Payment status: {payment_details.get('status')}")
                
                # Get payment amount
                amount_paise = payment_details.get('amount', 0)
                amount = Decimal(amount_paise) / 100
                payment_status = payment_details.get('status', '')
                
                logger.info(f"Payment amount: ₹{amount}, Status: {payment_status}")
                
                # Verify payment is captured/successful
                if payment_status not in ['captured', 'authorized']:
                    return JsonResponse({
                        'success': False,
                        'message': f'Payment not successful. Status: {payment_status}'
                    })
                
            except razorpay.errors.BadRequestError as e:
                logger.error(f"Razorpay BadRequestError fetching payment: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid payment details'
                })
            except Exception as e:
                logger.error(f"Error fetching payment details: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'message': 'Error fetching payment details from gateway'
                })
            
            # Check if payment already recorded
            existing_receipt = FeeReceipt.objects.filter(
                razorpay_payment_id=razorpay_payment_id
            ).first()
            
            if existing_receipt:
                logger.warning(f"Payment already recorded: {razorpay_payment_id}")
                return JsonResponse({
                    'success': True,
                    'message': 'Payment already recorded',
                    'receipt_id': existing_receipt.id,
                    'receipt_no': existing_receipt.receipt_no
                })
            
            # Use transaction to ensure data consistency
            try:
                with transaction.atomic():
                    # Create fee receipt
                    # Create fee receipt
                    receipt_count = FeeReceipt.objects.count()
                    receipt = FeeReceipt.objects.create(
                        student=fee_structure.student,
                        receipt_no=f"RZP{receipt_count + 1:06d}",
                        date=timezone.now().date(),
                        note=f"{fee_structure.name} - Online Payment",
                        razorpay_payment_id=razorpay_payment_id,
                        razorpay_signature=razorpay_signature,
                        status='paid'
                    )
                    
                    # Create PaymentMethod
                    from admission.models import PaymentMethod
                    PaymentMethod.objects.create(
                        fee_receipt=receipt,
                        payment_type='Razorpay',
                        amount=amount,
                        note=f"Razorpay Payment ID: {razorpay_payment_id}"
                    )
                    
                    logger.info(f"Receipt created: {receipt.receipt_no}")
                    
                    # Update fee structure
                    fee_structure.paid_amount = (fee_structure.paid_amount or Decimal(0)) + amount
                    
                    # Check if fully paid
                    if fee_structure.paid_amount >= fee_structure.amount:
                        fee_structure.is_paid = True
                        logger.info(f"Fee structure {fee_structure.id} marked as fully paid")
                    
                    fee_structure.razorpay_payment_id = razorpay_payment_id
                    fee_structure.razorpay_status = 'paid'
                    fee_structure.save()
                    
                    logger.info(f"Fee structure updated - Paid: ₹{fee_structure.paid_amount}/{fee_structure.amount}")
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Payment verified and recorded successfully',
                        'receipt_id': receipt.id,
                        'receipt_no': receipt.receipt_no,
                        'amount_paid': float(amount),
                        'total_paid': float(fee_structure.paid_amount),
                        'remaining': float(fee_structure.get_due_amount()),
                        'is_fully_paid': fee_structure.is_paid
                    })
                    
            except Exception as e:
                logger.error(f"Database transaction error: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'message': f'Error recording payment: {str(e)}'
                })
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request")
            return JsonResponse({
                'success': False,
                'message': 'Invalid request data'
            })
        except Exception as e:
            logger.error(f"Unexpected error in verify_payment: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': f'Unexpected error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@csrf_exempt
@require_POST
def update_admission_stage(request, pk):
    try:
        data = json.loads(request.body)
        admission = Admission.objects.get(pk=pk)

        new_status = data.get("stage_status")
        remark = data.get("remark")

        # Capture placement data from payload
        company = data.get("placed_company_name")
        position = data.get("placed_position")
        source = data.get("placement_source")

        # Update the status
        admission.stage_status = new_status

        # FIX: Ensure internship status also saves placement details
        if new_status in ["placed", "internship"]:
            # We use strip() to ensure empty strings aren't saved as whitespace
            admission.placed_company_name = company.strip() if company else None
            admission.placed_position = position.strip() if position else None
            
            # If source is an empty string, we set it to None 
            # (If your model defaults to 'not_applicable', this prevents that)
            admission.placement_source = source if source and source != "" else None
        else:
            # Clear details if status is not placed/internship
            admission.placed_company_name = None
            admission.placed_position = None
            admission.placement_source = None

        admission.save()

        # Create History Record (ensure history matches the student record)
        StudentStageStatusHistory.objects.create(
            student=admission,
            status=new_status,
            remark=remark,
            company_name=admission.placed_company_name,
            position=admission.placed_position,
            placement_source=admission.placement_source
        )

        return JsonResponse({
            "success": True,
            "message": f"Stage updated to {new_status} successfully"
        })

    except Admission.DoesNotExist:
        return JsonResponse({"success": False, "message": "Admission not found"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


@require_GET
def get_batches(request):
    course_id = request.GET.get("course_id") or request.GET.get("course")
    branch_id = request.GET.get("branch_id") or request.GET.get("branch")
    
    # Start with all active batches
    batches = Batch.objects.filter(is_active=True)
    
    # Only filter by course if provided and not 'all'
    if course_id and course_id != 'all':
        try:
            batches = batches.filter(course_id=int(course_id))
        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid course_id"}, status=400)
    
    # Only filter by branch if provided and not 'all'
    if branch_id and branch_id != 'all':
        try:
            batches = batches.filter(branch_id=int(branch_id))
        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid branch_id"}, status=400)
    
    # If both are 'all' or empty, return all batches
    batches = batches.values("id", "batch_name").order_by("batch_name")
    
    return JsonResponse({"batches": list(batches)})

def get_students_by_branch(request):
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        branch_id = request.GET.get('branch_id')

        if request.user.usertype in ["admin_staff", "ceo", "cfo", "coo", "hr", "cmo"] or request.user.is_superuser:
            if branch_id:
                students = Admission.objects.filter(branch_id=branch_id)
            else:
                students = Admission.objects.none() 

        else:
            if hasattr(request.user, 'branch'):
                branch_id = request.user.branch.id
                students = Admission.objects.filter(branch_id=branch_id)
            else:
                students = Admission.objects.none()

        students_list = [{
            'id': student.id,
            'display': student.fullname(),
        } for student in students]

        return JsonResponse({'success': True, 'students': students_list})

    return JsonResponse({'success': False, 'students': []})

@csrf_exempt
def admission_update_stage(request, pk):
    if request.method == "POST":
        data = json.loads(request.body)
        try:
            admission = Admission.objects.get(pk=pk)

            new_status = data.get("stage_status")
            remark = data.get("remark")

            admission.stage_status = new_status

            # ✅ Save placement details if "placed" or "internship"
            if new_status in ["placed", "internship"]:
                admission.placed_company_name = data.get("placed_company_name", "")
                admission.placed_position = data.get("placed_position", "")
                admission.placement_source = data.get("placement_source", "")
                admission.save()

                # Save stage change history
                StudentStageStatusHistory.objects.create(
                    student=admission,
                    status=new_status,
                    remark=remark,
                    company_name=admission.placed_company_name,
                    position=admission.placed_position,
                    placement_source=admission.placement_source
                )

                # ✅ Prepare WhatsApp Message for placed students only
                if new_status == "placed":
                    student_name = admission.fullname()
                    company = admission.placed_company_name or "a reputed company"
                    position = admission.placed_position or "a great position"

                    message = (
                        f"🎉 Congratulations {student_name}! "
                        f"\n\nWe're proud to announce that you've been successfully placed at *{company}* "
                        f"as *{position}*. \n\nYour hard work and dedication have truly paid off. "
                        f"\n\nBest wishes for your bright future ahead! 🌟"
                    )

                    # ✅ Send WhatsApp message to student and parent
                    phone_list = []
                    if admission.whatsapp_number:
                        phone_list.append(admission.whatsapp_number)
                    if admission.parent_whatsapp_number:
                        phone_list.append(admission.parent_whatsapp_number)

                    # Loop through and send to both
                    for phone in phone_list:
                        send_sms(phone, message)

                    return JsonResponse({
                        "success": True,
                        "message": f"Stage changed to Placed and WhatsApp notifications sent!"
                    })
                else:
                    # For internship status
                    return JsonResponse({
                        "success": True,
                        "message": f"Stage changed to {new_status.title()} and placement details saved successfully!"
                    })
            else:
                # For all other stages
                admission.save()

                StudentStageStatusHistory.objects.create(
                    student=admission,
                    status=new_status,
                    remark=remark
                )

                return JsonResponse({
                    "success": True,
                    "message": f"Student stage changed to {new_status.title()} successfully!"
                })

        except Admission.DoesNotExist:
            return JsonResponse({"success": False, "message": "Admission not found"})
        except Exception as e:
            print("Error:", str(e))
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)
    
    
    
@csrf_exempt
@require_POST
def bulk_update_student_stage(request):
    try:
        data = json.loads(request.body)
        branch_id = data.get('branch')
        course_id = data.get('course') 
        batch_id = data.get('batch')
        new_status = data.get('stage_status')
        remark = data.get('remark', '')
        excluded_students = data.get('excluded_students', [])  # List of student IDs to exclude

        print(f"Bulk update request: branch={branch_id}, course={course_id}, batch={batch_id}, status={new_status}")
        print(f"Excluded students: {excluded_students}")

        if not all([branch_id, course_id, batch_id, new_status]):
            return JsonResponse({'success': False, 'message': 'Branch, Course, Batch and Status are required'})

        # Validate that the status is a valid choice
        valid_statuses = [choice[0] for choice in choices.STUDENT_STAGE_STATUS_CHOICES]
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'message': f'Invalid status: {new_status}'})

        with transaction.atomic():
            # Get students matching the criteria, excluding the specified students
            students = Admission.objects.filter(
                branch_id=branch_id,
                course_id=course_id, 
                batch_id=batch_id,
                is_active=True
            ).exclude(id__in=excluded_students)

            print(f"Found {students.count()} students to update (excluding {len(excluded_students)} students)")

            if not students.exists():
                return JsonResponse({'success': False, 'message': 'No students found matching the criteria'})

            updated_count = 0
            history_records = []
            
            # Update each student individually
            for student in students:
                print(f"Updating student: {student.fullname()} from {student.stage_status} to {new_status}")
                
                # Store old status for history
                old_status = student.stage_status
                
                # Update the student stage status
                student.stage_status = new_status
                student.save()
                
                # Create history record
                history_records.append(
                    StudentStageStatusHistory(
                        student=student,
                        status=new_status,
                        remark=f"Bulk update: {remark} (Changed from {old_status} to {new_status})"
                    )
                )
                updated_count += 1

            # Bulk create history records
            if history_records:
                StudentStageStatusHistory.objects.bulk_create(history_records)
                print(f"Created {len(history_records)} history records")

        return JsonResponse({
            'success': True, 
            'message': f'Stage updated for {updated_count} students successfully. {len(excluded_students)} students were excluded.',
            'updated_count': updated_count,
            'excluded_count': len(excluded_students)
        })

    except Exception as e:
        print(f"Error in bulk_update_student_stage: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})


@require_GET
def get_batch_students(request):
    branch_id = request.GET.get("branch_id")
    course_id = request.GET.get("course_id")
    batch_id = request.GET.get("batch_id")
    
    if not all([branch_id, course_id, batch_id]):
        return JsonResponse({"error": "Missing parameters"}, status=400)
    
    students = Admission.objects.filter(
        branch_id=branch_id,
        course_id=course_id,
        batch_id=batch_id,
        is_active=True
    ).values("id", "first_name", "last_name", "admission_number", "stage_status")
    
    return JsonResponse({"students": list(students)})


from admission.services import calculate_student_fee_structure

def get_student_fee_structure(request):
    student_id = request.GET.get('student_id')
    exclude_receipt_id = request.GET.get('exclude_receipt_id')
    fee_structures = []

    if student_id:
        calculated_fees = calculate_student_fee_structure(student_id, exclude_receipt_id)
        
        for fs in calculated_fees:
            fee_structures.append({
                'installment_no': fs.installment_no or 0,
                'name': fs.name or f"Installment {fs.installment_no}",
                'amount': float(fs.amount or 0),
                'paid_amount': float(fs.paid_amount or 0),
                'due_date': fs.due_date.strftime('%Y-%m-%d') if fs.due_date else '',
                'is_paid': fs.is_paid,
            })

    return JsonResponse({'success': True, 'fee_structures': fee_structures})


@require_GET
def student_calendar_api(request, student_id):
    try:
        student = Admission.objects.get(id=student_id)
        year = int(request.GET.get('year', timezone.now().year))
        month = int(request.GET.get('month', timezone.now().month))
        
        view = AdmissionProfileDetailView()
        calendar_days = view.get_calendar_data(student, year, month)
        
        serialized_days = []
        for day in calendar_days:
            serialized_day = {
                'status': day['status'],
                'is_today': day['is_today']
            }
            if day['date']:
                serialized_day['date'] = day['date'].isoformat()
            else:
                serialized_day['date'] = None
            serialized_days.append(serialized_day)
        
        return JsonResponse({
            'calendar_days': serialized_days,
            'month': datetime(year, month, 1).strftime('%B'),
            'year': year
        })
    except Admission.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

class ImportEnquiryView(View):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            messages.error(request, "No file uploaded.")
            return redirect('admission:public_lead_list')

        try:
            if file.name.endswith('.xlsx'):
                wb = openpyxl.load_workbook(file)
                sheet = wb.active
                for row in sheet.iter_rows(min_row=3, values_only=True):
                    phone = row[0] if len(row) > 0 else None
                    full_name = row[1] if len(row) > 1 else None
                    city = row[2] if len(row) > 2 else None
                    enquiry_type = row[3] if len(row) > 3 else None

                    if phone:
                        AdmissionEnquiry.objects.create(
                            contact_number=phone,
                            full_name=full_name,
                            city=city,
                            enquiry_type=enquiry_type
                        )

            elif file.name.endswith('.csv'):
                decoded_file = file.read().decode('utf-8').splitlines()
                reader = csv.reader(decoded_file)
                next(reader, None)  # Skip header
                for row in reader:
                    full_name = row[0] if len(row) > 0 else None
                    city = row[1] if len(row) > 1 else None
                    phone = row[2] if len(row) > 2 else None
                    enquiry_type = row[3] if len(row) > 3 else None

                    if phone:
                        AdmissionEnquiry.objects.create(
                            contact_number=phone,
                            full_name=full_name,
                            city=city,
                            enquiry_type=enquiry_type
                        )

            else:
                messages.error(request, "Unsupported file type. Please upload .xlsx or .csv.")
                return redirect('admission:public_lead_list')

            messages.success(request, "Leads imported successfully.")
        except Exception as e:
            messages.error(request, f"Import failed: {e}")

        return redirect('admission:public_lead_list')

    
def add_to_me(request, pk):
    enquiry = get_object_or_404(AdmissionEnquiry, pk=pk)

    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, "You are not registered as an employee.")
        return redirect('admission:public_lead_list')

    if enquiry.tele_caller is None:
        enquiry.tele_caller = employee
        enquiry.save()
        messages.success(request, "You have been assigned to this enquiry.")
    else:
        messages.warning(request, "This enquiry already has a tele-caller.")
        
    return redirect('admission:public_lead_list')


@csrf_exempt
def assign_to(request, pk=None):
    if request.method == "POST" and request.user.usertype == "sales_head":
        try:
            data = json.loads(request.body)
            tele_caller_id = data.get("tele_caller_id")
            employee = Employee.objects.get(id=tele_caller_id)

            # Bulk assignment if enquiry_ids are provided
            enquiry_ids = data.get("enquiry_ids")
            if enquiry_ids:
                AdmissionEnquiry.objects.filter(id__in=enquiry_ids).update(tele_caller=employee)
                return JsonResponse({"status": "success", "message": "Bulk assigned successfully"})

            # Single assignment if pk is provided
            if pk:
                enquiry = get_object_or_404(AdmissionEnquiry, pk=pk)
                enquiry.tele_caller = employee
                enquiry.save()
                return JsonResponse({"status": "success", "message": "Assigned successfully"})

            return JsonResponse({"status": "error", "message": "No enquiries provided."})

        except Employee.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Invalid tele caller selected."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Invalid request."})

@csrf_exempt
@login_required
def bulk_add_to_me(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            enquiry_ids = data.get("enquiry_ids", [])
            
            if not enquiry_ids:
                return JsonResponse({"status": "error", "message": "No enquiries selected."})

            try:
                employee = Employee.objects.get(user=request.user)
            except Employee.DoesNotExist:
                return JsonResponse({"status": "error", "message": "You are not registered as an employee."})

            # Filter for enquiries that are currently unassigned
            updated_count = AdmissionEnquiry.objects.filter(
                id__in=enquiry_ids,
                tele_caller__isnull=True
            ).update(tele_caller=employee)

            if updated_count > 0:
                return JsonResponse({
                    "status": "success", 
                    "message": f"Successfully assigned {updated_count} leads to you."
                })
            else:
                return JsonResponse({
                    "status": "warning", 
                    "message": "No eligible leads were assigned (they might already be assigned)."
                })

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Invalid request method."})


def student_check_data(request):
    personal_email = request.GET.get('personal_email')
    student = AdmissionEnquiry.objects.filter(personal_email=personal_email).first()

    if student:
        return JsonResponse({
            'status': True,
            'student_name': student.full_name,
            'student_id': student.pk,
            'full_name': student.full_name,
            'date_of_birth': student.date_of_birth.strftime('%d/%m/%Y') if student.date_of_birth else None,
            'religion': student.religion,
            'city': student.city,
            'district': student.district,
            'state': student.state,
            'pin_code': student.pin_code,
            'personal_email': student.personal_email,
            'contact_number': student.contact_number,
            'whatsapp_number': student.whatsapp_number,
            'parent_full_name': student.parent_full_name,
            'parent_contact_number': student.parent_contact_number,
            'parent_whatsapp_number': student.parent_whatsapp_number,
            'parent_mail_id': student.parent_mail_id,
            # 'photo': student.photo.url if student.photo else None,  # Only if needed
        })
    else:
        return JsonResponse({'status': False})


def get_admission_history(request, pk):
    admission = get_object_or_404(Admission, pk=pk)
    history = StudentStageStatusHistory.objects.filter(student=admission).order_by('-created')
    
    history_data = []
    for h in history:
        # Construct a display string for the table
        placement_details = []
        if h.company_name: placement_details.append(f"Company: {h.company_name}")
        if h.position: placement_details.append(f"Pos: {h.position}")
        
        history_data.append({
            "id": h.id,
            "date": h.created.strftime("%d-%m-%Y %I:%M %p"),
            "status": h.get_status_display(),
            "status_key": h.status,
            "remark": h.remark or "",
            # THESE FIELDS MUST BE SENT INDIVIDUALLY FOR THE EDIT FORM
            "company_name": h.company_name or "", 
            "position": h.position or "",
            "placement_info": " | ".join(placement_details) if placement_details else ""
        })
    
    # Get the model-level latest data
    latest_remark = history.first().remark if history.exists() else ""
    
    latest_placement_data = None
    if admission.stage_status in ['placed', 'internship']:
        latest_placement_data = {
            "company_name": admission.placed_company_name or 'N/A',
            "position": admission.placed_position or 'N/A',
            "status": admission.stage_status
        }

    return JsonResponse({
        "success": True,
        "fullname": admission.fullname(),
        "latest_remark": latest_remark,
        "latest_placement_data": latest_placement_data,
        "history": history_data
    })

@login_required
@require_POST
def update_admission_history(request, pk):
    try:
        history_item = get_object_or_404(StudentStageStatusHistory, pk=pk)
        data = json.loads(request.body)
        
        # 1. Update basic fields
        history_item.remark = data.get('remark', history_item.remark)
        history_item.status = data.get('status', history_item.status) # NEW: Update status
        
        # 2. Update placement fields if they exist
        if history_item.status in ['placed', 'internship']:
            history_item.company_name = data.get('company_name', history_item.company_name)
            history_item.position = data.get('position', history_item.position)
        
        history_item.save()

        # 3. SYNC LOGIC: If this is the latest history entry, update the main Admission record
        admission = history_item.student
        latest_history = StudentStageStatusHistory.objects.filter(student=admission).latest('created')
        
        if latest_history.id == history_item.id:
            admission.stage_status = history_item.status
            if history_item.status in ['placed', 'internship']:
                admission.placed_company_name = history_item.company_name
                admission.placed_position = history_item.position
            admission.save()

        return JsonResponse({"success": True, "message": "Updated successfully"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@login_required
def calculate_fee_structure_preview(request):
    """
    AJAX View to calculate fee structure dynamically before saving.
    Logic: (Course Fee - Discount - Admission Fee) / Installments
    """
    if request.method != "GET":
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

    try:
        # 1. Get Inputs from Request
        admission_id = request.GET.get('admission_id')
        fee_type = request.GET.get('fee_type')
        installment_type = request.GET.get('installment_type')
        
        # Parse numeric inputs safely
        try:
            custom_months = int(request.GET.get('custom_months') or 0)
        except ValueError:
            custom_months = 0

        try:
            discount_amount = Decimal(request.GET.get('discount_amount') or 0)
        except:
            discount_amount = Decimal('0.00')

        try:
            admission_fee_amount = Decimal(request.GET.get('admission_fee_amount') or 0)
        except:
            admission_fee_amount = Decimal('0.00')

        # 2. Get Course Fee
        # We fetch the admission object to get the associated Course Fee
        # If this is a new admission (no ID yet), you might need to pass course_id via AJAX instead
        if not admission_id:
            return JsonResponse({'status': 'error', 'message': 'Admission ID not found'})
        
        admission = Admission.objects.get(pk=admission_id)
        
        if not admission.course:
            return JsonResponse({'status': 'error', 'message': 'Course not selected for this student'})

        course_fee = Decimal(str(admission.course.fees))
        
        # 3. Calculate Net Tuition Amount (The amount to be split into installments)
        # Formula: Course Fee - Discount - Admission Fee
        net_amount = course_fee - discount_amount - admission_fee_amount
        
        if net_amount < 0:
            net_amount = Decimal('0.00')

        # 4. Generate Structure
        structure = []
        today = timezone.now().date()
        # Use existing course start date if available, else today
        start_date = admission.course_start_date or today
        
        amounts = []

        if fee_type == 'installment':
            
            # --- CUSTOM INSTALLMENT LOGIC ---
            if installment_type == 'custom':
                if custom_months > 0:
                    # Divide Net Amount by Months
                    installment_amount = (net_amount / custom_months).quantize(Decimal('0.01'))
                    amounts = [installment_amount] * custom_months

                    # Handle Rounding Difference (Add remainder to last month)
                    total_calculated = sum(amounts)
                    if total_calculated != net_amount:
                        diff = net_amount - total_calculated
                        amounts[-1] += diff
            
            # --- REGULAR LOGIC (4 Months) ---
            elif installment_type == 'regular':
                num_installments = 4
                installment_amount = (net_amount / num_installments).quantize(Decimal('0.01'))
                amounts = [installment_amount] * num_installments
                
                total_calculated = sum(amounts)
                if total_calculated != net_amount:
                    amounts[-1] += (net_amount - total_calculated)

            # --- SPECIAL LOGIC (Fixed 5500) ---
            elif installment_type == 'special':
                installment_amount = Decimal('5500.00')
                if net_amount > 0:
                    num_installments = int((net_amount + installment_amount - Decimal('1.00')) // installment_amount)
                    num_installments = max(1, num_installments)
                    
                    remaining = net_amount
                    for i in range(num_installments):
                        if i == num_installments - 1:
                            amounts.append(remaining)
                        else:
                            amounts.append(installment_amount)
                            remaining -= installment_amount

        # --- ONE TIME PAYMENT ---
        elif fee_type in ['one_time', 'finance']:
            amounts = [net_amount]

        # 5. Build JSON Response
        for i, amt in enumerate(amounts, start=1):
            # Date Logic: Set to 10th of upcoming months
            base_date = start_date.replace(day=1)
            
            # If joined after 20th, first installment is next-next month, else next month
            # (Adjust this logic based on your company policy)
            if start_date.day >= 20:
                months_forward = i + 1
            else:
                months_forward = i
            
            future_date = base_date + relativedelta(months=months_forward)
            due_date = future_date.replace(day=10)

            structure.append({
                'installment': f"Installment {i}" if fee_type == 'installment' else "Full Payment",
                'due_date': due_date.strftime('%d-%b-%Y'),
                'amount': f"{amt:,.2f}"
            })

        return JsonResponse({
            'status': 'success',
            'net_amount': f"{net_amount:,.2f}",
            'structure': structure
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def refresh_student_fee_structure(request, pk):
    student = get_object_or_404(Admission, pk=pk)

    refresh_fee_structure_for_student(student)

    return JsonResponse({
        "success": True,
        "message": "Fee structure refreshed successfully"
    })


@login_required
@require_POST
def bulk_refresh_fee_structure(request):
    """
    Refresh fee structure for filtered students
    """
    ids = request.POST.getlist("ids[]")

    qs = Admission.objects.filter(id__in=ids) if ids else Admission.objects.all()
    count = refresh_fee_structure_queryset(qs)

    return JsonResponse({
        "success": True,
        "updated": count,
        "message": f"{count} students fee structure refreshed"
    })


def get_latest_admission_api(request):
    # Reduced threshold to 1 minute to keep it "Live"
    time_threshold = timezone.now() - timedelta(minutes=1)
    latest = Admission.objects.filter(
        updated__gte=time_threshold,
        care_of__isnull=False 
    ).select_related('care_of', 'branch', 'course').order_by('-updated').first()

    if latest:
        tele_name = latest.care_of.get_full_name() or latest.care_of.username
        return JsonResponse({
            "found": True,
            "id": latest.id,
            "update_key": f"{latest.id}", 
            "student_name": latest.fullname(),
            "telecaller": tele_name,
            "branch": latest.branch.name,
            "course": latest.course.name if latest.course else "General Program",
            # --- NEW TIME SYNC FIELDS ---
            "timestamp": int(latest.updated.timestamp()), 
            "server_now": int(timezone.now().timestamp())
        })
    return JsonResponse({"found": False})
    

class AllAdmissionListView(mixins.HybridListView):
    model = Admission
    table_class = tables.AdmissionTable
    filterset_fields = {
        'course': ['exact'], 
        'branch': ['exact'], 
        'batch': ['exact'],
        'batch_type': ['exact'],
        'admission_number': ['exact'], 
        'admission_date': ['exact'],
        'stage_status': ['exact'],
        'course_mode': ['exact']
    }
    permissions = ()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_all_admission"] = True
        return context

    
class AdmissionListView(mixins.HybridListView):
    template_name = "admission/admission_list.html"
    model = Admission
    table_class = tables.AdmissionTable
    filterset_fields = {
        'course': ['exact'], 
        'branch': ['exact'], 
        'batch': ['exact'],
        'batch_type': ['exact'],
        'admission_number': ['exact'], 
        'admission_date': ['exact'],
        'stage_status': ['exact'],
        'course_mode': ['exact'],
        'care_of': ['exact'],
    }
    permissions = ()

    def get_queryset(self):
        queryset = super().get_queryset().select_related('user') 
        
        if self.request.user.usertype in ["admin_staff", "ceo", "cfo", "coo", "hr", "cmo", "mentor"] or self.request.user.is_superuser:
            pass
        elif self.request.user.usertype == "teacher":
            queryset = queryset.filter(
                branch=self.request.user.branch,
                course=self.request.user.employee.course
            )
        else:
            queryset = queryset.filter(branch=self.request.user.branch)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_students"] = True
        context["placement_sources"] = choices.PLACEMENT_SOURCE_CHOICES
        context["stage_choices"] = choices.STUDENT_STAGE_STATUS_CHOICES
        qs = context["filter"].qs
        base_qs = self.get_queryset() 

        total_students_count = base_qs.count()
        active_stage_qs = base_qs.filter(is_active=True, stage_status="active")
        online_count = active_stage_qs.filter(course_mode="online").count()
        offline_count = active_stage_qs.filter(course_mode="offline").count()

        active_students_count_qs = base_qs.filter(is_active=True).values("stage_status").annotate(count=Count("id"))
        inactive_count = base_qs.filter(Q(is_active=False) | Q(stage_status="inactive")).count()
        counts_dict = {row["stage_status"]: row["count"] for row in active_students_count_qs}
        counts_dict["inactive"] = inactive_count
        for choice_value, _ in choices.STUDENT_STAGE_STATUS_CHOICES:
            counts_dict.setdefault(choice_value, 0)

        base_url = reverse("admission:admission_list")
        course_mode = self.request.GET.get("course_mode")
        stage_status = self.request.GET.get("stage_status")

        # URLs
        total_url = base_url
        online_url = f"{base_url}?{urlencode({'course_mode':'online', 'stage_status': stage_status} if stage_status else {'course_mode':'online'})}"
        offline_url = f"{base_url}?{urlencode({'course_mode':'offline', 'stage_status': stage_status} if stage_status else {'course_mode':'offline'})}"

        # Stage cards URLs
        stage_cards = []
        for key, val in list(choices.STUDENT_STAGE_STATUS_CHOICES) + [("inactive","Inactive")]:
            params = {}
            if course_mode:
                params["course_mode"] = course_mode
            params["stage_status"] = key
            url = f"{base_url}?{urlencode(params)}"
            stage_cards.append({
                "key": key,
                "label": val,
                "count": counts_dict.get(key,0),
                "url": url,
            })

        context.update({
            "total_students": total_students_count,
            "online_students": online_count,
            "offline_students": offline_count,
            "status_counts": counts_dict,
            "stage_cards": stage_cards,
            "total_url": total_url,
            "online_url": online_url,
            "offline_url": offline_url,
        })
        return context
    

class InactiveAdmissionListView(mixins.HybridListView):
    template_name = "admission/admission_list.html"
    model = Admission
    table_class = tables.AdmissionTable
    filterset_fields = {
        'course': ['exact'], 
        'branch': ['exact'], 
        'batch': ['exact'],
        'admission_number': ['exact'], 
        'admission_date': ['exact'],
        'stage_status': ['exact'],
        'course_mode': ['exact']
    }
    permissions = ("branch_staff", "teacher", "admin_staff", "is_superuser", "mentor", "ceo","cfo","coo","hr","cmo")

    def get_queryset(self):
        user = self.request.user
        queryset = Admission.objects.filter(is_active=False)
        
        if user.usertype in ["admin_staff", "ceo","cfo","coo","hr","cmo","mentor"] or user.is_superuser:
            pass
        else :
            queryset = queryset.filter(branch=user.branch)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        inactive_student = Admission.objects.filter(is_active=False)

        if self.request.user.usertype in ["admin_staff", "ceo","cfo","coo","hr","cmo"] or self.request.user.is_superuser:
            qs = inactive_student
        elif self.request.user.usertype == "teacher":
            qs = inactive_student
        else:
            qs = inactive_student
        
        online_students = inactive_student.filter(course_mode="online")
        offline_students = inactive_student.filter(course_mode="offline")


        context["title"] = "Inactive Students"
        context["is_admission"] = True
        context["is_inactive_students"] = True
        context["can_add"] = False
        context["total_students"] = qs.count()
        context['online_students'] = online_students.count()
        context['offline_students'] = offline_students.count()
        context["current_page_url"] = "admission:inactive_admission_list"
        return context
    

class CourseWiseAdmissionListView(mixins.HybridListView):
    model = Admission
    template_name = "admission/coursewise_admission_list.html"  
    filterset_fields = {
        'course': ['exact'], 
        'branch': ['exact'], 
        'batch': ['exact'],
        'admission_number': ['exact'], 
        'admission_date': ['exact'],
        'stage_status': ['exact'],
        'course_mode': ['exact']    
    }  
    permissions = ("branch_staff", "admin_staff", "is_superuser", "mentor", "ceo","cfo","coo","hr","cmo")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get active courses that have at least one active admission
        active_courses = (
            Course.objects.filter(is_active=True, admission__is_active=True, admission__stage_status="active")
            .distinct()
            .annotate(student_count=Count('admission', filter=Q(admission__is_active=True, admission__stage_status="active")))
        )

        context["title"] = "Students"
        context["courses"] = active_courses
        return context


class BatchTypeAdmissionListView(mixins.HybridListView):
    model = Admission
    template_name = "admission/batchtypewise_admission_list.html"
    filterset_fields = {
        'course': ['exact'],
        'branch': ['exact'],
        'batch': ['exact'],
        'admission_number': ['exact'],
        'admission_date': ['exact'],
        'stage_status': ['exact'],
        'course_mode': ['exact'],
    }
    permissions = ("branch_staff", "admin_staff", "is_superuser", "mentor", "ceo", "cfo", "coo", "hr", "cmo")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ✅ get selected course id from query params
        course_id = self.request.GET.get("course")

        # base queryset: only active admissions
        qs = Admission.objects.filter(is_active=True, stage_status="active")

        # ✅ if a course is selected, filter by that course
        if course_id:
            qs = qs.filter(course_id=course_id)
            try:
                selected_course = Course.objects.get(id=course_id)
                context["selected_course"] = selected_course
            except Course.DoesNotExist:
                selected_course = None

        # annotate student count by batch_type
        batch_counts = qs.values('batch_type').annotate(student_count=Count('id'))

        # Convert to dict for lookup
        batch_count_dict = {item['batch_type']: item['student_count'] for item in batch_counts}

        # Combine display names with counts
        batch_types_display = []
        for value, display in choices.BATCH_TYPE_CHOICES:
            count = batch_count_dict.get(value, 0)
            batch_types_display.append({
                "value": value,
                "display": display,
                "student_count": count
            })

        context["title"] = "Students"
        context["batch_types"] = batch_types_display
        return context
    

class AdmissionDetailView(mixins.HybridDetailView):
    queryset = Admission.objects.all()
    template_name = "admission/profile.html"
    permissions = ("branch_staff", "partner", "teacher", "admin_staff", "is_superuser", "mentor", "ceo","cfo","coo","hr","cmo")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admission = self.get_object()

        fields = admission.get_fields()

        formatted_fields = []
        for name, value in fields:
            if hasattr(value, "strftime"):  
                value = value.strftime("%m,%d,%Y")
            formatted_fields.append((name, value))

        context["formatted_fields"] = formatted_fields
        context['placement_status'] = admission.get_placement_status()
        context['age'] = admission.age() if admission.date_of_birth else None
        return context


class AdmissionCreateView(mixins.HybridCreateView):
    model = Admission
    form_class = forms.AdmissionPersonalDataForm
    permissions = ("branch_staff", "teacher", "admin_staff", "is_superuser", "mentor", "ceo","cfo","coo","hr","cmo")
    template_name = "admission/admission_form.html"
    exclude = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_admission"] = True
        context["is_personal"] = True
        context["is_create"] = True
        context["subtitle"] = "Personal Data"
        return context

    def get_success_url(self):
        if "save_and_next" in self.request.POST:
            url = build_url("admission:admission_update", kwargs={"pk": self.object.pk}, query_params={'type': 'parent'})
            return url
        return build_url("admission:admission_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        if hasattr(self.request.user, 'employee') and self.request.user.employee and self.request.user.employee.branch:
            branch = self.request.user.employee.branch
        else:
            form.add_error(None, "Current user has no branch assigned.")
            return self.form_invalid(form)

        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.branch = branch
        self.object.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_message(self, cleaned_data):
        return "Admission Personal Data Created Successfully"


class AdmissionUpdateView(mixins.HybridUpdateView):
    model = Admission
    permissions = ("branch_staff", "admin_staff", "mentor", "is_superuser", "ceo","cfo","coo","hr","cmo")
    template_name = "admission/admission_form.html"

    def form_valid(self, form):
        # Save the admission first
        response = super().form_valid(form)
        
        # Sync admission branch to user branch if user exists
        if self.object.user and self.object.branch:
            self.object.user.branch = self.object.branch
            self.object.user.save(update_fields=['branch'])
        
        return response

    def get_form_class(self):
        form_classes = {
            "parent": forms.AdmissionParentDataForm,
            "address": forms.AdmissionAddressDataForm,
            "official": forms.AdmissionOfficialDataForm,
            "personal": forms.AdmissionPersonalDataForm,
            "financial": forms.AdmissionFinancialDataForm
        }
        info_type = self.request.GET.get("type", "personal")
        return form_classes.get(info_type, forms.AdmissionPersonalDataForm)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        info_type = self.request.GET.get("type", "personal")
        subtitles = {
            "parent": "Parent Data",
            "address": "Address Data",
            "official": "Official Data",
            "financial": "Financial Data",
            "personal": "Personal Data"
        }
        urls = {
            "personal": build_url("admission:admission_update", kwargs={"pk": self.object.pk}, query_params={'type': 'personal'}),
            "parent": build_url("admission:admission_update", kwargs={"pk": self.object.pk}, query_params={'type': 'parent'}),
            "address": build_url("admission:admission_update", kwargs={"pk": self.object.pk}, query_params={'type': 'address'}),
            "official": build_url("admission:admission_update", kwargs={"pk": self.object.pk}, query_params={'type': 'official'}),
            "financial": build_url("admission:admission_update", kwargs={"pk": self.object.pk}, query_params={'type': 'financial'}),
        }
        context["title"] = "Edit Admission"
        context["subtitle"] = subtitles.get(info_type, "Personal Data")
        context['info_type_urls'] = urls
        context[f"is_{info_type}"] = True
        context["is_admission"] = True
        # context['batch_form'] = BatchForm(self.request.POST or None)
        return context
    
    def get_success_url(self):
        if "save_and_next" in self.request.POST:
            info_type = self.request.GET.get("type", "personal")
            if info_type == "official" and self.object.user:
                return build_url("accounts:student_user_update", kwargs={"pk": self.object.user.pk})
            else:
                urls = {
                    "personal": build_url("admission:admission_update", kwargs={"pk": self.object.pk}, query_params={'type': 'parent'}),
                    "parent": build_url("admission:admission_update", kwargs={"pk": self.object.pk}, query_params={'type': 'address'}),
                    "address": build_url("admission:admission_update", kwargs={"pk": self.object.pk}, query_params={'type': 'official'}),
                    "official": build_url("admission:admission_update", kwargs={"pk": self.object.pk}, query_params={'type': 'financial'}),
                    "financial": build_url("accounts:student_user_create", kwargs={"pk": self.object.pk}, query_params={'type': 'parent'}),
                }
                return urls.get(info_type, build_url("admission_detail", kwargs={"pk": self.object.pk}))
        return self.object.get_list_url()  

    def get_success_message(self, cleaned_data):
        info_type = self.request.GET.get("type", "personal")
        messages_dict = {
            "personal": "Personal data updated successfully.",
            "parent": "Parent data updated successfully.",
            "address": "Address data updated successfully.",
            "official": "Official data updated successfully.",
            "financial": "Financial data updated successfully.",
        }
        return messages_dict.get(info_type, "Data updated successfully.")


class AdmissionDeleteView(mixins.HybridDeleteView):
    model = Admission
    permissions = ("is_superuser", "teacher", "branch_staff")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # SOFT DELETE
        self.object.stage_status = "inactive"
        self.object.is_active = False
        self.object.save(update_fields=["stage_status", "is_active"])

        # Deactivate linked user
        if self.object.user:
            self.object.user.is_active = False
            self.object.user.save(update_fields=["is_active"])

        return HttpResponseRedirect(self.get_success_url())


class AdmissionProfileDetailView(mixins.DetailView):
    model = Admission
    template_name = "admission/profile_detail.html"
    permissions = ()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Student Profile"
        context["is_profile"] = True
        
        student = self.get_object()
        
        # 1. Get Approved Leaves
        approved_leaves = LeaveRequest.objects.filter(
            student=student,
            status='approved',
            is_active=True
        )
        
        approved_leave_dates = set()
        total_approved_leave_days = 0
        
        for leave in approved_leaves:
            current_date = leave.start_date
            while current_date <= leave.end_date:
                is_auto_holiday, _ = Holiday.is_auto_holiday(current_date)
                is_holiday = Holiday.objects.filter(
                    is_active=True, date=current_date
                ).filter(Q(scope="all") | Q(branch=student.branch)).exists()
                
                if not is_auto_holiday and not is_holiday:
                    approved_leave_dates.add(current_date)
                    total_approved_leave_days += 1
                current_date += timedelta(days=1)
        
        # 2. Get Valid Attendance Records (Active + Active Register)
        all_attendance_records = Attendance.objects.filter(
            student=student, 
            is_active=True,
            register__is_active=True
        ).select_related('register').order_by('-register__date') # Order by newest first
        
        valid_attendance_records = []
        leave_conflicted_records = []
        
        # Lists for structural display
        present_records_list = []
        absent_records_list = []
        
        # Sets for conflict detection
        dates_marked_present = set()
        dates_marked_absent = set()

        for record in all_attendance_records:
            if record.register.date in approved_leave_dates:
                leave_conflicted_records.append(record)
            else:
                valid_attendance_records.append(record)
                
                # Categorize for the display lists
                if record.status == 'Present':
                    present_records_list.append(record)
                    dates_marked_present.add(record.register.date)
                elif record.status == 'Absent':
                    absent_records_list.append(record)
                    dates_marked_absent.add(record.register.date)

        # 3. Calculate Statistics
        total_working_days = len(valid_attendance_records)
        total_present = len(present_records_list)
        total_absent = len(absent_records_list)
        total_late = len([r for r in valid_attendance_records if r.status == 'Late'])
        
        # 4. Identify Conflicts (Dates that are in both sets)
        conflicting_dates = dates_marked_present.intersection(dates_marked_absent)
        
        # Calculate percentages
        attendance_percentage = 0
        present_percentage = 0
        absent_percentage = 0
        
        if total_working_days > 0:
            attendance_percentage = round(((total_present + total_late) / total_working_days) * 100, 1)
            present_percentage = round((total_present / total_working_days) * 100, 1)
            absent_percentage = round((total_absent / total_working_days) * 100, 1)
        
        # Calendar Data
        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))
        calendar_days = self.get_calendar_data(student, year, month)
        
        context.update({
            'total_working_days': total_working_days,
            'total_present': total_present,
            'total_absent': total_absent,
            'total_late': total_late,
            'attendance_percentage': attendance_percentage,
            'present_percentage': present_percentage,
            'absent_percentage': absent_percentage,
            # New Context Variables for the Template
            'present_records_list': present_records_list,
            'absent_records_list': absent_records_list,
            'conflicting_dates': list(conflicting_dates), # Convert set to list for template
            # End New Context
            'calendar_days': calendar_days,
            'current_month': datetime(year, month, 1).strftime('%B'),
            'current_year': year,
            'total_approved_leaves': approved_leaves.count(),
            'total_approved_leave_days': total_approved_leave_days,
            'total_pending_leaves': LeaveRequest.objects.filter(student=student, status='pending', is_active=True).count(),
            'total_rejected_leaves': LeaveRequest.objects.filter(student=student, status='rejected', is_active=True).count(),
        })
        
        return context
    
    def get_calendar_data(self, student, year, month):
        # (Same as previous solution)
        approved_leaves = LeaveRequest.objects.filter(
            student=student,
            status='approved',
            is_active=True,
            start_date__lte=datetime(year, month, monthrange(year, month)[1]).date(),
            end_date__gte=datetime(year, month, 1).date()
        )
        
        approved_leave_dates = {}
        for leave in approved_leaves:
            current_date = leave.start_date
            while current_date <= leave.end_date:
                if current_date.year == year and current_date.month == month:
                    approved_leave_dates[current_date] = {
                        "type": "approved_leave",
                        "reason": leave.reason
                    }
                current_date += timedelta(days=1)
        
        attendance_records = Attendance.objects.filter(
            student=student,
            register__date__year=year,
            register__date__month=month,
            is_active=True,
            register__is_active=True
        ).select_related('register')
        
        holidays = Holiday.objects.filter(
            is_active=True,
            date__year=year,
            date__month=month
        ).filter(
            Q(scope="all") | Q(branch=student.branch)
        )
        
        attendance_by_date = {}
        for record in attendance_records:
            date_key = record.register.date
            if date_key in approved_leave_dates:
                attendance_by_date[date_key] = 'approved_leave'
            else:
                attendance_by_date[date_key] = record.status.lower()
        
        holiday_by_date = {}
        for holiday in holidays:
            if holiday.scope == "branch" and not holiday.branch.filter(id=student.branch.id).exists():
                continue
            holiday_by_date[holiday.date] = {
                "name": holiday.name,
                "is_auto": holiday.is_auto_holiday,
            }
        
        import calendar
        days_in_month = calendar.monthrange(year, month)[1]
        for day in range(1, days_in_month + 1):
            current_date_obj = datetime(year, month, day).date()
            is_auto_holiday, holiday_name = Holiday.is_auto_holiday(current_date_obj)
            if is_auto_holiday and current_date_obj not in holiday_by_date:
                holiday_by_date[current_date_obj] = {
                    "name": holiday_name, 
                    "is_auto": True
                }
        
        cal = calendar.Calendar(firstweekday=6)
        month_days = cal.monthdayscalendar(year, month)
        today = timezone.now().date()
        
        calendar_days = []
        for week in month_days:
            for day in week:
                if day == 0:
                    calendar_days.append({
                        'date': None, 
                        'status': 'empty',
                        'is_today': False,
                        'is_holiday': False
                    })
                else:
                    date = datetime(year, month, day).date()
                    is_today = (date == today)
                    
                    if date in holiday_by_date:
                        status = 'holiday'
                    elif date in approved_leave_dates:
                        status = 'approved_leave'
                    elif date in attendance_by_date:
                        status = attendance_by_date[date]
                    else:
                        status = 'normal'
                    
                    additional_info = None
                    if date in holiday_by_date:
                        additional_info = holiday_by_date[date]
                    elif date in approved_leave_dates:
                        additional_info = approved_leave_dates[date]
                    
                    calendar_days.append({
                        'date': date,
                        'status': status,
                        'is_today': is_today,
                        'is_holiday': (status == 'holiday'),
                        'is_approved_leave': (status == 'approved_leave'),
                        'holiday_info': additional_info
                    })
        
        return calendar_days
    

class DueStudentsListView(mixins.HybridListView):
    model = Admission 
    template_name = "admission/due_students_list.html"
    table_class = tables.DueStudentsTable
    filterset_fields = {'course': ['exact'], 'branch': ['exact'], 'batch': ['exact']}
    permissions = ("branch_staff", "admin_staff", "is_superuser", "mentor", "ceo", "cfo", "coo", "hr", "cmo")

    def get_queryset(self):
        # 1. Define Financial Stages (Same as Report View)
        FINANCIAL_STAGES = ["active", "inactive", "completed", "placed", "internship"]

        # 2. Start with Base Queryset of Students
        queryset = Admission.objects.filter(
            is_active=True,
            stage_status__in=FINANCIAL_STAGES
        ).select_related('course', 'branch', 'batch')

        # 3. Apply Student Status Filter
        selected_stage = self.request.GET.get('stage')
        if selected_stage and selected_stage in FINANCIAL_STAGES:
             queryset = queryset.filter(stage_status=selected_stage)

        # 4. Apply User Role Security
        user = self.request.user
        if user.usertype == "branch_staff":
            queryset = queryset.filter(branch=user.branch)

        # 5. Get filters
        course_id = self.request.GET.get('course')
        branch_id = self.request.GET.get('branch')
        batch_id = self.request.GET.get('batch')
        
        selected_year = self.request.GET.get('year')
        selected_month = self.request.GET.get('month')
        
        # Defaults: If no date filter, show Current Month
        today = timezone.now().date()
        if not selected_year and not selected_month:
            selected_year = str(today.year)
            selected_month = str(today.month)

        # 6. Apply Dropdown Filters
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        if batch_id:
            queryset = queryset.filter(batch_id=batch_id)
        
        # 7. Build FeeStructure Filter (The Core Fix)
        # We look for Active Fee Structures where Amount > Paid Amount
        # We use strict math comparison rather than just 'is_paid=False' to catch partial mismatched flags
        fee_filter = Q(
            feestructure__is_active=True,
            feestructure__amount__gt=F('feestructure__paid_amount')
        )

        # Filter by Year
        if selected_year and selected_year != 'all':
            fee_filter &= Q(feestructure__due_date__year=int(selected_year))
        
        # Filter by Month
        if selected_month and selected_month != 'all':
            fee_filter &= Q(feestructure__due_date__month=int(selected_month))

        # NOTE: If 'all' year and 'all' month are selected, we DO NOT filter by date.
        # This allows Future dues to show up, matching the "Report View" which shows global balance.
        # If you strictly want "Overdue" (Past), uncomment the line below:
        # if selected_year == 'all' and selected_month == 'all':
        #     fee_filter &= Q(feestructure__due_date__lt=today)

        # Apply the filter and distinct
        queryset = queryset.filter(fee_filter).distinct()
        
        # 8. Annotate Total Due Amount
        # Calculates the sum of remaining balance for the filtered fee structures
        queryset = queryset.annotate(
            total_due_amount=Sum(
                Case(
                    When(fee_filter, 
                         then=F('feestructure__amount') - F('feestructure__paid_amount')),
                    default=0,
                    output_field=DecimalField()
                )
            )
        )
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Due Students"
        context["is_due_students"] = True
        context["can_add"] = False
        
        today = timezone.now().date()
        
        selected_year = self.request.GET.get('year', str(today.year))
        selected_month = self.request.GET.get('month', str(today.month))
        
        # Year Options
        current_year = today.year
        year_range = range(current_year - 5, current_year + 3)
        year_options = [{'value': 'all', 'label': 'All Years'}]
        for y in sorted(year_range, reverse=True):
            year_options.append({'value': str(y), 'label': str(y)})

        # Month Options
        import calendar
        month_options = [{'value': 'all', 'label': 'All Months'}]
        for i in range(1, 13):
            month_options.append({
                'value': str(i),
                'label': calendar.month_name[i]
            })

        selected_course = self.request.GET.get('course')
        selected_branch = self.request.GET.get('branch')
        selected_batch = self.request.GET.get('batch')
        selected_stage = self.request.GET.get('stage')
        
        user = self.request.user
        context['courses'] = Course.objects.filter(is_active=True)
        
        if user.usertype == "branch_staff":
            context['branches'] = Branch.objects.filter(id=user.branch.id)
            base_batch_qs = Batch.objects.filter(branch=user.branch, is_active=True)
        else:
            context['branches'] = Branch.objects.filter(is_active=True)
            base_batch_qs = Batch.objects.filter(is_active=True)
        
        if selected_course and selected_branch:
            context['batches'] = base_batch_qs.filter(course_id=selected_course, branch_id=selected_branch)
        elif selected_course:
             context['batches'] = base_batch_qs.filter(course_id=selected_course)
        elif selected_branch:
             context['batches'] = base_batch_qs.filter(branch_id=selected_branch)
        else:
            context['batches'] = base_batch_qs

        stage_options = [
            ('active', "Active / Ongoing"), 
            ('inactive', "Inactive"),
            ('completed', "Course Completed"), 
            ('placed', "Placed"), 
            ('internship', "On Internship"),  
        ]

        context['year_options'] = year_options
        context['month_options'] = month_options
        context['selected_year'] = selected_year
        context['selected_month'] = selected_month
        context['selected_course'] = int(selected_course) if selected_course else None
        context['selected_branch'] = int(selected_branch) if selected_branch else None
        context['selected_batch'] = int(selected_batch) if selected_batch else None
        context['selected_stage'] = selected_stage
        context['stage_options'] = stage_options
        
        return context


class StudentCertificateView(PDFView):
    template_name = "admission/student_certificate.html"
    model = Admission

    pdfkit_options = {
        "page-width": "8.27in",
        "page-height": "11.69in",
        "margin-top": "0",
        "margin-bottom": "0",
        "margin-left": "0",
        "margin-right": "0",
        "encoding": "UTF-8",
        "disable-smart-shrinking": "",
        "zoom": "1",
        "print-media-type": "",
    }

    def get_object(self):
        return get_object_or_404(Admission, pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        instance = self.get_object()

        context["title"] = "Certificate"
        context["instance"] = instance

        context["certificate_image_url"] = self.request.build_absolute_uri(
            static("app/assets/images/certificate_template.jpg")
        )
        context["poppins_regular"] = self.request.build_absolute_uri(
            static("app/assets/font/Poppins/Poppins-Regular.ttf")
        )
        context["poppins_bold"] = self.request.build_absolute_uri(
            static("app/assets/font/Poppins/Poppins-Bold.ttf")
        )

        course_start_date = instance.course_start_date
        end_date = course_start_date + relativedelta(months=4)

        context["end_date"] = end_date.strftime("%d %B %Y")
        context["current_date"] = timezone.now().strftime("%d %B %Y")

        if instance.course.name == "Digital Marketing":
            context["certificate_content"] = (
                f"This is to proudly certify that <strong>{instance.fullname()}</strong> has successfully "
                f"completed the professional course <strong>AI Integrated Digital Marketing</strong> offered by "
                f"Oxdu Integrated Media School, held from "
                f"{course_start_date.strftime('%d %B %Y')} to "
                f"{end_date.strftime('%d %B %Y')}. "
                f"We commend their dedication and effort in acquiring advanced knowledge "
                f"and practical skills in Digital Marketing, enhanced by cutting-edge "
                f"artificial intelligence technologies."
            )

        elif instance.course.name == "Graphic Designing":
            context["certificate_content"] = (
                f"This is to proudly certify that <strong>{instance.fullname()}</strong> has successfully "
                f"completed the professional course <strong>AI Integrated Graphic Designing</strong> offered by "
                f"Oxdu Integrated Media School, held from "
                f"{course_start_date.strftime('%d %B %Y')} to "
                f"{end_date.strftime('%d %B %Y')}. "
                f"We commend their dedication and effort in acquiring advanced knowledge  "
                f"and practical skills in Graphic Designing, enhanced by cutting-edge "
                f"artificial intelligence technologies."
            )

        return context

    def get_filename(self):
        
        instance = self.get_object()
        return f"{instance.first_name}_{instance.last_name}_certificate.pdf"


class LeadList(mixins.HybridListView):
    model = AdmissionEnquiry
    context_object_name = 'leads'
    table_class = tables.AdmissionEnquiryTable
    branch_filter = None

    def get_queryset(self):
        queryset = AdmissionEnquiry.objects.filter(is_active=True)

        status = self.request.GET.get('status')
        branch = self.request.GET.get('branch')
        course = self.request.GET.get('course')
        enquiry_type = self.request.GET.get('enquiry_type')

        if status:
            queryset = AdmissionEnquiry.objects.filter(status=status)

        if branch:
            queryset = AdmissionEnquiry.objects.filter(branch=branch)

        if course:
            queryset = AdmissionEnquiry.objects.filter(course=course)

        if enquiry_type:
            queryset = AdmissionEnquiry.objects.filter(enquiry_type=enquiry_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = "Leads"
        context['filter_status'] = self.request.GET.get('status', '')
        context['filter_branch'] = self.request.GET.get('branch', '')
        context['filter_course'] = self.request.GET.get('course', '')
        context['filter_enquiry_type'] = self.request.GET.get('enquiry_type', '')
        context['can_add'] = False

        return context


class PublicLeadListView(mixins.HybridListView):
    template_name = "admission/enquiry/list.html"
    model = AdmissionEnquiry
    table_class = tables.PublicEnquiryListTable
    filterset_fields = {'city': ['exact'], 'branch': ['exact'], 'date': ['exact'], 'enquiry_type': ['exact'],}
    permissions = ("branch_staff", "partner", "admin_staff", "is_superuser", "tele_caller", "sales_head", "ceo","cfo","coo","hr","cmo", "mentor")
    branch_filter = False

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.request = self.request 
        return table

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        queryset = queryset.filter(tele_caller__isnull=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Public Leads"
        context["is_lead"] = True
        context["is_public_lead"] = True  
        context["tele_callers"] = Employee.objects.filter(user__usertype="tele_caller")
        user_type = self.request.user.usertype
        context["can_add"] = user_type in ("sales_head", "admin_staff", "branch_staff", "ceo","cfo","coo","hr","cmo")
        context["new_link"] = reverse_lazy("admission:admission_enquiry_create")    
        return context


class AssignedLeadListView(mixins.HybridListView):
    model = AdmissionEnquiry
    table_class = tables.AdmissionEnquiryTable
    filterset_fields = {'course': ['exact'], 'branch': ['exact'], 'status': ['exact'], 'enquiry_type': ['exact'], 'date': ['exact']}
    permissions = ("branch_staff", "admin_staff", "is_superuser", "tele_caller", "mentor", "sales_head", "ceo","cfo","coo","hr","cmo")
    branch_filter = False

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(tele_caller__isnull=False, is_active=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            "title": "Assigned Leads List",
            "is_assigned_lead": True,
            "can_add": False
        })

        return context


class MyleadListView(mixins.HybridListView):
    template_name = "admission/enquiry/my_lead_list.html"
    model = AdmissionEnquiry
    table_class = tables.AdmissionEnquiryTable
    filterset_fields = ['course', 'branch', 'status', 'enquiry_type']
    permissions = ("branch_staff", "admin_staff", "is_superuser", "tele_caller", "mentor", "sales_head", "ceo","cfo","coo","hr","cmo")
    branch_filter = False

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_superuser:
            if hasattr(user, "employee") and user.employee is not None:
                queryset = queryset.filter(tele_caller=user.employee)
            else:
                queryset = queryset.none()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Get the filtered queryset and current filter values from URL
        filtered_qs = self.filterset.qs 
        selected_status = self.request.GET.get('status')
        selected_type = self.request.GET.get('enquiry_type')
        selected_branch = self.request.GET.get('branch')
        selected_course = self.request.GET.get('course')
        
        # 2. Pre-calculate counts
        status_counts = {i['status']: i['count'] for i in filtered_qs.values('status').annotate(count=Count('id'))}
        type_counts = {i['enquiry_type']: i['count'] for i in filtered_qs.values('enquiry_type').annotate(count=Count('id'))}
        branch_counts = {i['branch_id']: i['count'] for i in filtered_qs.values('branch_id').annotate(count=Count('id'))}
        course_counts = {i['course_id']: i['count'] for i in filtered_qs.values('course_id').annotate(count=Count('id'))}

        # Helper function to sort: Active item gets True (1), others False (0). 
        # Reverse=True puts 1 (Active) at the top.
        def sort_summary(items, selected_val, key_name):
            if not selected_val:
                return items
            return sorted(items, key=lambda x: str(x.get(key_name)) == str(selected_val), reverse=True)

        # 3. Status Summary
        from .models import ENQUIRY_STATUS, ENQUIRY_TYPE_CHOICES
        status_list = [
            {'key': str(key), 'label': label, 'count': status_counts.get(key, 0)} 
            for key, label in ENQUIRY_STATUS
        ]
        context['status_summary'] = sort_summary(status_list, selected_status, 'key')

        # 4. Type Summary
        type_list = [
            {'key': str(key), 'label': label, 'count': type_counts.get(key, 0)} 
            for key, label in ENQUIRY_TYPE_CHOICES
        ]
        context['type_summary'] = sort_summary(type_list, selected_type, 'key')
        
        # 5. Branch Summary
        from branches.models import Branch # Ensure Branch is imported
        all_branches = Branch.objects.all() 
        branch_list = [
            {'id': str(b.id), 'name': b.name, 'count': branch_counts.get(b.id, 0)}
            for b in all_branches
        ]
        context['branch_summary'] = sort_summary(branch_list, selected_branch, 'id')

        # 6. Course Summary
        from masters.models import Course # Ensure Course is imported
        all_courses = Course.objects.all()
        course_list = [
            {'id': str(c.id), 'name': c.name, 'count': course_counts.get(c.id, 0)}
            for c in all_courses
        ]
        context['course_summary'] = sort_summary(course_list, selected_course, 'id')
        
        context.update({
            "title": "Lead Management Dashboard",
            "can_add": self.request.user.usertype == "tele_caller",
            "new_link": reverse_lazy("admission:admission_enquiry_create"),
            "total_count": filtered_qs.count(),
        })
        return context

    
class AdmissionEnquiryView(mixins.HybridListView):
    model = AdmissionEnquiry
    table_class = tables.AdmissionEnquiryTable
    filterset_fields = {'course': ['exact'], 'branch': ['exact'],'status': ['exact'],'date': ['exact']}
    permissions = ("branch_staff", "partner", "admin_staff", "is_superuser", "tele_caller", "mentor", "sales_head", "ceo","cfo","coo","hr","cmo")
    branch_filter = False

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.usertype == "branch_staff":
            queryset = queryset.filter(status="demo", branch=user.branch)
        elif user.usertype == "mentor":
            queryset = queryset.filter(status="demo")
        elif user.usertype == "tele_caller":
            queryset = queryset.filter(tele_caller=user.employee)
        elif user.usertype in ["admin_staff", "ceo","cfo","coo","hr","cmo", "partner"] or user.is_superuser:
            queryset = queryset.filter(tele_caller__isnull=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_type = self.request.user.usertype

        context.update({
            "title": "Leads",
            "is_lead": True,
            "is_enquiry": True,
            "can_add": user_type in ["tele_caller", "admin_staff", "branch_staff", "ceo","cfo","coo","hr","cmo"] or self.request.user.is_superuser,
            "new_link": reverse_lazy("admission:admission_enquiry_create"),
        })

        return context
    

class AdmissionEnquiryDetailView(mixins.HybridDetailView):
    model = AdmissionEnquiry
    permissions = ("branch_staff", "partner", "tele_caller", "admin_staff", "is_superuser", "sales_head", "ceo","cfo","coo","hr","cmo", "mentor")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lead Details"
        return context
    

class AdmissionEnquiryCreateView(mixins.HybridCreateView):
    model = AdmissionEnquiry
    # Permissions needed to access the view
    permissions = ("branch_staff", "tele_caller", "admin_staff", "is_superuser", "sales_head", "ceo", "cfo", "coo", "hr", "cmo", "mentor")
    # 'branch' is NOT excluded, so it will appear in the form if the user has permission
    exclude = ('tele_caller',)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_admission"] = True
        context["is_enquiry"] = True  
        context["is_create"] = True
        context["title"] = "New Lead"
        return context

    def form_valid(self, form):
        user = self.request.user
        
        if user.usertype == "tele_caller" and hasattr(user, "employee") and user.employee is not None:
            form.instance.tele_caller = user.employee
        else:
            form.instance.tele_caller = None

        self.object = form.save()

        return HttpResponseRedirect(self.get_success_url())
        
    def get_success_url(self):
        if self.request.user.usertype in ["tele_caller", "branch_staff"]:
            return reverse("admission:my_lead_list")
        else:
            return reverse("admission:admission_enquiry")


class AdmissionEnquiryUpdateView(mixins.HybridUpdateView):
    model = AdmissionEnquiry
    form_class = AdmissionEnquiryForm
    permissions = ("branch_staff", "tele_caller", "admin_staff", "is_superuser", "sales_head", "ceo", "cfo", "coo", "hr", "cmo", "mentor")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_admission"] = True
        context["is_enquiry"] = True
        context["title"] = "Edit Lead"
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        
        if not (user.is_superuser or user.usertype in ["admin_staff", "sales_head", "ceo", "cfo", "coo", "hr", "cmo"]):
            if 'tele_caller' in form.fields:
                del form.fields['tele_caller']
        return form

    def form_valid(self, form):
        user = self.request.user
        
        if hasattr(user, "employee") and user.usertype == "tele_caller":
            if not form.instance.tele_caller:
                form.instance.tele_caller = user.employee

        self.object = form.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self.request.user.usertype in ["tele_caller", "branch_staff"]:
            return reverse("admission:my_lead_list")
        else:
            return self.object.get_list_url()
    

class AdmissionEnquiryDeleteView(mixins.HybridDeleteView):
    model = AdmissionEnquiry
    permissions = ("branch_staff", "tele_caller", "admin_staff", "is_superuser", "sales_head", "ceo","cfo","coo","hr","cmo", "mentor")


class DeleteUnassignedLeadsView(View):
    def post(self, request):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            count, _ = AdmissionEnquiry.objects.filter(tele_caller__isnull=True).delete()
            return JsonResponse({'message': f'{count} unassigned leads deleted successfully.'})
        return JsonResponse({'error': 'Invalid request'}, status=400)


class AttendanceRegisterListView(mixins.HybridListView):
    model = AttendanceRegister
    table_class = tables.AttendanceRegisterTable 
    filterset_fields = {'batch': ['exact'],'date': ['exact'], 'course': ['exact'], 'branch': ['exact'],}  
    permissions = ("")
    template_name = 'admission/attendance/list.html'
    
    def get_queryset(self):
        user = self.request.user
        branch = self.request.session.get('branch', getattr(user, 'branch', None))
        attendance_register = AttendanceRegister.objects.filter(is_active=True)

        if user.usertype in ["admin_staff", "ceo","cfo","coo","hr","cmo"] or user.is_superuser:
            return attendance_register.filter(branch=branch)

        elif user.usertype == 'teacher':
            if hasattr(user, 'employee'):
                employee = user.employee
                teacher_courses = Course.objects.filter(employee=employee)
                if teacher_courses.exists():
                    return attendance_register.filter(branch=branch, course__in=teacher_courses)
        
        return attendance_register.filter(branch=branch)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.usertype == 'teacher':
            context["batches"] = Batch.objects.filter(is_active=True, course=self.request.user.employee.course, branch=self.request.user.branch)
        else:
            context["batches"] = Batch.objects.filter(is_active=True, branch=self.request.user.branch)
        context["title"] = "Attendance"
        context['is_admission'] = True
        context["is_attendance"] = True  
        context['is_batch_attendance'] = True
        user_type = self.request.user.usertype
        context["can_add"] = user_type in ("teacher",)
        return context
    
    
class AttendanceRegisterDetailView(mixins.HybridDetailView):
    model = AttendanceRegister
    permissions = ()
    template_name = "admission/attendance/object_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Attendance Register Details"
        return context
    
    
class AttendanceRegisterCreateView(mixins.HybridCreateView):
    model = AttendanceRegister
    permissions = ()
    form_class = forms.AttendanceRegisterForm
    template_name = "admission/attendance/object_form.html"

    def get_form(self):
        form = self.form_class(**self.get_form_kwargs())
        form.fields['date'].initial = date.today()

        user = self.request.user

        if user.usertype == 'teacher':
            try:
                employee = user.employee  
                teacher_courses = form.fields['course'].queryset.filter(employee=employee)

                if teacher_courses.exists():
                    form.fields['course'].queryset = teacher_courses
                    form.fields['course'].initial = teacher_courses.first()  
            except AttributeError:
                pass
        else:
            form.fields['course'].queryset = form.fields['course'].queryset.filter(is_active=True)

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batch = Batch.objects.get(pk=self.kwargs['pk'])
        context["batch"] = batch
        context["title"] = f"{batch.batch_name} Attendance"

        user = self.request.user
        course_id = self.request.GET.get('course')

        if user.usertype == 'teacher':
            try:
                employee = user.employee
                teacher_courses = Course.objects.filter(employee=employee)
                context["teacher_courses"] = teacher_courses 

                if teacher_courses.exists() and not course_id:
                    course_id = teacher_courses.first().id 

            except AttributeError:
                context["teacher_courses"] = None
        
        if hasattr(user, 'branch'):
            students = Admission.objects.filter(is_active=True, batch=batch, branch=user.branch)
        else:
            students = Admission.objects.filter(is_active=True, batch=batch)
        
        if course_id:
            students = students.filter(course_id=course_id)

        initial_data = [{'student_name': student, 'student_pk': student.id, 'status': 'Absent'} for student in students]

        AttendanceFormSet = formset_factory(AttendanceForm, extra=0)

        if self.request.POST:
            context['attendance_formset'] = AttendanceFormSet(self.request.POST)
        else:
            context['attendance_formset'] = AttendanceFormSet(initial=initial_data)

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        attendance_formset = context['attendance_formset']
        
        batch = Batch.objects.get(pk=self.kwargs['pk'])
        branch = batch.branch  
        date = form.cleaned_data.get('date')

        if AttendanceRegister.objects.filter(batch=batch, date=date, is_active=True).exists():
            form.add_error(None, "Attendance for this batch on this date already exists.")
            return self.form_invalid(form)

        try:
            with transaction.atomic():
                form.instance.batch = batch
                form.instance.branch = branch  
                data = form.save()

                if attendance_formset.is_valid():
                    for attendance_form in attendance_formset:
                        student_pk = attendance_form.cleaned_data.get('student_pk')
                        student = Admission.objects.get(pk=student_pk)
                        form_data = attendance_form.save(commit=False)
                        form_data.student = student
                        form_data.register = data
                        form_data.save()
                else:
                    # Print formset errors for debugging
                    print("Attendance formset errors:", attendance_formset.errors)
                    context['formset_errors'] = attendance_formset.errors
                    return render(self.request, self.template_name, context)

        except IntegrityError:
            form.add_error(None, "Attendance for this batch on this date already exists.")
            return self.form_invalid(form)

        return HttpResponseRedirect(self.get_success_url())
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        batch = Batch.objects.get(pk=self.kwargs['pk'])
        kwargs['batch'] = batch
        return kwargs
    
    def get_success_url(self):
        return reverse('admission:attendance_register_list')
    

class AttendanceRegisterUpdateView(mixins.HybridUpdateView):
    model = AttendanceRegister
    permissions = ("administration", "teacher", "accounting_staff", "finance", "worker", "hrm")
    exclude = ("batch", "branch", "course",)
    template_name = "admission/attendance/object_update.html"
    form_class = forms.AttendanceRegisterForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Attendance Register"

        # Fetch the attendance register instance and its batch
        attendance_register = self.object
        batch = attendance_register.batch
        students = Admission.objects.filter(is_active=True, batch=batch)

        # Fetch attendance records for this register
        attendance_queryset = Attendance.objects.filter(register=attendance_register)

        # Define the formset factory
        AttendanceUpdateFormSet = inlineformset_factory(
            AttendanceRegister, Attendance, form=AttendanceUpdateForm, extra=0, can_delete=True
        )

        if self.request.POST:
            context['attendance_formset'] = AttendanceUpdateFormSet(
                self.request.POST, instance=attendance_register
            )
        else:
            if attendance_queryset.exists():
                # If attendance records exist, use them
                context["attendance_formset"] = AttendanceUpdateFormSet(instance=attendance_register)
            else:
                # If no attendance records exist, create an initial dataset with students
                initial_data = [
                    {"student": student, "register": attendance_register, "status": "Absent"}
                    for student in students
                ]
                context["attendance_formset"] = AttendanceUpdateFormSet(initial=initial_data, instance=attendance_register)

        # Ensure students are available in context
        context["students"] = students
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        attendance_formset = context['attendance_formset']
        self.object = form.save()
        if attendance_formset.is_valid():
            attendance_formset.instance = self.object  
            attendance_formset.save()
            
        else:
            print('attendance_formset=',attendance_formset.errors)
            return render(self.request, self.template_name, context)
        return super().form_valid(form)
    

class AttendanceRegisterDeleteView(mixins.HybridDeleteView):
    permissions = ("admin_staff", "is_superuser", "teacher", "ceo","cfo","coo","hr","cmo", "mentor")  
    model = AttendanceRegister

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        return super().delete(request, *args, **kwargs)


class StudentAttendanceTableView(mixins.HybridTemplateView):
    template_name = "admission/attendance/attendance-table.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = now().date()

        course_id = self.request.GET.get('course')
        branch_id = self.request.GET.get('branch')
        batch_id = self.request.GET.get('batch')
        month = self.request.GET.get('month', today.month)
        year = self.request.GET.get('year', today.year)

        try:
            month = int(month)
            year = int(year)
        except (ValueError, TypeError):
            month = today.month
            year = today.year

        if month < 1 or month > 12:
            month = today.month
        if year < 2000 or year > today.year + 1:
            year = today.year

        selected_date = date(year, month, 1)
        days_in_selected_month = calendar.monthrange(year, month)[1]
        days_in_month_list = [f"{day:02d}" for day in range(1, days_in_selected_month + 1)]

        student_query = Admission.objects.filter(
            is_active=True,
            stage_status="active",
            batch__status="in_progress"
        )
        if course_id:
            student_query = student_query.filter(course_id=course_id)
        if branch_id:
            student_query = student_query.filter(branch_id=branch_id)
        if batch_id:
            student_query = student_query.filter(batch_id=batch_id)

        batch_query = Batch.objects.filter(is_active=True, status="in_progress")
        if course_id:
            batch_query = batch_query.filter(course_id=course_id)
        if branch_id:
            batch_query = batch_query.filter(branch_id=branch_id)
        filtered_batches = batch_query.order_by('batch_name')

        selected_month_attendance = Attendance.objects.filter(
            register__date__month=month,
            register__date__year=year,
            is_active=True
        )
        if course_id or branch_id or batch_id:
            filtered_student_ids = student_query.values_list('id', flat=True)
            selected_month_attendance = selected_month_attendance.filter(student_id__in=filtered_student_ids)

        present_count = selected_month_attendance.filter(status="Present").count()
        absent_count = selected_month_attendance.filter(status="Absent").count()

        today_attendance = Attendance.objects.filter(
            register__date=today,
            is_active=True
        )
        if course_id or branch_id or batch_id:
            today_attendance = today_attendance.filter(student_id__in=filtered_student_ids)

        today_present_count = today_attendance.filter(status="Present").count()
        today_absent_count = today_attendance.filter(status="Absent").count()

        courses = Course.objects.all()
        branches = Branch.objects.all()

        batches_for_attendance = []
        courses_for_attendance = []
        branches_for_attendance = []
        
        if user.usertype == "mentor":
            batches_for_attendance = Batch.objects.filter(
                is_active=True,
                status="in_progress"
            ).order_by('batch_name')
            courses_for_attendance = Course.objects.all()
            branches_for_attendance = Branch.objects.all()

        current_year = today.year
        year_choices = list(range(current_year - 5, current_year + 2))

        month_choices = [
            (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
            (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
            (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
        ]

        selected_month_name = dict(month_choices).get(month, 'Unknown')
        current_month_name = dict(month_choices).get(today.month, 'Unknown')

        context.update({
            'present_count': present_count,
            'absent_count': absent_count,
            'today_present_count': today_present_count,
            'today_absent_count': today_absent_count,
            'days_in_month': days_in_month_list,
            'student_count': student_query.count(),
            'courses': courses,
            'branches': branches,
            'filtered_batches': filtered_batches,
            'selected_course': course_id,
            'selected_branch': branch_id,
            'selected_batch': batch_id,
            'selected_month': month,
            'selected_year': year,
            'selected_month_name': selected_month_name,
            'current_month_name': current_month_name,
            'month_choices': month_choices,
            'year_choices': year_choices,
            'current_month': today.month,
            'current_year': today.year,
            "is_student_attendance_table": True,
            'current_date_obj': today,
            'batches_for_attendance': batches_for_attendance,
            'courses_for_attendance': courses_for_attendance,
            'branches_for_attendance': branches_for_attendance,
            'is_mentor': user.usertype == "mentor",
        })

        return context
    

class AttendanceTableDataAPIView(View):
    def get(self, request):
        try:
            page = int(request.GET.get('page', 1))
            per_page = int(request.GET.get('per_page', 50))
            
            course_id = request.GET.get('course')
            branch_id = request.GET.get('branch')
            batch_id = request.GET.get('batch')
            status_filter = request.GET.get('status')
            today_only = request.GET.get('today')
            
            today = now().date()
            month = request.GET.get('month', today.month)
            year = request.GET.get('year', today.year)
            
            try:
                month = int(month)
                year = int(year)
            except (ValueError, TypeError):
                month = today.month
                year = today.year
            
            if month < 1 or month > 12:
                month = today.month
            if year < 2000 or year > today.year + 1:
                year = today.year
            
            student_query = Admission.objects.select_related(
                "course", "branch", "user", "batch"
            ).filter(
                is_active=True,
                batch__status="in_progress"
            )

            # Filter students: Show if active OR (if inactive) the status change happened during/after this month start
            start_month_date = date(year, month, 1)
            student_query = student_query.filter(
                Q(stage_status="active") | 
                Q(studentstagestatushistory__created__gte=start_month_date)
            ).distinct()
            
            if course_id and course_id != 'all':
                student_query = student_query.filter(course_id=course_id)
            if branch_id and branch_id != 'all':
                student_query = student_query.filter(branch_id=branch_id)
            if batch_id and batch_id != 'all':
                student_query = student_query.filter(batch_id=batch_id)
            
            if today_only and status_filter:
                specific_date = date(year, month, int(today_only)) if today_only.isdigit() else today
                
                day_attendance = Attendance.objects.filter(
                    register__date=specific_date,
                    status=status_filter.capitalize(),
                    is_active=True
                ).select_related('student', 'student__batch', 'student__course', 'student__branch')
                
                if course_id or branch_id or batch_id:
                    filtered_student_ids = student_query.values_list('id', flat=True)
                    day_attendance = day_attendance.filter(student_id__in=filtered_student_ids)
                
                student_data = []
                for attendance in day_attendance:
                    student = attendance.student
                    course_name = student.course.name if student.course else "N/A"
                    branch_name = student.branch.name if student.branch else "N/A"
                    
                    student_data.append({
                        'id': student.id,
                        'fullname': self.get_student_fullname(student),
                        'admission_number': getattr(student, 'admission_number', 'N/A'),
                        'batch_name': student.batch.batch_name if student.batch else "No Batch",
                        'course_name': course_name,
                        'branch_name': branch_name,
                        'profile_url': self.get_student_profile_url(student),
                        'stage_status': student.stage_status,
                    })
                
                return JsonResponse({
                    'success': True,
                    'data': student_data,
                    'pagination': {
                        'current_page': 1,
                        'total_pages': 1,
                        'total_count': len(student_data),
                        'has_next': False,
                        'has_previous': False,
                    }
                })
            
            total_count = student_query.count()
            
            paginator = Paginator(student_query.order_by('batch__batch_name', 'first_name', 'last_name'), per_page)
            students_page = paginator.get_page(page)
            
            student_ids = list(students_page.object_list.values_list('id', flat=True))
            
            if not student_ids:
                return JsonResponse({
                    'success': True,
                    'data': [],
                    'pagination': {
                        'current_page': page,
                        'total_pages': paginator.num_pages,
                        'total_count': total_count,
                        'has_next': students_page.has_next(),
                        'has_previous': students_page.has_previous(),
                    }
                })
            
            monthly_attendance = Attendance.objects.select_related('register').filter(
                student_id__in=student_ids,
                is_active=True,
                register__date__month=month,
                register__date__year=year
            )
            
            leave_requests = LeaveRequest.objects.select_related('student').filter(
                student_id__in=student_ids,
                start_date__month=month,
                start_date__year=year
            )
            
            holidays = Holiday.objects.filter(
                is_active=True,
                date__month=month,
                date__year=year
            )
            
            holiday_map = {}
            for holiday in holidays:
                day = holiday.date.day
                holiday_map[day] = {
                    'name': holiday.name,
                    'scope': holiday.scope,
                    'branches': list(holiday.branch.values_list('id', flat=True)) if holiday.scope == 'branch' else []
                }
            
            attendance_map = {}
            for attendance in monthly_attendance:
                student_id = attendance.student_id
                day = attendance.register.date.day
                if student_id not in attendance_map:
                    attendance_map[student_id] = {}
                attendance_map[student_id][day] = {
                    'status': attendance.status,
                    'date': attendance.register.date,
                    'is_holiday': False 
                }
            
            leave_map = {}
            for leave in leave_requests:
                student_id = leave.student_id
                current = leave.start_date
                while current <= leave.end_date:
                    if current.month == month and current.year == year:
                        day = current.day
                        key = (student_id, day)
                        attachment_url = ""
                        if leave.attachment:
                            try:
                                attachment_url = leave.attachment.url
                            except:
                                attachment_url = ""
                        
                        leave_map[key] = {
                            "status": leave.status.lower(),
                            "subject": leave.subject or "No Subject",
                            "reason": leave.reason or "No Reason Provided",
                            "attachment_url": attachment_url,
                        }
                    current += timedelta(days=1)
            
            student_data = []
            for student in students_page:
                try:
                    student_info = self.get_student_attendance_summary(
                        student, attendance_map.get(student.id, {}), leave_map, holiday_map, month, year
                    )
                    student_data.append(student_info)
                except Exception as e:
                    print(f"Error processing student {student.id}: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                    course_name = student.course.name if student.course else "N/A"
                    branch_name = student.branch.name if student.branch else "N/A"
                    
                    student_data.append({
                        'id': student.id,
                        'fullname': self.get_student_fullname(student),
                        'admission_number': getattr(student, 'admission_number', 'N/A'),
                        'batch_name': student.batch.batch_name if student.batch else "No Batch",
                        'course_name': course_name,
                        'branch_name': branch_name,
                        'profile_url': self.get_student_profile_url(student),
                        'daily_attendance': {},
                        'total_present': 0,
                        'total_absent': 0,
                        'total_holiday': 0,
                    })
            
            return JsonResponse({
                'success': True,
                'data': student_data,
                'pagination': {
                    'current_page': page,
                    'total_pages': paginator.num_pages,
                    'total_count': total_count,
                    'has_next': students_page.has_next(),
                    'has_previous': students_page.has_previous(),
                },
                'filters': {
                    'month': month,
                    'year': year
                }
            })
            
        except Exception as e:
            print(f"=== API ERROR: {str(e)} ===")
            import traceback
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def get_student_fullname(self, student):
        """Safely get student fullname as string"""
        try:
            if hasattr(student, 'fullname') and callable(student.fullname):
                return student.fullname()
            elif hasattr(student, 'fullname'):
                return str(student.fullname)
            elif hasattr(student, 'get_full_name') and callable(student.get_full_name):
                return student.get_full_name()
            else:
                name_parts = []
                if getattr(student, 'first_name', None):
                    name_parts.append(student.first_name)
                if getattr(student, 'last_name', None):
                    name_parts.append(student.last_name)
                return ' '.join(name_parts).strip() or "Unknown Student"
        except Exception as e:
            print(f"Error getting fullname for student {student.id}: {e}")
            return "Unknown Student"
    
    def get_student_profile_url(self, student):
        """Safely get student profile URL"""
        try:
            if hasattr(student, 'get_profile_url') and callable(student.get_profile_url):
                return student.get_profile_url()
            elif hasattr(student, 'get_absolute_url') and callable(student.get_absolute_url):
                return student.get_absolute_url()
            else:
                return '#'
        except:
            return '#'
    
    def is_holiday_for_student(self, holiday_info, student_branch_id):
        """Check if a holiday applies to a specific student"""
        if holiday_info['scope'] == 'all':
            return True
        elif holiday_info['scope'] == 'branch':
            return student_branch_id in holiday_info['branches']
        return False
    
    def get_student_attendance_summary(self, student, student_attendance, leave_map, holiday_map, month, year):
        daily_attendance = {}
        total_present = 0
        total_absent = 0
        total_holiday = 0
        
        days_in_month = calendar.monthrange(year, month)[1]
        
        course_name = student.course.name if student.course else "N/A"
        branch_name = student.branch.name if student.branch else "N/A"
        
        for day in range(1, days_in_month + 1):
            current_date_obj = date(year, month, day)
            formatted_date = current_date_obj.strftime('%d-%m-%Y')
            
            is_manual_holiday = False
            holiday_name = ""
            if day in holiday_map:
                holiday_info = holiday_map[day]
                student_branch_id = student.branch.id if student.branch else None
                if self.is_holiday_for_student(holiday_info, student_branch_id):
                    is_manual_holiday = True
                    holiday_name = holiday_info['name']
            
            is_auto_holiday, auto_holiday_name = Holiday.is_auto_holiday(current_date_obj)
            
            is_holiday = is_manual_holiday or is_auto_holiday
            final_holiday_name = holiday_name if is_manual_holiday else (auto_holiday_name if is_auto_holiday else "")
            
            attendance_data = student_attendance.get(day)
            leave_info = leave_map.get((student.id, day))
            
            attendance_info = {
                'date': formatted_date,
                'has_data': False, 
                'is_holiday': is_holiday,
                'holiday_name': final_holiday_name,
                'is_auto_holiday': is_auto_holiday,
            }
            
            if attendance_data:
                attendance_info.update({
                    'status': attendance_data['status'],
                    'has_data': True,
                })
                
                if is_holiday:
                    attendance_info['status'] = 'Holiday'
                    total_holiday += 1
                else:
                    if attendance_info['status'] == "Present":
                        total_present += 1
                    elif attendance_info['status'] == "Absent":
                        total_absent += 1
                
                if leave_info and attendance_data['status'] == 'Absent' and not is_holiday:
                    attendance_info.update({
                        'leave_status': leave_info.get('status'),
                        'leave_subject': leave_info.get('subject', 'No Subject'),
                        'leave_reason': leave_info.get('reason', 'No Reason Provided'),
                        'leave_attachment': leave_info.get('attachment_url', ''),
                    })
                    
            elif is_holiday:
                attendance_info.update({
                    'status': 'Holiday',
                    'has_data': True,
                })
                total_holiday += 1
                
            elif leave_info:
                attendance_info.update({
                    'status': 'Absent',
                    'has_data': True,
                    'leave_status': leave_info.get('status'),
                    'leave_subject': leave_info.get('subject', 'No Subject'),
                    'leave_reason': leave_info.get('reason', 'No Reason Provided'),
                    'leave_attachment': leave_info.get('attachment_url', ''),
                })
                total_absent += 1
                
            else:
                attendance_info.update({
                    'status': None,
                    'has_data': False,
                })
            
            daily_attendance[day] = attendance_info
        
        return {
            'id': student.id,
            'fullname': self.get_student_fullname(student),
            'admission_number': getattr(student, 'admission_number', 'N/A'),
            'batch_name': student.batch.batch_name if student.batch else "No Batch",
            'course_name': course_name,  
            'branch_name': branch_name, 
            'profile_url': self.get_student_profile_url(student),
            'stage_status': student.stage_status,
            'daily_attendance': daily_attendance,
            'total_present': total_present,
            'total_absent': total_absent,
            'total_holiday': total_holiday,
        }


class FeeReceiptListView(mixins.HybridListView):
    model = FeeReceipt
    table_class = tables.FeeReceiptTable
    filterset_fields = {
        'student': ['exact'],
        'date': ['exact'],
        'receipt_no': ['exact'],
    }
    permissions = (
        "branch_staff", "teacher", "admin_staff", "is_superuser",
        "student", "ceo", "cfo", "coo", "hr", "cmo", "mentor"
    )
    branch_filter = False
    search_fields = [
        "receipt_no",
        "student__first_name",
        "student__last_name",
        "student__admission_number",
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        queryset = queryset.filter(is_active=True)

        if user.usertype == "student":
            queryset = queryset.filter(student__user=user)

        elif user.usertype == "teacher":
            queryset = queryset.filter(
                student__branch=user.branch,
                student__course=user.employee.course
            )

        elif user.usertype == "branch_staff":
            queryset = queryset.filter(student__branch=user.branch)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["is_admission"] = True
        context["fee_reciept"] = True

        user = self.request.user
        context["can_add"] = (
            user.is_superuser or
            user.usertype in [
                "teacher", "branch_staff", "admin_staff",
                "ceo", "cfo", "coo", "hr", "cmo"
            ]
        )

        if context["can_add"]:
            context["new_link"] = reverse_lazy("admission:feereceipt_create")

        return context

    
class FeeReceiptDetailView(mixins.HybridDetailView):
    model = FeeReceipt
    template_name = "admission/fee_receipt/receipt_view.html"
    permissions = ("branch_staff", "teacher", "admin_staff", "is_superuser", "student", "ceo","cfo","coo","hr","cmo", "mentor")
    
    
class FeeReceiptCreateView(mixins.HybridCreateView):
    model = FeeReceipt
    form_class = FeeReceiptForm
    permissions = ("is_superuser", "teacher", "branch_staff", "admin_staff",
                   "ceo", "cfo", "coo", "hr", "cmo", "mentor")
    template_name = "admission/fee_receipt/object_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Fee Receipt"
        context["branches"] = Branch.objects.filter(is_active=True)
        
        # Add formset to context
        if self.request.POST:
            context["formset"] = forms.PaymentMethodFormSet(
                self.request.POST, 
                self.request.FILES,
                prefix='paymentmethod'
            )
        else:
            context["formset"] = forms.PaymentMethodFormSet(prefix='paymentmethod')
            
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user

        # Remove branch field since FeeReceipt doesn't have it
        if 'branch' in form.fields:
            form.fields.pop('branch')

        # Teacher → filter by course + branch
        if user.usertype == "teacher":
            try:
                teacher = Employee.objects.get(user=user)
                form.fields["student"].queryset = Admission.objects.filter(
                    course=teacher.course, branch=teacher.branch, is_active=True
                )
            except Employee.DoesNotExist:
                form.fields["student"].queryset = Admission.objects.none()

        # Branch staff → only their branch
        elif user.usertype == "branch_staff":
            form.fields["student"].queryset = Admission.objects.filter(
                branch=user.branch, is_active=True
            )

        # Admin or Superuser → all active
        elif user.usertype == "admin_staff" or user.is_superuser:
            form.fields["student"].queryset = Admission.objects.filter(is_active=True)

        # Others → no access
        else:
            form.fields["student"].queryset = Admission.objects.none()

        return form

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]
        
        fee_receipt = form.save(commit=False)
        
        # Generate receipt no
        fee_receipt.receipt_no = generate_receipt_no(fee_receipt.student)
        
        if formset.is_valid():
            # First save the fee receipt
            fee_receipt.save()
            
            # Then save the formset with the fee receipt instance
            formset.instance = fee_receipt
            formset.save()
            
            # Apply payment to fee structure
            self.apply_payment_to_fee_structure(fee_receipt)
            
            return super().form_valid(form)
        else:
            print("Formset Errors:", formset.errors)
            print("Formset Non-form Errors:", formset.non_form_errors())
            return self.form_invalid(form)

    def apply_payment_to_fee_structure(self, receipt):
        """Apply payment to fee structure in order of due date"""
        # Use the receipt amount from payment methods
        remaining = receipt.get_amount()
        
        # If no amount, return early
        if remaining <= 0:
            return

        # Get unpaid fee structures ordered by due date
        unpaid_fees = FeeStructure.objects.filter(
            student=receipt.student, 
            is_paid=False
        ).order_by("due_date")

        for fee_structure in unpaid_fees:
            if remaining <= 0:
                break

            # Calculate outstanding amount for this fee structure
            outstanding = fee_structure.amount - fee_structure.paid_amount
            pay_amount = min(outstanding, remaining)

            # Update fee structure
            fee_structure.paid_amount += pay_amount
            remaining -= pay_amount

            # Mark as paid if fully paid
            if fee_structure.paid_amount >= fee_structure.amount:
                fee_structure.is_paid = True

            fee_structure.save()

    def form_invalid(self, form):
        print("Form Errors:", form.errors)
        return super().form_invalid(form)
    
    
class FeeReceiptUpdateView(mixins.HybridUpdateView):
    model = FeeReceipt
    form_class = FeeReceiptForm
    permissions = ("is_superuser", "teacher", "admin_staff", "branch_staff", "ceo", "cfo", "coo", "hr", "cmo", "mentor")
    template_name = "admission/fee_receipt/object_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Fee Receipt"
        context["branches"] = Branch.objects.filter(is_active=True)
        
        # Properly initialize formset with instance
        if self.request.POST:
            context["formset"] = forms.PaymentMethodFormSet(
                self.request.POST, 
                self.request.FILES, 
                instance=self.object,
                prefix='paymentmethod'
            )
        else:
            context["formset"] = forms.PaymentMethodFormSet(
                instance=self.object,
                prefix='paymentmethod'
            )
            
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user

        # Remove branch field since FeeReceipt doesn't have it
        if 'branch' in form.fields:
            form.fields.pop('branch')

        # Filter students based on user type
        if user.usertype == "teacher":
            try:
                teacher = Employee.objects.get(user=user)
                form.fields["student"].queryset = Admission.objects.filter(
                    course=teacher.course, branch=teacher.branch, is_active=True
                )
            except Employee.DoesNotExist:
                form.fields["student"].queryset = Admission.objects.none()

        elif user.usertype == "branch_staff":
            form.fields["student"].queryset = Admission.objects.filter(
                branch=user.branch, is_active=True
            )

        elif user.usertype == "admin_staff" or user.is_superuser:
            form.fields["student"].queryset = Admission.objects.filter(is_active=True)

        else:
            form.fields["student"].queryset = Admission.objects.none()

        return form

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]

        fee_receipt = form.save(commit=False)

        # Generate receipt no
        fee_receipt.receipt_no = generate_receipt_no(fee_receipt.student)

        if formset.is_valid():
            # First save the fee receipt
            fee_receipt.save()

            # Then save the formset with the fee receipt instance
            formset.instance = fee_receipt
            formset.save()

            # Apply payment to fee structure
            self.apply_payment_to_fee_structure(fee_receipt)

            # ✅ Mark receipt as paid
            fee_receipt.status = 'paid'
            fee_receipt.save(update_fields=['status'])

            return super().form_valid(form)
        else:
            print("Formset Errors:", formset.errors)
            print("Formset Non-form Errors:", formset.non_form_errors())
            return self.form_invalid(form)


    def reallocate_fees(self, receipt):
        # Reset all fee structures for this student
        fee_items = FeeStructure.objects.filter(student=receipt.student)
        for fee in fee_items:
            fee.paid_amount = 0
            fee.is_paid = False
            fee.save()

        # Reapply all receipts in correct order
        receipts = FeeReceipt.objects.filter(student=receipt.student).order_by("date", "id")

        for rec in receipts:
            remaining = rec.get_amount()

            unpaid = FeeStructure.objects.filter(
                student=rec.student, is_paid=False
            ).order_by("due_date")

            for fee in unpaid:
                if remaining <= 0:
                    break

                outstanding = fee.amount - fee.paid_amount
                pay = min(outstanding, remaining)

                fee.paid_amount += pay
                remaining -= pay

                if fee.paid_amount >= fee.amount:
                    fee.is_paid = True

                fee.save()

    def form_invalid(self, form):
        print("Form Errors:", form.errors)
        return super().form_invalid(form)
    

class FeeReceiptDeleteView(mixins.HybridDeleteView):
    model = FeeReceipt
    permissions = ("is_superuser", "teacher", "admin_staff", "branch_staff", "ceo","cfo","coo","hr","cmo")
    
    
class FeeReceiptReportView(mixins.HybridTemplateView):
    template_name = "admission/fee_receipt/receipt_report.html"
    permissions = (
        "branch_staff", "teacher", "admin_staff", "is_superuser",
        "student", "ceo", "cfo", "coo", "hr", "cmo", "mentor"
    )

    # Centralized stages - Removed 'inactive'
    FINANCIAL_STAGES = ["active", "completed", "placed", "internship"]

    # ---------- Helpers ----------
    def get_month_choices(self):
        return [
            (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
            (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
            (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
        ]
    
    def get_year_choices(self):
        current_year = datetime.now().year
        years = list(range(current_year - 5, current_year + 3))
        return [('all', 'All Years')] + [(year, year) for year in sorted(years, reverse=True)]

    def _is_branch_staff(self, user):
        return getattr(user, 'usertype', None) == 'branch_staff' or getattr(user, 'ussertype', None) == 'branch_staff'

    def _user_branch_id(self, user):
        return (
            getattr(user, 'branch_id', None)
            or getattr(getattr(user, 'branch', None), 'id', None)
        )

    # ---------- Core Payment Logic ----------
    def get_student_payment_status(self, branch_id=None, course_id=None, year=None, month=None, stage=None):
        # 1. Get relevant students using centralized stages
        students = Admission.objects.filter(stage_status__in=self.FINANCIAL_STAGES)
        
        if branch_id:
            students = students.filter(branch_id=branch_id)
        if course_id:
            students = students.filter(course_id=course_id)
        if stage and stage in self.FINANCIAL_STAGES:
            students = students.filter(stage_status=stage)

        paid_students, unpaid_students = [], []

        for student in students:
            fee_structures = FeeStructure.objects.filter(student=student, is_active=True)
            
            if year and year != 'all':
                fee_structures = fee_structures.filter(due_date__year=year)
            if month:
                fee_structures = fee_structures.filter(due_date__month=month)

            aggregates = fee_structures.aggregate(
                total_expected=Sum('amount'),
                total_paid=Sum('paid_amount')
            )
            
            total_fee = aggregates['total_expected'] or Decimal('0.00')
            paid_amount = aggregates['total_paid'] or Decimal('0.00')
            balance = max(total_fee - paid_amount, Decimal('0.00'))
            has_fee_structure = fee_structures.exists()

            student_data = {
                "student_name": student.fullname(),
                "student_status": student.stage_status,
                "fee_overview_url": student.get_fee_overview_absolute_url(),
                "branch": student.branch.name if student.branch else "N/A",
                "course": student.course.name if student.course else "N/A",
                "paid_amount": paid_amount,   
                "unpaid_amount": balance,
                "total_fee": total_fee,
                "balance": balance,
                "installments_count": fee_structures.count(),
                "paid_installments": fee_structures.filter(is_paid=True).count(),
                "has_fee_structure": has_fee_structure,
            }

            if not has_fee_structure or balance <= 0:
                paid_students.append(student_data)
            else:
                unpaid_students.append(student_data)

        return paid_students, unpaid_students

    # ---------- Context ----------
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Fee Receipt Report"
        context["is_fee_receipt_report"] = True

        user = self.request.user
        is_branch_staff = self._is_branch_staff(user)
        user_branch_id = self._user_branch_id(user)

        # GET Parameters
        branch_id = self.request.GET.get('branch')
        course_id = self.request.GET.get('course')
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')
        stage = self.request.GET.get('stage')
        
        if is_branch_staff and user_branch_id:
            branch_id = str(user_branch_id)
        
        is_ajax = self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # Filter students based on stage
        active_students = Admission.objects.filter(stage_status__in=self.FINANCIAL_STAGES)
        if stage and stage in self.FINANCIAL_STAGES:
            active_students = active_students.filter(stage_status=stage)
        
        # Summary Querysets
        fee_receipts = FeeReceipt.objects.filter(is_active=True, student__in=active_students).prefetch_related('payment_methods')
        fee_structures = FeeStructure.objects.filter(is_active=True, student__in=active_students)

        # Apply Filters to Querysets
        if branch_id:
            fee_receipts = fee_receipts.filter(student__branch_id=branch_id)
            fee_structures = fee_structures.filter(student__branch_id=branch_id)
        if course_id:
            fee_receipts = fee_receipts.filter(student__course_id=course_id)
            fee_structures = fee_structures.filter(student__course_id=course_id)
        if year and year != 'all':
            fee_structures = fee_structures.filter(due_date__year=int(year))
            fee_receipts = fee_receipts.filter(date__year=int(year))
        if month:
            fee_structures = fee_structures.filter(due_date__month=int(month))
            fee_receipts = fee_receipts.filter(date__month=int(month))

        # 1. Get Summary Stats (The Fix for Mathematical Reconciliation)
        total_fee = fee_structures.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        total_paid_amount = fee_receipts.aggregate(total=Sum('payment_methods__amount'))['total'] or Decimal('0.00')
        
        # Calculation Fix: Total - Paid = Unpaid (Reconciles ₹3,626,300.00 correctly)
        total_unpaid_balance = max(total_fee - total_paid_amount, Decimal('0.00'))

        # 2. Get Individual Student Lists for the Table
        paid_students, unpaid_students = self.get_student_payment_status(
            branch_id=branch_id,
            course_id=course_id,
            year=int(year) if year and year != 'all' else None,
            month=int(month) if month else None,
            stage=stage
        )

        # 3. Branch/Course Breakdown
        branch_summary = fee_receipts.values(
            'student__branch__name', 'student__course__name'
        ).annotate(
            total_amount=Sum('payment_methods__amount'),
            receipt_count=Count('id')
        ).order_by('student__branch__name', 'student__course__name')

        # Dropdown options
        month_choices = self.get_month_choices()
        year_choices = self.get_year_choices()
        stage_options = [
            ('active', "Active / Ongoing"), 
            ('completed', "Course Completed"), 
            ('placed', "Placed"), 
            ('internship', "On Internship"),  
        ]

        if not is_ajax:
            context.update({
                'fee_receipts': fee_receipts[:20],
                'branches': Branch.objects.filter(is_active=True) if not is_branch_staff else Branch.objects.filter(id=user_branch_id),
                'courses': Course.objects.filter(is_active=True),
                'branch_summary': branch_summary,
                'receipt_count': fee_receipts.count(),
                
                # Context Summary Variables
                'total_amount': total_fee,
                'paid_amount': total_paid_amount,
                'unpaid_amount': total_unpaid_balance,
                
                'selected_branch': str(branch_id) if branch_id else None,
                'selected_course': str(course_id) if course_id else None,
                'selected_year': str(year) if year is not None else None,
                'selected_month': str(month) if month else None,
                'selected_stage': stage,
                'month_choices': month_choices,
                'year_choices': year_choices,
                'stage_options': stage_options,
                'paid_students': paid_students,
                'unpaid_students': unpaid_students,
                'paid_students_count': len(paid_students),
                'unpaid_students_count': len(unpaid_students),
            })
        return context

    # ---------- AJAX Pagination ----------
    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return self.ajax_get_receipts(request)
        return super().get(request, *args, **kwargs)

    def ajax_get_receipts(self, request):
        try:
            page = int(request.GET.get('page', 1))
            per_page = 20
            
            # Re-apply same filters for AJAX
            user = request.user
            branch_id = request.GET.get('branch')
            if self._is_branch_staff(user) and self._user_branch_id(user):
                branch_id = str(self._user_branch_id(user))
            
            course_id = request.GET.get('course')
            year = request.GET.get('year')
            month = request.GET.get('month')
            stage = request.GET.get('stage')

            active_students = Admission.objects.filter(stage_status__in=self.FINANCIAL_STAGES)
            if stage and stage in self.FINANCIAL_STAGES:
                active_students = active_students.filter(stage_status=stage)

            fee_receipts = FeeReceipt.objects.filter(is_active=True, student__in=active_students).prefetch_related('payment_methods')
            
            if branch_id: fee_receipts = fee_receipts.filter(student__branch_id=branch_id)
            if course_id: fee_receipts = fee_receipts.filter(student__course_id=course_id)
            if year and year != 'all': fee_receipts = fee_receipts.filter(date__year=int(year))
            if month: fee_receipts = fee_receipts.filter(date__month=int(month))

            total_receipts = fee_receipts.count()
            start_index = (page - 1) * per_page
            end_index = start_index + per_page
            receipts_page = fee_receipts[start_index:end_index]

            receipts_data = []
            for r in receipts_page:
                payment_types = ", ".join(list(r.payment_methods.values_list('payment_type', flat=True)))
                receipts_data.append({
                    'receipt_no': r.receipt_no,
                    'date': r.date.strftime('%d-%m-%Y') if r.date else '',
                    'student_name': r.student.fullname(),
                    'student_status': r.student.stage_status,
                    'branch_name': r.student.branch.name if r.student.branch else 'N/A',
                    'course_name': r.student.course.name if r.student.course else 'N/A',
                    'amount': str(r.get_amount()),
                    'payment_type': payment_types or "-",
                    'balance': str(r.get_receipt_balance() if hasattr(r, 'get_receipt_balance') else 0),
                })

            return JsonResponse({
                'receipts': receipts_data,
                'has_next': end_index < total_receipts,
                'page': page,
                'total_receipts': total_receipts
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        

class StudentFeeOverviewListView(mixins.HybridListView):
    model = Admission
    table_class = tables.StudentFeeOverviewTable
    template_name = "admission/fee_receipt/student_fee_overview_list.html"
    filterset_fields = {'branch': ['exact'], 'course': ['exact'], 'batch': ['exact'], }
    permissions = ("branch_staff", "teacher", "admin_staff", "is_superuser", "student", "ceo","cfo","coo","hr","cmo", "mentor")
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        user = self.request.user
        
        if user.usertype == "teacher":
            employee = getattr(user, "employee", None)
            if employee and employee.course:
                queryset = queryset.filter(branch=user.branch, course=employee.course)

        elif user.usertype == "branch_staff":
            queryset = queryset.filter(branch=user.branch)

        return queryset
    
    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)
        context['title'] = "Student Receipt Overview"
        context["can_add"] = False
        context["is_admission"] = True
        context["fee_overview"] = True
        return context
    

class StudentFeeOverviewDetailView(mixins.HybridDetailView):
    model = Admission
    template_name = "admission/fee_receipt/student_fee_overview.html"
    permissions = (
        "branch_staff", "teacher", "admin_staff", "is_superuser",
        "student", "ceo", "cfo", "coo", "hr", "cmo", "mentor"
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admission = self.get_object()

        # Get all fee receipts with payment methods
        fee_receipts = admission.feereceipt_set.filter(
            is_active=True
        ).prefetch_related('payment_methods').order_by("-date")

        # Create a list to store all payment methods separately
        all_payment_methods = []
        for receipt in fee_receipts:
            for payment_method in receipt.payment_methods.all():
                all_payment_methods.append({
                    'receipt': receipt,
                    'payment_method': payment_method,
                    'receipt_no': receipt.receipt_no,
                    'date': receipt.date,
                })
        
        context["all_payment_methods"] = all_payment_methods
        context["fee_receipts"] = fee_receipts

        # Fee structures with calculated remaining amount
        fee_structures = admission.feestructure_set.all().order_by("installment_no")
        
        # Annotate remaining amount - simple calculation
        for fee in fee_structures:
            fee_amount = Decimal(str(fee.amount))
            paid_amount = Decimal(str(fee.paid_amount or 0))
            
            fee.get_remaining_amount = fee_amount - paid_amount
            
            # Calculate payment percentage
            if fee_amount > 0:
                fee.get_payment_percentage = (paid_amount / fee_amount * 100)
            else:
                fee.get_payment_percentage = Decimal('100.00')

        context["fee_structures"] = fee_structures

        # Calculate totals from fee structures (this reflects the NET amounts after discount)
        total_installment_amount = sum(Decimal(str(fee.amount)) for fee in fee_structures)
        total_paid_installments = sum(Decimal(str(fee.paid_amount or 0)) for fee in fee_structures)
        total_remaining = total_installment_amount - total_paid_installments

        context["total_paid"] = admission.get_total_fee_amount()
        context["total_amount"] = admission.get_current_fee()  # Course fee - discount
        context["balance_due"] = total_remaining  # Use the calculated remaining from fee structures

        return context
    

class FeeOverviewListView(mixins.HybridListView):
    model = Admission
    filterset_fields = {'branch': ['exact'], 'course': ['exact'], 'batch': ['exact']}
    permissions = ("branch_staff", "teacher", "admin_staff", "is_superuser", "student", "ceo","cfo","coo","hr","cmo", "mentor")
    template_name = "admission/fee_receipt/fee_overview.html"
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.usertype == "student":
            queryset = queryset.filter(user=user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admissions = self.get_queryset()

        # Calculate total fee and balance for all admissions (if multiple)
        total_fee_amount = sum(admission.get_total_fee_amount() for admission in admissions)
        balance_amount = sum(admission.get_balance_amount() for admission in admissions)

        # Collect fee receipts with prefetch for payment methods
        context["fee_receipts"] = FeeReceipt.objects.filter(
            student__in=admissions, 
            is_active=True
        ).prefetch_related('payment_methods').order_by("-date")

        # Collect fee structures
        fee_structures = []
        for admission in admissions:
            fs_list = admission.feestructure_set.all().order_by("installment_no")
            for fs in fs_list:
                fs.remaining_amount = max(fs.amount - fs.paid_amount, 0)
                fs.status_display = "Paid" if fs.is_paid or fs.paid_amount >= fs.amount else "Pending"
                fs.payment_percentage = round((fs.paid_amount / fs.amount) * 100, 0) if fs.amount > 0 else 0
                fs.admission_name = admission.fullname()
                fee_structures.append(fs)

        context["fee_structures"] = fee_structures
        context["total_fee_amount"] = total_fee_amount
        context["balance_amount"] = balance_amount
        return context
    

class RegistrationView(mixins.FormView):
    template_name = 'admission/registration_form.html'
    form_class = forms.RegistrationForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Registration"   
        return context

    def form_valid(self, form):
        # password = form.cleaned_data.get("password")
        email = form.cleaned_data.get("personal_email")

        # if not password or not email:
        #     form.add_error("password", "Password is required.")
        #     form.add_error("personal_email", "Email is required.")
        #     return self.form_invalid(form)

        admission = form.save(commit=False)

        if not User.objects.filter(email=email).exists():
            user = User.objects.create_user(
                email=email,
                # password=password,
                first_name=admission.first_name,
                last_name=admission.last_name,
                branch=admission.branch, 
                is_active=False,
                usertype="student",
            )
            admission.user = user

        admission.save()
        self.admission_pk = admission.pk

        # Detect which button the user clicked
        if "save_next" in self.request.POST:
            self.next_page = "save_next"
        else:
            self.next_page = "save"

        return super().form_valid(form)

    def form_invalid(self, form):
        print("Form is invalid:", form.errors)
        return super().form_invalid(form)
    
    def get_success_url(self):
        if getattr(self, "next_page", "") == "save_next":
            return reverse("admission:registration_detail", kwargs={"pk": self.admission_pk})

        return reverse("admission:terms_condition", kwargs={"pk": self.admission_pk})
    
    
class TermsConditionView(View):
    template_name = "admission/terms_condition.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Terms and Conditions"   
        return context

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"pk": self.kwargs.get("pk")})

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        return redirect(reverse("admission:registration_detail", kwargs={"pk": pk}))
    

class RegistrationDetailView(PDFView):
    template_name = 'admission/registration_pdf.html'
    pdfkit_options = {
        "page-height": 297,
        "page-width": 210,
        "encoding": "UTF-8",
        "margin-top": "0",
        "margin-bottom": "0",
        "margin-left": "0",
        "margin-right": "0",
    }
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instance = get_object_or_404(Admission, pk=self.kwargs["pk"])
        context["title"] = "Registration"
        context["instance"] = instance
        context["photo_url"] = self.request.build_absolute_uri(instance.photo.url)
        print(context["photo_url"])
        return context
    
    def get_filename(self):
        return "registration_form.pdf"


@csrf_exempt
def attendance_save_api(request):
    """API endpoint to save attendance data"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        try:
            data = json.loads(request.body)
            date_str = data.get('date')
            records = data.get('records', [])
            batch_id = data.get('batch_id', 'all')
            course_id = data.get('course_id', 'all')
            branch_id = data.get('branch_id', 'all')
            send_whatsapp = data.get('send_whatsapp', True)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        
        if not date_str:
            return JsonResponse({'error': 'Date is required'}, status=400)
        
        if not records:
            return JsonResponse({'error': 'No attendance records provided'}, status=400)
        
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
        
        if selected_date > timezone.now().date():
            return JsonResponse({'error': 'Cannot mark attendance for future dates'}, status=400)
        
        # IMPROVED HOLIDAY CHECKING: Consider branch-specific holidays
        is_holiday = False
        holiday_type = None
        holiday_name = None
        
        # Check for auto holidays first (Sundays, Second Saturdays)
        is_auto_holiday, auto_holiday_name = Holiday.is_auto_holiday(selected_date)
        if is_auto_holiday:
            is_holiday = True
            holiday_type = 'automatic weekend'
            holiday_name = auto_holiday_name
        
        # Check for manual holidays
        try:
            Holiday._meta.get_field('is_auto_holiday')
            manual_holidays = Holiday.objects.filter(
                is_active=True,
                date=selected_date,
                is_auto_holiday=False
            )
        except FieldDoesNotExist:
            manual_holidays = Holiday.objects.filter(
                is_active=True,
                date=selected_date
            )
        
        # Get all student IDs from records to determine affected branches
        student_ids = [record.get('student_id') for record in records if record.get('student_id')]
        if not student_ids:
            return JsonResponse({'error': 'No valid student IDs found in records'}, status=400)
        
        # Get students to determine their branches for holiday checking
        students_for_branch_check = Admission.objects.filter(
            id__in=student_ids,
            is_active=True
        ).select_related('branch')
        
        # Get unique branches from the students in the records
        student_branches = set()
        for student in students_for_branch_check:
            if student.branch:
                student_branches.add(student.branch.id)
        
        # Check manual holidays considering branch scope
        for holiday in manual_holidays:
            if holiday.scope == 'all':
                # All-branch holiday applies to everyone
                is_holiday = True
                holiday_type = 'manual'
                holiday_name = holiday.name
                break
            elif holiday.scope == 'branch':
                # Branch-specific holiday - check if it applies to any of the student branches
                holiday_branch_ids = set(holiday.branch.values_list('id', flat=True))
                
                # Check if any student branch matches the holiday branches
                if student_branches.intersection(holiday_branch_ids):
                    is_holiday = True
                    holiday_type = 'manual'
                    holiday_name = holiday.name
                    break
        
        # If it's a holiday, block attendance saving
        if is_holiday:
            return JsonResponse({
                'error': f'Cannot mark attendance - {selected_date.strftime("%B %d, %Y")} is a {holiday_type} holiday ({holiday_name})'
            }, status=400)
        
        try:
            # Base query for students - get ALL students from the records
            students = Admission.objects.filter(
                id__in=student_ids,
                is_active=True,
                batch__status='in_progress'
            ).select_related('batch', 'branch', 'course')
        except Exception as e:
            return JsonResponse({'error': f'Error fetching students: {str(e)}'}, status=500)
        
        if not students.exists():
            return JsonResponse({'error': 'No students found with the provided IDs'}, status=400)
        
        # Apply user permissions
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        if user.usertype == "mentor":
            allowed_students = students
            
        elif user.usertype == "teacher":
            employee = getattr(user, 'employee', None)
            teacher_course = getattr(employee, 'course', None) if employee else None
            teacher_branch = getattr(employee, 'branch', None) if employee else None
            
            if not teacher_course or not teacher_branch:
                return JsonResponse({'error': 'Teacher must be assigned to a course and branch'}, status=403)
            
            allowed_students = students.filter(
                branch=teacher_branch,
                course=teacher_course
            )
            
        elif user.usertype == "branch_staff":
            if user.branch:
                allowed_students = students.filter(branch=user.branch)
            else:
                return JsonResponse({'error': 'Branch staff must be assigned to a branch'}, status=403)
                
        elif user.usertype in ["admin_staff", "ceo", "cfo", "coo", "hr", "cmo"] or user.is_superuser:
            allowed_students = students
        else:
            user_branch = getattr(user, 'branch', None)
            if user_branch:
                allowed_students = students.filter(branch=user_branch)
            else:
                return JsonResponse({'error': 'Insufficient permissions'}, status=403)
        
        if not allowed_students.exists():
            return JsonResponse({'error': 'No students found matching your permissions'}, status=403)
        
        # Create a mapping of student IDs to student objects for quick lookup
        student_map = {student.id: student for student in allowed_students}
        
        # Filter records to only include allowed students
        filtered_records = [record for record in records if record.get('student_id') in student_map]
        
        if not filtered_records:
            return JsonResponse({'error': 'No valid records found after permission check'}, status=403)
        
        # Group students by batch
        students_by_batch = {}
        for record in filtered_records:
            student_id = record.get('student_id')
            student = student_map.get(student_id)
            if not student:
                continue
                
            batch_key = (
                student.batch.id if student.batch else None, 
                student.course.id if student.course else None,
                student.branch.id if student.branch else None
            )
            if batch_key not in students_by_batch:
                students_by_batch[batch_key] = []
            students_by_batch[batch_key].append(student)
        
        # Get batches that user is allowed to modify
        user_allowed_batches = set(students_by_batch.keys())
        
        # ✅ FIXED: Store SMS history BEFORE deleting existing records
        sms_history = {}
        try:
            existing_registers = AttendanceRegister.objects.filter(date=selected_date)
            
            for register in existing_registers:
                register_key = (
                    register.batch.id if register.batch else None,
                    register.course.id if register.course else None,
                    register.branch.id if register.branch else None
                )
                if register_key in user_allowed_batches:
                    # Get all attendance records with SMS sent flag
                    existing_attendance = Attendance.objects.filter(
                        register=register,
                        sms_sent=True
                    ).values_list('student_id', flat=True)
                    
                    # Store which students already received SMS
                    for student_id in existing_attendance:
                        sms_history[student_id] = True
            
            print(f"📝 SMS History preserved for {len(sms_history)} students")
            
        except Exception as e:
            print(f"Warning: Could not retrieve SMS history: {str(e)}")
            sms_history = {}
        
        # Delete existing attendance records for the selected date and allowed batches
        try:
            existing_registers = AttendanceRegister.objects.filter(date=selected_date)
            registers_to_delete = []
            
            for register in existing_registers:
                register_key = (
                    register.batch.id if register.batch else None,
                    register.course.id if register.course else None,
                    register.branch.id if register.branch else None
                )
                if register_key in user_allowed_batches:
                    registers_to_delete.append(register.id)
            
            # Delete existing records in transaction
            if registers_to_delete:
                with transaction.atomic():
                    Attendance.objects.filter(register_id__in=registers_to_delete).delete()
                    AttendanceRegister.objects.filter(id__in=registers_to_delete).delete()
        except Exception as e:
            return JsonResponse({'error': f'Error deleting existing records: {str(e)}'}, status=500)
        
        # Create new attendance records
        total_attendance_created = 0
        students_to_notify = []
        
        try:
            with transaction.atomic():
                for (batch_id, course_id, branch_id), batch_students in students_by_batch.items():
                    if not batch_students:
                        continue
                    
                    # Use first student to get batch, course, branch info
                    first_student = batch_students[0]
                    
                    # Validate required relationships
                    if not first_student.batch:
                        return JsonResponse({'error': f'Student {first_student.fullname()} has no batch assigned'}, status=400)
                    if not first_student.course:
                        return JsonResponse({'error': f'Student {first_student.fullname()} has no course assigned'}, status=400)
                    if not first_student.branch:
                        return JsonResponse({'error': f'Student {first_student.fullname()} has no branch assigned'}, status=400)
                    
                    # Create attendance register
                    attendance_register = AttendanceRegister.objects.create(
                        date=selected_date,
                        batch=first_student.batch,
                        course=first_student.course,
                        branch=first_student.branch,
                        is_active=True
                    )
                    
                    # Create attendance records
                    attendance_objects = []
                    for student in batch_students:
                        # Find the record for this student
                        record = next(
                            (r for r in filtered_records if r.get('student_id') == student.id), 
                            None
                        )
                        
                        if not record:
                            continue
                            
                        # Validate status
                        status = record.get('status', 'Absent')
                        if status not in ['Present', 'Absent', 'Holiday']:
                            status = 'Absent'
                        
                        # ✅ FIXED: Preserve SMS sent status from history
                        was_sms_sent = sms_history.get(student.id, False)
                        
                        # Create attendance object
                        attendance = Attendance(
                            register=attendance_register,
                            student=student,
                            status=status,
                            sms_sent=was_sms_sent  # ✅ Preserve existing SMS status
                        )
                        attendance_objects.append(attendance)
                        
                        # ✅ FIXED: Only add to notify list if:
                        # 1. Status is Absent
                        # 2. WhatsApp is enabled
                        # 3. SMS was NOT previously sent
                        if status == 'Absent' and send_whatsapp and not was_sms_sent:
                            students_to_notify.append((student, selected_date))
                    
                    # Bulk create attendance records
                    if attendance_objects:
                        Attendance.objects.bulk_create(attendance_objects)
                        total_attendance_created += len(attendance_objects)
        
        except Exception as e:
            return JsonResponse({'error': f'Error creating attendance records: {str(e)}'}, status=500)
        
        # Send SMS notifications for absent students (only if WhatsApp is enabled)
        sms_sent_count = 0
        sms_skipped_count = 0
        
        if send_whatsapp:
            print(f"📱 Processing {len(students_to_notify)} students for WhatsApp notifications")
            
            for student, date in students_to_notify:
                try:
                    phone_number = student.parent_whatsapp_number
                    if not phone_number:
                        print(f"⚠️ No WhatsApp number for student {student.fullname()}")
                        continue
                    
                    # ✅ FIXED: Double-check if SMS was already sent (shouldn't happen now, but safety check)
                    if sms_history.get(student.id, False):
                        print(f"⏭️ Skipping {student.fullname()} - SMS already sent previously")
                        sms_skipped_count += 1
                        continue
                    
                    # Check for approved leave
                    has_leave = LeaveRequest.objects.filter(
                        student=student,
                        status='approved',
                        start_date__lte=date,
                        end_date__gte=date
                    ).exists()
                    
                    # Prepare message
                    if has_leave:
                        message = (
                            f"*Oxdu Integrated Media School - Leave Notification / അവധി അറിയിപ്പ്*\n\n"
                            f"*English:*\n"
                            f"Dear Parent,\n\n"
                            f"This is to inform you that your child *{student.fullname()}* "
                            f"has an approved leave on *{date.strftime('%B %d, %Y')}*.\n"
                            f"Our records show that the leave request was submitted and approved.\n"
                            f"This message is just to confirm that you are aware of your child's leave.\n\n"
                            f"*Malayalam:*\n"
                            f"പ്രിയപ്പെട്ട രക്ഷിതാവേ,\n\n"
                            f"താങ്കളുടെ മകന്‍/മകളായ *{student.fullname()}* "
                            f"*{date.strftime('%Y-%m-%d')}* തീയതിയില്‍ അവധിയിലാണ്.\n"
                            f"അവധി അപേക്ഷ സമർപ്പിക്കുകയും അത് അംഗീകരിക്കുകയും ചെയ്തിട്ടുണ്ട്.\n"
                            f"താങ്കൾ ഈ അവധിയെക്കുറിച്ച് അറിയുന്നുവെന്ന് ഉറപ്പാക്കാനാണ് ഈ സന്ദേശം അയച്ചിരിക്കുന്നത്.\n\n"
                            f"Regards,\n"
                            f"*Oxdu Integrated Media School*"
                        )
                    else:
                        message = (
                            f"*Oxdu Integrated Media School - Attendance Notification / ഹാജര്‍ അറിയിപ്പ്*\n\n"
                            f"*English:*\n"
                            f"Dear Parent,\n\n"
                            f"This is to inform you that your child *{student.fullname()}* "
                            f"was marked absent on *{date.strftime('%B %d, %Y')}*.\n"
                            f"If there is a valid reason for the absence, kindly inform the placement officer and the teacher.\n\n"
                            f"*Malayalam:*\n"
                            f"പ്രിയപ്പെട്ട രക്ഷിതാവേ,\n\n"
                            f"താങ്കളുടെ മകന്‍/മകളായ *{student.fullname()}* "
                            f"*{date.strftime('%Y-%m-%d')}* തീയതിയില്‍ ഹാജരായിരുന്നില്ല.\n"
                            f"ആയതിനാൽ യഥാർത്ഥ കാരണം, ദയവായി പ്ലേസ്മെന്റ് ഓഫീസറേയും അധ്യാപകനേയും അറിയിക്കുക.\n\n"
                            f"Regards,\n"
                            f"*Oxdu Integrated Media School*"
                        )
                    
                    # Send SMS
                    if send_sms(phone_number, message):
                        # Mark SMS as sent
                        Attendance.objects.filter(
                            student=student,
                            register__date=date
                        ).update(sms_sent=True)
                        sms_sent_count += 1
                        print(f"✅ SMS sent to {student.fullname()}")
                    else:
                        print(f"❌ SMS failed for {student.fullname()}")
                        
                except Exception as e:
                    print(f"❌ SMS sending failed for student {student.fullname()}: {str(e)}")
                    continue
        
        response_data = {
            'success': True,
            'message': f'Attendance saved successfully for {total_attendance_created} students',
            'date': date_str,
            'total_records': total_attendance_created,
            'sms_sent': sms_sent_count,
            'sms_skipped': sms_skipped_count,
            'whatsapp_enabled': send_whatsapp,
            'batches_processed': len(students_by_batch)
        }
        
        print(f"✅ Attendance saved: {total_attendance_created} records, {sms_sent_count} SMS sent, {sms_skipped_count} SMS skipped")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Attendance save error: {str(e)}")
        print(f"Traceback: {error_details}")
        
        return JsonResponse({
            'error': 'Internal server error',
            'details': str(e)
        }, status=500)
    

@csrf_exempt
def attendance_data_api(request):
    """API endpoint to get attendance data for a specific date"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        date_str = request.GET.get('date')
        batch_id = request.GET.get('batch_id')
        course_id = request.GET.get('course_id')
        branch_id = request.GET.get('branch_id')

        if not date_str:
            return JsonResponse({'error': 'Date parameter is required'}, status=400)

        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            return JsonResponse({'error': 'Invalid date format. Expected YYYY-MM-DD'}, status=400)

        user = request.user

        # Base queryset with select_related for course and branch
        # Base queryset with select_related for course and branch
        students = Admission.objects.filter(
            is_active=True,
            batch__status='in_progress',
        ).filter(
            Q(stage_status='active') |
            Q(studentstagestatushistory__created__date__gt=selected_date)
            # Include students who were active on the selected date
            # Logic: If student is inactive now, but history shows they became inactive AFTER selected_date,
            # then they were active on selected_date. Use __date to handle same-day changes correctly (hide if changed today).
        ).distinct().select_related('batch', 'branch', 'course')

        # User permissions
        usertype = getattr(user, 'usertype', None)

        if not user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        # Store the actual branch filter for holiday checking
        actual_branch_id = None
        
        # FIXED: Mentors can see ALL students but apply filters
        if usertype == "mentor":
            # Apply filters based on selections
            if branch_id and branch_id != 'all':
                students = students.filter(branch_id=branch_id)
                actual_branch_id = branch_id
            if course_id and course_id != 'all':
                students = students.filter(course_id=course_id)
            if batch_id and batch_id != 'all':
                students = students.filter(batch__id=batch_id)

        elif usertype == "teacher":
            # FIXED: Teachers can only see students from their assigned branch and course
            employee = getattr(user, 'employee', None)
            teacher_course = getattr(employee, 'course', None) if employee else None
            teacher_branch = getattr(employee, 'branch', None) if employee else None
            
            if not teacher_course or not teacher_branch:
                return JsonResponse({'error': 'Teacher must be assigned to a course and branch'}, status=403)
            
            # Teachers can only see students from their assigned branch and course
            students = students.filter(
                branch=teacher_branch,
                course=teacher_course
            )
            actual_branch_id = str(teacher_branch.id)
            
            # Apply batch filter if selected
            if batch_id and batch_id != 'all':
                students = students.filter(batch__id=batch_id)

        elif usertype == "branch_staff":
            if user.branch:
                students = students.filter(branch=user.branch)
                actual_branch_id = str(user.branch.id)
                # Apply additional filters
                if course_id and course_id != 'all':
                    students = students.filter(course_id=course_id)
                if batch_id and batch_id != 'all':
                    students = students.filter(batch__id=batch_id)

        elif usertype in ["admin_staff", "ceo", "cfo", "coo", "hr", "cmo"] or user.is_superuser:
            # Admin users - apply filters based on selections
            if branch_id and branch_id != 'all':
                students = students.filter(branch_id=branch_id)
                actual_branch_id = branch_id
            if course_id and course_id != 'all':
                students = students.filter(course_id=course_id)
            if batch_id and batch_id != 'all':
                students = students.filter(batch__id=batch_id)
        else:
            user_branch = getattr(user, 'branch', None)
            if user_branch:
                students = students.filter(branch=user_branch)
                actual_branch_id = str(user_branch.id)
                # Apply additional filters
                if course_id and course_id != 'all':
                    students = students.filter(course_id=course_id)
                if batch_id and batch_id != 'all':
                    students = students.filter(batch__id=batch_id)

        # IMPROVED HOLIDAY CHECKING: Consider branch-specific holidays
        is_holiday = False
        holiday_type = None
        holiday_name = None
        holiday_scope = None
        holiday_branches = []
        
        # Check for auto holidays first (Sundays, Second Saturdays)
        is_auto_holiday, auto_holiday_name = Holiday.is_auto_holiday(selected_date)
        if is_auto_holiday:
            is_holiday = True
            holiday_type = 'auto'
            holiday_name = auto_holiday_name
            holiday_scope = 'all'
        
        # Check for manual holidays
        try:
            Holiday._meta.get_field('is_auto_holiday')
            manual_holidays = Holiday.objects.filter(
                is_active=True,
                date=selected_date,
                is_auto_holiday=False
            )
        except FieldDoesNotExist:
            manual_holidays = Holiday.objects.filter(
                is_active=True,
                date=selected_date
            )
        
        for holiday in manual_holidays:
            if holiday.scope == 'all':
                # All-branch holiday applies to everyone
                is_holiday = True
                holiday_type = 'manual'
                holiday_name = holiday.name
                holiday_scope = 'all'
                break
            elif holiday.scope == 'branch' and actual_branch_id:
                # Branch-specific holiday - check if it applies to the selected branch
                holiday_branch_ids = list(holiday.branch.values_list('id', flat=True))
                holiday_branches = holiday_branch_ids
                
                # Convert to string for comparison
                holiday_branch_ids_str = [str(bid) for bid in holiday_branch_ids]
                
                if actual_branch_id in holiday_branch_ids_str:
                    is_holiday = True
                    holiday_type = 'manual'
                    holiday_name = holiday.name
                    holiday_scope = 'branch'
                    break
        
        # If it's a holiday, return holiday response
        if is_holiday:
            students_by_batch = {}
            for s in students.order_by('batch__batch_name', 'first_name'):
                batch_name = s.batch.batch_name if s.batch else 'No Batch'
                course_name = s.course.name if s.course else 'N/A'
                branch_name = s.branch.name if s.branch else 'N/A'
                
                students_by_batch.setdefault(batch_name, []).append({
                    'id': s.id,
                    'fullname': s.fullname(),
                    'batch_name': batch_name,
                    'course_name': course_name,
                    'branch_name': branch_name,
                    'course': {
                        'id': s.course.id if s.course else None,
                        'name': course_name
                    },
                    'branch': {
                        'id': s.branch.id if s.branch else None,
                        'name': branch_name
                    },
                    'status': 'Holiday',
                    'sms_sent': True,
                    'is_holiday': True,
                    'holiday_type': holiday_type,
                    'holiday_name': holiday_name
                })

            return JsonResponse({
                'success': True, 
                'students_by_batch': students_by_batch,
                'is_holiday': True,
                'holiday_type': holiday_type,
                'holiday_name': holiday_name,
                'holiday_scope': holiday_scope,
                'holiday_branches': holiday_branches
            })

        # Normal attendance flow for non-holidays
        attendance_records = {}
        sms_status_records = {}
        registers = AttendanceRegister.objects.filter(date=selected_date)
        for reg in registers:
            for record in Attendance.objects.filter(register=reg):
                attendance_records[record.student.id] = record.status
                sms_status_records[record.student.id] = record.sms_sent

        students_by_batch = {}
        for s in students.order_by('batch__batch_name', 'first_name'):
            batch_name = s.batch.batch_name if s.batch else 'No Batch'
            course_name = s.course.name if s.course else 'N/A'
            branch_name = s.branch.name if s.branch else 'N/A'
            
            students_by_batch.setdefault(batch_name, []).append({
                'id': s.id,
                'fullname': s.fullname(),
                'batch_name': batch_name,
                'course_name': course_name,
                'branch_name': branch_name,
                'course': {
                    'id': s.course.id if s.course else None,
                    'name': course_name
                },
                'branch': {
                    'id': s.branch.id if s.branch else None,
                    'name': branch_name
                },
                'status': attendance_records.get(s.id, 'Absent'),
                'sms_sent': sms_status_records.get(s.id, False),
                'is_holiday': False
            })

        return JsonResponse({
            'success': True, 
            'students_by_batch': students_by_batch, 
            'is_holiday': False
        }, status=200)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)
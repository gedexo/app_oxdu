# employees/api.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from fcm_django.models import FCMDevice
import logging
import time
import json

logger = logging.getLogger(__name__)

class RegisterDeviceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Register device for FCM notifications
        Expected JSON: {"token": "fcm_token", "type": "web", "name": "device_name"}
        """
        try:
            # Enhanced logging
            logger.info(f"🔔 Device registration attempt for user: {request.user.id} ({request.user.usertype})")
            logger.info(f"Request data: {request.data}")
            logger.info(f"User agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
            
            token = request.data.get("token") or request.data.get("registration_id")
            device_type = request.data.get("type", "web").lower()
            device_name = request.data.get("name") or f"{request.user.usertype} - {request.META.get('HTTP_USER_AGENT', '')[:100]}"

            if not token:
                logger.warning("❌ No FCM token provided in request")
                return Response(
                    {"detail": "FCM token is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            logger.info(f"Token received (first 50 chars): {token[:50]}...")
            logger.info(f"Device type: {device_type}")
            logger.info(f"Device name: {device_name}")

            # Validate device type
            valid_types = ['android', 'ios', 'web']
            if device_type not in valid_types:
                device_type = 'web'
                logger.info(f"Device type normalized to: {device_type}")

            # Check if this token already exists for any user
            existing_device = FCMDevice.objects.filter(registration_id=token).first()
            
            if existing_device:
                logger.info(f"📱 Existing device found: ID {existing_device.id}, User: {existing_device.user_id}")
                
                # If token exists but for different user, update it
                if existing_device.user != request.user:
                    old_user = existing_device.user_id
                    existing_device.user = request.user
                    existing_device.active = True
                    existing_device.type = device_type
                    if hasattr(FCMDevice, "name"):
                        existing_device.name = device_name
                    existing_device.save()
                    
                    logger.info(f"✅ Device token reassigned from user {old_user} to user {request.user.id}")
                    return Response({
                        "status": "reassigned",
                        "message": "Device reassigned to current user",
                        "registration_id": existing_device.registration_id,
                        "type": existing_device.type,
                        "device_id": existing_device.id,
                        "previous_user": old_user,
                        "current_user": request.user.id
                    }, status=status.HTTP_200_OK)
                else:
                    # Token already exists for this user, just update
                    existing_device.active = True
                    existing_device.type = device_type
                    if hasattr(FCMDevice, "name"):
                        existing_device.name = device_name
                    existing_device.save()
                    
                    logger.info(f"✅ Device token updated for user {request.user.id}")
                    return Response({
                        "status": "updated",
                        "message": "Device already registered and updated",
                        "registration_id": existing_device.registration_id,
                        "type": existing_device.type,
                        "device_id": existing_device.id
                    }, status=status.HTTP_200_OK)
            else:
                # Create new device
                device_data = {
                    "user": request.user,
                    "registration_id": token,
                    "type": device_type,
                    "active": True,
                }
                
                # Add name if the model supports it
                if hasattr(FCMDevice, "name"):
                    device_data["name"] = device_name
                
                device = FCMDevice.objects.create(**device_data)
                
                logger.info(f"✅ New device created: ID {device.id} for user {request.user.id}")
                logger.info(f"Device details: {device.__dict__}")
                
                # Count user's active devices
                user_devices_count = FCMDevice.objects.filter(user=request.user, active=True).count()
                logger.info(f"User now has {user_devices_count} active device(s)")
                
                return Response({
                    "status": "created",
                    "message": "New device registered successfully",
                    "registration_id": device.registration_id,
                    "type": device.type,
                    "device_id": device.id,
                    "total_devices": user_devices_count
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"❌ Device registration error: {str(e)}", exc_info=True)
            return Response(
                {"detail": f"Internal server error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_devices(request):
    """Get all devices for the current user"""
    try:
        devices = FCMDevice.objects.filter(user=request.user).order_by('-id')
        
        device_list = []
        for device in devices:
            device_list.append({
                "id": device.id,
                "registration_id": device.registration_id[:50] + "..." if device.registration_id else None,
                "type": device.type,
                "name": getattr(device, 'name', 'N/A'),
                "active": device.active,
                "created": device.date_created.isoformat() if hasattr(device, 'date_created') else 'N/A'
            })
        
        return Response({
            "success": True,
            "devices": device_list,
            "total_devices": len(device_list),
            "active_devices": devices.filter(active=True).count()
        })
        
    except Exception as e:
        logger.error(f"Error fetching devices: {str(e)}")
        return Response({
            "success": False,
            "error": str(e)
        }, status=500)
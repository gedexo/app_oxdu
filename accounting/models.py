from django.db import models
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from mptt.models import MPTTModel
from mptt.models import TreeForeignKey
from simple_history.models import HistoricalRecords
from django.utils.functional import cached_property
from django.db.models import Sum

from core.base import BaseModel
from core.choices import ACCOUNTING_MASTER_CHOICES, MAIN_GROUP_CHOICES
from accounting.constants import LOCKED_ACCOUNT_CHOICES, ACCOUNT_GROUP_CHOICES


class GroupMaster(MPTTModel, BaseModel):
    branch = models.ForeignKey('branches.Branch', on_delete=models.CASCADE)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subgroups')
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    nature_of_group = models.CharField(max_length=30, choices=ACCOUNTING_MASTER_CHOICES)
    main_group = models.CharField(max_length=30, choices=MAIN_GROUP_CHOICES)
    is_locked = models.BooleanField(default=False)
    locking_group = models.CharField(max_length=50, choices=ACCOUNT_GROUP_CHOICES, null=True, blank=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        unique_together = [['branch', 'code']]
        ordering = ['main_group', 'code']

    def clean(self):
        """Validate group master"""
        super().clean()
        
        # NEW: Validate parent is in same branch/company
        if self.parent:
            if self.parent.branch_id != self.branch_id:
                raise ValidationError({
                    'parent': 'Parent group must be in the same branch'
                })
            
            # Prevent circular reference
            if self.parent == self:
                raise ValidationError({
                    'parent': 'Group cannot be its own parent'
                })

    def get_full_path(self):
        """Returns full hierarchical path of the group"""
        path = []
        current = self
        while current:
            path.insert(0, current.name)
            current = current.parent
        return ' > '.join(path)

    @property
    def is_parent(self):
        return not self.parent and self.subgroups.exists()

    @property
    def is_child(self):
        return self.parent is not None

    
class Account(BaseModel):
    LEDGER_TYPES = (('STUDENT', 'Student'), ('EMPLOYEE', 'Employee'), ('GENERAL', 'General Ledger'))
    # Branch and Price Slab
    branch = models.ForeignKey('branches.Branch', on_delete=models.CASCADE, null=True, blank=True)
    ledger_type = models.CharField(max_length=15, choices=LEDGER_TYPES, default='GENERAL')
    opening_transaction =models.OneToOneField('transactions.Transaction',on_delete=models.SET_NULL,null=True,blank=True)
    # Identification
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    alias_name = models.CharField(max_length=150, blank=True, null=True)
    under = TreeForeignKey(GroupMaster, on_delete=models.CASCADE)
   
    #Credit
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    credit_days = models.PositiveIntegerField(null=True, blank=True)
    credit_bill = models.CharField(max_length=120, null=True, blank=True)
    # Lock Status
    is_locked = models.BooleanField(default=False)
    locking_account = models.CharField(max_length=40, choices=LOCKED_ACCOUNT_CHOICES, null=True, blank=True)

    class Meta:
        unique_together = ("branch", "code")
        indexes = [
            models.Index(fields=['ledger_type']),
            models.Index(fields=['branch', 'ledger_type']),
            models.Index(fields=['branch', 'under']),
            models.Index(fields=['branch', 'code']),
            models.Index(fields=['is_locked']),
        ]

    def __str__(self):
        if self.alias_name:
            return f"{self.name} | {self.alias_name}"
        return self.name

    @cached_property
    def current_balance(self):
        from transactions.models import TransactionEntry
        aggregates = TransactionEntry.objects.filter(account=self).aggregate(
            total_debit=Sum('debit_amount'),
            total_credit=Sum('credit_amount')
        )
        return round((aggregates['total_debit'] or 0) - (aggregates['total_credit'] or 0), 2)
        

    @property
    def current_balance_type(self):
        """
        Determine the current balance type (DR/CR) based on the calculated balance
        Returns: 'DR' if positive balance, 'CR' if negative balance
        """
        balance = self.current_balance
        
        # For all accounts, positive balance = DR, negative balance = CR
        # This follows standard accounting where:
        # - Assets/Expenses increase with debits (positive)
        # - Liabilities/Equity/Income increase with credits (negative in our calculation)
        return 'DR' if balance >= 0 else 'CR'

    @property
    def current_balance_absolute(self):
        """
        Get the absolute value of current balance (always positive)
        Returns: Absolute decimal value
        """
        return abs(self.current_balance)

    def get_balance_as_of_date(self, as_of_date):
        """
        Calculate balance as of a specific date
        Args:
            as_of_date: Date to calculate balance up to
        Returns: Decimal value representing balance as of the specified date
        """
        from transactions.models import TransactionEntry
        
        # Get transaction entries up to the specified date (includes opening balance)
        entries = TransactionEntry.objects.filter(
            account=self,
            transaction__date__lte=as_of_date
        )
        
        # Calculate total debits and credits up to date
        total_debits = entries.aggregate(
            total_dr=Sum('debit_amount')
        )['total_dr'] or Decimal('0.00')
        
        total_credits = entries.aggregate(
            total_cr=Sum('credit_amount')
        )['total_cr'] or Decimal('0.00')
        
        # Balance as of date is simply net movement (debits - credits)
        # Opening balance is already included in the transaction entries
        balance_as_of_date = total_debits - total_credits
        
        return round(balance_as_of_date,2)

    def get_balance_between_dates(self, start_date, end_date):
        """
        Calculate balance movement between two dates
        Args:
            start_date: Start date for calculation
            end_date: End date for calculation
        Returns: Decimal value representing net movement between dates
        """
        from transactions.models import TransactionEntry
        
        # Get transaction entries within date range
        entries = TransactionEntry.objects.filter(
            account=self,
            transaction__date__gte=start_date,
            transaction__date__lte=end_date
        )
        
        # Calculate total debits and credits in the period
        total_debits = entries.aggregate(
            total_dr=Sum('debit_amount')
        )['total_dr'] or Decimal('0.00')
        
        total_credits = entries.aggregate(
            total_cr=Sum('credit_amount')
        )['total_cr'] or Decimal('0.00')
        
        # Return net movement (debits - credits)
        return round(total_debits - total_credits,2)

    @property
    def is_overdue(self):
        """
        Check if account has overdue amounts (for customer/supplier accounts)
        Returns: Boolean indicating if account is overdue
        """
        if self.ledger_type not in ['CUSTOMER', 'SUPPLIER'] or not self.credit_days:
            return False
        
        from django.utils import timezone
        from datetime import timedelta
        
        # Check for transactions older than credit days with outstanding balance
        cutoff_date = timezone.now().date() - timedelta(days=self.credit_days)
        balance_as_of_cutoff = self.get_balance_as_of_date(cutoff_date)
        
        # For customers, positive balance means outstanding receivables
        # For suppliers, negative balance means outstanding payables
        if self.ledger_type == 'CUSTOMER':
            return balance_as_of_cutoff > 0
        elif self.ledger_type == 'SUPPLIER':
            return balance_as_of_cutoff < 0
        
        return False

    @property
    def available_credit(self):
        """
        Calculate available credit limit for customer/supplier accounts
        Returns: Decimal value of available credit (None if no credit limit set)
        """
        if not self.credit_limit:
            return None
        
        current_balance = self.current_balance
        
        # For customers, credit limit is against outstanding receivables
        if self.ledger_type == 'CUSTOMER':
            return self.credit_limit - max(current_balance, Decimal('0.00'))
        # For suppliers, credit limit is against outstanding payables  
        elif self.ledger_type == 'SUPPLIER':
            return self.credit_limit - max(abs(current_balance), Decimal('0.00'))
        
        return self.credit_limit
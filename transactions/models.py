from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy

from core.base import BaseModel
import core.choices

class Transaction(BaseModel):

    # --------------------
    # CHOICES
    # --------------------
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    TRANSACTION_TYPE_CHOICES = [
        ('course_fee', 'Course Fee'),
        ('payroll', 'Payroll'),
        ('sale_invoice', 'Sale Invoice'),
        ('sale_order', 'Sale Order'),
        ('sale_return', 'Sale Return'),
        ('credit_note', 'Credit Note'),
        ('purchase_invoice', 'Purchase Invoice'),
        ('purchase_order', 'Purchase Order'),
        ('purchase_return', 'Purchase Return'),
        ('debit_note', 'Debit Note'),
        ('receipt', 'Receipt'),
        ('payment', 'Payment'),
        ('journal_voucher', 'Journal Voucher'),
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('opening_balance', 'Opening Balance'),
        ('opening_stock', 'Opening Stock'),
        ('stock_adjustment', 'Stock Adjustment'),
        ('stock_transfer', 'Stock Transfer'),
        ('contra', 'Contra Voucher'),
        ('stakeholder_investment', 'Stakeholder Investment'),
        ('stakeholder_withdrawal', 'Stakeholder Withdrawal'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    PAYMENT_TERMS = [
        ('IMMEDIATE', 'Immediate Payment'),
        ('7D', '7 Days'),
        ('15D', '15 Days'),
        ('30D', '30 Days'),
        ('45D', '45 Days'),
        ('60D', '60 Days'),
        ('90D', '90 Days'),
    ]

    # --------------------
    # BASIC INFO
    # --------------------
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    transaction_type = models.CharField(
        max_length=30,
        choices=TRANSACTION_TYPE_CHOICES,
        db_index=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True
    )

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal'
    )

    voucher_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True
    )

    is_double_entry = models.BooleanField(default=False)

    external_reference = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="PO number / External reference"
    )

    # --------------------
    # DATES
    # --------------------
    date = models.DateTimeField(default=timezone.now, db_index=True)

    payment_term = models.CharField(
        max_length=20,
        choices=PAYMENT_TERMS,
        null=True,
        blank=True
    )

    due_date = models.DateField(null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)

    # --------------------
    # DESCRIPTION
    # --------------------
    reference = models.CharField(max_length=100, null=True, blank=True)
    narration = models.TextField(null=True, blank=True)
    remark = models.TextField(null=True, blank=True)

    attachment = models.FileField(
        upload_to="transactions/",
        null=True,
        blank=True
    )

    # --------------------
    # AMOUNTS
    # --------------------
    invoice_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )

    received_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )

    balance_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )

    outstanding_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )

    outstanding_type = models.CharField(
        max_length=2,
        choices=[('DR', 'DR'), ('CR', 'CR')],
        default='DR'
    )

    total_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )

    # --------------------
    # STRING
    # --------------------
    def __str__(self):
        branch_name = self.branch.name if self.branch else "No Branch"
        return f"{branch_name} | {self.get_transaction_type_display()}"

    # --------------------
    # VALIDATION
    # --------------------
    def clean(self):
        super().clean()

        if self.due_date and self.date:
            if self.due_date < self.date.date():
                raise ValidationError("Due date cannot be before transaction date.")

        if self.received_amount < 0:
            raise ValidationError("Received amount cannot be negative.")

        if self.invoice_amount < 0:
            raise ValidationError("Invoice amount cannot be negative.")

        if self.received_amount > self.invoice_amount:
            raise ValidationError("Received amount cannot exceed invoice amount.")

        if self.balance_amount < 0:
            raise ValidationError("Balance amount cannot be negative.")

    # --------------------
    # PROPERTIES
    # --------------------
    @property
    def is_paid(self):
        return self.balance_amount <= Decimal('0.00')

    @property
    def is_overdue(self):
        if not self.due_date or self.is_paid:
            return False
        return self.due_date < timezone.now().date()

    @property
    def payment_status(self):
        if self.received_amount == Decimal('0.00'):
            return 'unpaid'
        if self.received_amount >= self.invoice_amount:
            return 'paid'
        return 'partial'

    @property
    def days_overdue(self):
        if not self.is_overdue:
            return 0
        return (timezone.now().date() - self.due_date).days

    # --------------------
    # ACTIONS
    # --------------------
    def approve(self):
        if self.status == 'pending_approval':
            self.status = 'approved'
            self.save(update_fields=['status'])
            return True
        return False

    def post(self):
        if self.status not in ('draft', 'approved'):
            return False

        summary = self.get_entries_summary()
        if not summary['is_balanced']:
            raise ValidationError("Debit and Credit totals must match.")

        self.status = 'posted'
        self.save(update_fields=['status', 'voucher_number'])
        return True

    def cancel(self, reason=None):
        if self.status == 'cancelled':
            return False

        self.status = 'cancelled'
        if reason:
            self.remark = f"Cancelled: {reason}"
        self.save(update_fields=['status', 'remark'])
        return True

    def add_payment(self, amount):
        amount = Decimal(str(amount))
        if amount <= 0:
            return False

        new_received = self.received_amount + amount
        if new_received > self.invoice_amount:
            raise ValidationError("Payment exceeds invoice amount.")

        self.received_amount = new_received
        self.balance_amount = self.invoice_amount - new_received
        self.save(update_fields=['received_amount', 'balance_amount'])
        return True

    # --------------------
    # ENTRIES
    # --------------------
    def get_entries_summary(self):
        entries = self.entries.all()

        total_debits = sum(
            (e.debit_amount or Decimal('0.00')) for e in entries
        )
        total_credits = sum(
            (e.credit_amount or Decimal('0.00')) for e in entries
        )

        return {
            'total_debits': total_debits,
            'total_credits': total_credits,
            'entry_count': entries.count(),
            'is_balanced': total_debits == total_credits,
        }
    


class TransactionEntry(BaseModel):
    transaction = models.ForeignKey(Transaction, related_name='entries', on_delete=models.CASCADE)
    account = models.ForeignKey('accounting.Account', on_delete=models.CASCADE)
    debit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Transaction Entries"
        indexes = [
            models.Index(fields=['transaction', 'account']),
            models.Index(fields=['account', 'debit_amount']),
            models.Index(fields=['account', 'credit_amount']),
        ]
        constraints = [
            # UPDATED: Not both debit and credit
            models.CheckConstraint(
                check=~(models.Q(debit_amount__gt=0) & models.Q(credit_amount__gt=0)),
                name='not_both_debit_and_credit'
            ),
            # NEW: Must have at least one amount
            models.CheckConstraint(
                check=models.Q(debit_amount__gt=0) | models.Q(credit_amount__gt=0),
                name='entry_has_amount'
            ),
            # NEW: Amounts must be non-negative
            models.CheckConstraint(
                check=models.Q(debit_amount__gte=0),
                name='debit_amount_non_negative'
            ),
            models.CheckConstraint(
                check=models.Q(credit_amount__gte=0),
                name='credit_amount_non_negative'
            ),
        ]

    def __str__(self):
        amount = self.debit_amount if self.debit_amount > 0 else self.credit_amount
        entry_type = "DR" if self.debit_amount > 0 else "CR"
        return f"{self.account} - {entry_type}: {amount}"
    

    @property
    def amount(self):
        """Get the non-zero amount"""
        return self.debit_amount if self.debit_amount > 0 else self.credit_amount

    @property
    def is_debit(self):
        """Check if this is a debit entry"""
        return self.debit_amount > 0

    @property
    def is_credit(self):
        """Check if this is a credit entry"""
        return self.credit_amount > 0

    def get_update_url(self):
        return self.transaction.get_update_url()
    
    def get_ledger_report_url(self):
        return reverse_lazy('reports:ledger_report') + f'?account={self.account.id}'


class IncomeExpense(BaseModel):
    INCOME_EXPENSE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    
    # Link to the main transaction record
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        related_name='income_expense_detail'
    )
    
    # Branch field (same as transaction's branch)
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Branch associated with this income/expense"
    )
    
    # Type: Income or Expense
    type = models.CharField(
        max_length=10,
        choices=INCOME_EXPENSE_CHOICES,
        db_index=True
    )
    
    # Cash/Bank account where money flows in/out (the cash account)
    party = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='income_expenses',
        help_text="Cash or bank account for the transaction"
    )
    
    # Income/Expense category account (the income/expense account)
    category = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='income_expense_category',
        help_text="Income or expense category account"
    )
    
    # Amount of the income/expense
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount of the income or expense"
    )
    
    # Payment method
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=core.choices.PAYMENT_METHOD_CHOICES,
        help_text="Method of payment received/spent"
    )
    
    # Reference number
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Reference number for the transaction"
    )
    
    # Description
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed description of the income or expense"
    )
    
    # Date of the transaction
    date = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Date of the income or expense transaction"
    )
    
    # Attachment
    attachment = models.FileField(
        upload_to="income_expense/",
        null=True,
        blank=True,
        help_text="Supporting document for the transaction"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Income/Expense"
        verbose_name_plural = "Income/Expenses"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['type', 'date']),
            models.Index(fields=['party']),
            models.Index(fields=['category']),
            models.Index(fields=['branch']),
        ]
    
    def __str__(self):
        branch_name = self.branch.name if self.branch else "No Branch"
        return f"{self.get_type_display()} - {self.amount} - {branch_name}"
    

    
    def clean(self):
        super().clean()
        # Validate that both party and category are set for proper accounting
        if not self.party and not self.category:
            raise ValidationError("Both cash account (party) and category account must be selected.")
        elif not self.party:
            raise ValidationError("Cash account (party) must be selected.")
        elif not self.category:
            raise ValidationError("Income/Expense category account must be selected.")
    
    def save(self, *args, **kwargs):
        # Set the amount from the transaction if not provided
        if self.amount == Decimal('0.00') and hasattr(self, 'transaction'):
            self.amount = self.transaction.invoice_amount
        # Synchronize branch with transaction's branch
        if hasattr(self, 'transaction') and self.transaction:
            self.branch = self.transaction.branch
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        if self.type == 'income':
            return reverse('transactions:income_detail', kwargs={'pk': self.pk})
        else:
            return reverse('transactions:expense_detail', kwargs={'pk': self.pk})



class ContraVoucher(BaseModel):
    transaction = models.OneToOneField(
        'transactions.Transaction', 
        on_delete=models.CASCADE, 
        primary_key=True
    )
    from_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.PROTECT,
        related_name='contra_from',
        help_text="Source account (Cash/Bank)",
        limit_choices_to={'under__locking_group__in': ['CASH_ACCOUNT', 'BANK_ACCOUNT']},
    )
    
    to_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.PROTECT,
        related_name='contra_to',
        help_text="Destination account (Cash/Bank)",
        limit_choices_to={'under__locking_group__in': ['CASH_ACCOUNT', 'BANK_ACCOUNT']},
    )
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Transfer amount"
    )
    cheque_number = models.CharField(max_length=50, null=True, blank=True, verbose_name="Cheque/Reference Number")
    cheque_date = models.DateField(null=True, blank=True, verbose_name="Cheque/Transaction Date")
    bank_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Bank Name")
    is_denomination = models.BooleanField(default=False)
    # ... denomination fields ...
    denomination_500 = models.PositiveIntegerField(null=True, blank=True, verbose_name="₹500 Notes")
    denomination_200 = models.PositiveIntegerField(null=True, blank=True, verbose_name="₹200 Notes")
    denomination_100 = models.PositiveIntegerField(null=True, blank=True, verbose_name="₹100 Notes")
    denomination_50 = models.PositiveIntegerField(null=True, blank=True, verbose_name="₹50 Notes")
    denomination_20 = models.PositiveIntegerField(null=True, blank=True, verbose_name="₹20 Notes")
    denomination_10 = models.PositiveIntegerField(null=True, blank=True, verbose_name="₹10 Notes")
    denomination_5 = models.PositiveIntegerField(null=True, blank=True, verbose_name="₹5 Coins")
    denomination_2 = models.PositiveIntegerField(null=True, blank=True, verbose_name="₹2 Coins")
    denomination_1 = models.PositiveIntegerField(null=True, blank=True, verbose_name="₹1 Coins")
    
    transaction_mode = models.CharField(
        max_length=20,
        choices=[
            ('cheque', 'Cheque'),
            ('dd', 'Demand Draft'),
            ('neft', 'NEFT'),
            ('rtgs', 'RTGS'),
            ('imps', 'IMPS'),
            ('upi', 'UPI'),
            ('cash', 'Cash'),
        ],
        default='cash',
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['-transaction__date', '-created']
        indexes = [
            models.Index(fields=['from_account', 'to_account']),
            models.Index(fields=['transaction']),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(from_account=models.F('to_account')),
                name='contra_different_accounts'
            ),
            models.CheckConstraint(
                check=models.Q(amount__gt=0),
                name='contra_amount_positive'
            ),
        ]

    def __str__(self):
        return f"Contra: {self.from_account.name} → {self.to_account.name} - ₹{self.amount}"
    
    def clean(self):
        """Validate contra voucher"""
        super().clean()
        
        valid_groups = ['CASH_ACCOUNT', 'BANK_ACCOUNT']
        
        if self.from_account:
            from_group = getattr(self.from_account.under, 'locking_group', None)
            if from_group not in valid_groups:
                raise ValidationError({
                    'from_account': f'Source account must be Cash or Bank account. Got: {from_group}'
                })
        
        if self.to_account:
            to_group = getattr(self.to_account.under, 'locking_group', None)
            if to_group not in valid_groups:
                raise ValidationError({
                    'to_account': f'Destination account must be Cash or Bank account. Got: {to_group}'
                })
        
        if self.from_account and self.to_account:
            if self.from_account == self.to_account:
                raise ValidationError('Source and destination accounts cannot be the same')
        
        if self.is_denomination and self.amount:
            denomination_total = self.calculate_denomination_total()
            if denomination_total != self.amount:
                raise ValidationError(
                    f'Denomination total (₹{denomination_total}) does not match transfer amount (₹{self.amount})'
                )
    
    def calculate_denomination_total(self):
        total = Decimal('0')
        denominations = {
            500: self.denomination_500 or 0,
            200: self.denomination_200 or 0,
            100: self.denomination_100 or 0,
            50: self.denomination_50 or 0,
            20: self.denomination_20 or 0,
            10: self.denomination_10 or 0,
            5: self.denomination_5 or 0,
            2: self.denomination_2 or 0,
            1: self.denomination_1 or 0,
        }
        for value, count in denominations.items():
            total += Decimal(str(value * count))
        return total
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.transaction:
            self.transaction.invoice_amount = self.amount
            self.transaction.total_amount = self.amount
            self.transaction.balance_amount = Decimal('0.00')
            self.transaction.save(update_fields=['invoice_amount', 'total_amount', 'balance_amount'])
    
    def get_transfer_type(self):
        from_group = getattr(self.from_account.under, 'locking_group', None)
        to_group = getattr(self.to_account.under, 'locking_group', None)
        
        if from_group == 'BANK_ACCOUNT' and to_group == 'CASH_ACCOUNT':
            return 'Cash Withdrawal'
        elif from_group == 'CASH_ACCOUNT' and to_group == 'BANK_ACCOUNT':
            return 'Cash Deposit'
        elif from_group == 'BANK_ACCOUNT' and to_group == 'BANK_ACCOUNT':
            return 'Bank Transfer'
        elif from_group == 'CASH_ACCOUNT' and to_group == 'CASH_ACCOUNT':
            return 'Cash Transfer'
        return 'Fund Transfer'
    
    def create_accounting_entries(self):
        from transactions.models import TransactionEntry
        TransactionEntry.objects.filter(transaction=self.transaction).delete()
        
        voucher_no = self.transaction.voucher_number
        date_str = self.transaction.date.strftime('%d/%m/%Y')
        transfer_type = self.get_transfer_type()
        
        TransactionEntry.objects.create(
            transaction=self.transaction,
            account=self.to_account,
            debit_amount=self.amount,
            credit_amount=Decimal('0.00'),
            description=f"{transfer_type} - Contra Voucher No. {voucher_no} dated {date_str} - Amount received from {self.from_account.name}",
            creator=self.creator
        )
        
        TransactionEntry.objects.create(
            transaction=self.transaction,
            account=self.from_account,
            debit_amount=Decimal('0.00'),
            credit_amount=self.amount,
            description=f"{transfer_type} - Contra Voucher No. {voucher_no} dated {date_str} - Amount transferred to {self.to_account.name}",
            creator=self.creator
        )
    
    def get_absolute_url(self):
        return reverse_lazy('transactions:contravoucher_update', kwargs={'pk': self.pk})
from django.contrib import admin
from .models import Transaction, TransactionEntry
from core.base import BaseAdmin


class TransactionEntryInline(admin.TabularInline):
    model = TransactionEntry
    extra = 1
    fields = (
        'account',
        'debit_amount',
        'credit_amount',
        'description',
    )
    autocomplete_fields = ('account',)


@admin.register(Transaction)
class TransactionAdmin(BaseAdmin):
    list_display = (
        'voucher_number',
        'transaction_type',
        'status',
        'date',
        'invoice_amount',
    )

    list_filter = BaseAdmin.list_filter + (
        'transaction_type',
        'status',
        'date',
    )

    search_fields = (
        'voucher_number',
        'reference',
        'narration',
    )

    inlines = (TransactionEntryInline,)
    date_hierarchy = 'date'
    autocomplete_fields = ()

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'transaction_type',
                'status',
                'priority',
            )
        }),
        ('Reference Details', {
            'fields': (
                'voucher_number',
                'external_reference',
                'reference',
            )
        }),
        ('Dates', {
            'fields': (
                'date',
                'due_date',
                'delivery_date',
            )
        }),
        ('Amounts', {
            'fields': (
                'invoice_amount',
                'received_amount',
                'balance_amount',
            )
        }),
        ('Additional Information', {
            'fields': (
                'narration',
                'remark',
                'attachment',
            ),
            'classes': ('collapse',),
        }),
    )


@admin.register(TransactionEntry)
class TransactionEntryAdmin(BaseAdmin):
    list_display = (
        'transaction',
        'account',
        'debit_amount',
        'credit_amount',
    )

    list_filter = BaseAdmin.list_filter + (
        'transaction__transaction_type',
    )

    search_fields = (
        'transaction__voucher_number',
        'account__name',
        'description',
    )

    autocomplete_fields = (
        'transaction',
        'account',
    )
from django.contrib import admin
from core.base import BaseAdmin
from .models import Account, GroupMaster

@admin.register(Account)
class AccountAdmin(BaseAdmin):
    list_display = ['code', 'name', 'ledger_type', 'under', 'branch']
    list_filter = BaseAdmin.list_filter + (
        'ledger_type',
        'branch',
        'under',
        'is_locked',
    )
    search_fields = ['code', 'name', 'alias_name']
    autocomplete_fields = ['under']
    readonly_fields = ['current_balance', 'current_balance_type']


@admin.register(GroupMaster)
class GroupMasterAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'main_group', 'nature_of_group', 'is_locked', 'branch']
    list_filter = ['main_group', 'nature_of_group', 'is_locked', 'branch']
    search_fields = ['code', 'name']
    autocomplete_fields = ['parent']
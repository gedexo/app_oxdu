from django.contrib import admin
from core.base import BaseAdmin
from .models import Branch

@admin.register(Branch)
class BranchAdmin(BaseAdmin):
    pass

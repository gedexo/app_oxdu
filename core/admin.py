from .base import BaseAdmin
from .models import Link, CompanyProfile
from django.contrib import admin


@admin.register(Link)
class LinkAdmin(BaseAdmin):
    readonly_fields = ()
    search_fields = ("view", "name", "value", "module", "description")
    paginate_by = 300
    list_display = ("view", "module", "name", "gen_link", "employee_access", "admin_staff_access")
    list_filter = ("module", "view_type", "is_hidden", "is_dashboard_link", "created", "employee_access", "admin_staff_access")
    list_editable = ("employee_access", "admin_staff_access")


@admin.register(CompanyProfile)
class CompanyProfileAdmin(BaseAdmin):
    readonly_fields = ()
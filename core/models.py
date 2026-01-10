from core.choices import MODULE_CHOICES
from core.choices import MONTH_CHOICES
from core.choices import VIEW_TYPE_CHOICES
from core.choices import YEAR_CHOICES

from .base import BaseModel
from django.db import models
from django.urls import reverse_lazy


class Setting(BaseModel):
    instance_id = models.CharField(max_length=50, null=True)
    access_token = models.CharField(max_length=50, null=True)

    def __str__(self):
        return str(self.access_token)

    class Meta:
        verbose_name = "Settings"
        verbose_name_plural = "Settings"


class Link(models.Model):
    """
    A model representing a link, which can be displayed in the application.
    """

    value = models.CharField("Title", max_length=200, blank=True, null=True)
    description = models.CharField(max_length=200)
    module = models.CharField(max_length=200, choices=MODULE_CHOICES)
    view = models.CharField(max_length=200)
    name = models.CharField(max_length=200, unique=True)
    view_type = models.CharField(max_length=200, choices=VIEW_TYPE_CHOICES)
    is_dashboard_link = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    is_quick_access = models.BooleanField(default=False)
    created = models.DateTimeField(db_index=True, auto_now_add=True)

    employee_access = models.BooleanField(default=True)
    admin_staff_access = models.BooleanField(default=False)

    class Meta:
        ordering = ("view",)

    def gen_link(self):
        name = self.name.split(".")
        if self.view_type in ["CreateView", "DashboardView", "ListView", "TemplateView", "View"]:
            try:
                return reverse_lazy(f"{name[0]}:{name[1]}") if len(name) == 2 else reverse_lazy(f"{name[0]}")
            except:
                return ""
        return ""

    def __str__(self):
        return str(self.view)


class CompanyProfile(BaseModel):
    name = models.CharField(max_length=200)
    total_value = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Total Value")
    number_of_shares = models.PositiveIntegerField(verbose_name="Number of Total Shares")
    company_hold_shares = models.PositiveIntegerField(verbose_name="Number of Company Hold Shares")
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Company Profile"
        verbose_name_plural = "Company Profiles"
        
    def get_total_shares(self):
        return self.number_of_shares - self.company_hold_shares
        
    def get_hold_shares(self):
        return self.company_hold_shares
        
    def get_total_value(self):
        return self.total_value
        
    def get_hold_percentage(self):
        if self.number_of_shares == 0:
            return 0
        return round((self.company_hold_shares / self.number_of_shares) * 100)

    def get_single_share_value(self):
        return self.total_value / self.number_of_shares
        
    @staticmethod
    def get_list_url():
        return reverse_lazy("core:company_profile")
    
    def get_absolute_url(self):
        return reverse_lazy("core:company_profile",)    
    
    def get_update_url(self):
        return reverse_lazy("core:company_profile_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("core:company_profile_delete", kwargs={"pk": self.pk})
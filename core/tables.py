from core.base import BaseTable
from .models import Setting
from django_tables2 import columns

class SettingsTable(BaseTable):
    created = None
    instance_id = columns.Column(verbose_name="Instance Id",)
    access_token = columns.Column(verbose_name="Access Token")

    def render_instance_id(self, value):
        return value[:6] + '*' * (len(value) - 6)

    def render_access_token(self, value):
        return value[:6] + '*' * (len(value) - 6)
    
    class Meta:
        model = Setting
        fields = ("instance_id","access_token",)
        attrs = {"class": "table star-student table-hover table-bordered"}
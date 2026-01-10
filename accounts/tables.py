from core.base import BaseTable

from .models import User
from django_tables2 import columns


class UserTable(BaseTable):
    email = columns.Column(linkify=True)
    created = None
    name = columns.Column(empty_values=(), order_by='first_name')

    class Meta:
        model = User
        fields = ("name", "email", "usertype", "date_joined", "last_login", "is_active")
        attrs = {"class": "table key-buttons border-bottom"}

    def render_name(self, record):
        return record.get_full_name()

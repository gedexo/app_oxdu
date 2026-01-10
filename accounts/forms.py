from core.base import BaseForm
from branches.models import Branch

from .models import User
from django import forms
from django.contrib.auth.forms import AuthenticationForm


class CustomLoginForm(AuthenticationForm):
   
    branch = forms.ModelChoiceField(queryset=Branch.objects.all(), required=True, label="Branch", empty_label="Select Branch", widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        fields = [ 'branch', 'username', 'password']


class UserForm(BaseForm):
    class Meta:
        model = User
        fields = ("email", "usertype", "password")


class StudentUserForm(BaseForm):
    class Meta:
        model = User
        fields = ("email", "password")

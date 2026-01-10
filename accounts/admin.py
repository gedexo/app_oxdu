from .models import User  # Ensure this is your custom User model
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from import_export.admin import ImportExportActionModelAdmin


class MyUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'


class MyUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email",)

    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError("A user with that email already exists.")


class MyUserAdmin(BaseUserAdmin, ImportExportActionModelAdmin):
    form = MyUserChangeForm
    add_form = MyUserCreationForm
    ordering = ["email"]
    list_display = ["email", "usertype", "first_name", "is_active", "is_staff", "is_superuser"]
    list_display_links = ["email", "first_name"]
    readonly_fields = ["last_login", "date_joined", "pk"]
    list_filter = ["is_active", "is_staff", "is_superuser", "date_joined", "last_login", "usertype"]

    fieldsets = (
        ("Basic Info", {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "usertype", "branch")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Groups", {"fields": ("groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "is_active", "is_staff", "is_superuser")}),)

    search_fields = ["email"]  # Update search_fields to use email instead of username
    ordering = ["email"]  # Order by email instead of username


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(ImportExportActionModelAdmin):
    ordering = ["name"]
    list_display = ["name", "id"]


admin.site.register(User, MyUserAdmin)

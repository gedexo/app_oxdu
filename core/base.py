from core.actions import mark_active
from core.actions import mark_inactive
from core.choices import BOOL_CHOICES

from .functions import generate_fields
from django import forms
from django.db import models
from django.db.models import ForeignKey
from django.db.models import ManyToManyField
from django.db.models import OneToOneField
from django.http import HttpResponseRedirect
from django.urls import NoReverseMatch
from django.urls import reverse_lazy
from django_tables2 import Table
from django_tables2 import columns
from django_tables2 import CheckBoxColumn
from import_export.admin import ImportExportModelAdmin
from simple_history.models import HistoricalRecords


class BaseModel(models.Model):
    created = models.DateTimeField(db_index=True, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey("accounts.User", editable=False, blank=True, null=True, related_name="%(app_label)s_%(class)s_creator", on_delete=models.PROTECT)
    is_active = models.BooleanField("Mark as Active", default=True, choices=BOOL_CHOICES)
    history = HistoricalRecords(inherit=True,excluded_fields=['lft', 'rght', 'tree_id', 'level'])

    class Meta:
        abstract = True
        ordering = ["-created"]

    def get_fields(self):
        return generate_fields(self)

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.save()
        return HttpResponseRedirect(self.get_list_url())

    @classmethod
    def get_create_url(cls):
        """Generate create URL dynamically. Return None if URL not found."""
        try:
            return reverse_lazy(f"{cls._meta.app_label}:{cls._meta.model_name}_create")
        except NoReverseMatch:
            return None

    @classmethod
    def get_list_url(cls):
        """Generate list URL dynamically. Return None if URL not found."""
        try:
            return reverse_lazy(f"{cls._meta.app_label}:{cls._meta.model_name}_list")
        except NoReverseMatch:
            return None

    def get_update_url(self):
        """Generate update URL dynamically. Return None if URL not found."""
        try:
            return reverse_lazy(f"{self._meta.app_label}:{self._meta.model_name}_update", kwargs={"pk": self.pk})
        except NoReverseMatch:
            return None

    def get_absolute_url(self):
        """Generate detail URL dynamically. Return None if URL not found."""
        try:
            return reverse_lazy(f"{self._meta.app_label}:{self._meta.model_name}_detail", kwargs={"pk": self.pk})
        except NoReverseMatch:
            return None

    def get_delete_url(self):
        """Generate delete URL dynamically. Return None if URL not found."""
        try:
            return reverse_lazy(f"{self._meta.app_label}:{self._meta.model_name}_delete", kwargs={"pk": self.pk})
        except NoReverseMatch:
            return None


class BaseAdmin(ImportExportModelAdmin):
    exclude = ["creator", "is_active"]
    list_display = ("__str__", "created", "updated", "is_active")
    list_filter = ("is_active",)
    actions = [mark_active, mark_inactive]
    readonly_fields = ("is_active", "creator", "pk")
    search_fields = ("pk",)

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context.update({"show_save_and_continue": False, "show_save_and_add_another": True})
        return super().render_change_form(request, context, add, change, form_url, obj)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.creator = request.user
        super().save_model(request, obj, form, change)

    class Media:
        css = {"all": ("extra_admin/css/admin.css",)}


class BaseTable(Table):
    pk = columns.Column(visible=False)
    created = columns.DateTimeColumn(verbose_name="Created At", format="d/m/Y g:i A")
    action = columns.TemplateColumn(template_name="app/partials/table_actions.html", orderable=False)

    class Meta:
        attrs = {"class": "table  table-vcenter text-nowrap table-bordered border-bottom table-striped"}


class CustomBaseTable(Table):
    selection = CheckBoxColumn(
        accessor="pk",
        attrs={
            "th__input": {
                "class": "form-check-input select-all-checkbox",
            },
            "td__input": {
                "class": "form-check-input select-checkbox",
            },
            "th": {
                "class": "checkbox-column table-primary w-5",
                "style":""
            },
            "td": {
                "class": "checkbox-column table-primary",
            }
        },
        orderable=False,
        empty_values=()
    )
    pk = columns.Column(visible=False)
    action = columns.TemplateColumn(
        template_name="app/partials/table_actions.html",
        orderable=False,
        attrs={"th": {"class": "w-5"}}
    )

    class Meta:
        attrs = {
            "class": "table table-vcenter text-nowrap table-bordered border-bottom table-striped",
            "id": "selectable-table"  # Added ID for easier jQuery targeting
        }
        sequence = ("selection", "...", "action")    # The "..." will be replaced with remaining fields
        template_name = "django_tables2/basic.html"


class BaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Iterate over form fields, including explicitly defined ones
        for field_name, field in self.fields.items():
            if isinstance(field, (forms.ModelChoiceField, forms.ModelMultipleChoiceField)):
                # Handle explicitly set fields and model-defined fields
                model_field = None
                if hasattr(self._meta.model, "_meta"):
                    try:
                        model_field = self._meta.model._meta.get_field(field_name)
                    except Exception:
                        pass  # The field is explicitly defined in the form

                # Get the related model and filter only active objects
                related_model = None
                if model_field and isinstance(model_field, (ForeignKey, OneToOneField, ManyToManyField)):
                    related_model = model_field.remote_field.model
                elif hasattr(field, "queryset"):  # Explicitly defined fields
                    related_model = field.queryset.model

                if related_model and hasattr(related_model, "is_active"):
                    field.queryset = related_model.objects.filter(is_active=True)

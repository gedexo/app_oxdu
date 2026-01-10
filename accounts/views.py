from core import mixins
from django.contrib.auth.hashers import make_password
from django import forms
from core.utils import build_url
from employees.models import Employee, Partner
from admission.models import Admission

from . import tables
from .forms import CustomLoginForm
from .forms import UserForm, StudentUserForm
from .models import User
from django.contrib.auth.views import LoginView
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    form_class = CustomLoginForm

    def form_valid(self, form):
        super().form_valid(form)
        branch = form.cleaned_data.get('branch')
        self.request.session['branch'] = branch.id
        return HttpResponseRedirect(self.get_success_url())


class UserListView(mixins.HybridListView):
    model = User
    table_class = tables.UserTable
    filterset_fields = ("is_active", "is_staff")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Users"
        context["can_add"] = True
        context["new_link"] = reverse_lazy("accounts:user_create")
        return context


class UserDetailView(mixins.HybridDetailView):
    model = User


class UserCreateView(mixins.HybridCreateView):
    model = User
    form_class = UserForm
    permissions = ("manager", "admin_staff", "branch_staff", "ceo", "cfo", "coo", "hr", "cmo")
    exclude = None

    def get_template_names(self):
        if "pk" in self.kwargs:
            return "employees/employee_form.html"
        return super().get_template_names()

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        if "pk" in self.kwargs:
            employee = get_object_or_404(Employee, pk=self.kwargs["pk"])
            form.fields['email'].initial = employee.personal_email or None
        return form

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password"])

        pk = self.kwargs.get("pk")
        if pk:
            employee = get_object_or_404(Employee, pk=pk)
            user.first_name = employee.first_name
            user.last_name = employee.last_name or ""
            user.branch = form.cleaned_data.get('branch', employee.branch)
            user.save()

            employee.user = user
            employee.save()

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'New Employee'
        context['subtitle'] = 'Account Details'
        context['is_account'] = True
        if "pk" in self.kwargs:
            context['object'] = get_object_or_404(Employee, pk=self.kwargs["pk"])
        return context

    def get_success_url(self):
        return Employee.get_list_url()

    def get_success_message(self, cleaned_data):
        return "Employee created successfully!"


class StudentUserCreateView(mixins.HybridCreateView):
    model = User
    form_class = StudentUserForm
    permissions = ("manager", "admin_staff", "branch_staff", "ceo","cfo","coo","hr","cmo")
    exclude = None

    def get_template_names(self):
        if "pk" in self.kwargs:
            return "admission/admission_form.html"
        return super().get_template_names()

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        if "pk" in self.kwargs:
            student = get_object_or_404(Admission, pk=self.kwargs["pk"])
            form.fields['email'].initial = student.personal_email if student.personal_email else None
        return form

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password"])

        pk = self.kwargs.get("pk")  
        if pk:
            student = get_object_or_404(Admission, pk=pk)
            user.first_name = student.first_name
            user.last_name = student.last_name or ""

            user.save()
            student.user = user 
            student.user.usertype = 'student'
            student.save()

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        urls = {
            "personal": build_url("admission:admission_update", kwargs={"pk": self.kwargs.get('pk')}, query_params={'type': 'personal'}),
            "parent": build_url("admission:admission_update", kwargs={"pk": self.kwargs.get('pk')}, query_params={'type': 'parent'}),
            "address": build_url("admission:admission_update", kwargs={"pk": self.kwargs.get('pk')}, query_params={'type': 'address'}),
            "official": build_url("admission:admission_update", kwargs={"pk": self.kwargs.get('pk')}, query_params={'type': 'official'}),
            "account": build_url("accounts:student_user_create", kwargs={"pk": self.kwargs.get('pk')}, query_params={'type': 'account'}),
        }
        context['info_type_urls'] = urls
        context['title'] = 'New Admission'
        context['subtitle'] = 'Account Details'
        context['is_account'] = True
        if "pk" in self.kwargs:
            context['object'] = get_object_or_404(Admission, pk=self.kwargs["pk"])
        return context

    def get_success_url(self):
        return Admission.get_list_url()

    def get_success_message(self, cleaned_data):
        message = "Admission created successfully"
        return message


class StudentUserUpdateView(mixins.HybridUpdateView):
    model = User
    exclude = None
    fields = ("email", "password", "usertype")
    template_name = "admission/admission_form.html"
    permissions = ("manager", "admin_staff", "branch_staff", "mentor", "ceo","cfo","coo","hr","cmo")

    def get_initial(self):
        initial= super().get_initial()
        initial['password'] = None  
        return initial
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['password'].help_text = "Leave blank if you don't want to change the password."
        form.fields['password'].widget = forms.PasswordInput(render_value=False)
        form.fields['password'].required = False
        return form
    
    def form_valid(self, form):
        password = form.cleaned_data.get('password')
        if password:
            form.instance.password = make_password(password)
        else:
            form.instance.password = self.get_object().password
        return super().form_valid(form)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Edit Admission"
        context['subtitle'] = "Account Form"
        urls = {
            "personal": build_url("admission:admission_update", kwargs={"pk": self.object.student.pk}, query_params={'type': 'personal'}),
            "parent": build_url("admission:admission_update", kwargs={"pk": self.object.student.pk}, query_params={'type': 'parent'}),
            "address": build_url("admission:admission_update", kwargs={"pk": self.object.student.pk}, query_params={'type': 'address'}),
            "official": build_url("admission:admission_update", kwargs={"pk": self.object.student.pk}, query_params={'type': 'official'}),
            "financial": build_url("admission:admission_update", kwargs={"pk": self.object.student.pk}, query_params={'type': 'financial'}),
        }
        context['info_type_urls'] = urls
        context['is_account'] = True
        return context

    def get_success_url(self):
        return reverse_lazy("admission:admission_list")
    
class PartnerUserCreateView(mixins.HybridCreateView):
    model = User
    form_class = UserForm
    permissions = ("manager", "admin_staff", "branch_staff", "ceo", "cfo", "coo", "hr", "cmo")
    exclude = None

    def get_template_names(self):
        if "pk" in self.kwargs:
            return "employees/partner/partner_form.html"
        return super().get_template_names()

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        if "pk" in self.kwargs:
            partner = get_object_or_404(Partner, pk=self.kwargs["pk"])
            form.fields['email'].initial = partner.email or None
        return form

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password"])

        pk = self.kwargs.get("pk")
        if pk:
            partner = get_object_or_404(Partner, pk=pk)
            user.first_name = partner.full_name.split(" ")[0] if partner.full_name else ""
            user.last_name = " ".join(partner.full_name.split(" ")[1:]) if len(partner.full_name.split(" ")) > 1 else ""
            user.save()

            partner.user = user
            partner.user.usertype = 'partner'
            partner.save()

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        urls = {
            "personal": build_url("employees:partner_update", kwargs={"pk": self.kwargs.get('pk')}, query_params={'type': 'personal'}),
            "photo": build_url("employees:partner_update", kwargs={"pk": self.kwargs.get('pk')}, query_params={'type': 'photo'}),
            "account": build_url("accounts:partner_user_create", kwargs={"pk": self.kwargs.get('pk')}, query_params={'type': 'account'}),
        }
        context['info_type_urls'] = urls
        context['title'] = 'New Partner'
        context['subtitle'] = 'Account Details'
        context['is_account'] = True
        if "pk" in self.kwargs:
            context['object'] = get_object_or_404(Partner, pk=self.kwargs["pk"])
        return context

    def get_success_url(self):
        return Partner.get_list_url()

    def get_success_message(self, cleaned_data):
        return "Partner account created successfully!"
    
class PartnerUserUpdateView(mixins.HybridUpdateView):
    model = User
    exclude = None
    fields = ("email", "password", "usertype")
    template_name = "employees/partner/partner_form.html"
    permissions = ("manager", "admin_staff", "branch_staff", "ceo", "cfo", "coo", "hr", "cmo")

    def get_initial(self):
        initial = super().get_initial()
        initial['password'] = None
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['password'].help_text = "Leave blank if you don't want to change the password."
        form.fields['password'].widget = forms.PasswordInput(render_value=False)
        form.fields['password'].required = False
        return form

    def form_valid(self, form):
        password = form.cleaned_data.get('password')
        if password:
            form.instance.password = make_password(password)
        else:
            form.instance.password = self.get_object().password
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Edit Partner"
        context['subtitle'] = "Account Form"
        urls = {
            "personal": build_url("employees:partner_update", kwargs={"pk": self.object.partner.pk}, query_params={'type': 'personal'}),
            "photo": build_url("employees:partner_update", kwargs={"pk": self.object.partner.pk}, query_params={'type': 'photo'}),
            "account": build_url("accounts:partner_user_update", kwargs={"pk": self.object.partner.pk}, query_params={'type': 'account'}),
        }
        context['info_type_urls'] = urls
        context['is_account'] = True
        return context

    def get_success_url(self):
        return reverse_lazy("employees:partner_list")
    
    
class UserUpdateView(mixins.HybridUpdateView):
    model = User
    exclude = None
    fields = ("email", "password", "usertype")
    template_name = "employees/employee_form.html"
    permissions = ("manager", "admin_staff", "branch_staff", "ceo","cfo","coo","hr","cmo")

    def get_initial(self):
        initial= super().get_initial()
        initial['password'] = None  
        return initial
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['password'].help_text = "Leave blank if you don't want to change the password."
        form.fields['password'].widget = forms.PasswordInput(render_value=False)
        form.fields['password'].required = False
        return form
    
    def form_valid(self, form):
        password = form.cleaned_data.get('password')
        if password:
            form.instance.password = make_password(password)
        else:
            form.instance.password = self.get_object().password
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Edit Employee"
        context['subtitle'] = "Account Form"
        urls = {
            "personal": build_url("employees:employee_update", kwargs={"pk": self.object.employee.pk}, query_params={'type': 'personal'}),
            "parent": build_url("employees:employee_update", kwargs={"pk": self.object.employee.pk}, query_params={'type': 'parent'}),
            "address": build_url("employees:employee_update", kwargs={"pk": self.object.employee.pk}, query_params={'type': 'address'}),
            "official": build_url("employees:employee_update", kwargs={"pk": self.object.employee.pk}, query_params={'type': 'official'}),
            "financial": build_url("employees:employee_update", kwargs={"pk": self.object.employee.pk}, query_params={'type': 'financial'}),
        }
        context['info_type_urls'] = urls
        context['is_account'] = True
        return context

    def get_success_url(self):
        return reverse_lazy("employees:employee_list")


class UserDeleteView(mixins.HybridDeleteView):
    model = User

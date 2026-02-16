from django import forms
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from phonenumber_field.formfields import PhoneNumberField
from django.core.exceptions import ValidationError
from app_modules.company.models import Company
from allauth.account.forms import LoginForm
from allauth.account.adapter import get_adapter
from allauth.account import app_settings
from django.core.validators import RegexValidator
from django.contrib.auth.models import Group , Permission
from django.conf import settings
from django.apps import apps

from app_modules.users.models import WorkingHours
User = get_user_model()

class UserCreateForm(forms.ModelForm):
    company = forms.ModelChoiceField(queryset=Company.objects.all(), required=False)

    # password = forms.CharField(widget=forms.PasswordInput, label=("Password"), required=True, validators=[validate_password])
    # phone = PhoneNumberField(
    #     
    #     widget=forms.TextInput(attrs={"placeholder": "Phone"}), label=("Phone"), required=False
    # )
    phone_regex = RegexValidator(regex=r'^\d{9,15}$', message="Enter Valid Phone number , Up to 15 digits allowed.")
    phone = forms.CharField(validators=[phone_regex],max_length=20, required=False)
    

    # phone.error_messages['invalid'] = 'Incorrect International Calling Code or Mobile Number!'
    class Meta:
        model = User
        fields = ("email", "full_name","username", "image", "phone", "role", "company")

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(UserCreateForm, self).__init__(*args, **kwargs)

        self.fields['full_name'].required = True

        if self.user.role == User.COMPANY_ADMIN:
            self.fields["role"].choices = [
                (User.COMPANY_ADMIN, "Company Admin"),
                (User.SALES_REPRESENTATIVE, "Sales Representative"),
                (User.DRIVER, "Driver"),
                (User.ACCOUNTANT, "Accountant"),
            ]

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label

        self.fields["company"].widget.attrs["class"] = "select2-data-array form-control company-list"
        self.fields["role"].widget.attrs["class"] = "select2-data-array form-control user-role"
        # self.fields["phone"].widget.attrs["type"] = "tel"
        self.fields["image"].required = False
        self.fields["email"].required = False
        self.fields["role"].required = True
        self.fields['phone'].widget.attrs['placeholder'] = self.fields['phone'].label or 'Phone'


    def clean_company(self):
        company = self.cleaned_data["company"]
        role = self.data["role"]
        if role in [User.COMPANY_ADMIN, User.SALES_REPRESENTATIVE, User.DRIVER] and (self.user.role in [User.SUPER_ADMIN]):
            if not company:
                raise ValidationError("This field is required.")
        return company
    
    # def save(self, commit):
    #     instance = super(UserCreateForm, self).save(commit=False)
    #     country_code = self.cleaned_data.get("country_code")
    #     phone_number = self.cleaned_data.get("phone_number")
    #     instance.phone = f"+{country_code}{phone_number}" if country_code and phone_number else None
    #     if commit:
    #         instance.save()
    #     return instance


class UserUpdateForm(forms.ModelForm):
    
    company = forms.ModelChoiceField(queryset=Company.objects.all(), required=False)
    # phone = PhoneNumberField(
    #     widget=forms.TextInput(attrs={"placeholder": "Phone"}), label=("Phone"), required=False
    # )
    phone_regex = RegexValidator(regex=r'^\d{9,15}$', message="Enter Valid Phone number , Up to 15 digits allowed.")
    phone = forms.CharField(validators=[phone_regex],max_length=20, required=False)
    class Meta:
        model = User
        fields = ("email", "full_name", "phone", "role", "company", "username")

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(UserUpdateForm, self).__init__(*args, **kwargs)

        self.fields['full_name'].required = True
        self.fields["role"].required = True

        if self.instance.role not in [User.SUPER_ADMIN]:
            self.fields['company'].initial = self.instance.company_users.first().company

        if self.user.role == User.COMPANY_ADMIN:
            self.fields["role"].choices = [
                (User.COMPANY_ADMIN, "Company Admin"),
                (User.SALES_REPRESENTATIVE, "Sales Representative"),
                (User.DRIVER, "Driver"),
                (User.ACCOUNTANT, "Accountant"),
            ]

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label

        self.fields["company"].widget.attrs["class"] = "select2-data-array form-control company-list"
        self.fields["role"].widget.attrs["class"] = "select2-data-array form-control user-role"
        self.fields["username"].widget.attrs["readonly"] = "true"
        self.fields['phone'].widget.attrs['placeholder'] = self.fields['phone'].label or 'Phone'


    def clean_company(self):
        company = self.cleaned_data["company"]
        role = self.cleaned_data["role"]
        if role in [User.COMPANY_ADMIN, User.SALES_REPRESENTATIVE, User.DRIVER] and (self.user.role in [User.SUPER_ADMIN]):
            if not company:
                raise ValidationError("This field is required.")
        return company


class CustomLoginForm(LoginForm):
    def clean(self):
        super(LoginForm, self).clean()
        if self._errors:
            return
        credentials = self.user_credentials()
        user_obj = User.objects.filter(email = self.cleaned_data["login"]).first()
        if user_obj:
            if user_obj.role not in [User.SUPER_ADMIN, User.COMPANY_ADMIN, User.SALES_REPRESENTATIVE, User.ACCOUNTANT]:
                raise forms.ValidationError("You can't access this site")
        user = get_adapter(self.request).authenticate(self.request, **credentials)
        if user:
            self.user = user
        else:
            auth_method = app_settings.AUTHENTICATION_METHOD
            if auth_method == app_settings.AuthenticationMethod.USERNAME_EMAIL:
                login = self.cleaned_data["login"]
                if self._is_login_email(login):
                    auth_method = app_settings.AuthenticationMethod.EMAIL
                else:
                    auth_method = app_settings.AuthenticationMethod.USERNAME
            raise forms.ValidationError(
                self.error_messages["%s_password_mismatch" % auth_method]
            )
        return self.cleaned_data
    
class ProfileManageForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ("email", "full_name", "image", "phone", "role")


    def __init__(self, *args, **kwargs):
        super(ProfileManageForm, self).__init__(*args, **kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label
        self.fields["role"].disabled = True
        self.fields["email"].widget.attrs["readonly"] = True
        self.fields["image"].required = True
        
class AddRoleForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ("name", "permissions", )
        
    def __init__(self, *args, **kwargs):
        super(AddRoleForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label
        models = []
        for app_name in settings.LOCAL_APPS:
            if app_name == "unity_wholesale":
                pass
            else:
                app = apps.get_app_config(app_name.split('.')[1])
                models.extend(app.get_models())
        app_lbl = [model._meta.app_label for model in models]
        model_name = [model._meta.model_name for model in models]
        self.fields['permissions'].queryset = Permission.objects.filter(content_type__app_label__in=app_lbl, content_type__model__in=model_name)
        self.fields['permissions'].widget.attrs = {'class': 'form-control', 'rows': 10}
        
class WorkingHoursForm(forms.ModelForm):
    class Meta:
        model = WorkingHours
        fields = ['week_day', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'end_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        }   

class PasswordResetForm(forms.Form):
    password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'New Password'}),
        required=True
    )
    password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm New Password'}),
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match")
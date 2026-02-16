from django import forms
from django.contrib.auth import get_user_model
from app_modules.vendors.models import Vendor,VendorDocument,VendorPayment
from phonenumber_field.formfields import PhoneNumberField
from django.forms.widgets import HiddenInput
from datetime import datetime
from django.core.validators import RegexValidator
User = get_user_model()

class VendorCreateForm(forms.ModelForm):

    # phone = PhoneNumberField(
    #     widget=forms.TextInput(attrs={"placeholder": "Phone"}), label=("Phone"), required=False
    # )
    phone_regex = RegexValidator(regex=r'^\d{9,15}$', message="Enter Valid Phone number , Up to 15 digits allowed.")
    phone = forms.CharField(validators=[phone_regex],max_length=20, required=False)

    class Meta:
        model = Vendor
        fields = ("email", "phone", "first_name", "last_name", "company", "website", "office_number_1", "office_number_2", "address_line_1", "address_line_2", "city", "state", "zip_code", "country", "status")

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(VendorCreateForm, self).__init__(*args, **kwargs)

        if self.user.role in [User.COMPANY_ADMIN] or self.user.role in [User.SALES_REPRESENTATIVE]:
            self.fields['company'].initial = self.user.company_users.first().company

        self.fields['company'].required = True
        self.fields['address_line_1'].required = True
        self.fields['city'].required = True
        self.fields['state'].required = True
        self.fields['zip_code'].required = True
        self.fields['country'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

        self.fields['email'].required = False

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label
        
        # self.fields["status"].widget.attrs.update({'class' : "mt-1"})


        self.fields["company"].widget.attrs["class"] = "select2-data-array form-control company-list"
        self.fields["status"].widget.attrs["class"] = "select2-data-array form-control vendor-status"
        self.fields['phone'].widget.attrs['placeholder'] = self.fields['phone'].label or 'Phone'
        self.fields["country"].widget.attrs["readonly"] = "true"
        self.fields["country"].initial = "India"


class VendorUpdateForm(forms.ModelForm):

    # phone = PhoneNumberField(
    #     widget=forms.TextInput(attrs={"placeholder": "Phone"}), label=("Phone"), required=False
    # )
    phone_regex = RegexValidator(regex=r'^\d{9,15}$', message="Enter Valid Phone number , Up to 15 digits allowed.")
    phone = forms.CharField(validators=[phone_regex],max_length=20, required=False)


    class Meta:
        model = Vendor
        fields = ("email", "phone", "first_name", "last_name", "company", "website", "office_number_1", "office_number_2", "address_line_1", "address_line_2", "city", "state", "zip_code", "country", "status")

    def __init__(self, *args, **kwargs):
        super(VendorUpdateForm, self).__init__(*args, **kwargs)

        self.fields['company'].required = True
        self.fields['address_line_1'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['zip_code'].required = True
        self.fields['country'].required = True

        self.fields['email'].required = False

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label

        # self.fields["phone"].widget.attrs["type"] = "tel"
        
        self.fields["status"].widget.attrs["class"] = "select2-data-array form-control vendor-status"
        self.fields["company"].widget.attrs["class"] = "select2-data-array form-control company-list"
        self.fields['phone'].widget.attrs['placeholder'] = self.fields['phone'].label or 'Phone'

class VendorDocumentCreateForm(forms.ModelForm):
    class Meta:
        model= VendorDocument
        fields= ("vendor", "document_name", "document")

    def __init__(self, vendor_pk, *args, **kwargs):
        super(VendorDocumentCreateForm, self).__init__(*args, **kwargs)
        self.fields["vendor"].initial = Vendor.objects.get(id=vendor_pk)

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label

class VendorPaymentCreateForm(forms.ModelForm):
    class Meta:
        model = VendorPayment
        fields= ("__all__")

    def __init__(self, user ,*args, **kwargs):
        super(VendorPaymentCreateForm, self).__init__(*args, **kwargs)

        if user.role in [User.COMPANY_ADMIN] or user.role in [User.SALES_REPRESENTATIVE]:
            self.fields['vendor'].queryset = Vendor.objects.filter(company__id = user.get_company_id)
            self.fields["vendor"].widget.attrs["onchange"] = "loadVendortablelist()"

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label
        
        
        self.fields["payment_date"].widget.attrs.update({"class": "form-control pickadate-selectors picker__input"})
        self.fields["payment_mode"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["payment_amount"].widget.attrs["min"] = 0
        self.fields["vendor"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["payment_date"].initial = datetime.now().strftime("%-d %B, %Y")

        
        



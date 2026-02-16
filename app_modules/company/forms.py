from django import forms
from app_modules.company.models import Company,Warehouse
from app_modules.users.models import User
from phonenumber_field.formfields import PhoneNumberField
from django.core.validators import RegexValidator

class CompanyForm(forms.ModelForm):
    
    # phone = PhoneNumberField(
    #     widget=forms.TextInput(attrs={"placeholder": "Phone"}), label=("Phone"), required=False
    # )

    phone_regex = RegexValidator(regex=r'^\d{9,15}$', message="Enter Valid Phone number , Up to 15 digits allowed.")
    phone = forms.CharField(validators=[phone_regex],max_length=20, required=False)
    class Meta:
        model = Company
        fields = ("company_name","contact_person","email","phone","status","address_line_1","city","state","zip_code","country","latitude","longitude","address_line_2","logo")

    def __init__(self,*args,**kwargs):
        super().__init__(*args, **kwargs)

        if kwargs["instance"]:
            self.fields['status'].required = True
        else:
            self.fields['status'].required = False

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs["placeholder"] = visible.field.label
            
        self.fields['address_line_1'].required = True
        self.fields['city'].required = True
        self.fields['state'].required = True
        self.fields['zip_code'].required = True
        self.fields['country'].required = True

        self.fields['latitude'].required = False
        self.fields['longitude'].required = False
        self.fields['address_line_2'].required = False
        self.fields['logo'].required = False
        self.fields['phone'].widget.attrs['placeholder'] = self.fields['phone'].label or 'Phone'

class WarehouseForm(forms.ModelForm):
    
    class Meta:
        model = Warehouse
        fields = ("name","address_line_1","address_line_2","city","state","zip_code","country","company","status","latitude","longitude")
        # widgets = {
        #     'address1': forms.Textarea(attrs={'rows': 3}),
        #     'address2': forms.Textarea(attrs={'rows': 3}),
        # }

    def __init__(self,user,*args,**kwargs):
        self.user = user
        super(WarehouseForm,self).__init__(*args, **kwargs)

        if self.user.role == User.COMPANY_ADMIN:
            self.fields.pop('company')

        if kwargs["instance"]:
            self.fields['status'].required = True
        else:
            self.fields['status'].required = False
        self.fields['address_line_1'].required = True
        self.fields['city'].required = True
        self.fields['state'].required = True
        self.fields['zip_code'].required = True
        self.fields['country'].required = True

        self.fields['country'].initial = "India"
        self.fields["country"].widget.attrs["readonly"] = "True"

        self.fields['latitude'].required = False
        self.fields['longitude'].required = False
        self.fields['address_line_2'].required = False

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs["placeholder"] = visible.field.label
        
        if self.user.role == User.SUPER_ADMIN:
            self.fields["company"].widget.attrs["class"] = "select2-data-array form-control category-list"

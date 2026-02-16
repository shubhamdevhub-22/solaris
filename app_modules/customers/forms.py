from django import forms
from app_modules.customers.models import Customer, MultipleContact, Payment, SalesRoute, PriceLevel, PriceLevelProduct, CustomerBillingAddress, CustomerShippingAddress, CustomerDocuments, Zone, Discount, MultipleVendorDiscount, Replacement, ReplacementProduct
from phonenumber_field.formfields import PhoneNumberField
from app_modules.company.models import Company, CompanyUsers
from app_modules.users.models import User
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from datetime import datetime
from app_modules.product.models import Brand
from app_modules.vendors.models import Vendor
from django.core.validators import MinValueValidator


'''form for Customer'''
class CustomerCreateForm(forms.ModelForm):
    phone_regex = RegexValidator(regex=r'^\d{6,15}$', message="Enter Valid Phone number , Up to 15 digits allowed.")
    phone_1 = forms.CharField(validators=[phone_regex],max_length=20, required=False)
    phone_2 = forms.CharField(validators=[phone_regex],max_length=20, required=False)
    mobile = forms.CharField(validators=[phone_regex],max_length=20)

    document_name = forms.CharField(max_length=100, label="Document Name", required=False)
    document = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={"multiple": False}))

    
    shipping_address_line_1 = forms.CharField(max_length=100, label="Address Line 1" ,required=False)
    shipping_address_line_2 = forms.CharField(max_length=100, label="Address Line 2" ,required=False)
    shipping_suite_apartment = forms.CharField(max_length=50, label="Address Line 3" ,required=False)
    shipping_city = forms.CharField(max_length=20, label="City" ,required=False)
    shipping_state = forms.CharField(max_length=20, label="State" ,required=False)
    shipping_country = forms.CharField(max_length=20, label="Country" ,required=False)
    shipping_zip_code = forms.IntegerField(label="Zip Code" ,required=False)
    shipping_latitude = forms.FloatField(label="Latitude" ,required=False)
    shipping_longitude = forms.FloatField(label="Longitude" ,required=False)

    billing_address_line_1 = forms.CharField(max_length=100, label="Address Line 1")
    billing_address_line_2 = forms.CharField(max_length=100, label="Address Line 2")
    billing_suite_apartment = forms.CharField(max_length=50, label="Address Line 3" ,required=False)
    billing_city = forms.CharField(max_length=20, label="City")
    billing_state = forms.CharField(max_length=20, label="State",required=False)
    billing_country = forms.CharField(max_length=20, label="Country" ,required=False)
    billing_zip_code = forms.IntegerField(label="Zip Code" ,required=False)
    billing_latitude = forms.FloatField(label="Latitude" ,required=False)
    billing_longitude = forms.FloatField(label="Longitude" ,required=False)


    class Meta:
        model = Customer
        fields = [
                    "customer_name", 
                    "customer_type",
                    "status" ,
                    "sales_rep" ,
                    "tax_id" ,
                    "terms" ,
                    "dba_name" ,
                    "company" ,
                    "price_level" ,
                    "store_open_time" ,
                    "store_close_time" ,
                    "document_name",

                    "zone", 
                    "area", 
                    "transport",
                    "cst" ,
                    "gst" ,
                    "phone_1" ,
                    "phone_2" ,
                    "mobile" ,
                    # "past_due_amount" ,
                    "fax" ,
                    "remark" ,
                    "email" ,
                    "code",
                    "contact_name",

                    "document" ,
                    "shipping_address_line_1" ,
                    "shipping_address_line_2" ,
                    "shipping_suite_apartment" ,
                    "shipping_city" ,
                    "shipping_state" ,
                    "shipping_country" ,
                    "shipping_zip_code" ,
                    "shipping_latitude" ,
                    "shipping_longitude" ,
                    "billing_address_line_1" ,
                    "billing_address_line_2" ,
                    "billing_suite_apartment" ,
                    "billing_city" ,
                    "billing_state" ,
                    "billing_country" ,
                    "billing_zip_code" ,
                    "billing_latitude" ,
                    "billing_longitude" ,
                    ]
         
        widgets={
                'store_open_time' : forms.TextInput(attrs={'type':'time'}),
                'store_close_time' : forms.TextInput(attrs={'type':'time'}),
                
        }

        
    def __init__(self, user, *args, **kwargs):
        super(CustomerCreateForm, self).__init__(*args, **kwargs)

        if user.role == User.COMPANY_ADMIN:
            company_user_ids = list(CompanyUsers.objects.filter(company__id=user.get_company_id, user__role = User.SALES_REPRESENTATIVE).values_list("user__id", flat=True))
            self.fields["sales_rep"].queryset = User.objects.filter(id__in=company_user_ids)
            self.fields["price_level"].queryset = PriceLevel.objects.filter(company__id=user.get_company_id, status=PriceLevel.ACTIVE)
            self.fields["zone"].queryset = Zone.objects.filter(company__id = user.get_company_id)

        if user.role == User.SALES_REPRESENTATIVE:
            company_user_ids = list(CompanyUsers.objects.filter(user__id=user.id, user__role = User.SALES_REPRESENTATIVE).values_list("user__id", flat=True))
            self.fields["sales_rep"].queryset = User.objects.filter(id__in=company_user_ids)
            self.fields["price_level"].queryset = PriceLevel.objects.filter(company__id=user.get_company_id, status=PriceLevel.ACTIVE)

        self.fields['company'].queryset = self.fields['company'].queryset.exclude(status=Company.IS_INACTIVE)
        self.fields['price_level'].queryset = self.fields['price_level'].queryset.exclude(status=PriceLevel.INACTIVE)
        
        self.fields['customer_type'].required = False
        self.fields['phone_1'].required = False
        self.fields['phone_2'].required = False
        self.fields['zone'].required = True
        self.fields['area'].required = True
        
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label
        self.fields["customer_type"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["terms"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["sales_rep"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["company"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["status"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["zone"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["price_level"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["company"].widget.attrs["onchange"] = "load_company_sales_rep()"    
        self.fields["customer_type"].widget.attrs["onchange"] = "load_company_sales_rep()"    

        self.fields['phone_1'].widget.attrs['placeholder'] = self.fields['phone_1'].label or 'Phone'
        self.fields['phone_2'].widget.attrs['placeholder'] = self.fields['phone_2'].label or 'Phone'
        self.fields['mobile'].widget.attrs['placeholder'] = self.fields['mobile'].label or 'Phone'

        self.fields["shipping_country"].initial = "India"
        self.fields["billing_country"].initial = "India"
        self.fields['shipping_country'].widget.attrs["readonly"] = "true"
        self.fields['billing_country'].widget.attrs["readonly"] = "true"


        # self.fields["billing_address_line_1"].widget.attrs["placeholder"]="Address Line 1"


class CustomerUpdateForm(forms.ModelForm):

    phone_regex = RegexValidator(regex=r'^\d{6,15}$', message="Enter Valid Phone number , Up to 15 digits allowed.")
    phone_1 = forms.CharField(max_length=255, required=False)
    phone_2 = forms.CharField(max_length=255, required=False)
    mobile = forms.CharField(max_length=255, required=False)

    shipping_address = forms.CharField(max_length=100, label="Shipping Address")
    shipping_address_line_1 = forms.CharField(max_length=100, label="Address Line 1" ,required=False)
    shipping_address_line_2 = forms.CharField(max_length=100, label="Address Line 2" ,required=False)
    shipping_suite_apartment = forms.CharField(max_length=50, label="Address Line 3" ,required=False)
    shipping_city = forms.CharField(max_length=20, label="City" ,required=False)
    shipping_state = forms.CharField(max_length=20, label="State" ,required=False)
    shipping_country = forms.CharField(max_length=20, label="Country" ,required=False)
    shipping_zip_code = forms.IntegerField(label="Zip Code" ,required=False)
    shipping_latitude = forms.FloatField(label="Latitude" ,required=False)
    shipping_longitude = forms.FloatField(label="Longitude" ,required=False)

    billing_address = forms.CharField(max_length=100, label="Billing Address")
    billing_address_line_1 = forms.CharField(max_length=100, label="Address Line 1")
    billing_address_line_2 = forms.CharField(max_length=100, label="Address Line 2")
    billing_suite_apartment = forms.CharField(max_length=50, label="Address Line 3" ,required=False)
    billing_city = forms.CharField(max_length=20, label="City")
    billing_state = forms.CharField(max_length=20, label="State",required=False)
    billing_country = forms.CharField(max_length=20, label="Country" ,required=False)
    billing_zip_code = forms.IntegerField(label="Zip Code" ,required=False)
    billing_latitude = forms.FloatField(label="Latitude" ,required=False)
    billing_longitude = forms.FloatField(label="Longitude" ,required=False)

    class Meta:
        model = Customer
        fields = [
            "customer_name",
            "customer_type",
            "status",
            "sales_rep",
            "tax_id",
            "terms",
            "dba_name",
            "company",
            "price_level",
            "store_open_time",
            "store_close_time",

            "zone", 
            "area", 
            "transport",
            "cst" ,
            "gst" ,
            "phone_1" ,
            "phone_2" ,
            "mobile" ,
            # "past_due_amount" ,
            "fax" ,
            "remark" ,
            "email" ,
            "code",
            "contact_name",

            "shipping_address",
            "shipping_address_line_1" ,
            "shipping_address_line_2" ,
            "shipping_suite_apartment" ,
            "shipping_city" ,
            "shipping_state" ,
            "shipping_country" ,
            "shipping_zip_code" ,

            "billing_address",
            "billing_address_line_1" ,
            "billing_address_line_2" ,
            "billing_suite_apartment" ,
            "billing_city" ,
            "billing_state" ,
            "billing_country" ,
            "billing_zip_code" ,
        ]
        widgets={
                'store_open_time' : forms.TextInput(attrs={'type':'time'}),
                'store_close_time' : forms.TextInput(attrs={'type':'time'}),
                
        }

    def __init__(self, user, customer_id, *args, **kwargs):
        super(CustomerUpdateForm, self).__init__(*args, **kwargs)
        self.fields['company'].queryset = self.fields['company'].queryset.exclude(status=Company.IS_INACTIVE)

        # self.fields["sales_rep"].queryset = CompanyUsers.objects.filter(company__id=company_id, user__role = User.SALES_REPRESENTATIVE).values('user_id')
        # self.fields["sales_rep"].initial = self.instance.sales_rep

        if user.role == User.COMPANY_ADMIN:
            company_user_ids = list(CompanyUsers.objects.filter(company__id=user.get_company_id, user__role = User.SALES_REPRESENTATIVE).values_list("user__id", flat=True))
            self.fields["sales_rep"].queryset = User.objects.filter(id__in=company_user_ids)
            self.fields["price_level"].queryset = PriceLevel.objects.filter(company__id=user.get_company_id, status=PriceLevel.ACTIVE)
            self.fields["zone"].queryset = Zone.objects.filter(company__id = user.get_company_id)

        if user.role == User.SALES_REPRESENTATIVE:
            company_user_ids = list(CompanyUsers.objects.filter(user__id=user.id, user__role = User.SALES_REPRESENTATIVE).values_list("user__id", flat=True))
            self.fields["sales_rep"].queryset = User.objects.filter(id__in=company_user_ids)
            self.fields["price_level"].queryset = PriceLevel.objects.filter(company__id=user.get_company_id, status=PriceLevel.ACTIVE)

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label

        billing_address = CustomerBillingAddress.objects.filter(customer__id = customer_id, is_default=True).last()
        if billing_address:
            self.fields["billing_address"].initial = billing_address.id
            self.fields["billing_address_line_1"].initial = billing_address.billing_address_line_1
            self.fields["billing_address_line_2"].initial = billing_address.billing_address_line_2
            self.fields["billing_suite_apartment"].initial = billing_address.billing_suite_apartment
            self.fields["billing_city"].initial = billing_address.billing_city
            self.fields["billing_state"].initial = billing_address.billing_state
            self.fields["billing_country"].initial = billing_address.billing_country
            self.fields["billing_zip_code"].initial = billing_address.billing_zip_code

        shipping_address = CustomerShippingAddress.objects.filter(customer__id = customer_id, is_default=True).last()
        if shipping_address:
            self.fields["shipping_address"].initial = shipping_address.id
            self.fields["shipping_address_line_1"].initial = shipping_address.shipping_address_line_1
            self.fields["shipping_address_line_2"].initial = shipping_address.shipping_address_line_2
            self.fields["shipping_suite_apartment"].initial = shipping_address.shipping_suite_apartment
            self.fields["shipping_city"].initial = shipping_address.shipping_city
            self.fields["shipping_state"].initial = shipping_address.shipping_state
            self.fields["shipping_country"].initial = shipping_address.shipping_country
            self.fields["shipping_zip_code"].initial = shipping_address.shipping_zip_code

        self.fields["billing_address"].widget.attrs["class"] = "d-none"
        self.fields["shipping_address"].widget.attrs["class"] = "d-none"
        
        self.fields['shipping_country'].widget.attrs["readonly"] = "true"
        self.fields['billing_country'].widget.attrs["readonly"] = "true"

        self.fields["sales_rep"].required = False
        self.fields['customer_type'].required = False
        self.fields['phone_1'].required = False
        self.fields['phone_2'].required = False
        self.fields['zone'].required = True
        self.fields['area'].required = True

        self.fields["customer_type"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["terms"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["sales_rep"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["company"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["status"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["price_level"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["zone"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["company"].widget.attrs["onchange"] = "load_company_sales_rep()"
        self.fields["customer_type"].widget.attrs["onchange"] = "load_company_sales_rep()" 

        self.fields['phone_1'].widget.attrs['placeholder'] = self.fields['phone_1'].label or 'Phone Number'
        self.fields['phone_2'].widget.attrs['placeholder'] = self.fields['phone_2'].label or 'Phone Number'
        self.fields['mobile'].widget.attrs['placeholder'] = self.fields['mobile'].label or 'Mobile Number'


        # if self.form.cleaned_data["sales_rep"] is None:
        #     return self.form.cleaned_data["sales_rep"]==""


class CustomerBillingAddressCreateForm(forms.ModelForm):
    class Meta:
        model = CustomerBillingAddress
        fields = '__all__'


    def __init__(self, *args, **kwargs):
        super(CustomerBillingAddressCreateForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label
        
        self.fields["billing_address_line_2"].required = True
        self.fields["billing_state"].required = False
        self.fields["billing_country"].required = False

        self.fields["billing_country"].widget.attrs["readonly"] = "true"
        self.fields["billing_country"].initial = "India"
        self.fields['is_default'].widget.attrs = {'class': 'mt-2',}

class CustomerBillingAddressUpdateForm(forms.ModelForm):

    class Meta:
        model = CustomerBillingAddress
        fields = '__all__'


    def __init__(self, *args, **kwargs):
        super(CustomerBillingAddressUpdateForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label
        
        self.fields["billing_address_line_2"].required = True
        self.fields["billing_state"].required = False
        self.fields["billing_country"].required = False

        if self.instance.id:
            # self.fields["customer"].widget.attrs["disabled"] = 'disabled'
            self.fields["customer"].widget.attrs["readonly"] = True
            self.fields['is_default'].widget.attrs = {'class': 'mt-2',}
            self.fields["billing_country"].widget.attrs["readonly"] = "true"
            self.fields["billing_country"].initial = "India"


class CustomerShippingAddressCreateForm(forms.ModelForm):
    class Meta:
        model = CustomerShippingAddress
        fields = '__all__'


    def __init__(self, *args, **kwargs):
        super(CustomerShippingAddressCreateForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label
        
        self.fields["shipping_address_line_2"].required = True
        self.fields["shipping_state"].required = False
        self.fields["shipping_country"].required = False

        self.fields["shipping_country"].widget.attrs["readonly"] = "true"
        self.fields["shipping_country"].initial = "India"
        self.fields['is_default'].widget.attrs = {'class': 'mt-2',}

class CustomerShippingAddressUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomerShippingAddress
        fields = '__all__'


    def __init__(self, *args, **kwargs):
        super(CustomerShippingAddressUpdateForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label

        self.fields["shipping_address_line_2"].required = True
        self.fields["shipping_state"].required = False
        self.fields["shipping_country"].required = False
        
        if self.instance.id:
            self.fields["customer"].widget.attrs["readonly"] = True
            self.fields['is_default'].widget.attrs = {'class': 'mt-2',}

            self.fields["shipping_country"].widget.attrs["readonly"] = "true"
            self.fields["shipping_country"].initial = "India"


'''form for Multiple Contact''' 
class MultipleContactForm(forms.ModelForm):

    # mobile_no = PhoneNumberField(
    #     widget=forms.TextInput(attrs={"placeholder": "Mobile No"}), label=("Mobile No"), required=False
    # )

    phone_regex = RegexValidator(regex=r'^\d{9,15}$', message="Enter Valid Phone number , Up to 15 digits allowed.")
    mobile_no = forms.CharField(validators=[phone_regex],max_length=20, required=False)
    class Meta:
        model = MultipleContact
        fields = [
            "customer_obj",
            "type",
            "contact_person",
            "email",
            "mobile_no",
            "is_default",
        ]

    def __init__(self, *args, **kwargs):
        super(MultipleContactForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label
        self.fields['customer_obj'].required = False
        self.fields['is_default'].widget.attrs = {'class': 'mt-2',}
        self.fields["type"].widget.attrs["class"] = "select2-data-array form-control"

        self.fields['mobile_no'].widget.attrs['placeholder'] = self.fields['mobile_no'].label or 'Mobile Number'
        self.fields['mobile_no'].widget.attrs['class'] = "form-control mobile-number"


class CustomerDocumentForm(forms.ModelForm):

    class Meta:
        model = CustomerDocuments
        fields = '__all__'

    def __init__(self, id_customer, *args, **kwargs):
        super(CustomerDocumentForm, self).__init__(*args, **kwargs)

        if not self.instance.id:
            self.fields["customer"].initial = Customer.objects.get(id=id_customer)

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label 
        self.fields['document_name'].required = True

class CustomerContactForm(forms.ModelForm):

    # mobile_no = PhoneNumberField(
    #     widget=forms.TextInput(attrs={"placeholder": "Mobile No"}), label=("Mobile No"), required=False
    # )

    phone_regex = RegexValidator(regex=r'^\d{9,15}$', message="Enter Valid Phone number , Up to 15 digits allowed.")
    mobile_no = forms.CharField(validators=[phone_regex],max_length=20, required=False)
    class Meta:
        model = MultipleContact
        fields = '__all__'

    def __init__(self, id_customer, *args, **kwargs):
        super(CustomerContactForm, self).__init__(*args, **kwargs)

        if not self.instance.id:
            self.fields["customer_obj"].initial = Customer.objects.get(id=id_customer)

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label
        self.fields['is_default'].widget.attrs = {'class': 'mt-2',}
        self.fields["type"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields['mobile_no'].widget.attrs['placeholder'] = self.fields['mobile_no'].label or 'Mobile Number'


        

'''form for Payment Route'''
class PaymentForm(forms.ModelForm):

    class Meta:
        model = Payment
        fields = '__all__'
        widgets={
                'receive_date' : forms.TextInput(attrs={'type':'date'}),
                'entry_date' : forms.TextInput(attrs={'type':'date'}),
                
        }

    def __init__(self, user, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)

        if user.role == User.COMPANY_ADMIN:
            self.fields["customer_name"].queryset = Customer.objects.filter(company__id=user.get_company_id, status=Customer.ACTIVE)
            self.fields["customer_name"].widget.attrs["onchange"] = "changeCustomer()"
        if user.role == User.SALES_REPRESENTATIVE:
            self.fields["customer_name"].queryset = Customer.objects.filter(sales_rep__id=user.id, company__id=user.get_company_id, status=Customer.ACTIVE)
            self.fields["customer_name"].widget.attrs["onchange"] = "changeCustomer()"

        self.fields['customer_name'].queryset = self.fields['customer_name'].queryset.exclude(status=Customer.INACTIVE)
        self.fields["entry_date"].required = False

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label
        self.fields["payment_mode"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["customer_name"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        # self.fields["check_no"].widget.attrs["onchange"] = "paymentMode()"    


'''form for Sales Route'''
class SalesRouteForm(forms.ModelForm):
     
    class Meta:
        model = SalesRoute
        fields = '__all__'
    
    def __init__(self, user, *args, **kwargs):
        super(SalesRouteForm, self).__init__(*args, **kwargs)
        self.user =user

        if user.role == User.COMPANY_ADMIN:
            self.fields["customer"].queryset = Customer.objects.filter(company__id=user.get_company_id)
            company_user_ids = list(CompanyUsers.objects.filter(company__id=user.get_company_id, user__role = User.SALES_REPRESENTATIVE).values_list("user__id", flat=True))
            self.fields["sales_rep"].queryset = User.objects.filter(id__in=company_user_ids)
            if self.instance.id:
                self.fields["customer"].initial = self.instance.customer
                self.fields["sales_rep"].initial = self.instance.sales_rep
                self.fields["customer"].queyset = Customer.objects.filter(company__id = self.user.get_company_id)
                company_user_ids = list(CompanyUsers.objects.filter(company__id = self.user.get_company_id, user__role = User.SALES_REPRESENTATIVE).values_list("user__id", flat=True))
                self.fields["sales_rep"].queyset = User.objects.filter(id__in=company_user_ids)
        if user.role == User.SALES_REPRESENTATIVE:
            self.fields["customer"].queryset = Customer.objects.filter(sales_rep__id=user.id, company__id=user.get_company_id, status=Customer.ACTIVE)
            company_user_ids = list(CompanyUsers.objects.filter(company__id=user.get_company_id, user__role = User.SALES_REPRESENTATIVE).values_list("user__id", flat=True))
            self.fields["sales_rep"].queryset = User.objects.filter(id__in=company_user_ids)
            if self.instance.id:
                self.fields["customer"].initial = self.instance.customer
                self.fields["sales_rep"].initial = self.instance.sales_rep
                self.fields["customer"].queyset = Customer.objects.filter(sales_rep__id=user.id, company__id = self.user.get_company_id)
                company_user_ids = list(CompanyUsers.objects.filter(company__id = self.user.get_company_id, user__role = User.SALES_REPRESENTATIVE).values_list("user__id", flat=True))
                self.fields["sales_rep"].queyset = User.objects.filter(id__in=company_user_ids)
        elif self.instance.id:
            self.fields["customer"].initial = self.instance.customer
            self.fields["sales_rep"].initial = self.instance.sales_rep
            self.fields["customer"].queyset = Customer.objects.filter(company = self.instance.company)
            company_user_ids = list(CompanyUsers.objects.filter(company = self.instance.company, user__role = User.SALES_REPRESENTATIVE).values_list("user__id", flat=True))
            self.fields["sales_rep"].queyset = User.objects.filter(id__in=company_user_ids)



        # else:
        #     self.fields["sales_rep"].queryset = User.objects.filter(role='sales representative')

        # if self.instance.id:
        #     self.fields["customer"].initial = self.instance.customer
        #     self.fields["sales_rep"].initial = self.instance.sales_rep


        #     if user.role == User.COMPANY_ADMIN:
        #         self.fields["customer"].queyset = Customer.objects.filter(company__id = self.user.get_company_id)

        #         company_user_ids = list(CompanyUsers.objects.filter(company__id = self.user.get_company_id, user__role = User.SALES_REPRESENTATIVE).values_list("user__id", flat=True))

        #     else: 
        #         self.fields["customer"].queyset = Customer.objects.filter(company = self.instance.company)

        #         company_user_ids = list(CompanyUsers.objects.filter(company = self.instance.company, user__role = User.SALES_REPRESENTATIVE).values_list("user__id", flat=True))


        # self.fields['customer'].queryset = self.fields['customer'].queryset.exclude(status=Customer.INACTIVE)

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"    
            visible.field.widget.attrs["placeholder"] = visible.field.label
        self.fields["sales_rep"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["customer"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["status"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["company"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["company"].widget.attrs["onchange"] = "load_customer_sales_rep()"  

'''form for Price Level'''
class PriceLevelForm(forms.ModelForm):
     
    class Meta:
        model = PriceLevel
        fields = '__all__'
    
    def __init__(self,  *args, **kwargs):
        super(PriceLevelForm, self).__init__(*args, **kwargs)
        self.fields['company'].queryset = self.fields['company'].queryset.exclude(status=Company.IS_INACTIVE)

        if self.instance.id:
            self.fields['company'].widget.value_from_datadict = lambda *args: self.instance.company
            self.fields["company"].widget.attrs.update({"disabled": "disabled"})
            self.fields['customer_type'].widget.value_from_datadict = lambda *args: self.instance.customer_type
            self.fields["customer_type"].widget.attrs.update({"disabled": "disabled"})

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label
        self.fields["customer_type"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["company"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["status"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields['company'].required = True


'''form for PriceLevelProduct'''
class PriceLevelProductForm(forms.ModelForm):

    class Meta:
        model = PriceLevelProduct
        fields = '__all__'


class ImportCustomerCSVForm(forms.Form):
    csv_file = forms.FileField(widget=forms.FileInput(attrs={'accept': ".xlsx" or ".xls"}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(ImportCustomerCSVForm, self).__init__(*args, **kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label

    def clean_csv_file(self):
        csv_file = self.cleaned_data["csv_file"]
        if not [csv_file.name.endswith('.xlsx') or csv_file.name.endswith('.xls')]:
            raise ValidationError("Only .xlsx  and .xls file is accepted.")
        return csv_file
    
class CreateCustomerCSVForm(forms.ModelForm):

    class Meta:
        model = Customer
        fields = ("customer_name", "zone", "area", "transport", "cst", "gst", "phone_1", "phone_2", "mobile", "past_due_amount", "fax", "remark", "email","code")
    
class CreateZoneCSVForm(forms.ModelForm):

    class Meta:
        model = Zone
        fields = ("zone_code", "zone_description")

class MultipleContactFromCSVForm(forms.ModelForm):
    class Meta:
        model = MultipleContact
        fields = ("customer_obj", "type", "contact_person","email","mobile_no")
class ZoneForm(forms.ModelForm):

    class Meta:
        model = Zone
        fields = "__all__"

    def __init__(self,  *args, **kwargs):
        super(ZoneForm, self).__init__(*args, **kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label
        
        self.fields['zone_description'].widget.attrs = {'class': 'form-control','rows': 4 ,'placeholder':'Description'}
        self.fields['zone_description'].required = False
        self.fields["company"].widget.attrs["class"] = "select2-data-array form-control select2-list"



class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = "__all__"

    def __init__(self, user, *args, **kwargs):
        super(DiscountForm, self).__init__(*args, **kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label
        
        self.fields["category"].required = True
        self.fields["discount"].required = True
        self.fields["brand"].required = False
        self.fields["company"].required = False

        # if not user.is_superuser:
        #     self.fields["brand"].queryset = Brand.objects.filter(company__id = user.get_company_id, status = Brand.ACTIVE)
        
        self.fields["company"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        

class MultipleVendorDiscountForm(forms.ModelForm):

    class Meta:
        model = MultipleVendorDiscount
        fields = "__all__"

    def __init__(self,  *args, **kwargs):
        super(MultipleVendorDiscountForm, self).__init__(*args, **kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label
        
        self.fields['customer'].required = False
        self.fields["discount"].widget.attrs["data-id"] = "__prefix__"
        self.fields["brand"].widget.attrs["data-id"] = "__prefix__"

        self.fields["brand"].required = True
        self.fields["discount_percent"].required = True
        self.fields["additional_discount"].required = True
        self.fields["discount"].required = True


class ReplacementForm(forms.ModelForm):
    total_amount = forms.IntegerField(initial="0")
    class Meta:
        model = Replacement
        fields = (
            "order",
            "customer",
            "total_amount",
            "return_type",
        )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["return_type"].initial = Replacement.STATUS_CHOICES[0]

        if self.instance.id:
            self.fields["total_amount"].initial = self.instance.get_replacement_total
            self.fields["customer"].disabled = True
            self.fields["order"].disabled = True
            self.fields["return_type"].disabled = True
        
        self.fields["total_amount"].widget.attrs["readonly"] = "true"

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs["placeholder"] = visible.field.label


class ReplacementProductForm(forms.ModelForm):
    unit_price = forms.IntegerField(widget=MinValueValidator(0), required=True)
    class Meta:
        model = ReplacementProduct
        fields = ("replace_quantity","unit_price", "order_product")

    def __init__(self,*args,**kwargs):
        super().__init__(*args, **kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs["placeholder"] = visible.field.label
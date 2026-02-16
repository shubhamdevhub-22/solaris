import datetime
from django import forms
from app_modules.order.models import AssignDriverRoutes, Order,OrderedProduct, Car
from app_modules.company.models import Company, CompanyUsers,Warehouse
from app_modules.customers.models import Customer
from app_modules.product.models import Product
from app_modules.users.models import Driver, User
from django.urls import reverse


class OrderFrom(forms.ModelForm):

    class Meta:
        model = Order
        fields = (
            "customer",
            "company",
            "status",
            "item_total",
            "shipping_charges",
            "adjustments",
            "use_credits",
            "grand_total",
            "paid_amount",
            "balance_amount",
            "status",
            "internal_remarks",
            "order_date",
            "packing_charges",
            "reference_number",
            "created_by"
        )
        widgets={
            'internal_remarks' : forms.Textarea(attrs={'rows':4 ,'class':'form-control'}),
            # 'internal_remarks' : forms.Textarea(attrs={'rows':4 ,'class':'form-control'})
            # 'order_date' :forms.DateInput(format = '%d / %m / %Y'),            
        }

    def __init__(self,user,*args,**kwargs):
        self.user = user

        super().__init__(*args, **kwargs)
        
        self.fields['customer'].queryset = self.fields['customer'].queryset.exclude(status=Customer.INACTIVE)
        self.fields['company'].queryset = self.fields['company'].queryset.exclude(status=Company.IS_INACTIVE)

        # self.fields['shipping_country'].initial = "India"
        # self.fields["shipping_country"].widget.attrs.update({"readonly": "true"})
        # self.fields['billing_country'].initial = "India"
        # self.fields["billing_country"].widget.attrs.update({"readonly": "true"})
        
        self.fields['status'].required = False
        self.fields['packing_charges'].required = False
        self.fields["customer"].widget.attrs.update({"class": "form-control"})
        self.fields["customer"].widget.attrs.update({"data-url": reverse('order:get_customer_details_ajax')})
        self.fields["order_date"].widget.attrs.update({"readonly": "readonly"})
        self.fields["item_total"].widget.attrs.update({"value":"0.00","readonly": "readonly"})
        self.fields["shipping_charges"].widget.attrs.update({"value":"0.00"})
        self.fields["packing_charges"].widget.attrs.update({"value":"0.00"})
        self.fields["adjustments"].widget.attrs.update({"readonly":"readonly"})
        self.fields["balance_amount"].widget.attrs.update({"readonly":"readonly"})
        
        self.fields["grand_total"].widget.attrs.update({"value":"0.00","readonly": "readonly"})   
        self.fields["paid_amount"].widget.attrs.update({"min":"0"})
        self.fields["balance_amount"].widget.attrs.update({"min":"0"})
        
        if self.user.role == User.COMPANY_ADMIN or self.user.role == User.SALES_REPRESENTATIVE:
            self.fields.pop('company')

        if kwargs["instance"]:
            self.fields['status'].widget.value_from_datadict = lambda *args: self.instance.status
            self.fields['customer'].widget.value_from_datadict = lambda *args: self.instance.customer
            self.fields["customer"].widget.attrs.update({"disabled": "disabled"})
            self.fields["paid_amount"].widget.attrs.update({"disabled": "disabled"})
            
            if self.user.role == User.SUPER_ADMIN:
                self.fields['company'].widget.value_from_datadict = lambda *args: self.instance.company
                self.fields["company"].widget.attrs.update({"disabled": "disabled"})

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs["placeholder"] = visible.field.label
            
        
        if kwargs["instance"]:
            self.fields['status'].widget.value_from_datadict = lambda *args: self.instance.status
            self.fields["status"].widget.attrs.update({"disabled": "disabled"})
            self.fields.pop('created_by')


        if self.user.role == User.SUPER_ADMIN:
            self.fields["company"].required = True 
            self.fields["company"].widget.attrs.update({"class": "form-control"})
        



class OrderedProductForm(forms.ModelForm):
    SELECT = ""
    CHOICES = (
        (SELECT, "---------"),
    )
    unit_type = forms.ChoiceField(choices=CHOICES)
    
    class Meta:
        model = OrderedProduct
        fields = ("product","unit_type","product_discount1","product_discount2","quantity","unit_price",)
        

    def __init__(self,*args,**kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = self.fields['product'].queryset.exclude(status=Product.INACTIVE)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs["placeholder"] = visible.field.label
        self.fields["product"].widget.attrs.update({"class": "form-control"})
        self.fields["product"].widget.attrs.update({"data-url": reverse('order:ajax_get_product_unit_type')})
        self.fields["unit_type"].widget.attrs.update({"data-url": reverse('order:ajax_get_product_price_stock')})
        self.fields["product"].widget.attrs.update({"data-customer-id": ''})
        self.fields["product_discount1"].widget.attrs.update({"value":"0.00", "min": "0.00", "max":"100.00", "step": "0.01"})
        self.fields["product_discount2"].widget.attrs.update({"value":"0.00", "min": "0.00", "max":"100.00", "step": "0.01"})


class CarForm(forms.ModelForm):

    class Meta:
        model = Car
        fields = "__all__"
        widgets={
                'inspect_exp_date' : forms.TextInput(attrs={'type':'date'}),
        }

    def __init__(self, user,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if self.user.role == User.COMPANY_ADMIN or self.user.role == User.SALES_REPRESENTATIVE:
            company_drivers = list(CompanyUsers.objects.filter(company__id=self.user.get_company_id).values_list("user__id", flat=True))
            self.fields['driver'].queryset = Driver.objects.filter(id__in=company_drivers)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label
            

        self.fields["status"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["company"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["driver"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields['description'].widget.attrs = {'class': 'form-control','rows': 4}
        self.fields["company"].widget.attrs["onchange"] = "loadDriver()"



class OrderPackingForm(forms.Form):
    order_id = forms.IntegerField(required=False)

class AssignDriverRoutesForm(forms.ModelForm):
    class Meta:
        model = AssignDriverRoutes
        fields = ("name", "driver", "date", "start_location")

    def __init__(self, user,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label

        self.fields["date"].widget.attrs.update({"class": "form-control pickadate-selectors picker__input"})
        self.fields["driver"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["start_location"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["date"].initial= datetime.date.today().strftime("%-d %B, %Y")
        
        if self.user.role == User.COMPANY_ADMIN or self.user.role == User.SALES_REPRESENTATIVE:
            company_drivers = list(CompanyUsers.objects.filter(company__id=self.user.get_company_id).values_list("user__id", flat=True))
            self.fields['driver'].queryset = Driver.objects.filter(id__in=company_drivers)
            self.fields['start_location'].queryset = Warehouse.objects.filter(company__id = user.get_company_id)
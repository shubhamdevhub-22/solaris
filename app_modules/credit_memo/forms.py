from django import forms
from app_modules.credit_memo.models import CreditMemo, CreditMemoProduct
from app_modules.company.models import Company
from app_modules.customers.models import Customer
from app_modules.users.models import User
from django.urls import reverse
import datetime

class CreditMemoForm(forms.ModelForm):

    class Meta:
        model = CreditMemo
        fields = ("company", "customer", "date", "credit_type", "remark", "item_total", "grand_total", "adjustment", "discount")
        widgets={
            'remark' : forms.Textarea(attrs={'rows':2 ,'class':'form-control'}),
            'date' :forms.DateInput(format = '%-d %B, %Y'),
        }

    def __init__(self,user,*args,**kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        self.fields["company"].queryset = self.fields['company'].queryset.exclude(status=Company.IS_INACTIVE)
        if self.user.role == User.COMPANY_ADMIN :
            self.fields.pop('company')

        if self.user.role == User.SALES_REPRESENTATIVE:
            self.fields.pop('company')
            self.fields['customer'].queryset=Customer.objects.filter(sales_rep__id=self.user.id, status=Customer.ACTIVE)
        
        # if kwargs["instance"]:
        #     self.fields['status'].required = True

        #     # self.fields["company"].widget.attrs.update({"disabled": "disabled"})
        #     # self.fields["vendor"].widget.attrs.update({"disabled": "disabled"})
            
        # else:
        #     self.fields['status'].required = False

        self.fields["date"].initial = datetime.datetime.now().date()
        self.fields["date"].widget.attrs['readonly'] = True
        self.fields['credit_type'].widget.value_from_datadict = lambda *args: CreditMemo.WEB_CREDIT
        self.fields["credit_type"].widget.attrs['disabled'] = 'disabled'
        self.fields["item_total"].widget.attrs['readonly'] = True
        self.fields["adjustment"].widget.attrs['readonly'] = True
        self.fields["grand_total"].widget.attrs['readonly'] = True
        self.fields["adjustment"].required = False
        self.fields["discount"].required = False
        self.fields["remark"].required = False
        # if self.user.role == User.COMPANY_ADMIN:
        #     self.fields.pop('company')

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs["placeholder"] = visible.field.label

        self.fields["discount"].widget.attrs.update({"min": "0.00", "step": "0.01"})

        if self.user.role == User.SUPER_ADMIN:
            # self.fields["company"].widget.attrs["class"] = "select2-data-array form-control category-list"
            self.fields["company"].required = True
        


class CreditMemoProductForm(forms.ModelForm):

    SELECT = ""

    CHOICES = (
        (SELECT, "---------"),
    )
    unit_type = forms.ChoiceField(choices=CHOICES)

    class Meta:
        model = CreditMemoProduct
        fields = ("product", "unit_type", "return_quantity", "fresh_return_quantity", "damage_return_quantity",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs["placeholder"] = visible.field.label
        self.fields["product"].widget.attrs.update({"class": "form-control select2"})
        self.fields["unit_type"].widget.attrs.update({"class": "form-control select2"})
        self.fields["product"].widget.attrs.update({"data-url": reverse('credit_memo:get_product_details_ajax')})
        

class CreditMemoUpdateForm(forms.ModelForm):
    
    class Meta:
        model = CreditMemo
        fields = ("company", "customer", "date", "credit_type", "remark", "item_total", "grand_total", "adjustment", "discount", "status")
        widgets={
            'remark' : forms.Textarea(attrs={'rows':2 ,'class':'form-control'}),
            'date' :forms.DateInput(format = '%-d %B, %Y'),
        }

    def __init__(self,user,*args,**kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        self.fields["company"].queryset = self.fields['company'].queryset.exclude(status=Company.IS_INACTIVE)
        if self.user.role == User.COMPANY_ADMIN:
            self.fields.pop('company')

        if self.user.role == User.SALES_REPRESENTATIVE:
            self.fields.pop('company')
        
        
        self.fields['status'].required = True
        # self.fields["company"].widget.attrs.update({"disabled": "disabled"})
        # self.fields["vendor"].widget.attrs.update({"disabled": "disabled"})

        self.fields["date"].initial = self.instance.date
        self.fields["date"].widget.attrs['readonly'] = True
        self.fields['credit_type'].widget.value_from_datadict = lambda *args: CreditMemo.WEB_CREDIT
        self.fields["credit_type"].widget.attrs['disabled'] = 'disabled'
        self.fields["item_total"].widget.attrs['readonly'] = True
        self.fields["adjustment"].widget.attrs['readonly'] = True
        self.fields["grand_total"].widget.attrs['readonly'] = True
        self.fields["adjustment"].required = False
        self.fields["discount"].required = False
        self.fields["remark"].required = False

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs["placeholder"] = visible.field.label

        self.fields["discount"].widget.attrs.update({"min": "0.00", "step": "0.01"})

        if self.user.role == User.SUPER_ADMIN:
            # self.fields["company"].widget.attrs["class"] = "select2-data-array form-control category-list"
            self.fields["company"].required = True
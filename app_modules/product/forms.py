from django import forms
from app_modules.vendors.models import Vendor
from app_modules.product.models import Brand, Product, WarehouseProductStock, Barcode, ProductVehicle, Warehouse
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.core.exceptions import ValidationError
from app_modules.company.models import Company  
from django.contrib.auth import get_user_model
User = get_user_model()



class BrandCreateForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(BrandCreateForm, self).__init__(*args, **kwargs)

        self.fields['company'].queryset = self.fields['company'].queryset.exclude(status=Company.IS_INACTIVE)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label
        self.fields['description'].widget.attrs = {'class': 'form-control','rows': 4}
        self.fields["company"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["status"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields['description'].required=False

                                                          

class ProductCreateForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            "company",
            "name",
            "genericname",
            "code",
            "vehicle",
            "product_image",
            "brand",
            # "is_apply_ml_quantity",
            # "ml_quantity",
            # "is_apply_weight",
            "box",
            # "weight",
            "box_piece",
            "case",
            "case_piece",
            # "srp",
            "status",
            # "is_type_a_invoice",
            "mrp",
            "wholesale_rate",
            "retail_rate",
            "purchase_price",
            "unit",
            ) 
        # exclude = ("case_upc", "box_upc", "product_upc")

    def __init__(self, user, *args, **kwargs):
        super( ProductCreateForm, self).__init__(*args, **kwargs)
        if user.role in [User.COMPANY_ADMIN, User.SALES_REPRESENTATIVE]:
            self.fields["brand"].queryset = Brand.objects.filter(company__id=user.get_company_id,status = Brand.ACTIVE)


        if user.role == User.SUPER_ADMIN:
            self.fields["brand"].queryset = Brand.objects.filter(status = Brand.ACTIVE)

        if self.instance.id:
            self.fields["brand"].initial = self.instance.brand
            if user.role in [User.COMPANY_ADMIN, User.SALES_REPRESENTATIVE]:
                self.fields["brand"].queryset = Brand.objects.filter(company__id=user.get_company_id,status = Brand.ACTIVE)
            else:
                self.fields["brand"].queryset = Brand.objects.filter(company=self.instance.company,status = Brand.ACTIVE)
            if self.instance.code:
                self.fields["code"].disabled = True
        self.fields['company'].queryset = self.fields['company'].queryset.exclude(status=Company.IS_INACTIVE)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label
        # self.fields['is_apply_ml_quantity'].widget.attrs = {'class': 'mt-2',}
        # self.fields['is_apply_weight'].widget.attrs = {'class': 'mt-2',}
        # self.fields['is_type_a_invoice'].widget.attrs = {'class': 'mt-2',}
        self.fields['box'].widget.attrs = {'class': 'mt-2',}
        self.fields['case'].widget.attrs = {'class': 'mt-2',}

        # self.fields['ml_quantity'].required=False
        # self.fields['weight'].required=False
        self.fields['box_piece'].required=False
        self.fields['case_piece'].required=False
        self.fields['product_image'].required=False
        self.fields['purchase_price'].required=False
        # self.fields['is_apply_ml_quantity'].required=False
        # self.fields['is_apply_weight'].required=False
        self.fields['wholesale_rate'].required=False
        self.fields['retail_rate'].required=False
        self.fields['unit'].required=False
        self.fields['code'].required=True

        self.fields["brand"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["company"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["status"].widget.attrs["class"] = "select2-data-array form-control select2-list"
        self.fields["vehicle"].widget.attrs["class"] = "select2-data-array form-control"
        # self.fields["ml_quantity"].widget.attrs["placeholder"] = "0.0"
        # self.fields["weight"].widget.attrs["placeholder"] = "0.0"
        self.fields["box_piece"].widget.attrs["placeholder"] = "0"
        self.fields["case_piece"].widget.attrs["placeholder"] = "0"
        # self.fields["ml_quantity"].widget.attrs["min"] = 0
        
        # self.fields["product_image"].widget.attrs["class"] = "custom-file-input"
        # self.fields["company"].widget.attrs["onchange"] = "loadCategory()"

    # def clean_ml_quantity(self):
    #     return self.clean_method_save_value(
    #         'is_apply_ml_quantity', 'ml_quantity'
    #     )
    
    # def clean_weight(self):
    #     return self.clean_method_save_value('is_apply_weight', 'weight')
    
    def clean_box_piece(self):
        return self.clean_method_save_value('box', 'box_piece')
    
    def clean_case_piece(self):
        return self.clean_method_save_value('case', 'case_piece')
    
    def clean_method_save_value(self, arg0, arg1):
        arg_0 = self.cleaned_data.get(arg0)
        arg_1 = self.cleaned_data.get(arg1)
        return arg_1 if arg_0 else 0.0

    # def clean_retail_rate(self):
    #     wholesale_rate = self.cleaned_data.get("wholesale_rate")
    #     retail_rate = self.cleaned_data.get("retail_rate")

    #     if wholesale_rate == 0 and retail_rate == 0:
    #         raise forms.ValidationError("Please enter wholesale rate or retail rate.")
        
    #     return retail_rate
        
    
    # def clean_product_upc(self):
    #     product_upc = self.cleaned_data.get("product_upc")
    #     box_upc = self.cleaned_data.get("box_upc")
    #     case_upc = self.cleaned_data.get("case_upc")

    #     if Product.objects.filter(Q(product_upc=product_upc) | Q(box_upc=product_upc) | Q(case_upc=product_upc)).exists():
    #         raise ValidationError("UPC already exists.")
        
    #     # if product_upc == box_upc or box_upc == case_upc or product_upc == case_upc:
    #     #     print("product_upc:::::", product_upc, box_upc, case_upc)
    #     #     raise ValidationError("Product UPC, Box UPC and Case UPC are not same.")

    #     return product_upc

    # def clean_box_upc(self):
    #     product_upc = self.cleaned_data.get("product_upc")
    #     box_upc = self.cleaned_data.get("box_upc")
    #     case_upc = self.cleaned_data.get("case_upc")

    #     if Product.objects.filter(Q(product_upc=box_upc) | Q(box_upc=box_upc) | Q(case_upc=box_upc)).exists():
    #         raise ValidationError("UPC already exists.")
        
    #     # if product_upc == box_upc or box_upc == case_upc or product_upc == case_upc:
    #     #     print("box_upc:::::", product_upc, box_upc, case_upc)
    #     #     raise ValidationError("Product UPC, Box UPC and Case UPC are not same.")

    #     return box_upc

    # def clean_case_upc(self):
    #     product_upc = self.cleaned_data.get("product_upc")
    #     box_upc = self.cleaned_data.get("box_upc")
    #     case_upc = self.cleaned_data.get("case_upc")

    #     if Product.objects.filter(Q(product_upc=case_upc) | Q(box_upc=case_upc) | Q(case_upc=case_upc)).exists():
    #         raise ValidationError("UPC already exists.")
        
    #     # if product_upc == box_upc or box_upc == case_upc or product_upc == case_upc:
    #     #     print("case_upc:::::", product_upc, box_upc, case_upc)
    #     #     raise ValidationError("Product UPC, Box UPC and Case UPC are not same.")

    #     return case_upc

    # def clean(self):
    #     cleaned_data = self.cleaned_data
    #     product_upc = cleaned_data.get("product_upc")
    #     box_upc = cleaned_data.get("box_upc")
    #     case_upc = cleaned_data.get("case_upc")
    #     if product_upc == box_upc or box_upc == case_upc or product_upc == case_upc:
    #         print("------->>>>>>>>>>>>>")
    #         raise ValidationError({"case_upc": "Product UPC, Box UPC and Case UPC are not same."})
    #     return cleaned_data

    # `clean_ml_quantity`, `clean_weight`, `clean_box_piece` and `clean_case_piece`
    
    
    
class ProductPriceUpdateForm(forms.ModelForm):
    class Meta:
        model =  Product
        fields = ("name", "mrp", "wholesale_rate", "retail_rate", "purchase_price",)

    def __init__(self, *args, **kwargs):
        super(ProductPriceUpdateForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label
        self.fields["name"].widget.attrs["readonly"] = True
        
   


class ImportProductCSVForm(forms.Form):
    csv_file = forms.FileField(widget=forms.FileInput(attrs={'accept': ".xlsx" or ".xls"}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(ImportProductCSVForm, self).__init__(*args, **kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label

    def clean_csv_file(self):
        csv_file = self.cleaned_data["csv_file"]
        if not [csv_file.name.endswith('.xlsx') or csv_file.name.endswith('.xls')]:
            raise ValidationError("Only .xlsx  and .xls file is accepted.")
        return csv_file


class CreateProductCSVForm(forms.ModelForm):
    
    class Meta:
        model = Product
        fields = (
            "name",
            "code",
            "vehicle",
            "product_image",
            "brand",
            "is_apply_ml_quantity",
            "ml_quantity",
            "is_apply_weight",
            "weight",
            "srp",
            "status",
            "is_type_a_invoice",
            "box",
            "box_piece",
            "case",
            "case_piece",
            "company",
            "mrp",
            "wholesale_rate",
            "retail_rate",
            "purchase_price",
        )  
    
    
                                                                            

    # def clean_product_upc(self):
    #     product_upc = self.cleaned_data.get("product_upc")
    #     box_upc = self.cleaned_data.get("box_upc")
    #     case_upc = self.cleaned_data.get("case_upc")

    #     if Product.objects.filter(Q(product_upc=product_upc) | Q(box_upc=product_upc) | Q(case_upc=product_upc)).exists():
    #         raise ValidationError("UPC already exists.")
        
    #     # if product_upc == box_upc or box_upc == case_upc or product_upc == case_upc:
    #     #     print("product_upc:::::", product_upc, box_upc, case_upc)
    #     #     raise ValidationError("Product UPC, Box UPC and Case UPC are not same.")

    #     return product_upc

    # def clean_box_upc(self):
    #     product_upc = self.cleaned_data.get("product_upc")
    #     box_upc = self.cleaned_data.get("box_upc")
    #     case_upc = self.cleaned_data.get("case_upc")

    #     if Product.objects.filter(Q(product_upc=box_upc) | Q(box_upc=box_upc) | Q(case_upc=box_upc)).exists():
    #         raise ValidationError("UPC already exists.")
        
    #     # if product_upc == box_upc or box_upc == case_upc or product_upc == case_upc:
    #     #     print("box_upc:::::", product_upc, box_upc, case_upc)
    #     #     raise ValidationError("Product UPC, Box UPC and Case UPC are not same.")

    #     return box_upc

    # def clean_case_upc(self):
    #     product_upc = self.cleaned_data.get("product_upc")
    #     box_upc = self.cleaned_data.get("box_upc")
    #     case_upc = self.cleaned_data.get("case_upc")

    #     if Product.objects.filter(Q(product_upc=case_upc) | Q(box_upc=case_upc) | Q(case_upc=case_upc)).exists():
    #         raise ValidationError("UPC already exists.")
        
    #     # if product_upc == box_upc or box_upc == case_upc or product_upc == case_upc:
    #     #     print("case_upc:::::", product_upc, box_upc, case_upc)
    #     #     raise ValidationError("Product UPC, Box UPC and Case UPC are not same.")

    #     return case_upc

    # def clean(self):
    #     cleaned_data = self.cleaned_data
    #     product_upc = cleaned_data.get("product_upc")
    #     box_upc = cleaned_data.get("box_upc")
    #     case_upc = cleaned_data.get("case_upc")
    #     if product_upc == box_upc or box_upc == case_upc or product_upc == case_upc:
    #         raise ValidationError("Product UPC, Box UPC and Case UPC are not same.")
    #     return cleaned_data


class AddStockCSVForm(forms.Form):
    csv_file = forms.FileField(widget=forms.FileInput(attrs={'accept': ".xlsx" or ".xls"}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(AddStockCSVForm, self).__init__(*args, **kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label

    def clean_csv_file(self):
        csv_file = self.cleaned_data["csv_file"]
        if not [csv_file.name.endswith('.xlsx') or csv_file.name.endswith('.xls')]:
            raise ValidationError("Only .xlsx  and .xls file is accepted.")
        return csv_file


class UpdateStockCSVForm(forms.ModelForm):

    class Meta:
        model = WarehouseProductStock
        fields = ("warehouse", "product", "stock")


class WarehouseStockForms(forms.Form):
    warehouse= forms.IntegerField()
    company= forms.IntegerField()
    stock= forms.IntegerField()


class StockCreateForm(forms.ModelForm):
    class Meta:
        model = WarehouseProductStock
        fields = ("warehouse", "product", "stock")
    
    def __init__(self, *args, **kwargs):
        super(StockCreateForm, self).__init__(*args, **kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.required = False
            visible.field.widget.attrs['placeholder'] = visible.field.label

        self.fields["warehouse"].widget.attrs['class'] = 'select2-list'
        self.fields["product"].widget.attrs['class'] = 'select2-list'
                                                                             
class BarcodeForm(forms.ModelForm):
    class Meta:
        model = Barcode
        fields = ("__all__")

    def __init__(self, *args, **kwargs):
        
        super(BarcodeForm, self).__init__(*args, **kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label
        self.fields['barcode_number'].widget.attrs={'placeholder':'Barcode Number(Code128)','class':'form-control'}


class BarcodeCreateFromCSVForm(forms.ModelForm):
    class Meta:
        model = Barcode
        fields = ("product", "product_type", "barcode_number")


class ProductVehicleForm(forms.ModelForm):

    class Meta:
        model = ProductVehicle
        fields = ("name", "company")

    def __init__(self, *args, **kwargs):
        super(ProductVehicleForm, self).__init__(*args, **kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label
        
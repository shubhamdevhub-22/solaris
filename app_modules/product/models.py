import math  
from django.db import models
from app_modules.base.models import BaseModel
from app_modules.vendors.models import Vendor
from app_modules.company.models import Company,Warehouse
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from app_modules.customers.validators import validate_file_extension
from django.contrib.auth import get_user_model
User = get_user_model()
# Create your models here.


class Brand(BaseModel):
    ACTIVE = "active"
    INACTIVE = "inactive"

    STATUS_CHOICES = (
        (ACTIVE, "Active"),
        (INACTIVE, "Inactive"),
    )
    name = models.CharField(
        max_length=50,
        verbose_name='Brand Name'
    )

    company = models.ForeignKey(
        Company,
        verbose_name="Company",
        on_delete=models.CASCADE,
        related_name="brand_company"
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        verbose_name='Status',
        default=ACTIVE
    )

    description = models.TextField(
        max_length=150,
        verbose_name="Description",
        null=True, blank=True
    )

    discount_a = models.FloatField(_("Discount A (%)"), null=True, blank=True, default=0)
    discount_b = models.FloatField(_("Discount B (%)"), null=True, blank=True, default=0)

    def __str__(self):
        return f'{self.name}'

    @property
    def product_count(self):
        return Product.objects.filter(brand__id=self.id).count()

    @property
    def active_product_count(self):
        return Product.objects.filter(
            brand__id=self.id, status=Product.ACTIVE).count()

    @property
    def inactive_product_count(self):
        return Product.objects.filter(
            brand__id=self.id, status=Product.INACTIVE).count()

class ProductVehicle(BaseModel):
    name = models.CharField(verbose_name="Vehicle name", max_length=1000, unique=True)
    company = models.ForeignKey(Company, verbose_name="Company", on_delete=models.CASCADE, related_name="product_vehicle_set")

    def __str__(self):
        return self.name

class Product(BaseModel):

    ACTIVE = "active"
    INACTIVE = "inactive"

    STATUS_CHOICES = (
        (ACTIVE, "Active"),
        (INACTIVE, "Inactive"),
    )

    name = models.CharField(max_length=50,verbose_name='Product Name')
    genericname = models.CharField(max_length=50,verbose_name='Product Generic Name',blank=True,null=True)
    code = models.CharField(max_length=50,verbose_name='Product Code',blank=True,null=True, unique=True)
    vehicle = models.ForeignKey(ProductVehicle, related_name="vehicle_set", on_delete=models.CASCADE,blank=True,null=True)
    product_image = models.ImageField(verbose_name="Product Image",upload_to='product-images',height_field=None,width_field=None,)
    brand = models.ForeignKey(Brand,on_delete=models.CASCADE,related_name="product_brand")
    is_apply_ml_quantity = models.BooleanField(verbose_name="Is Apply ML Quantity",default=False)
    ml_quantity = models.FloatField(verbose_name="ML Quantity",default=0.00)
    is_apply_weight = models.BooleanField(verbose_name="Is Apply Weight (OZ)",default=False)
    weight = models.FloatField(verbose_name="Weight (Oz)",default=0.00)
    # stock = models.PositiveIntegerField(verbose_name="Stock(Pieces)",default=0)
    srp = models.FloatField(verbose_name="SRP(Suggested Retail Price)",blank=True,null=True)
    status = models.CharField(max_length=10,choices=STATUS_CHOICES,verbose_name='Status',default=False)
    is_type_a_invoice = models.BooleanField(verbose_name="Is Type A Invoice",default=False)
    box = models.BooleanField(verbose_name="Box",default=False)
    box_piece = models.IntegerField(verbose_name="Pieces in Box",default=0)
    case = models.BooleanField(verbose_name="Case",default=False)
    case_piece = models.IntegerField(verbose_name="Pieces in Case",default=0)
    company = models.ForeignKey(Company,verbose_name="Company",on_delete=models.CASCADE,related_name="product_company")
    #product price sagement
    mrp = models.FloatField(verbose_name="MRP",default=0.00)
    wholesale_rate = models.FloatField(verbose_name="Wholesale Rate",default=0.00)
    retail_rate = models.FloatField(verbose_name="Retail  Rate",default=0.00)
    purchase_price = models.FloatField(verbose_name="Purchase Price",default=0.00)
    cost_price = models.FloatField(verbose_name="Cost Price",default=0.00)
    unit = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name
    
    @property
    def get_product_available_total_pieces(self):
        pieces = 0
        pieces =  self.product_stock.all().aggregate(available_pieces = Sum("stock"))
        return pieces['available_pieces']
    
    @property
    def get_product_available_total_box(self):
        available_boxes = 0
        if self.box:
            pieces = self.product_stock.all().aggregate(available_pieces = Sum("stock"))
            pieces = pieces['available_pieces']
            available_boxes = pieces/self.box_piece
            available_boxes = math.floor(available_boxes)
        return available_boxes
    
    @property
    def get_product_available_total_case(self):
        available_cases = 0
        if self.case:
            pieces = self.product_stock.all().aggregate(available_pieces = Sum("stock"))
            pieces = pieces['available_pieces']
            available_cases = pieces/self.case_piece
            available_cases = math.floor(available_cases)
        return available_cases
    
    @property
    def get_wholesale_base_price(self):
        if self.box:
            return self.box_piece * self.wholesale_rate
        if self.case:
            return self.case_piece * self.wholesale_rate
    
    @property
    def get_retail_base_price(self):
        if self.box:
            return self.box_piece * self.retail_rate
        if self.case:
            return self.case_piece * self.retail_rate
    
    @property
    def get_distributor_base_price(self):
        if self.box:
            return self.box_piece * self.mrp
        if self.case:
            return self.case_piece * self.mrp
        
    # @property
    # def get_wholesale_min_price(self):
    #     if self.box:
    #         return self.box_piece * self.wholesale_min_price
    #     if self.case:
    #         return self.case_piece * self.wholesale_min_price
    
    # @property
    # def get_retail_min_price(self):
    #     if self.box:
    #         return self.box_piece * self.retail_min_price
    #     if self.case:
    #         return self.case_piece * self.retail_min_price
    
    @property
    def get_distributor_min_price(self):
        if self.box:
            return self.box_piece * self.purchase_price
        if self.case:
            return self.case_piece * self.purchase_price
        
class WarehouseProductStock(BaseModel):

    warehouse=models.ForeignKey(
        Warehouse,
        verbose_name="Warehouse",
        related_name="warehouse_stock",
        on_delete=models.CASCADE)
    
    product=models.ForeignKey(
        Product,
        verbose_name="Product",
        related_name="product_stock",
        on_delete=models.CASCADE)
    
    stock = models.PositiveIntegerField(
        verbose_name="Stock(Pieces)",
        default=0)
    
    ready_for_dispatch = models.PositiveIntegerField(
        verbose_name="Ready for Dispatch Stock(Pieces)",
        default=0)
    
    def __str__(self):
        return self.product.name
    
class WarehouseProductStockHistory(BaseModel):

    warehouse=models.ForeignKey(
        Warehouse,
        verbose_name="Warehouse",
        related_name="warehouse_stock_history",
        on_delete=models.CASCADE)
    
    product=models.ForeignKey(
        Product,
        verbose_name="Product",
        related_name="product_stock_history",
        on_delete=models.CASCADE)
    
    before_stock = models.PositiveIntegerField(
        verbose_name="Before Stock(Pieces)",
        default=0)
    
    affected_stock = models.IntegerField(
        verbose_name="Affected Stock(Pieces)",
        default=0)
    
    stock = models.PositiveIntegerField(
        verbose_name="Current Stock(Pieces)",
        default=0)

    remark = models.TextField(
        verbose_name="Remark",
        null= True,
        blank=True,
    ) 

    vehicle = models.ForeignKey(ProductVehicle, on_delete=models.CASCADE, related_name="product_stock_history_set", null=True, blank=True)

    def __str__(self):
        return self.product.name


class Barcode(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_barcode")
    product_type = models.CharField(verbose_name="Product Type", max_length=10 )
    barcode_number = models.CharField(unique=True, max_length=255)
    barcode_code = models.FileField(upload_to='product-barcode', validators=[validate_file_extension])

    def __str__(self):
        return self.product.name

    


class CSVFile(BaseModel):
    csv_file=models.FileField(upload_to='csv')


class ProductLog(BaseModel):
    product = models.ForeignKey(Product, verbose_name=_("Product"), on_delete=models.CASCADE, null=True, blank=True)
    action_by = models.ForeignKey(User, verbose_name=_("Action By"), on_delete=models.CASCADE, null=True, blank=True)
    remark = models.TextField(_("Remark"))
    credit_memo = models.ForeignKey("credit_memo.CreditMemo", verbose_name=_("Credit Memo"), on_delete=models.CASCADE, null=True, blank=True)
    warehouse = models.ForeignKey("company.Warehouse", verbose_name=_("Warehouse"), on_delete=models.CASCADE, null=True, blank=True)
    before_stock = models.PositiveIntegerField(
        verbose_name="Before Stock(Pieces)",
        null=True, blank=True)
    affected_stock = models.IntegerField(
        verbose_name="Affected Stock(Pieces)",
        null=True, blank=True)
    stock = models.PositiveIntegerField(
        verbose_name="Current Stock(Pieces)",
        null=True, blank=True)
    
    def __str__(self):
        return self.product.name
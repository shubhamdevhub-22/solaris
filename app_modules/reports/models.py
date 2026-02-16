from django.db import models
from app_modules.base.models import BaseModel
from app_modules.customers.models import Customer
from app_modules.order.models import OrderedProduct
from app_modules.users.models import User
from app_modules.product.models import Product
from django.utils.translation import gettext_lazy as _
# Create your models here.

class SalesRepCommissionCodeReport(BaseModel):
    
    EXCHANGE="exchange"
    TEXTABLE="textable"
    FREE_ITEM="free item"

    PRODUCT_LABEL_CHOICES= (
        (EXCHANGE,'Exchange'),
        (TEXTABLE,'Textable'),
        (FREE_ITEM,'Free Item')
    )
    order_product = models.ForeignKey(OrderedProduct, on_delete=models.CASCADE, related_name="order_product_report")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="report_product")
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE,null=True,related_name="report_customers")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sales_rep_report")
    product_commission_code = models.FloatField(verbose_name="Product Commission Code",default=0.00)
    total_sales_rep_commision = models.FloatField(verbose_name="Total Sales Rep Commission",default=0.00)
    unit_sold = models.PositiveIntegerField(_('Product Unit Sold'))
    unit_type = models.CharField(_('Product Unit Type'), max_length=50)
    product_label= models.CharField(_('Product Label'), choices = PRODUCT_LABEL_CHOICES, default=TEXTABLE, max_length=10)
    product_ml_quantity = models.FloatField(_("Product ML Quantity"), default=0)
    is_apply_ml = models.BooleanField( verbose_name="Is Apply ML Quantity", default=False)
    total_sold_piece = models.IntegerField(_("Total Sold Piece"))
    product_total_ml_quantity =  models.FloatField(_("Total Product ML Quantity"), default=0)
    ml_tax = models.FloatField(_("Product ML Tax"), default=0)
    product_cost_price = models.FloatField(verbose_name="Product Cost Price",default=0.00)
    product_wholesale_min_price = models.FloatField(verbose_name="Product Wholesale Min Price",default=0.00)
    product_wholesale_base_price = models.FloatField(verbose_name="Product Wholesale Base Price",default=0.00)
    product_retail_min_price = models.FloatField(verbose_name="Product Retail Min Price",default=0.00)
    product_retail_base_price = models.FloatField(verbose_name="Product Retail Base Price",default=0.00)
    product_sold_price = models.FloatField(verbose_name="Product Sold Price",default=0.00)

    def __str__(self):
        return self.created_by.role
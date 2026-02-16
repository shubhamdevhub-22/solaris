from django.contrib import admin
from app_modules.purchase_order.models import PurchaseOrder,PurchaseOrderProducts
# Register your models here.
admin.site.register(PurchaseOrder)
admin.site.register(PurchaseOrderProducts)
from django.contrib import admin
from app_modules.product.models import Brand,Product,WarehouseProductStock,WarehouseProductStockHistory,Barcode,CSVFile,ProductLog

# Register your models here.

admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(WarehouseProductStock)
admin.site.register(WarehouseProductStockHistory)
admin.site.register(Barcode)
admin.site.register(CSVFile)
admin.site.register(ProductLog)


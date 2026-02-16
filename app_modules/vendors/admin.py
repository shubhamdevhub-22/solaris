from django.contrib import admin
from app_modules.vendors.models import VendorDocument, VendorBill,VendorPaymentBill,Vendor,VendorPayment

# Register your models here.

admin.site.register(VendorDocument)
admin.site.register(VendorBill)
admin.site.register(VendorPaymentBill)
admin.site.register(Vendor)
admin.site.register(VendorPayment)
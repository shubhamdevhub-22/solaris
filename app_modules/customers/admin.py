from django.contrib import admin
from app_modules.customers.models import Customer, Payment,PriceLevel,CustomerDocuments,CustomerShippingAddress,CustomerBillingAddress,MultipleContact,CustomerBill,CustomerPaymentBill,SalesRoute,PriceLevelProduct,CustomerLog,Zone

# Register your models here.
admin.site.register(Customer)
admin.site.register(Payment)
admin.site.register(PriceLevel)
admin.site.register(CustomerDocuments)
admin.site.register(CustomerShippingAddress)
admin.site.register(CustomerBillingAddress)
admin.site.register(MultipleContact)
admin.site.register(CustomerBill)
admin.site.register(CustomerPaymentBill)
admin.site.register(SalesRoute)
admin.site.register(PriceLevelProduct)
admin.site.register(CustomerLog)
admin.site.register(Zone)
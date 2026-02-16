from django.contrib import admin
from app_modules.order.models import Order,OrderedProduct,Car,OrderLog,AssignDriverRoutes,AssignOrderRoutes, OrderBill
# Register your models here.
 
admin.site.register(Order)
admin.site.register(OrderBill)
admin.site.register(OrderedProduct)
admin.site.register(Car)
admin.site.register(OrderLog)
admin.site.register(AssignDriverRoutes)
admin.site.register(AssignOrderRoutes)
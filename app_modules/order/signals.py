import contextlib
from django.db.models.signals import  post_save
from django.dispatch import receiver
from app_modules.order.models import OrderedProduct, Order
from app_modules.reports.models import SalesRepCommissionCodeReport
from django.http import JsonResponse


@receiver(post_save, sender=Order)
def save_sales_rep_commision_model(sender,created, instance, **kwargs):
    
    if created:
        with contextlib.suppress(Exception):
            order_product = instance
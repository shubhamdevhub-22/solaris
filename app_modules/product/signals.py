import contextlib
from django.db.models.signals import  post_save
from django.dispatch import receiver
from app_modules.customers.models import PriceLevel, PriceLevelProduct
from app_modules.product.models import Product
from django.http import JsonResponse


@receiver(post_save, sender=Product)
def add_new_product_in_price_level(sender, instance, created, **kwargs):
    product = instance
    price_levels = PriceLevel.objects.filter(company=product.company)
    if created:
        for price_level in price_levels:
            PriceLevelProduct.objects.create(price_level=price_level, product=product, unit_type=PriceLevelProduct.PIECE, custom_price=0)
            if product.box:
                PriceLevelProduct.objects.create(price_level=price_level, product=product, unit_type=PriceLevelProduct.BOX, custom_price=0)

            if product.case:
                PriceLevelProduct.objects.create(price_level=price_level, product=product, unit_type=PriceLevelProduct.CASE, custom_price=0)
    if not created:
        for price_level in price_levels:
            if product.box:
                if not PriceLevelProduct.objects.filter(price_level=price_level, product=product, unit_type=PriceLevelProduct.BOX).exists():
                    PriceLevelProduct.objects.create(price_level=price_level, product=product, unit_type=PriceLevelProduct.BOX, custom_price=0)

            if product.case:
                if not PriceLevelProduct.objects.filter(price_level=price_level, product=product, unit_type=PriceLevelProduct.CASE).exists():
                    PriceLevelProduct.objects.create(price_level=price_level, product=product, unit_type=PriceLevelProduct.CASE, custom_price=0)
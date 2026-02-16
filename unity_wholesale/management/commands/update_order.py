from django.core.management import BaseCommand
from app_modules.order.models import OrderedProduct


class Command(BaseCommand):
    help = "Update discounts of ordered products."

    def handle(self, *args, **options):
        self.update_orders()

    def update_orders(self):
        order_products = OrderedProduct.objects.all()

        for order_product in order_products:
            if not order_product.product_discount1:
                order_product.product_discount1 = 0.0
                order_product.save()

            if not order_product.product_discount2:
                order_product.product_discount2 = 0.0
                order_product.save()
            
            if not order_product.special_rate:
                order_product.special_rate = 0
                order_product.save()
            
            if not order_product.special_discount:
                order_product.special_discount = 0.0
                order_product.save()


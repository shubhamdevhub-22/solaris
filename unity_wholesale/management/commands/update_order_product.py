from django.core.management import BaseCommand, call_command
from app_modules.order.models import OrderedProduct

class Command(BaseCommand):
    help = "Update Order Product information."

    def handle(self, *args, **options):
        self.update_order_product()

    def update_order_product(self):
        products = OrderedProduct.objects.all()
        for product in products:
            product.unpacked_quantity = product.quantity
            product.save()

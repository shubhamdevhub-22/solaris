from django.core.management import BaseCommand, call_command
from app_modules.order.models import Order

class Command(BaseCommand):
    help = "Generate order ID."

    def handle(self, *args, **options):
        self.generate_order_id()

    def generate_order_id(self):
        orders = Order.objects.all()
        for order in orders:
            if order.order_id:
                order.order_id = "{}{:05d}".format("ORD#", order.id)
                order.save()
                

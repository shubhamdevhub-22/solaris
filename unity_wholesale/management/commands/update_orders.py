from django.core.management import BaseCommand
from app_modules.order.models import OrderBill, Order


class Command(BaseCommand):
    help = "Update generate bill order."

    def handle(self, *args, **options):
        self.update_orders()

    def update_orders(self):
        order_bills = OrderBill.objects.all()
        for order_bill in order_bills:
            order = Order.objects.filter(id = order_bill.order.id).last()
            order.is_bill_generated = True
            if order.status not in [Order.DISPATCH, Order.COMPLETED]:
                order.status = Order.NEW
            order.save()
        
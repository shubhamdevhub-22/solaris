from django.core.management import BaseCommand
from app_modules.customers.models import Customer, Brand, MultipleVendorDiscount

class Command(BaseCommand):
    help = "Update customer discounts."

    def handle(self, *args, **options):
        self.update_discounts()

    def update_discounts(self):
        customers = Customer.objects.all()

        for customer in customers:
            brands = Brand.objects.filter(company = customer.company)
            for brand in brands:
                discount, created = MultipleVendorDiscount.objects.get_or_create(customer = customer, brand = brand)
                if created:
                    discount.primary_percent = 0
                    discount.additional_percent = 0
                    discount.save()

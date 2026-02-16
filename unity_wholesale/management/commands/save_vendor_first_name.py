from django.core.management import BaseCommand, call_command
from app_modules.vendors.models import Vendor

class Command(BaseCommand):
    help = "Update Vendor information."

    def handle(self, *args, **options):
        self.save_client_full_name()

    def save_client_full_name(self):
        vendors = Vendor.objects.all()
        for vendor in vendors:
            if not vendor.first_name:
                vendor.first_name = vendor.email.split("@")[0]
                vendor.save()

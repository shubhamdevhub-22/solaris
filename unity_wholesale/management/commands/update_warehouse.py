from django.core.management import BaseCommand, call_command
from app_modules.company.models import Warehouse
from app_modules.company.tasks import set_geocode_for_warehouse
from utils.helpers import get_geo_code_from_address



class Command(BaseCommand):
    help = "Update Warehouse Latitude and Logitude."

    def handle(self, *args, **options):
        self.update_warehouse_lat_long()

    def update_warehouse_lat_long(self):
        warehouses = Warehouse.objects.all()
        for warehouse in warehouses:
            set_geocode_for_warehouse.delay(warehouse.id)
            


            
           

 

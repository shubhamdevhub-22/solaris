from celery import shared_task
from app_modules.company.models import Warehouse,Company

from utils.helpers import get_geo_code_from_address

@shared_task()
def set_geocode_for_warehouse(warehouse_id):
    try:
        address = Warehouse.objects.get(id=warehouse_id)
        location = get_geo_code_from_address(address.address_line_1, address.city, address.state, address.country)
        if location:
            address.latitude = location.get("lat")
            address.longitude = location.get("lng")
        else:
            address.latitude = 0
            address.longitude = 0
        address.save()
    except Exception as e:
        import traceback
        print("exception in warehouse address::>>...", traceback.format_exc())


@shared_task()
def set_geocode_for_company(company_id):
    try:
        address = Company.objects.get(id=company_id)
        location = get_geo_code_from_address(address.address_line_1, address.city, address.state, address.country)
        if location:
            address.latitude = location.get("lat")
            address.longitude = location.get("lng")
        else:
            address.latitude = 0
            address.longitude = 0
        address.save()
    except Exception as e:
        import traceback
        print("exception in company address::>>...", traceback.format_exc())

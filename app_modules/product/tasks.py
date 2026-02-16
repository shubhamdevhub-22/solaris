import traceback
import pandas as pd
import io
from celery import shared_task
from app_modules.company.models import Company, Warehouse
from app_modules.product.forms import BarcodeCreateFromCSVForm, BarcodeForm, CreateProductCSVForm, UpdateStockCSVForm
from app_modules.product.models import CSVFile, Brand, Product, WarehouseProductStock, WarehouseProductStockHistory, ProductVehicle
from app_modules.vendors.models import Vendor
from barcode import Code39
from django.core.files import File
from barcode.writer import ImageWriter
import uuid
from io import BytesIO

@shared_task()
def import_product_from_xlsx(file):
    skip_records = []
    try:
        df = pd.read_excel(file)
        df = df.fillna('')
        product_list = df.to_dict(orient='records')

        company_dict = {}
        warehouse_dict = {}
        brand_dict = {}

        for record in product_list:
            #<--------------------product details---------------------->

            try:
                if not record.get('COMPANY') or not record.get('BRAND') or \
                    not record.get('PRODUCT_NAME') or not record.get('CODE'):
                    continue

                code = record.get('CODE')
                product_name = record.get('PRODUCT_NAME')

                if record.get('COMPANY') not in company_dict:
                    try:
                        company = Company.objects.get(company_name=record.get('COMPANY'))
                        company_dict[record.get('COMPANY')] = company
                    except:
                        print("Company `%s` not found" % record.get('COMPANY'))
                        continue
                else:
                    company = company_dict[record.get('COMPANY')]

                if record.get('BRAND') not in company_dict:
                    brand, _ = Brand.objects.get_or_create(name=record.get('BRAND'), company=company)
                    brand_dict[record.get('BRAND')] = brand
                else:
                    brand = brand_dict[record.get('BRAND')]

                warehouse = None
                stock = record.get('STOCK')
                if record.get('WAREHOUSE') and record.get('STOCK'):
                    if record.get('WAREHOUSE') not in company_dict:
                        warehouse, _ = Warehouse.objects.get_or_create(name=record.get('WAREHOUSE'), company=company)
                        warehouse_dict[record.get('WAREHOUSE')] = warehouse
                    else:
                        warehouse = warehouse_dict[record.get('WAREHOUSE')]
                
                status = Product.INACTIVE if record.get("STATUS") == 0 else Product.ACTIVE
                brand.description = record.get('BRAND_DESC')
                brand.save()
                product_obj,_ = Product.objects.get_or_create(company = company, name=product_name, brand=brand, code=code)
                product_vehicle, _ = ProductVehicle.objects.get_or_create(name = record.get('VEHICLE'), company=company)
                product_obj.vehicle = product_vehicle
                product_obj.genericname = record.get('PRODUCT_GENERIC_NAME')
                #<--------------------end of product details--------------->
                
                
                #<---------------quantity detials--------------------------->
                product_obj.is_apply_ml_quantity = True if str(record.get('IS_APPLY_ML_QUANTITY')).lower() == "yes" else False
                product_obj.ml_quantity = record.get('ML_QUANTITY') if product_obj.is_apply_ml_quantity  else 0
                product_obj.is_apply_weight = True if str(record.get('IS_APPLY_WEIGHT')).lower() == "yes" else False
                product_obj.weight = record.get('WEIGHT') if product_obj.is_apply_weight else 0
                product_obj.box = True if str(record.get('IS_BOX')).lower() == "yes" else False
                product_obj.box_piece = record.get('BOX_PIECE') if product_obj.box else 0
                product_obj.case = True if str(record.get('IS_CASE')).lower() == "yes" else False
                product_obj.case_piece = record.get('CASE_PIECE') if product_obj.case else 0
                #<---------------end of quantity detials---------------------->

                
                #<----------------product price details--------------------->
                product_obj.status = status
                product_obj.unit = record.get('UNIT') if record.get('UNIT') else ""
                product_obj.mrp = record.get('MRP') if record.get('MRP') else 0
                product_obj.wholesale_rate = record.get('WHOLESALE_RATE') if record.get('WHOLESALE_RATE') else 0
                product_obj.retail_rate = record.get('RETAIL_RATE') if record.get('RETAIL_RATE') else 0
                product_obj.purchase_price = record.get('PURCHASE_PRICE') if record.get('PURCHASE_PRICE') else 0
                #<----------------end of product price details-------------->
                
                product_obj.save()
            except:
                print("traceback ", traceback.format_exc())
                print(record)
                skip_records.append(record)
                continue
            
            # <---------------------Barcode Data-------------------------------->
            # barcode_data = {}
            # barcode_data["product"] = product_obj
            # barcode_data["product_type"] = "piece" if product_obj.case else "box"
            # barcode_data["barcode_number"] = record.get('BARCODE_NUMBER')
            # barcode_form = BarcodeCreateFromCSVForm(barcode_data)
            # if barcode_form.is_valid():
            #     barcode_instance = barcode_form.save(commit=False)
            #     barcode_instance.save()
            #     buffer = BytesIO()
            #     my_code = Code39(barcode_instance.barcode_number, writer=ImageWriter())
            #     my_code.write(buffer)
            #     barcode_instance.barcode_code = File(buffer, name=f"{str(uuid.uuid4())}.png")
            #     barcode_instance.save()
            # # <---------------------End Of Barcode Data--------------------------->

            if warehouse and stock:
                data_dict = {}
                data_dict["warehouse"] = warehouse
                data_dict["product"] = product_obj
                data_dict["stock"] = record.get('STOCK') if record.get('STOCK') else 0
                data_dict["ready_for_dispatch"] = data_dict["stock"]

                product_stock_obj = WarehouseProductStock.objects.filter(warehouse=warehouse, product=product_obj).first()
                if product_stock_obj:
                    stock_form = UpdateStockCSVForm(instance=product_stock_obj, data=data_dict)
                else:
                    stock_form = UpdateStockCSVForm(data_dict)
                if stock_form.is_valid():
                    instance = stock_form.save(commit=False)
                    instance.save()

                    last_product_stock_history = WarehouseProductStockHistory.objects.filter(warehouse=warehouse, product=product_obj).last()
                    if last_product_stock_history:
                        if last_product_stock_history.stock != instance.stock:
                            new_product_stock_history = WarehouseProductStockHistory.objects.create(warehouse=warehouse, product=product_obj)
                            new_product_stock_history.stock = instance.stock
                            # if last_product_stock_history.stock > instance.stock:
                            new_product_stock_history.affected_stock = instance.stock - last_product_stock_history.stock
                            new_product_stock_history.before_stock = last_product_stock_history.stock
                            new_product_stock_history.save()
                            # elif last_product_stock_history.stock < instance.stock:
                        
                    else:
                        new_product_stock_history = WarehouseProductStockHistory.objects.create(warehouse=warehouse, product=product_obj)
                        new_product_stock_history.before_stock = 0
                        new_product_stock_history.affected_stock = instance.stock
                        new_product_stock_history.stock = instance.stock
                        new_product_stock_history.save()
                else:
                    pass
                
                
    except Exception as e:
        print("exception::>>...", traceback.format_exc())
    
    
    print("skip_records ============")
    print(skip_records)


@shared_task()
def import_product_stock_from_xlsx(file):
    try:
        df = pd.read_excel(file)
        df = df.fillna('')
        stock_list = df.to_dict(orient='records')

        for idx, record in enumerate(stock_list):
            try:
                data_dict = {}
                company = Company.objects.get(company_name=record.get('COMPANY'))
                warehouse, _ = Warehouse.objects.get_or_create(name=record.get('WAREHOUSE'), company=company)
                data_dict["warehouse"] = warehouse
                # category = Category.objects.get(name=fields[3], company=company)
                product = Product.objects.get(name=record.get('PRODUCT_NAME'), company=company)
                data_dict["product"] = product
                data_dict["stock"] = record.get('STOCK') if record.get('STOCK') else 0
                data_dict["ready_for_dispatch"] = data_dict["stock"]
                product_stock_obj = WarehouseProductStock.objects.filter(warehouse=warehouse, product=product).first()
                if product_stock_obj:
                    stock_form = UpdateStockCSVForm(instance=product_stock_obj, data=data_dict)
                else:
                    stock_form = UpdateStockCSVForm(data_dict)
                if stock_form.is_valid():
                    instance = stock_form.save(commit=False)
                    instance.save()

                    last_product_stock_history = WarehouseProductStockHistory.objects.filter(warehouse=warehouse, product=product).last()
                    if last_product_stock_history:
                        if last_product_stock_history.stock != instance.stock:
                            new_product_stock_history = WarehouseProductStockHistory.objects.create(warehouse=warehouse, product=product)
                            new_product_stock_history.stock = instance.stock
                            # if last_product_stock_history.stock > instance.stock:
                            new_product_stock_history.affected_stock = instance.stock - last_product_stock_history.stock
                            new_product_stock_history.before_stock = last_product_stock_history.stock
                            new_product_stock_history.save()
                            # elif last_product_stock_history.stock < instance.stock:
                        
                    else:
                        new_product_stock_history = WarehouseProductStockHistory.objects.create(warehouse=warehouse, product=product)
                        new_product_stock_history.before_stock = 0
                        new_product_stock_history.affected_stock = instance.stock
                        new_product_stock_history.stock = instance.stock
                        new_product_stock_history.save()
                else:
                    pass
            except:
                import traceback
                print(f"exception:: {idx}  >>. \n {record} \n..", traceback.format_exc())        

    except Exception as e:
        import traceback
        print("exception::>>...", traceback.format_exc())

        
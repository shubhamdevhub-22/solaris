from cmath import nan
from celery import shared_task
from app_modules.company.models import Company
from app_modules.customers.forms import CreateCustomerCSVForm, CreateZoneCSVForm, MultipleContactFromCSVForm

from app_modules.customers.models import Customer, CustomerBillingAddress, CustomerShippingAddress, MultipleContact, Zone, MultipleVendorDiscount, Brand
from app_modules.product.models import CSVFile
from utils.helpers import get_geo_code_from_address
import pandas as pd
import io
import math

from app_modules.users.models import User

@shared_task()
def set_geocode_for_customer_billing_address(customer_billing_address_id):
    try:
        billing_address = CustomerBillingAddress.objects.get(id=customer_billing_address_id)
        location = get_geo_code_from_address(billing_address.billing_address_line_1, billing_address.billing_city, billing_address.billing_state, billing_address.billing_country)
        if location:
            billing_address.billing_latitude = location.get("lat")
            billing_address.billing_longitude = location.get("lng")
            billing_address.save()
    except Exception as e:
        import traceback
        print("exception in billing address::>>...", traceback.format_exc())

@shared_task()
def set_geocode_for_customer_shipping_address(customer_shipping_address_id):
    try:
        shipping_address = CustomerShippingAddress.objects.get(id=customer_shipping_address_id)
        location = get_geo_code_from_address(shipping_address.shipping_address_line_1, shipping_address.shipping_city, shipping_address.shipping_state, shipping_address.shipping_country)
        if location:
            shipping_address.shipping_latitude = location.get("lat")
            shipping_address.shipping_longitude = location.get("lng")
            shipping_address.save()
    except Exception as e:
        import traceback
        print("exception in shipping address::>>...", traceback.format_exc())

def remove_quotes(val):
    if isinstance(val, str):
        val = val.replace("\"", "")
        val = val.replace("'", "")
    return val

def remove_double_space(val):
    if isinstance(val, str):
        val = val.replace("  ", " ")
    return val

def update_number_to_str(val):
    if isinstance(val, float) or isinstance(val, int):
        val = str(int(val))
    return val

@shared_task()
def import_customer_from_xlsx(file):
    
    # try:
    context = {
        'messages':[]
    }

    skip_customers = []

    df = pd.read_excel(file)
    df = df.fillna('')
    customer_list = df.to_dict(orient='records')

    for record in customer_list:
        try:
            
            print(record['CUST_CODE'])
            

            record['CUST_CODE'] = remove_quotes(record['CUST_CODE'])
            record['CUST_CODE'] = update_number_to_str(record['CUST_CODE'])
            print("After ")
            print(record['CUST_CODE'])
            lock = True if record['LOCK'] == "Y" else False
           
            print('record[company-before]: ', record['CUST_COMPANY'])
            record['CUST_COMPANY'] = remove_quotes(record['CUST_COMPANY'])
            record['CUST_COMPANY'] = remove_double_space(record['CUST_COMPANY'])
            print('record[company-after]: ', record['CUST_COMPANY'])
            
            print('record[zone-before]: ', record['CUST_ZONE'])
            record['CUST_ZONE'] = remove_quotes(record['CUST_ZONE'])
            print('record[zone-after]: ', record['CUST_ZONE'])
            
            print('record[CUST_AREA-before]: ', record['CUST_AREA'])
            record['CUST_AREA'] = remove_quotes(record['CUST_AREA'])
            print('record[CUST_AREA-after]: ', record['CUST_AREA'])

            print('record[CUST_PHONE1-before]: ', record['CUST_PHONE1'])
            record['CUST_PHONE1'] = remove_quotes(record['CUST_PHONE1'])
            print('record[CUST_PHONE1-after]: ', record['CUST_PHONE1'])

            print('record[CUST_PHONE2-before]: ', record['CUST_PHONE2'])
            record['CUST_PHONE2'] = remove_quotes(record['CUST_PHONE2'])
            print('record[CUST_PHONE2-after]: ', record['CUST_PHONE2'])

            print('record[CUST_MOBILE-before]: ', record['CUST_MOBILE'])
            record['CUST_MOBILE'] = remove_quotes(record['CUST_MOBILE'])
            print('record[CUST_MOBILE-after]: ', record['CUST_MOBILE'])

            print('record[CUST_NAME-before]: ', record['CUST_NAME'])
            record['CUST_NAME'] = remove_quotes(record['CUST_NAME'])
            record['CUST_NAME'] = remove_double_space(record['CUST_NAME'])
            print('record[CUST_NAME-after]: ', record['CUST_NAME'])

            record['CUST_AMOUNT'] = remove_quotes(record['CUST_AMOUNT'])
            if record['CUST_PIN']:
                print('record[CUST_PIN-before]: ', record['CUST_PIN'])
                record['CUST_PIN'] = remove_quotes(record['CUST_PIN'])
                print('record[CUST_PIN-after]: ', record['CUST_PIN'])
            
            print('record[CUST_PHONE1-before]: ', record['CUST_PHONE1'])
            record['CUST_PHONE1'] = update_number_to_str(record['CUST_PHONE1'])
            print('record[CUST_PHONE1-after]: ', record['CUST_PHONE1'])

            print('record[CUST_PHONE2-before]: ', record['CUST_PHONE2'])
            record['CUST_PHONE2'] = update_number_to_str(record['CUST_PHONE2'])
            print('record[CUST_PHONE2-after]: ', record['CUST_PHONE2'])
            
            print('record[CUST_MOBILE-before]: ', record['CUST_MOBILE'])
            record['CUST_MOBILE'] = update_number_to_str(record['CUST_MOBILE'])
            print('record[CUST_MOBILE-after]: ', record['CUST_MOBILE'])
            
            if not record.get('CUST_CODE') or not record.get('CUST_COMPANY'):
                print(f"Skipping row due to blank required fields: {record}")
                continue

            zone,_ = Zone.objects.get_or_create(zone_code=record['CUST_ZONE'])
            zone.save()
            company_obj = Company.objects.filter(company_name__iexact = record['CUST_COMPANY']).last()
            if company_obj:
                try:
                    customer = Customer.objects.get(code= record['CUST_CODE'])
                    customer.customer_name=record['CUST_NAME']
                    customer.zone = zone
                    customer.area = record['CUST_AREA']
                    customer.transport=record['CUST_TRANSPORT'] 
                    # customer.cst= record['CUST_CST']
                    # customer.gst= record['CUST_GST']

                    if record['CUST_PHONE1']:
                        customer.phone_1= record['CUST_PHONE1']
                    if record['CUST_PHONE2']:
                        customer.phone_2= record['CUST_PHONE2']
                    if record['CUST_MOBILE']:
                        customer.mobile= record['CUST_MOBILE']

                    customer.past_due_amount= record['CUST_AMOUNT']
                    # customer.fax= record['CUST_FAX']
                    # customer.remark= record['CUST_REMARK']
                    customer.email= record['CUST_EMAIL']
                    customer.contact_name = record['CUST_CONTACT_NAME']
                    customer.company = company_obj
                    customer.is_locked = lock
                    customer.save()

                    # Check for existing shipping address
                    shipping_address = CustomerShippingAddress.objects.filter(customer=customer).first()
                    if record['CUST_PIN'] and not math.isnan(float(record['CUST_PIN'])):
                            zip_code = record['CUST_PIN']
                    else:
                        zip_code = 0
                    if shipping_address:
                        print('shipping_address: ', shipping_address)
                        # Validate and assign CUST_PIN
                        shipping_address.shipping_address_line_1 = record['CUST_ADD1']
                        shipping_address.shipping_address_line_2 = record['CUST_ADD2']
                        shipping_address.shipping_address_line_3 = record['CUST_ADD3']
                        shipping_address.shipping_city = record['CUST_CITY']
                        shipping_address.shipping_state = record['CUST_STATE']
                        shipping_address.shipping_country = "India"
                        shipping_address.shipping_zip_code = zip_code
                        shipping_address.is_default = True
                        shipping_address.save()
                    else:
                        CustomerShippingAddress.objects.create(
                            customer=customer,
                            shipping_address_line_1=record['CUST_ADD1'],
                            shipping_address_line_2=record['CUST_ADD2'],
                            shipping_address_line_3=record['CUST_ADD3'],
                            shipping_city=record['CUST_CITY'],
                            shipping_state=record['CUST_STATE'],
                            shipping_country="India",
                            shipping_zip_code=zip_code,
                            is_default=True
                        )

                    # Check for existing billing address
                    billing_address = CustomerBillingAddress.objects.filter(customer=customer).first()
                    if billing_address:
                        print('billing_address: ', billing_address)
                        billing_address.billing_address_line_1 = record['CUST_ADD1']
                        billing_address.billing_address_line_2 = record['CUST_ADD2']
                        billing_address.billing_address_line_3 = record['CUST_ADD3']
                        billing_address.billing_city = record['CUST_CITY']
                        billing_address.billing_state = record['CUST_STATE']
                        billing_address.billing_country = "India"
                        billing_address.billing_zip_code = zip_code
                        billing_address.is_default = True
                        billing_address.save()
                    else:
                        CustomerBillingAddress.objects.create(
                            customer=customer,
                            billing_address_line_1=record['CUST_ADD1'],
                            billing_address_line_2=record['CUST_ADD2'],
                            billing_address_line_3=record['CUST_ADD3'],
                            billing_city=record['CUST_CITY'],
                            billing_state=record['CUST_STATE'],
                            billing_country="India",
                            billing_zip_code=zip_code,
                            is_default=True
                        )

                except:
                    customer = Customer.objects.create(
                        customer_name=record['CUST_NAME'],
                        code= record['CUST_CODE'],
                        zone = zone,
                        area = record['CUST_AREA'],
                        transport =record['CUST_TRANSPORT'] ,
                        # cst = record['CUST_CST'],
                        # gst= record['CUST_GST'],
                        past_due_amount= record['CUST_AMOUNT'],
                        # fax= record['CUST_FAX'],
                        # remark= record['CUST_REMARK'],
                        email= record['CUST_EMAIL'],
                        contact_name = record['CUST_CONTACT_NAME'],
                        company = company_obj,
                    )
                    if record['CUST_PHONE1']:
                        customer.phone_1 = record['CUST_PHONE1']
                    if record['CUST_PHONE2']:
                        customer.phone_1 = record['CUST_PHONE2']
                    if record['CUST_MOBILE']:
                        customer.mobile= record['CUST_MOBILE']
                    customer.save()

                    if record['CUST_PIN'] and not math.isnan(float(record['CUST_PIN'])):
                            zip_code = record['CUST_PIN']
                    else:
                        zip_code = 0


                    CustomerShippingAddress.objects.create(
                        customer = customer,
                        shipping_address_line_1= record['CUST_ADD1'],
                        shipping_address_line_2= record['CUST_ADD2'],
                        shipping_address_line_3= record['CUST_ADD3'],
                        shipping_city = record['CUST_CITY'],
                        shipping_state = record['CUST_STATE'],
                        shipping_country = "India",
                        shipping_zip_code = zip_code,
                        is_default = True,
                    )
                    CustomerBillingAddress.objects.create(
                        customer = customer,
                        billing_address_line_1= record['CUST_ADD1'],
                        billing_address_line_2= record['CUST_ADD2'],
                        billing_address_line_3= record['CUST_ADD3'],
                        billing_city = record['CUST_CITY'],
                        billing_state = record['CUST_STATE'],
                        billing_country = "India",
                        billing_zip_code = zip_code,
                        is_default = True,
                    )

                brands = Brand.objects.filter(company = customer.company)
                for brand in brands:
                    MultipleVendorDiscount.objects.create(
                        customer = customer,
                        brand = brand,
                        is_primary_brand_discount = True,
                        is_secondary_brand_discount = True,
                        primary_percent = brand.discount_a,
                        additional_percent = brand.discount_b,
                    )
                # MultipleContact.objects.create(
                #     customer_obj= customer,
                #     type=record['GRADE'],
                #     contact_person= record['CUST_PERSON'],
                #     email=record['CUST_EMAIL'],
                #     mobile_no=record['CUST_MOBILE'],
                # )
        except:
            import traceback
            print(traceback.format_exc())
            skip_customers.append(record)
            continue

    print("skip_customers ", skip_customers)


@shared_task()
def import_zone_from_xlsx(file, user_id):
    try:
        context = {
            'messages':[]
        }
        df = pd.read_excel(file)
        df = df.fillna('')
        zone_list = df.to_dict(orient='records')

        user = User.objects.filter(id = user_id).last()

        for record in zone_list:
            try:
                if user.is_superuser:
                    company = record['COMPANY']
                    company = Company.objects.filter(company_name = company).last()

                    if company:
                        zone, _ = Zone.objects.get_or_create(
                            zone_code = record['ZONE_CODE'],
                            company = company
                        )
                        zone.zone_description= record['ZONE_DESC']
                        zone.save()
                else:
                    company = Company.objects.filter(id = user.get_company_id).last()
                    
                    if company:
                        zone, _ = Zone.objects.get_or_create(
                            zone_code = record['ZONE_CODE'],
                            company = company,
                        )
                        zone.zone_description= record['ZONE_DESC']
                        zone.save()
            except Exception as e:
                context['exceptions_raised'] = e

        # lines = file_data.split("\n")
        # for line in lines[1:]:
        #     fields = line.split(",")
        #     try:
        #         if len(fields) > 0:
        #             data_dict = {}
        #             data_dict["zone_code"] = fields[0]
        #             # company = Company.objects.get(company_name=fields[0])
        #             data_dict["zone_description"] = fields[1]
        #             # category, _ = Category.objects.get_or_create(name=fields[3], company=company)
        #             # category.description = fields[4]
        #             # category.is_type_a_invoice = str(fields[5]).lower() == "yes"
        #             # category.save()
                    
        #             zone_obj = CreateZoneCSVForm(data_dict)
        #             if zone_obj.is_valid():
        #                 instance = zone_obj.save(commit=False)
        #                 instance.save()
        #     except Exception as e:
        #         import traceback
        #         print("exception::>>...", traceback.format_exc())
        #         continue

    except Exception as e:
        import traceback
        print("exception::>>...", traceback.format_exc())








# csv = request.FILES['csv']
#         csv_data = pd.read_csv(
#             io.StringIO(
#                 csv.read().decode("utf-8")
#             )
#         )

#         for record in csv_data.to_dict(orient="records"):
#             try:
#                 Students.objects.create(
#                     first_name = record['first_name'],
#                     last_name = record['last_name'],
#                     marks = record['marks'],
#                     roll_number = record['roll_number'],
#                     section = record['section']
#                 )
#             except Exception as e:
#                 context['exceptions_raised'] = e

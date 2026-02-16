import datetime
import json
import os
from typing import Any, Dict
from django.conf import settings
from django.core.files.base import ContentFile
from io import BytesIO
from xhtml2pdf import pisa

from django.forms import BaseModelForm
from app_modules.product.models import Product, Barcode, WarehouseProductStock,Brand
from app_modules.order.models import AssignDriverRoutes, AssignOrderRoutes, Order, OrderLog,OrderedProduct, Car, OrderBill
from app_modules.order.forms import AssignDriverRoutesForm, OrderFrom, OrderPackingForm,OrderedProductForm, CarForm
from django.contrib.messages.views import SuccessMessageMixin
from app_modules.users.models import User, Driver
from app_modules.company.models import Company, CompanyUsers, Warehouse
from app_modules.customers.models import Customer, CustomerBill,CustomerBillingAddress,CustomerShippingAddress, CustomerLog, MultipleVendorDiscount, Discount, Replacement, ReplacementProduct, Payment, CustomerPaymentBill
from django.views.generic import CreateView, View, ListView, UpdateView, DetailView, FormView,TemplateView
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from app_modules.utils import order_utils
from django.urls import reverse,reverse_lazy
from django.template.loader import get_template
from django.template.loader import render_to_string
from django_datatables_too.mixins import DataTableMixin
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import HttpResponseRedirect, redirect
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.utils.dateparse import parse_date
from app_modules.base.mixins import SalesLoginRequiredMixin, CompanyAdminLoginRequiredMixin
from num2words import num2words
from app_modules.order import utils
from app_modules.order.utils import get_best_route
from django.db.models import F

# Create your views here.

class OrderCreateView(SalesLoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderFrom
    # template_name = "order/create_order_form.html"
    success_url = reverse_lazy("order:order_list")

    def has_permission(self):
        if "bill/" in self.request.path and self.request.user.role in [User.SALES_REPRESENTATIVE]:
            return self.request.user.role in [User.COMPANY_ADMIN, User.SUPER_ADMIN]
        
        return super().has_permission()

    def get_template_names(self):
        if "bill/" in self.request.path:
            template_name = "order/bills/create_bill_form.html"
        else:
            template_name = "order/order_form.html"
        return template_name

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form2"] =  OrderedProductForm
        context["customers"] = Customer.objects.all().exclude(status=Customer.INACTIVE)
        return context
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.save()

        instance.order_id = "{}{:05d}".format("ORD#", instance.id)
        instance.save()

        # set adjustment to customer's store credit
        customer = Customer.objects.filter(id=instance.customer.id).first()
        customer.total_credit_amount += instance.adjustments
        customer.save()

        customer_billing_address = CustomerBillingAddress.objects.filter(customer=customer).first()
        if customer_billing_address:
            instance.billing_address_line_1 = customer_billing_address.billing_address_line_1
            instance.billing_address_line_2 = customer_billing_address.billing_address_line_2
            instance.billing_city = customer_billing_address.billing_city
            instance.billing_state = customer_billing_address.billing_state
            instance.billing_country = customer_billing_address.billing_country
            instance.billing_zip_code = customer_billing_address.billing_zip_code
            instance.save()

        customer_shipping_address = CustomerShippingAddress.objects.filter(customer=customer, is_default=True).first()
        if customer_shipping_address:
            instance.shipping_address_line_1 = customer_shipping_address.shipping_address_line_1
            instance.shipping_address_line_2 = customer_shipping_address.shipping_address_line_2
            instance.shipping_city = customer_shipping_address.shipping_city
            instance.shipping_state = customer_shipping_address.shipping_state
            instance.shipping_country = customer_shipping_address.shipping_country
            instance.shipping_zip_code = customer_shipping_address.shipping_zip_code
            instance.save()

        if instance.paid_amount > 0:
            Payment.objects.create(customer_name=customer, receive_amount=instance.paid_amount)

        if self.request.user.role in[User.COMPANY_ADMIN, User.SALES_REPRESENTATIVE]:
            instance.company = self.request.user.company_users.first().company
            instance.save()

        submit_type = self.request.POST.get("submit")

        # warehouse = Warehouse.objects.filter(id = instance.warehouse.id).first()

        # add products in order and upate product stock
        product_ids=self.request.POST.get('product_id_list').split(',')
        refrance = []
        if product_ids[0]!='':
            for product_id in product_ids:
                order_utils.add_product_list_in_order(self,instance,product_id,submit_type,refrance)
        instance.product_reference=refrance
        instance.save()

        if submit_type != "draft":

            if submit_type == "generate":
                shipping_charges = form.data.get('shipping_charges', 0)
                packing_charges = form.data.get('packing_charges', 0)

                shipping_charges = float(shipping_charges) if shipping_charges else 0
                packing_charges = float(packing_charges) if packing_charges else 0

                instance.shipping_charges = shipping_charges
                instance.packing_charges = packing_charges
                instance.grand_total = instance.item_total + shipping_charges + packing_charges
                instance.payment_method = form.data.get("payment_choice")
                instance.is_bill_generated = True

                if instance.payment_method == Order.CASH:
                    instance.paid_amount = instance.grand_total
                    Payment.objects.create(customer_name=instance.customer, receive_amount=instance.paid_amount)
                
                instance.save()


                order_bill = OrderBill(order = instance, customer = instance.customer, bill_amount = instance.grand_total)
                order_bill.slip_no = form.data["slip_no"]

                bill_date = form.data.get("bill_date")
                if bill_date:
                    order_bill.bill_date = datetime.datetime.strptime(bill_date, "%Y-%m-%d")

                due_date = form.data.get("due_date")
                if due_date:
                    order_bill.due_date = datetime.datetime.strptime(due_date, "%Y-%m-%d")

                if form.data["local_bill"] == "true":
                    order_bill.is_local_bill = True
                    order_bill.gr_date = None
                    order_bill.gr_number = ""
                    order_bill.case_number = None
                    order_bill.transporter = ""
                else:
                    order_bill.is_local_bill = False

                    gr_date = form.data.get("gr_date")
                    if gr_date:
                        order_bill.gr_date = datetime.datetime.strptime(gr_date, "%Y-%m-%d")
                    order_bill.gr_number = form.data["gr_number"]
                    order_bill.case_number = form.data["case_number"]
                    order_bill.transporter = form.data["transporter"]
                
                order_bill.written_by = form.data["written_by"]
                order_bill.checked_by = form.data["checked_by"]
                order_bill.packed_by = form.data["packed_by"]
                order_bill.due_amount = instance.grand_total - instance.paid_amount
                order_bill.paid_amount = instance.paid_amount
                order_bill.save()

                order_bill.bill_id = "{}{:05d}".format("BILL#", order_bill.id)

                if order_bill.due_amount == 0:
                    order_bill.status = OrderBill.COMPLETE
                order_bill.save()

                context = {}
                context["order_products"] = OrderedProduct.objects.filter(order=instance)
                context["order"] = instance
                context["order_bill"] = order_bill
                context["amount_in_words"] = num2words(instance.grand_total, lang='en_IN').title()

                if order_bill.due_date and order_bill.bill_date and order_bill.due_date > order_bill.bill_date:
                    due_days = (order_bill.due_date - order_bill.bill_date).days
                    context["due_days"] = "Within " + num2words(due_days, lang='en_IN').title() + " Days"

                pdf = utils.render_to_pdf('order/bills/print_order_bill.html', context)
                pdf_name = "order-%s.pdf" % str(instance.order_id)

                if pdf:
                    order_bill.bill_pdf.save(pdf_name, ContentFile(pdf))
                    order_bill.save()

                log_msg = f"New sales bill has been generated with Order ID:{instance.order_id}"
                CustomerLog.objects.create(customer=instance.customer, action_by=self.request.user, order=instance, remark=log_msg)
                OrderLog.objects.create(order=instance, remark=log_msg, action_by=self.request.user)

                messages.add_message(self.request, messages.SUCCESS, "Order bill generated.")
                return JsonResponse({"bill_pdf_url": order_bill.bill_pdf.url, "redirect_url": reverse("order:order_bill_list")})

            log_msg = f"New order has been created with Order ID:{instance.order_id}"
            CustomerLog.objects.create(customer=instance.customer, action_by=self.request.user, order=instance, remark=log_msg)
            OrderLog.objects.create(order=instance, remark=log_msg, action_by=self.request.user)

            messages.add_message(self.request, messages.SUCCESS, "New order created")
        else:
            instance.status = Order.DRAFT
            instance.save()
            messages.add_message(self.request, messages.SUCCESS, "Draft Order Created")

        return JsonResponse({"redirect_url": reverse("order:order_list")})
        # return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class AddProductDetailsInOrderListAjax(View):
    template1_name = "order/add_product_details_in_order_list.html"
    template2_name = "order/bills/add_product_details_in_bill_list.html"

    def post(self,request,*args, **kwargs):
        # sourcery skip: boolean-if-exp-identity, merge-dict-assign, move-assign-in-block, remove-unnecessary-cast
        context={}
        data={}
        product_id = request.POST['product_id']
        quantity = request.POST.get('quantity', 0)
        unit_price = request.POST.get('unit_price', 0)
        special_rate = request.POST.get('special_rate', 0)
        special_discount = request.POST.get('special_discount', 0)
        free_quantity = request.POST.get('free_quantity', 0)
        primary_discount = request.POST.get('primary_discount', 0)
        secondary_discount = request.POST.get('secondary_discount', 0)
        is_bill_create = request.POST.get('is_bill_create')
        price_type = request.POST.get('price_type')
        
        product = Product.objects.get(id = product_id)
    
        context['product'] = product
        context['base_price'] = float(unit_price)
        
        special_rate = float(special_rate) if special_rate else 0
        special_discount = float(special_discount) if special_discount else 0
        context["special"] = max(float(special_rate), float(special_discount))
        context["special_rate"] = special_rate
        context["special_discount"] = special_discount
        
        free_quantity = int(free_quantity) if free_quantity else 0
        quantity = int(quantity) if quantity else 0
        
        context['total_quantity'] = quantity
        context["free_quantity"] = free_quantity
        context["price_type"] = price_type

        # quantity = quantity - free_quantity
        # context['quantity'] = quantity

        if price_type == "retail":
            context["applied_product_price"] = product.retail_rate
        elif price_type == "wholesale":
            context["applied_product_price"] = product.wholesale_rate
        else:
            context["applied_product_price"] = product.mrp

        if is_bill_create == "false":
            if special_discount > 0 or special_rate > 0:
                context["unit_price"] = float(unit_price) - ((float(unit_price) / 100) * special_discount) if special_discount > 0 else special_rate
            else:
                context["unit_price"] = float(unit_price)
            context["net_amount"] = context["unit_price"] * quantity
            data['product_row']=render_to_string(self.template1_name, context, request=request)
        else:
            context["primary_discount"] = 0
            context["secondary_discount"] = 0

            if special_discount > 0:
                context["unit_price"] = float(unit_price) - ((float(unit_price) / 100) * special_discount)
            elif special_rate > 0:
                context["unit_price"] = special_rate
            else:
                discount_total = float(unit_price) - ((float(unit_price)*float(primary_discount))/100)
                additional_discount_total = discount_total - ((discount_total*float(secondary_discount))/100)
                context["unit_price"] = additional_discount_total
                
                context["primary_discount"] = float(primary_discount)
                context["secondary_discount"] = float(secondary_discount)

            context["net_amount"] = context["unit_price"] * quantity
            data['product_row']=render_to_string(self.template2_name, context, request=request)

        return JsonResponse(data)

class GetProductUnitTypesAjax(View):
    template_name = "order/get_product_unit_type.html"

    def post(self,request,*args, **kwargs):
        context={}
        data={}
        product_id = request.POST.get('product_id')
        customer_id = request.POST.get('customer_id')
        # product_barcode = request.POST['prd_barcode']
        # barcode = None

        # try:
        #     barcode = Barcode.objects.get(barcode_number=product_barcode)
        # except Barcode.DoesNotExist:
        #     barcode = None
        product = Product.objects.filter(id = product_id).last()
        context['product'] = product

        product_stock = WarehouseProductStock.objects.filter(product = product)
        data["stock"] = 0
        if product_stock:
            total_stock = product_stock.aggregate(total_stock = Sum("stock"))["total_stock"]
            data["stock"] = total_stock

        data["unit"] = product.unit
        data["brand"] = product.brand.id
        data["brand_name"] = product.brand.name
        data["code"] = product.code
        data["previous_price"] = 0
        data["vehicle"] = product.vehicle.name if product.vehicle else ""

        if (product.brand.discount_a and product.brand.discount_a > 0) or (product.brand.discount_b and product.brand.discount_b > 0):
            data["primary_discount"] = product.brand.discount_a
            data["secondary_discount"] = product.brand.discount_b
            data['applied_discount'] = "Brand discount applied"
        else:
            data['primary_discount'] = 0
            data['secondary_discount'] = 0
            data['applied_discount'] = "No discount found"

        if customer_id:
            customer = Customer.objects.filter(id = customer_id).last()
            # if customer.customer_type == Customer.RETAIL:
            #     data['base_price'] = product.retail_rate if product.retail_rate and product.retail_rate != 0 else product.mrp
            #     data['applied_price'] = "Retail"
            # elif customer.customer_type == Customer.WHOLESALE:
            #     data['base_price'] = product.wholesale_rate if product.wholesale_rate and product.wholesale_rate != 0 else product.mrp
            #     data['applied_price'] = "Wholesale"
            # else:
            data['base_price'] = product.mrp
            data['applied_price'] = "MRP"
        
            customer_discount = MultipleVendorDiscount.objects.filter(customer = customer, brand = product.brand).exclude( Q(primary_percent = 0), Q(additional_percent = 0)).last()
            if customer_discount:
                data['primary_discount'] = customer_discount.primary_percent
                data['secondary_discount'] = customer_discount.additional_percent
                data['applied_discount'] = "Customer discount applied"
            
            order_product = OrderedProduct.objects.filter(order__customer = customer, product = product, order__status = Order.COMPLETED).order_by("created_at").last()
            if order_product:
                data["previous_price"] = order_product.unit_price
        else:
            data['base_price'] = product.mrp
            data['applied_price'] = "MRP"


        # if barcode:
        #     barcode_product_type = barcode.product_type.capitalize()
        #     context['barcode_product_type'] = barcode_product_type
        #     data['product_unit_types']=render_to_string(self.template_name,context,request=request)
        # else:
        #     data['product_unit_types']=render_to_string(self.template_name,context,request=request)
            
        return JsonResponse(data)

class GetProductPriceStockAjax(View):
    template_name = "order/get_product_price_stock.html"
    
    def post(self,request,*args, **kwargs):
        context={}
        data={}
        
        product_id = request.POST['product_id']
        customer_id = request.POST['customer_id']
        unit_type = request.POST['unit_type']
        warehouse_stock_obj = WarehouseProductStock.objects.filter(product_id=product_id)
        avallable_stock = 0
        for item in warehouse_stock_obj:
            avallable_stock += item.stock
        if(unit_type !=''):
            context =  order_utils.get_customer_price_level(customer_id,product_id,unit_type)
            data['product_price_stock']=render_to_string(self.template_name,context,request=request)
            data['base_price'] = context['base_price']
            data['quantity_max'] = context['available_stock']
        return JsonResponse(data)      



class GetCustomersProductsAjax(View):

    template_name = "order/get_customers_products.html"

    def post(self,request,*args, **kwargs):

        context = {}
        data = {}
        company_id = request.POST['company_id']
        brand_id = request.POST.get('brand')
        is_update = request.POST.get('is_update')

        if self.request.user.role == User.SALES_REPRESENTATIVE:
            company_customers = Customer.objects.filter(company = company_id, sales_rep__id = self.request.user.id ,status = Customer.ACTIVE)
        else:
            company_customers = Customer.objects.filter(company = company_id, status = Customer.ACTIVE)
        
        if is_update == "false":
            company_customers = company_customers.filter(is_locked = False)

        company_warehouses = Warehouse.objects.filter(company = company_id, status = Warehouse.IS_ACTIVE)
        company_products = Product.objects.filter(company = company_id, status = Product.ACTIVE, brand__status = Brand.ACTIVE)

        if brand_id and brand_id != "0":
            company_products = company_products.filter(brand__id = brand_id)

        context['company_customers'] = company_customers
        data['company_customers']=render_to_string(self.template_name,context,request=request)
        context['company_customers'] = None
        context['company_warehouses'] = company_warehouses
        data['company_warehouses']=render_to_string(self.template_name,context,request=request)
        context['company_warehouses'] = None
        context['company_products'] = company_products
        data['company_products']=render_to_string(self.template_name,context,request=request)
        return JsonResponse(data)
    



class GetCustomerDetailsAjax(View):

    def post(self,request,*args, **kwargs):

        data = {}

        billing_address = {}

        customer_id = request.POST['customer_id']
        customer = Customer.objects.get(id = customer_id, status = Customer.ACTIVE)
        customer_billing_address = CustomerBillingAddress.objects.filter(customer=customer).first()
        billing_address["billing_address_line_1"]=customer_billing_address.billing_address_line_1
        billing_address["billing_address_line_2"]=customer_billing_address.billing_address_line_2
        billing_address["billing_city"]=customer_billing_address.billing_city
        billing_address["billing_state"]=customer_billing_address.billing_state
        billing_address["billing_country"]=customer_billing_address.billing_country
        billing_address["billing_zip_code"]=customer_billing_address.billing_zip_code

        customer_shipping_address = CustomerShippingAddress.objects.filter(customer=customer).first()
        shipping_address = customer_shipping_address.shipping_address_line_1
        shipping_address += ", "+customer_shipping_address.shipping_address_line_2
        shipping_address += ", "+customer_shipping_address.shipping_city
        shipping_address += ", "+customer_shipping_address.shipping_state if customer_shipping_address.shipping_state else ""
        shipping_address += "-"+str(customer_shipping_address.shipping_zip_code) if customer_shipping_address.shipping_zip_code else ""
        shipping_address += ", "+customer_shipping_address.shipping_country
        shipping_address += "\nZone: "+customer.zone.zone_code
        shipping_address += "\nArea: "+customer.area
        
        customer_past_due_amount = OrderBill.objects.filter(customer=customer, status=OrderBill.INCOMPLETE).aggregate(Sum('due_amount'))

        # data['customer_sales_representative'] = f'{customer.sales_rep}'
        # data['billing_address'] = f"{customer_billing_address.billing_address_line_1} {customer_billing_address.billing_address_line_2} {customer_billing_address.billing_suite_apartment} {customer_billing_address.billing_city},{customer_billing_address.billing_state}, {customer_billing_address.billing_country}-{customer_billing_address.billing_zip_code} "
        # data['shipping_address'] = f"{customer_shipping_address.shipping_address_line_1} {customer_shipping_address.shipping_address_line_2} {customer_shipping_address.shipping_suite_apartment} {customer_shipping_address.shipping_city},{customer_shipping_address.shipping_state}, {customer_shipping_address.shipping_country}-{customer_shipping_address.shipping_zip_code} "
        data['customer_sales_representative'] = customer.sales_rep.full_name if customer.sales_rep else ""
        data['billing_address'] = billing_address
        data['shipping_address'] = shipping_address
        data['area'] = customer.area
        data['past_due_amount'] = customer_past_due_amount["due_amount__sum"]
        data['total_credit_amount'] = customer.total_credit_amount
        return JsonResponse(data)


class OrderListView(SalesLoginRequiredMixin, ListView):

    template_name = "order/order_list.html"
    model = Order

    def has_permission(self):
        if "draft-orders/" in self.request.path and self.request.user.role in [User.SALES_REPRESENTATIVE]:
            return self.request.user.role in [User.COMPANY_ADMIN, User.SUPER_ADMIN]
        
        return super().has_permission()
    
    def get_queryset(self):        
        if self.request.user.is_superuser or self.request.user.role == User.COMPANY_ADMIN:
            qs = Order.objects.all()
        else:
            qs = Order.objects.filter(order_date = datetime.date.today())
        return qs

    # def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    #     order = Order.objects.all()
    #     order.update(status = Order.PACKED)
    #     return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
            
        context = super().get_context_data(**kwargs)
        if "draft-orders" in self.request.path:
            is_draft = True
            context["is_draft"] = is_draft
        else:
            is_new = True
            context["is_new"] = is_new
        # status = self.request.GET.get("status")
        # if status == Order.DRAFT:
            # is_draft = True

        context["order_statuses"] = Order.STATUS_CHOICES
        context["companies"] = Company.objects.filter(status=Company.IS_ACTIVE)
        context["customers"] = Customer.objects.filter(status=Customer.ACTIVE)
        if self.request.user.role == User.COMPANY_ADMIN:
            company_admin_company = self.request.user.company_users.first().company
            context["customers"] = Customer.objects.filter(status=Customer.ACTIVE, company = company_admin_company)
        if self.request.user.role == User.SALES_REPRESENTATIVE:
            context["customers"] = Customer.objects.filter(status=Customer.ACTIVE, sales_rep = self.request.user.id)

        return context

class DispatchOrderListView(CompanyAdminLoginRequiredMixin, ListView):
    template_name = "order/order_list.html"
    model = Order

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_dispatch"] = True
        context["order_statuses"] = Order.STATUS_CHOICES
        context["companies"] = Company.objects.filter(status=Company.IS_ACTIVE)
        context["customers"] = Customer.objects.filter(status=Customer.ACTIVE)
        if self.request.user.role == User.COMPANY_ADMIN:
            company_admin_company = self.request.user.company_users.first().company
            context["customers"] = Customer.objects.filter(status=Customer.ACTIVE, company = company_admin_company)
        if self.request.user.role == User.SALES_REPRESENTATIVE:
            context["customers"] = Customer.objects.filter(status=Customer.ACTIVE, sales_rep = self.request.user.id)

        return context


class OrderListAjax(DataTableMixin,View):
    model = Order

    def get_queryset(self):
        
        # if self.request.user.is_superuser or self.request.user.role == User.COMPANY_ADMIN:
        qs = Order.objects.all()
        # else:
        #     qs = Order.objects.filter(order_date=datetime.date.today())

        is_new = self.request.GET.get("is_new")
        is_draft = self.request.GET.get("is_draft")
        is_dispatch = self.request.GET.get("is_dispatch")
        is_generate = self.request.GET.get("is_generate")

        if is_new == "True":
            qs = qs.filter(status=Order.NEW, is_bill_generated=False)

        if is_draft == "True":
            qs = qs.filter(status=Order.DRAFT)
        
        if is_dispatch == "True":
            qs = qs.filter(Q(status=Order.COMPLETED) | Q(status=Order.DISPATCH))
        
        if is_generate =="True":
            qs = qs.filter(is_bill_generated = True)
        
        if self.request.user.role == User.COMPANY_ADMIN:
            company_id = list(self.request.user.company_users.all().values_list("company_id", flat=True))
            company_list = list(Company.objects.filter(id__in=company_id).values_list("id",flat=True))
            qs = qs.filter(company__in=company_list)

        if self.request.user.role == User.SALES_REPRESENTATIVE:
            company_id = self.request.user.get_company_id
            customers = list(Customer.objects.filter(sales_rep__id = self.request.user.id).values_list("id", flat=True))
            qs = qs.filter(company__id=company_id, customer__id__in = customers).filter(created_at__date = datetime.datetime.today())

        order_list_company=self.request.GET.get("order_list_company")
        if order_list_company:
            companies=list(Order.objects.filter(company__in = order_list_company).values_list("id",flat=True))
            qs = qs.filter(id__in = companies)
        
        order_status = self.request.GET.get("order_status")
        if order_status:
            order_list = list(Order.objects.filter(status = order_status).values_list("id",flat=True))
            qs = qs.filter(id__in = order_list)

        order_customer = self.request.GET.get("order_customer")
        if order_customer:
            qs = qs.filter(customer__id=int(order_customer))

        start_date = self.request.GET.get("from_date")
        end_date = self.request.GET.get("to_date")
        if end_date:
            order_list = list(Order.objects.filter(order_date__range=[start_date,end_date]).values_list("id",flat=True))
            qs = qs.filter(id__in = order_list)
    
        return qs.order_by("-id")
    
    def filter_queryset(self, qs):
        if self.search:
            return qs.filter(
                Q(order_id__icontains=self.search) |
                Q(status__icontains=self.search)
            )
        return qs
    
    def _get_actions_buttons(self,obj):
        order_bill = OrderBill.objects.filter(order = obj).last()

        if obj.status not in [Order.PACKED, Order.PACKING, Order.READY_TO_SHIP, Order.UNDELIVERED,Order.CANCEL,Order.SHIPPED, Order.READY_FOR_DISPATCH, Order.COMPLETED, Order.DISPATCH]:
            if obj.is_bill_generated:
                update_url = reverse("order:order_update", kwargs={"pk": obj.id, "type": "bill"})
            else:
                update_url = reverse("order:order_update", kwargs={"pk": obj.id, "type": "order"})
        else:
            update_url = None
        logs_url = reverse("order:order_log_ajax", kwargs={"pk": obj.id})
        detail_url = reverse("order:order_detail", kwargs={"pk": obj.id})

        is_dispatch = False
        if obj.status in [Order.NEW, Order.UNDELIVERED] and obj.is_bill_generated:
            is_dispatch = True

        print_table_url = None
        if order_bill:
            print_table_url = order_bill.bill_pdf.url if order_bill.bill_pdf else ""
        
            # print_table_url = reverse("order:order_table_print_ajax")
        # return f'<center><label data-id="{obj.id}" data-url="{logs_url}" title="Delete" data-toggle="modal" data-target="#default" class="danger p-0 mr-2 order-log-history-btn"><i class="ft-clock font-medium-3" style="color: #975AFF;"></i></label><label data-id="{obj.id}" data-url="{print_table_url}" title="Delete" data-toggle="modal" data-target="#default" class="danger p-0 mr-2 order-print-btn"><i class="ft-printer font-medium-3" style="color: #975AFF;"></i></label><a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a></center>'
        t = get_template("order/get_order_action_button.html")
        return t.render(
            {
            'obj':obj, 
            'update_url':update_url,
            'logs_url':logs_url,
            'print_table_url':print_table_url, 
            'detail_url': detail_url,
            'user':self.request.user,
            'is_dispatch': is_dispatch
            }
        )
    def _get_status(self,obj):
        t = get_template("order/get_order_status.html")
        return t.render(
            {"order": obj, "request": self.request}
        )
    
    def get_customer_details(self, obj):
        t = get_template("reports/report_customer_details.html")
        return t.render(
            {"customer_id": obj.customer, "request": self.request}
        )
    
    def get_order_id(self, obj):
        t = get_template("order/get_order_id.html")
        order_bill = OrderBill.objects.filter(order = obj).last()
        return t.render(
            {"order": obj, "order_bill": order_bill, "request": self.request}
        )
        
    # def get_order_created_by_user(self,obj):
    #     user = self.request.user
    #     user_id = OrderLog.objects.filter(action_by=user, order=obj).first()

    #     return str(user_id)
    
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'order_id': self.get_order_id(o),
                'customer': self.get_customer_details(o),
                'created_by': o.created_by.full_name.title(),
                'company': f'{o.company.company_name}',
                'order_date': f'{o.order_date.strftime("%-d %B, %Y")}',
                'grand_total': o.grand_total if o.grand_total else 0,
                'paid_amount': o.get_paid_amount,
                'status':self._get_status(o),
                'actions':self._get_actions_buttons(o),
            }
            for o in qs
        ]
    
    def get(self, request, *args, **kwargs):
            context_data = self.get_context_data(request)
            return JsonResponse(context_data)


class OrderBillListView(CompanyAdminLoginRequiredMixin, ListView):
    template_name = "order/order_list.html"
    model = Order
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_generate"] = True
        context["order_statuses"] = Order.STATUS_CHOICES
        context["companies"] = Company.objects.filter(status=Company.IS_ACTIVE)
        context["customers"] = Customer.objects.filter(status=Customer.ACTIVE)
        if self.request.user.role == User.COMPANY_ADMIN:
            company_admin_company = self.request.user.company_users.first().company
            context["customers"] = Customer.objects.filter(status=Customer.ACTIVE, company = company_admin_company)
        if self.request.user.role == User.SALES_REPRESENTATIVE:
            context["customers"] = Customer.objects.filter(status=Customer.ACTIVE, sales_rep = self.request.user.id)

        return context

class OrderBillListAjax(DataTableMixin,View):
    model = OrderBill

    def get_queryset(self):  
        qs = OrderBill.objects.all()
        
        if self.request.user.role == User.COMPANY_ADMIN:
            company_id = self.request.user.get_company_id
            qs = qs.filter(order__company__id = company_id)

        if self.request.user.role == User.SALES_REPRESENTATIVE:
            company_id = self.request.user.get_company_id
            customers = list(Customer.objects.filter(sales_rep__id = self.request.user.id).values_list("id", flat=True))
            qs = qs.filter(order__company__id=company_id, customer__id__in = customers)
        
        order_list_company=self.request.GET.get("order_list_company")
        if order_list_company:
            qs = qs.filter(order__company = order_list_company)

        order_bill_status = self.request.GET.get("order_bill_status")
        if order_bill_status:
            qs = qs.filter(status = order_bill_status)

        order_customer = self.request.GET.get("order_customer")
        if order_customer:
            qs = qs.filter(customer__id = order_customer)
    
        return qs.order_by("-id")
    
    def filter_queryset(self, qs):
        if self.search:
            return qs.filter(
                Q(status__icontains=self.search) |
                Q(order__order_id__icontains=self.search) |
                Q(customer__customer_name__icontains=self.search)
            )
        return qs
    
    def _get_actions_buttons(self,obj):
        bill_url = reverse("order:generate_bill", kwargs={"pk": obj.order.id})
        t = get_template("order/bills/get_order_bill_action_button.html")
        
        return t.render(
            {
            'obj': obj,
            'bill_url': bill_url,
            'user': self.request.user
            }
        )

    def _get_status(self,obj):
        t = get_template("order/bills/get_order_bill_status.html")
        return t.render(
            {"order_bill": obj, "request": self.request}
        )
    
    def get_customer_details(self, obj):
        t = get_template("reports/report_customer_details.html")
        return t.render(
            {"customer_id": obj.customer}
        )
    
    # def get_order_created_by_user(self,obj):
    #     user = self.request.user
    #     user_id = OrderLog.objects.filter(action_by=user, order=obj).first()

    #     return str(user_id)
    
    def prepare_results(self, qs):
        return [
            {
                'id': o.order.order_id,
                'customer': self.get_customer_details(o),
                'company': f'{o.order.company.company_name}',
                'created_at': f'{o.created_at.strftime("%-d %B, %Y")}',
                'due_date': f'{o.due_date.strftime("%-d %B, %Y")}' if o.due_date else "-",
                'bill_amount': o.bill_amount,
                'paid_amount': o.paid_amount,
                'due_amount': o.due_amount,
                'status':self._get_status(o),
                'actions':self._get_actions_buttons(o),
            }
            for o in qs
        ]
    
    def get(self, request, *args, **kwargs):
            context_data = self.get_context_data(request)
            return JsonResponse(context_data)


class OrderUpdateView(SalesLoginRequiredMixin,UpdateView):
    model = Order
    form_class = OrderFrom
    success_url = reverse_lazy("order:order_list")

    def has_permission(self):
        if "bill/" in self.request.path and self.request.user.role in [User.SALES_REPRESENTATIVE]:
            return self.request.user.role in [User.COMPANY_ADMIN, User.SUPER_ADMIN]
        
        return super().has_permission()

    def get_template_names(self):
        if "bill/" in self.request.path:
            template_name = "order/bills/create_bill_form.html"
        else:
            template_name = "order/order_form.html"
        return template_name

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form2"] =  OrderedProductForm
        order_bill = OrderBill.objects.filter(order = self.object).last()
        if order_bill:
            context["order_bill"] = order_bill
        
        customer = self.object.customer
        customer_shipping_address = CustomerShippingAddress.objects.filter(customer=customer).first()
        shipping_address = customer_shipping_address.shipping_address_line_1
        shipping_address += ", "+customer_shipping_address.shipping_address_line_2
        shipping_address += ", "+customer_shipping_address.shipping_city
        shipping_address += ", "+customer_shipping_address.shipping_state
        shipping_address += "-"+str(customer_shipping_address.shipping_zip_code)
        shipping_address += ", "+customer_shipping_address.shipping_country
        shipping_address += "\nZone: "+customer.zone.zone_code
        shipping_address += "\nArea: "+customer.area
        context["shipping_address"] = shipping_address

        return context

    def form_valid(self, form):
        before_save = Order.objects.get(id = self.object.id)
        instance = form.save()

        if self.request.user.role == User.COMPANY_ADMIN:
            instance.company = self.request.user.company_users.first().company
            instance.save()

        submit_type = self.request.POST.get("submit")

        if submit_type == "draft-to-new":
            instance.status = Order.NEW
            instance.save()
            
            # due_amount= instance.grand_total - instance.paid_amount
            # new_customer_bill = CustomerBill(order=instance, customer=instance.customer, bill_amount=instance.grand_total, paid_amount=instance.paid_amount, due_amount=due_amount)  
            # new_customer_bill.save()
        
        product_ids=self.request.POST.get('product_id_list').split(',')
        order_utils.update_product_list_in_order(self,instance,product_ids, before_save, submit_type)
        
        if submit_type == "generate":
            shipping_charges = form.data.get('shipping_charges', 0)
            packing_charges = form.data.get('packing_charges', 0)

            shipping_charges = float(shipping_charges) if shipping_charges else 0
            packing_charges = float(packing_charges) if packing_charges else 0

            instance.shipping_charges = shipping_charges
            instance.packing_charges = packing_charges
            instance.grand_total = instance.item_total + shipping_charges + packing_charges
            instance.is_bill_generated = True
            instance.save()
            
            order_bill, created = OrderBill.objects.get_or_create(order = instance, customer = instance.customer)
            if created:
                order_bill.bill_id = "{}{:05d}".format("BILL#", order_bill.id)
                order_bill.slip_no = form.data["slip_no"]
                instance.payment_method = form.data.get("payment_choice")

                if instance.payment_method == Order.CASH:
                    instance.paid_amount = instance.grand_total
                    new_payment = Payment(customer_name=instance.customer, receive_amount=instance.paid_amount)
                    new_payment.save()
                    CustomerPaymentBill.objects.create(customer_payment=new_payment, customer_bill=order_bill, amount=instance.paid_amount)
                instance.save()
                log_msg = f"New sales bill has been generated with Order ID:{instance.order_id}"
            else:
                log_msg = f"Sales bill has been updated with Order ID:{instance.order_id}"
                
            order_bill.bill_amount = instance.grand_total

            bill_date = form.data.get("bill_date")
            if bill_date:
                order_bill.bill_date = datetime.datetime.strptime(bill_date, "%Y-%m-%d")

            due_date = form.data.get("due_date")
            if due_date:
                order_bill.due_date = datetime.datetime.strptime(due_date, "%Y-%m-%d")
            
            if form.data["local_bill"] == "true":
                order_bill.is_local_bill = True
                order_bill.gr_date = None
                order_bill.gr_number = ""
                order_bill.case_number = None
                order_bill.transporter = ""
            else:
                order_bill.is_local_bill = False
                gr_date = form.data.get("gr_date")
                if gr_date:
                    order_bill.gr_date = datetime.datetime.strptime(gr_date, "%Y-%m-%d")
                order_bill.gr_number = form.data["gr_number"]
                order_bill.case_number = form.data["case_number"]
                order_bill.transporter = form.data["transporter"]
            
            order_bill.written_by = form.data["written_by"]
            order_bill.checked_by = form.data["checked_by"]
            order_bill.packed_by = form.data["packed_by"]
            order_bill.due_amount = instance.grand_total - instance.paid_amount
            order_bill.paid_amount = instance.paid_amount
            order_bill.save()

            if order_bill.due_amount == 0:
                order_bill.status = OrderBill.COMPLETE
            order_bill.save()

            context = {}
            context["order_products"] = OrderedProduct.objects.filter(order=instance)
            context["order"] = instance
            context["order_bill"] = order_bill
            context["amount_in_words"] = num2words(instance.grand_total, lang='en_IN').title()
            local_bill = form.data["local_bill"]
            context["local_bill"] = local_bill

            if order_bill.due_date and order_bill.bill_date and order_bill.due_date > order_bill.bill_date:
                due_days = (order_bill.due_date - order_bill.bill_date).days
                context["due_days"] = "Within " + num2words(due_days, lang='en_IN').title() + " Days"

            pdf = utils.render_to_pdf('order/bills/print_order_bill.html', context)
            pdf_name = "order-%s.pdf" % str(instance.order_id)

            if pdf:
                if order_bill.bill_pdf:
                    order_bill.bill_pdf.delete()
                order_bill.bill_pdf.save(pdf_name, ContentFile(pdf))
                order_bill.save()

            CustomerLog.objects.create(customer=instance.customer, action_by=self.request.user, order=instance, remark=log_msg)
            OrderLog.objects.create(order=instance, remark=log_msg, action_by=self.request.user)

            messages.add_message(self.request, messages.SUCCESS, "Order bill generated.")
            return JsonResponse({"bill_pdf_url": order_bill.bill_pdf.url, "redirect_url": reverse("order:order_bill_list")})

        if instance.status != Order.DRAFT:
            messages.add_message(self.request, messages.SUCCESS, "Order Updated")
            if "status" in form.changed_data:
                log_msg = f"Order status changed from {before_save.status} to {instance.status} for Order ID:{instance.id}"
                CustomerLog.objects.create(customer=instance.customer, action_by=self.request.user, order=instance, remark=log_msg)

                order_log_msg = f"Order status changed from {before_save.status} to {instance.status}"
                OrderLog.objects.create(order=instance, remark=order_log_msg, action_by=self.request.user)
            else:
                log_msg = f"Order has been updated Order ID:{instance.id}"
                CustomerLog.objects.create(customer=instance.customer, action_by=self.request.user, order=instance, remark=log_msg)

                order_log_msg = f"Order has been updated"
                OrderLog.objects.create(order=instance, remark=order_log_msg, action_by=self.request.user)
        else:
            messages.add_message(self.request, messages.SUCCESS, "Draft Order Updated")
            
        return JsonResponse({"redirect_url": reverse("order:order_list")})
    
    # def get_queryset(self):
    #     qs = super().get_queryset()
    #     if self.request.user.role == User.COMPANY_ADMIN:
    #         qs = qs.filter(company__id=self.request.user.get_company_id)
    #     if self.request.user.role == User.SALES_REPRESENTATIVE:
    #         qs = qs.filter(company__id=self.request.user.get_company_id, created_by = self.request.user)
    #     return qs
    

class AjaxGetUpdateOrderProductDetails(View):
    template1_name = "order/add_product_details_in_order_list.html"
    template2_name = "order/bills/add_product_details_in_bill_list.html"

    def post(self, request, *args, **kwargs):
        context={}
        data={}
        order_id = request.POST['order_id']
        is_bill_create = request.POST.get("is_bill_create")

        order = Order.objects.get(id = order_id)
        order_products = OrderedProduct.objects.filter(order__id=order_id)

        if order_products:
            order__product_ids = list(order_products.values_list('product',flat=True))
            # order_product_list = []
            # for order_product in order_products:
            #     data = {}
            #     data["order_product"] = order_product
            #     data["available_stock"] = ""

            context['order_update_id'] = order_id
            context['order'] = order
            context['order_products'] = order_products
            data['order__product_ids'] = order__product_ids

            if is_bill_create == "false":
                data['existing_product_list']=render_to_string(self.template1_name, context, request=request)
            else:
                data['existing_product_list']=render_to_string(self.template2_name, context, request=request)

        return JsonResponse(data)
    
class GetProductForOrderByBarcodeAjax(View):
    def post(self, request):
        barcode_number = request.POST.get('barcode_number')
        company_id = request.POST.get('company_id')
        
        if company_id:
            product = Product.objects.filter(code=barcode_number, company__id = company_id).last()
        else:
            product = Product.objects.filter(code=barcode_number).last()

        # if not product_code:
        #     barcode = Barcode.objects.filter(barcode_number=barcode_number).last()
        #     product = barcode.product if barcode else None
        # else:
        #     product = product_code

        data = {}
        if product:
            data["product_id"] = product.id
            if product.vehicle:
                data["product_vehicle"] = product.vehicle.name

        return JsonResponse(data)
    

class GetWarehouseProductsAjax(View):
    
    template_name = "order/get_customers_products.html"

    def post(self,request,*args, **kwargs):

        context = {}
        data = {}

        warehouse_id = request.POST['warehouse_id']
        warehouse_products = WarehouseProductStock.objects.filter(warehouse = warehouse_id)
        context['warehouse_products'] = warehouse_products
        data['warehouse_products']=render_to_string(self.template_name,context,request=request)
        return JsonResponse(data)


'''views for car model'''
class CarCreateView(SalesLoginRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = "order/car_form.html"
    form_class = CarForm
    success_message = "Car Details Created Successfully."
    success_url = reverse_lazy("order:car_list")

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

class CarListView(SalesLoginRequiredMixin, SuccessMessageMixin, ListView):
    template_name = "order/car_list.html"
    model = Car

    def get_context_data(self, **kwargs):
        contaxt = super().get_context_data(**kwargs)
        contaxt["status_choices"] = Car.STATUS_CHOICES
        return contaxt

class CarDataTableAjaxPagination(LoginRequiredMixin, DataTableMixin, View):
    model = Car

    def get_queryset(self):
        qs = Car.objects.all()
        if self.request.user.role == User.COMPANY_ADMIN or self.request.user.role == User.SALES_REPRESENTATIVE:
            company = self.request.user.company_users.first().company
            qs = qs.filter(company=company)
        status_choice = self.request.GET.get("status")
        if status_choice:
            status_car = Car.objects.filter(status=status_choice)
            qs = qs.filter(id__in=status_car)
            return qs
        return qs.order_by("-id")
    
    def _get_actions(self, obj):
        update_url = reverse("order:car_update", kwargs={"pk":obj.id})
        delete_url = reverse("order:car_delete")
        return f'<center><a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a> <label data-title="{obj.car_nickname}" data-url="{delete_url}" data-id="{obj.id}" title="Delete" id="delete_btn" class="danger p-0 ajax-delete-btn"><i class="ft-trash font-medium-3 "></i></label></center>'
    
    def filter_queryset(self, qs):
        # sourcery skip: assign-if-exp, reintroduce-else
        if self.search:
            return qs.filter(
                Q(car_nickname__icontains=self.search)
            )
        return qs
    
    def _get_status(self,obj):
        t = get_template("order/get_order_status.html")
        return t.render(
            {"order": obj, "request": self.request}
        )
    
    def prepare_results(self, qs):
        return[
            {
                'id': o.id,
                'company':o.company.company_name,
                'car_nickname': o.car_nickname,
                'year': o.year,
                'status': self._get_status(o),
                'make': o.make,
                'model': o.model,
                'vin_number': o.vin_number,
                'licence_plate': o.licence_plate,
                'inspect_exp_date': o.inspect_exp_date,
                'start_mileage': o.start_mileage,
                'actions': self._get_actions(o),
            }
            for o in qs
        ]
    
    def get(self, request, *args, **kwargs):
        contaxt_data = self.get_context_data(request)
        return JsonResponse(contaxt_data)
    
class CarUpdateView(SalesLoginRequiredMixin, SuccessMessageMixin, UpdateView):
    template_name = "order/car_form.html"
    model = Car
    form_class = CarForm
    success_message = "Car Details Updated Successfully."
    success_url = reverse_lazy("order:car_list")

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == User.COMPANY_ADMIN:
            qs = qs.filter(company__id=self.request.user.get_company_id)
        return qs

class CarDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request):
        car_id = self.request.POST.get("id")
        Car.objects.filter(id=car_id).delete()
        return JsonResponse({"message":"Car Details Deleted Successfully."})


class OrderLogAjaxView(LoginRequiredMixin, ListView):
    template_name = "order/order_log_list.html"
    model = OrderLog

    def get_queryset(self):
        qs = OrderLog.objects.all()
        pk = self.kwargs.get("pk")
        if pk:
            qs = qs.filter(order__id=pk)
        return super().get_queryset()
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order_id"] = self.kwargs.get("pk")
        return context


class OrderLogDatatableAjaxView(DataTableMixin,View):
    model= OrderLog
    
    def get_queryset(self):
        """Get queryset."""
        qs = OrderLog.objects.all()
        order_id = self.request.GET.get("order_id")
        if order_id:
            qs = qs.filter(order__id=order_id)

        return qs.order_by("-id")

    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'action_by': o.action_by.full_name,
                'remark': o.remark,
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class OrderTablePrintAjaxView(SalesLoginRequiredMixin, ListView):
    template_name = "order/order_table_print.html"
    model = Order

    def get_queryset(self):
        qs = Order.objects.all()
        pk = self.request.GET.get("order_id")
        if pk:
            qs = qs.filter(id=pk)
        return qs.order_by("-id")
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order_products"] = OrderedProduct.objects.filter(order__id=self.request.GET.get("order_id"))
        context["order"] = Order.objects.get(id=self.request.GET.get("order_id"))
        context['ordernumber'] = Order.objects.filter(id__lt=self.request.GET.get("order_id"),created_at__date = datetime.date.today()).count() + 1
        return context


class GenerateBillView(SalesLoginRequiredMixin, DetailView):
    template_name = "order/bills/print_order_bill.html"
    model = Order

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        order = Order.objects.filter(id = self.object.id).last()
        order_bill = OrderBill.objects.filter(order = order).last()
        order_products = OrderedProduct.objects.filter(order = self.object)
        amount_in_words = num2words(order.grand_total, lang='en_IN').title()
        
        context = {"order": self.object, "order_bill": order_bill, "order_products": order_products, "amount_in_words": amount_in_words}
        return context


# For Create Driver Route 
class AssignDriverRoutesCreateView(CompanyAdminLoginRequiredMixin, CreateView):
    model = AssignDriverRoutes
    form_class = AssignDriverRoutesForm
    template_name = "order/form_assign_driver_route.html"
    success_url = reverse_lazy("order:assigned_order_driver_list")

    def get_context_data(self, **kwargs): 
        context = super().get_context_data(**kwargs)
        context["company_list"] = Company.objects.filter(status = Company.IS_ACTIVE)
        return context
    
    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs
    
class LoadDriverAjaxView(View):
    def get(self, request):
        company_id = self.request.GET['company_id']
        company_drivers = list(CompanyUsers.objects.filter(company__id = company_id).values_list("user__id", flat=True))
        data = {
        "driver" : list(Driver.objects.filter(id__in=company_drivers).values('id', 'full_name')),
        "warehouse": list(Warehouse.objects.filter(company__id=company_id).values("id","name"))
        }
        return JsonResponse(data, safe=False)

# For assign Routes to the orders while it's status in a packed
class AssignDriverOrderView(LoginRequiredMixin, ListView):
    template_name = "order/order_assign_list_page.html"
    model = Order

    def get_queryset(self):
        qs = super().get_queryset()
        order_id = self.request.GET.get('orders_id').split(',')
        qs = qs.filter(id__in=order_id)
        return qs.order_by("-id")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.request.GET.get('orders_id')
        drivers = Driver.objects.all()
        if self.request.user.role in[User.COMPANY_ADMIN,User.SALES_REPRESENTATIVE] :
            company_drivers = list(CompanyUsers.objects.filter(company__id=self.request.user.get_company_id).values_list("user__id", flat=True))
            warehouse_list = Warehouse.objects.filter(company__id = self.request.user.get_company_id)
        else:
            order_company = Order.objects.get(id=order_id)
            company_drivers = list(CompanyUsers.objects.filter(company__id=order_company.company.id).values_list("user__id", flat=True))
            warehouse_list = Warehouse.objects.filter(company__id = order_company.company.id)
        drivers = drivers.filter(id__in=company_drivers)

        context["driver_list"] = drivers
        context["order_id"] = order_id
        context["warehouse_list"] = warehouse_list
        return context
    
# Ajax form submitting of while order assign to the driver's route
class PlanRouteAjaxView(View):
    # template_name = "order/render_map.html"
    def post(self,request):
        orders_id = self.request.POST.get('orders_id').split(",")
        driver_id = self.request.POST.get('driver_id')
        assign_routes_id = self.request.POST.get('assign_routes')
        create_route_name = self.request.POST.get('create_route')
        start_location_id = self.request.POST.get('start_location')
        bill_date = self.request.POST.get('bill_date')
        date = parse_date(bill_date)
        
        # print("➡ orders_id :", len(orders_id))
        # print("➡ orders_id :", orders_id, type(orders_id))
        # print("➡ driver_id :", driver_id)
        # print("➡ assign_routes_id :", assign_routes_id)
        # print("➡ create_route :", create_route_name)
        # print("➡ start_location_id :", start_location_id)
        # print("➡ bill_date :", (bill_date))
        # print("➡ bill_date :", type(bill_date))
        # print("➡ date :", date)
        # print("➡ date :", type(date))

       

        if assign_routes_id:
            assign_driver_route=AssignDriverRoutes.objects.get(id=assign_routes_id)
        else:
            
            assign_driver_route=AssignDriverRoutes.objects.create(name=create_route_name, driver=Driver.objects.get(id=driver_id),date=date,start_location = Warehouse.objects.get(id=start_location_id))
            assign_driver_route.save()
            
        for id in orders_id:
            assign_order_route_obj=AssignOrderRoutes.objects.create(order=Order.objects.get(id=id),driver_route=assign_driver_route,stop = len(orders_id))

            assign_order_route_obj.driver_route.synchronized_route = False
            assign_order_route_obj.save()
            assign_order_route_obj.driver_route.save()

            order = Order.objects.filter(id=id).last()
            customer_address = CustomerShippingAddress.objects.filter(customer = order.customer, is_default=True).last()
            if customer_address:
                order.shipping_address_line_1 = customer_address.shipping_address_line_1
                order.shipping_address_line_2 = customer_address.shipping_address_line_2
                order.shipping_city = customer_address.shipping_city
                order.shipping_state = customer_address.shipping_state
                order.shipping_country = customer_address.shipping_country
                order.shipping_zip_code = customer_address.shipping_zip_code
                order.save()
            # print("➡ shipping_address :", shipping_address)

        order_obj = Order.objects.filter(id__in=orders_id)
        # print("➡ order_obj :", order_obj)
        for order in order_obj:
            log_msg = f"Order status changed from {order.status} to {Order.DISPATCH} for Order ID:{order.id}"
            CustomerLog.objects.create(customer=order.customer, action_by=self.request.user, order=order, remark=log_msg)

            order_log_msg = f"Order status changed from {order.status} to {Order.DISPATCH}"
            OrderLog.objects.create(order=order, remark=order_log_msg, action_by=self.request.user)
        order_obj.update(status=Order.DISPATCH)

        # url = reverse("order:render_optimize_route_map", kwargs={"assigned_route":assign_driver_route.id})
        url = reverse_lazy("order:assigned_order_driver_list")

        # api call 
        # update_stop = AssignOrderRoutes.objects.filter(driver_route__id=assign_driver_route.id)
        # print("➡ update_stop :", update_stop)
        # print(".....",start_location_id)
        # start_location = Warehouse.objects.filter(id= start_location_id).values_list("name","address_line_1","address_line_2","city","state","country","zip_code")
        # print("➡ start_location :", start_location)
        # call api for updating stops and use update_stop varible for update

        return JsonResponse({"url": url,})
    
# Rendring Optimized Routes of givin routes
class RenderOptimizedMap(LoginRequiredMixin, TemplateView):
    template_name = "order/render_map.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Initialize dictionaries
        address_to_orders = {}
        client_lat_long_dict = {}
        customer_order_map = {}
        order_stop_map = []

        # Fetch the list of orders for the assigned route
        orders_id_list = AssignOrderRoutes.objects.filter(driver_route__id=self.kwargs["assigned_route"]).values_list("order__id", "stop")
        print('orders_id_list: ', orders_id_list)
        
        # Convert QuerySet to list of tuples
        orders_id_list = list(orders_id_list)

        # Sort by stop value to ensure correct order
        orders_id_list.sort(key=lambda x: x[1])  # Sort by stop value

        # Extract unique order IDs in sorted order
        unique_order_ids = [order_id for order_id, _ in orders_id_list]
        print('unique_order_ids: ', unique_order_ids)
        
        # Fetch orders with unique IDs
        orders = Order.objects.filter(id__in=unique_order_ids)

        # Create a dictionary to quickly access orders by their ID
        order_dict = {order.id: order for order in orders}

        # Reorder the orders based on unique_order_ids
        ordered_orders = [order_dict[order_id] for order_id in unique_order_ids if order_id in order_dict]

        # Get assigned route and start point
        assigned_route = AssignDriverRoutes.objects.get(id=self.kwargs["assigned_route"])
        warehouse = assigned_route.start_location
        start_point = f"{warehouse.latitude},{warehouse.longitude}"

        # Process each order and its shipping addresses
        for order in ordered_orders:
            customer_shipping_addresses = CustomerShippingAddress.objects.filter(customer=order.customer)

            for address in customer_shipping_addresses:
                lat_lng = f"{address.shipping_latitude},{address.shipping_longitude}"
                address_key = (
                    address.shipping_address_line_1,
                    address.shipping_address_line_2,
                    address.shipping_suite_apartment,
                    address.shipping_city,
                    address.shipping_state,
                    address.shipping_country,
                    address.shipping_zip_code,
                )

                # Update address_to_orders to group orders by address
                if address_key not in address_to_orders:
                    address_to_orders[address_key] = []

                address_to_orders[address_key].append(order.id)

                # Update client_lat_long_dict to handle the case where multiple orders have the same location
                if lat_lng not in client_lat_long_dict:
                    client_lat_long_dict[order.id] = lat_lng

                # Add order info with stop value
                stop_value = next((stop for oid, stop in orders_id_list if oid == order.id), None)
                if stop_value:
                    order_stop_map.append((lat_lng, order.order_id, stop_value))

                # Update customer_order_map to handle multiple orders with the same location
                if lat_lng in customer_order_map:
                    customer_order_map[lat_lng]['order_ids'].append(order.order_id)
                else:
                    customer_order_map[lat_lng] = {
                        'customer_pk': order.customer.id,
                        'order_ids': [order.order_id]
                    }

        # Sort order_stop_map by stop values to match the required sequence
        order_stop_map.sort(key=lambda x: x[2])  # Sort by stop value
        
        # Prepare data for the map
        context["start_point"] = start_point
        context["order_locations"] = [item[0] for item in order_stop_map]
        context["order_ids"] = [item[1] for item in order_stop_map]
        
        context["address_to_orders"] = address_to_orders
        context["client_lat_long_dict"] = client_lat_long_dict
        context["customer_order_map"] = customer_order_map

        print('start_point: ', start_point)
        print('list(client_lat_long_dict.values()): ', list(client_lat_long_dict.values()))
        print('address_to_orders: ', address_to_orders)
        print('client_lat_long_dict: ', client_lat_long_dict)
        print('customer_order_map: ', customer_order_map)

        return context
    
# Ajax call for While selcting driver for orders in assign driver respected drivers route will be appear in drop down to select it's existing routes
class DriverAssignRoutesAjax(View):
    def get(self,request):
        today = datetime.date.today()
        data = {
            'assign_routes':list(AssignDriverRoutes.objects.filter(driver__id = self.request.GET.get('driver_id'),date__range=[today,"2099-12-31"],status=AssignDriverRoutes.PENDING).values('id','name','date')),
        }
        return JsonResponse(data , safe=False)
    
# List View of Assign Routes of the driver
class AssignedDriverOrderList(CompanyAdminLoginRequiredMixin, ListView):
    model = AssignDriverRoutes
    template_name = 'order/assigned__order_driver_list.html'
 
class AssignedDriverOrderDataTableAjaxPagination(DataTableMixin,View):
    model = AssignDriverRoutes

    def get_queryset(self):
        qs = AssignDriverRoutes.objects.all()
        if self.request.user.role in [User.COMPANY_ADMIN, User.SALES_REPRESENTATIVE] :
            company_drivers = list(CompanyUsers.objects.filter(company__id=self.request.user.get_company_id).values_list("user__id", flat=True))
            qs = qs.filter(driver__id__in=company_drivers)
        
        return qs
    
    def _get_actions(self, obj):
        """Get action buttons w/links."""
        update_url = reverse("order:detail_assigned_order", kwargs={"assigned_route": obj.id})
        location_url = reverse("order:detail_assigned_order_location", kwargs={"assigned_route": obj.id})
        return f'<center><a href="{update_url}" title="Edit"><i class="ft-eye font-medium-3 mr-2"></i></a><a href="{location_url}" title="Edit"><i class="icon-pointer font-medium-3 mr-2"></i></a></center>'
    
    # def get_no_of_stop(self,obj):
    #     xyz =AssignOrderRoutes.objects.filter(driver_route__id = obj.id).values("stop")
    #     print("➡ xyz :", xyz)

    def _get_status(self, obj):
        t = get_template("order/get_routes_status.html")
        return t.render(
            {"obj": obj, "request": self.request}
        )
    
    
        
    
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'name': o.driver.full_name,
                'route_name': o.name,
                'order_count': o.get_order_count,
                'status': self._get_status(o),
                'date': f'{o.date.strftime("%-d %B, %Y")}',
                'action':self._get_actions(o),
                # 'action':self.get_no_of_stop(o),
            }
            for o in qs
        ]
    
    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)

# Showing assigned order in detail view of assign routes      
class DetailViewAssignDriverOrderView(SalesLoginRequiredMixin, ListView):
    model = AssignOrderRoutes
    template_name = 'order/assign_order_routes_details.html'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(driver_route__id=self.kwargs["assigned_route"])
        assigned_route_obj = AssignDriverRoutes.objects.get(id=self.kwargs["assigned_route"])
        
        if assigned_route_obj.synchronized_route:
            queryset = queryset.order_by('stop')  # Order by stop in descending order
        
        order = self.request.GET.get("order")
        if order:
            queryset = queryset.filter(order__id=order)
        
        # Ensure that if not synchronized, it is ordered by ID
        if not assigned_route_obj.synchronized_route:
            queryset = queryset.order_by('-id')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assigned_route"] = self.kwargs["assigned_route"]
        context["assigned_route_obj"] = AssignDriverRoutes.objects.get(id=self.kwargs["assigned_route"])
        return context


# In Model Listview of Orders
class DetailViewAssignDriverOrderForCompleteView(LoginRequiredMixin,ListView):
    model = AssignOrderRoutes
    template_name = 'order/assign_order_complete.html'
    
    def get_queryset(self):
        queryset = super(DetailViewAssignDriverOrderForCompleteView, self).get_queryset()
        queryset = queryset.filter(driver_route__id=self.kwargs["assigned_route"])
        order = self.request.GET.get("order")
        if order:
            queryset = queryset.filter(order__id = order)
        return queryset.order_by("-id")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assigned_route"] = self.kwargs["assigned_route"]
        context["status"] = AssignDriverRoutes.objects.get(id=self.kwargs["assigned_route"])
        return context
    
class DetailViewAssignDriverOrderForCancelView(View):
    def get(self,request,*args, **kwargs):
        assign_route_name = AssignDriverRoutes.objects.filter(id=self.kwargs["assigned_route"])
        assign_route_name.update(status = AssignDriverRoutes.CANCEL)
        assign_route_orders = AssignOrderRoutes.objects.filter(driver_route__id=self.kwargs["assigned_route"]).values_list("order__id", flat=True)
        order_list = Order.objects.filter(id__in = assign_route_orders)
        for order in order_list:
            order_log_msg = f"Order status changed from {order.status} to {Order.PACKED} due to Route Cancelled"
            OrderLog.objects.create(order=order, remark=order_log_msg, action_by=self.request.user)
            log_msg = f"Order status changed from {order.status} to {Order.PACKED} for Order ID:{order.id} due to Route Cancelled"
            CustomerLog.objects.create(customer=order.customer, action_by=self.request.user, order=order, remark=log_msg)
        order_list.update(status = Order.PACKED)
        url = reverse_lazy("order:assigned_order_driver_list")
        return JsonResponse({"url": url,})
        


#Ajax Call While submitting The status of the order is deliverd or undelivered  
class DriverAssignRoutesOrderStatusAjax(View):
    def get(self,request):
        order_id_completed = self.request.GET.get("order_id_completed").split(',')
        order_id_uncompleted = self.request.GET.get("order_id_uncompleted").split(',')
        assign_route_id = self.request.GET.get("assign_route_id")

        order_id_with_remark = self.request.GET.get("order_id_with_remark")
        for i in json.loads(order_id_with_remark):
            asssign_route_order_remark = AssignOrderRoutes.objects.filter(order__id = i['order_id'])
            asssign_route_order_remark.update(remark = i['remark_text'])

        order_id_completed = [eval(i) for i in order_id_completed] if order_id_completed[0]!='' else [0]
        order_id_uncompleted = [eval(i) for i in order_id_uncompleted] if order_id_uncompleted[0]!= '' else [0]

        order_status_complete =  Order.objects.filter(id__in=order_id_completed)
        for order in order_status_complete:
            order_log_msg = f"Order status changed from {order.status} to {Order.COMPLETED}"
            OrderLog.objects.create(order=order, remark=order_log_msg, action_by=self.request.user)
            log_msg = f"Order status changed from {order.status} to {Order.COMPLETED} for Order ID:{order.id}"
            CustomerLog.objects.create(customer=order.customer, action_by=self.request.user, order=order, remark=log_msg)

            order_products = OrderedProduct.objects.filter(order = order)
            refrance = []
            for product in order_products:
                order_utils.manage_stock(product=product.product, product_id=product.product.id, refrance=refrance, product_total_pieces=product.get_total_quantity)
            order.product_reference=refrance
            order.save()
            
        order_status_complete.update(status= Order.COMPLETED)
        
        order_status_uncomplete =  Order.objects.filter(id__in=order_id_uncompleted)
        for order in order_status_uncomplete:
            order_log_msg = f"Order status changed from {order.status} to {Order.UNDELIVERED}"
            OrderLog.objects.create(order=order, remark=order_log_msg, action_by=self.request.user)
            log_msg = f"Order status changed from {order.status} to {Order.UNDELIVERED} for Order ID:{order.id}"
            CustomerLog.objects.create(customer=order.customer, action_by=self.request.user, order=order, remark=log_msg)
        order_status_uncomplete.update(status= Order.UNDELIVERED)

        assign_route=AssignDriverRoutes.objects.filter(id = assign_route_id)
        assign_route.update(status=AssignDriverRoutes.COMPLETED)

        messages.add_message(self.request, messages.SUCCESS, "Route Status Updated Successfully.")
        url = reverse_lazy("order:assigned_order_driver_list")
        
        return JsonResponse({"url": url,})
        
    

    
# class DetailViewAssignDriverOrderLocationView(LoginRequiredMixin,ListView):
#     model = AssignOrderRoutes
#     template_name = 'order/assign_order_routes_details.html'
    
#     def get_queryset(self):
#         queryset = super(DetailViewAssignDriverOrderLocationView, self).get_queryset()
#         queryset = queryset.filter(driver_route__id=self.kwargs["assigned_route"])
#         print("➡ queryset :", queryset)
#         return queryset
    
class OrderDetailView(SalesLoginRequiredMixin, DetailView):
    template_name='order/order_details.html'
    model = Order

    def has_permission(self):
        order_bill = OrderBill.objects.filter(order__id = self.kwargs["pk"]).last()

        if order_bill and self.request.user.role in [User.SALES_REPRESENTATIVE]:
            return self.request.user.role in [User.COMPANY_ADMIN, User.SUPER_ADMIN]

        return super().has_permission()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        order_bill = OrderBill.objects.filter(order__id = self.kwargs["pk"]).last()
        if order_bill and self.request.user.role in [User.SALES_REPRESENTATIVE]:
            pass

        context["order_bill"] = order_bill

        order_products = OrderedProduct.objects.filter(order__id=self.kwargs["pk"]).order_by("product")
        context["order_products"] = order_products

        replacement_settlements = Replacement.objects.filter(order__id = self.kwargs["pk"], return_type = Replacement.SETTLEMENT, settlement_completed = False)
        if replacement_settlements.count() > 0:
            context["is_replacement_settlement_available"] = True
        else:
            context["is_replacement_settlement_available"] = False

        is_order_ready_to_dispatch = True
        for order_product in order_products:
            if order_product.get_ready_for_dispatch_stock != order_product.quantity:
                is_order_ready_to_dispatch = False
                break

        context["is_order_ready_to_dispatch"] = is_order_ready_to_dispatch

        driver_details = AssignOrderRoutes.objects.filter(order__id=self.kwargs["pk"])

        if driver_details.last():
            context["driver_route"] = driver_details.last()
            context["driver"] = driver_details.last().driver_route
        
        context["driver_details"] = driver_details

        if not self.object.is_bill_generated:
            customer_address = CustomerShippingAddress.objects.filter(customer = self.object.customer, is_default = True)
            context["customer_address"] = customer_address.exists()
        else:
            context["customer_address"] = True
        
        is_order_ready = False
        for order_product in order_products:
            if order_product.get_product_total_stock != order_product.quantity:
                is_order_ready = True
                break
        context["is_order_ready"] = is_order_ready
        return context
    
    # def get_queryset(self):
    #     qs = super().get_queryset()
    #     if self.request.user.role == User.COMPANY_ADMIN:
    #         qs = qs.filter(company__id=self.request.user.get_company_id)
    #     if self.request.user.role == User.SALES_REPRESENTATIVE:
    #         qs = qs.filter(company__id=self.request.user.get_company_id, created_by = self.request.user)
    #     return qs


class OrderPackingView(FormView):
    template_name = 'order/order_packing.html'
    form_class = OrderPackingForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order"] = Order.objects.get(id=self.kwargs["pk"])
        context["order_products"] = OrderedProduct.objects.filter(order__id=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        order = Order.objects.get(id=self.kwargs["pk"])
        before_save = order
        before_save_status = order.status
        
        order_products = OrderedProduct.objects.filter(order__id=self.kwargs["pk"])

        packing_status = []
        order_packing = False

        for order_product in order_products:
            order_product.packed_quantity = int(self.request.POST.get(f'product_{order_product.id}__packedquantity'))
            order_product.unpacked_quantity = int(self.request.POST.get(f'product_{order_product.id}__unpackedquantity'))
            order_product.save()

            # if order_product.unpacked_quantity != 0:
            #     pass
            if order_product.unpacked_quantity == order_product.quantity:
                packing_status.append(False)
            elif order_product.unpacked_quantity != order_product.quantity:
                order_packing = True
                packing_status.append(False)
            if order_product.unpacked_quantity == 0:
                packing_status.pop()
                packing_status.append(True)

        
        if order_packing:
            order.status = Order.PACKING
            order.save()
            
            order_log_msg = f"Order packing has been updated"
            OrderLog.objects.create(order=order, remark=order_log_msg, action_by=self.request.user)

        if False not in packing_status:
            order.status = Order.PACKED
            order.save()
            log_msg = f"Order status changed from {before_save_status} to {order.status} for Order ID:{order.id}"
            CustomerLog.objects.create(customer=order.customer, action_by=self.request.user, order=order, remark=log_msg)

            order_log_msg = f"Order status changed from {before_save_status} to {order.status}"
            OrderLog.objects.create(order=order, remark=order_log_msg, action_by=self.request.user)
        
        return HttpResponseRedirect(reverse("order:order_list"))

            
class SetOrderProductPackingDetailAjaxView(View):

    def get(self,request):
        data={}
        order_id = request.GET.get('order_id')
        product_barcode = request.GET.get('barcode')
        order_product_ids = list(OrderedProduct.objects.filter(order__id=order_id).values_list("product__id", flat=True))
        
        if product_barcode:
            barcode = Barcode.objects.filter(barcode_number=product_barcode).first()
            if barcode:
                if barcode.product.id in order_product_ids:
                    product = OrderedProduct.objects.filter(product__id=barcode.product.id,order__id=order_id).first()
                    product_id = product.id
                else:
                    product_id = None
                    data["message"] = "Barcode didn't match.."
            else:
                product_id = None
                data["message"] = "Barcode didn't match.."
        else:
            pass
        
        data["product_id"] = product_id
        return JsonResponse(data)


class SetOrderShippedAjaxView(LoginRequiredMixin, View):

    def get(self,request):
        data={}
        order_id = request.GET.get('order_id')
        order = Order.objects.get(id=order_id)
        before_save_status = order.status
        # order.status = Order.SHIPPED
        order.status = Order.READY_FOR_DISPATCH
        order.save()
        log_msg = f"Order status changed from {before_save_status} to {order.status} for Order ID:{order.id}"
        CustomerLog.objects.create(customer=order.customer, action_by=self.request.user, order=order, remark=log_msg)

        order_log_msg = f"Order status changed from {before_save_status} to {order.status}"
        OrderLog.objects.create(order=order, remark=order_log_msg, action_by=self.request.user)
        data["message"] = "Order has been updated.."
        return JsonResponse(data)
    
class SetOrderUndeliveredAjaxView(LoginRequiredMixin, View):

    def get(self,request):
        data={}
        order_id = request.GET.get('order_id')
        order = Order.objects.get(id=order_id)
        before_save_status = order.status
        order.status = Order.UNDELIVERED
        order.save()
        log_msg = f"Order status changed from {before_save_status} to {order.status} for Order ID:{order.id}"
        CustomerLog.objects.create(customer=order.customer, action_by=self.request.user, order=order, remark=log_msg)

        order_log_msg = f"Order status changed from {before_save_status} to {order.status}"
        OrderLog.objects.create(order=order, remark=order_log_msg, action_by=self.request.user)
        data["message"] = "Order has been updated.."
        return JsonResponse(data)

class SetOrderCompletedAjaxView(SalesLoginRequiredMixin, View):

    def get(self,request):
        data={}
        order_id = request.GET.get('order_id')
        order = Order.objects.get(id=order_id)
        before_save_status = order.status
        order.status = Order.COMPLETED
        order.save()

        order_products = OrderedProduct.objects.filter(order = order)
        refrance = []
        for product in order_products:
            order_utils.manage_stock(product=product.product, product_id=product.product.id, refrance=refrance, product_total_pieces=product.get_total_quantity)
        order.product_reference=refrance
        order.save()

        log_msg = f"Order status changed from {before_save_status} to {order.status} for Order ID:{order.id}"
        CustomerLog.objects.create(customer=order.customer, action_by=self.request.user, order=order, remark=log_msg)

        order_log_msg = f"Order status changed from {before_save_status} to {order.status}"
        OrderLog.objects.create(order=order, remark=order_log_msg, action_by=self.request.user)
        data["message"] = "Order has been updated."
        return JsonResponse(data)

class OrderCancelAjaxView(SalesLoginRequiredMixin, View):
    
    def get(self,request):
        data={}
        order_id = request.GET.get('order_id')
        order = Order.objects.get(id=order_id)
        before_save_status = order.status
        order.status = Order.CANCEL
        order.save()
        # order_utils.add_stock_when_order_cancel(order_id)
        log_msg = f"Order status changed from {before_save_status} to {order.status} for Order ID:{order.id}"
        CustomerLog.objects.create(customer=order.customer, action_by=self.request.user, order=order, remark=log_msg)

        order_log_msg = f"Order status changed from {before_save_status} to {order.status}"
        OrderLog.objects.create(order=order, remark=order_log_msg, action_by=self.request.user)
        data["message"] = "Order has been updated.."
        return JsonResponse(data)


class BrandSearchAjaxView(View):
    def get(self, request):
        company_id = self.request.GET.get("company")
        term = self.request.GET.get("search")
        is_order = self.request.GET.get("is_order", None)

        queryset = Brand.objects.filter(status = Brand.ACTIVE)

        if term:
            queryset = queryset.filter(name__icontains = term)

        if company_id:
            queryset = queryset.filter(company__id = company_id)
        
        data = [{"id": brand.id, "text": brand.name} for brand in queryset]
        if is_order:
            data.insert(0, {"id": 0, "text": "All"})

        return JsonResponse({"items": data})


class OrderSearchAjaxView(View):
    def get(self, request):
        company_id = self.request.GET.get("company")
        customer_id = self.request.GET.get("customer", "0")
        term = self.request.GET.get("search")

        queryset = Order.objects.filter(status = Order.COMPLETED)

        if term:
            queryset = queryset.filter(order_id__icontains = term)

        if company_id:
            queryset = queryset.filter(company__id = company_id)
        
        queryset = queryset.filter(customer__id = customer_id)
        
        data = [{"id": order.id, "text": order.order_id +" - "+str(order.created_at.strftime("%-d %B, %Y"))} for order in queryset]

        return JsonResponse({"items": data})


class ProductSearchAjaxView(View):
    def get(self, request):
        added_product_list = self.request.GET.get("added_product_list")
        company_id = self.request.GET.get("company")
        customer_id = self.request.GET.get("customer", "0")
        order_id = self.request.GET.get("order", "0")
        term = self.request.GET.get("search")

        queryset = OrderedProduct.objects.filter(order__customer__id = customer_id, order__id = order_id)

        if term:
            queryset = queryset.filter(order_id__icontains = term)

        if company_id:
            queryset = queryset.filter(order__company__id = company_id)
        
        if added_product_list:
            added_product_list = json.loads(added_product_list)
            queryset = queryset.exclude(id__in = added_product_list)
        
        data = []
        for product in queryset:
            if product.get_available_replacement_stock > 0:
                data.append({"id": product.id, "text": product.product.name})

        return JsonResponse({"items": data})


class AddReplacementProductAjaxView(View):
    template_name = "customer/replacement/add_product_details_in_replacement_list.html"

    def post(self, request, *args, **kwargs):
        order_product_id = request.POST.get('order_product_id')
        replacement_id = request.POST.get('replacement_id')

        context = {}
        data = {}
        if not replacement_id:
            order_product = OrderedProduct.objects.filter(id = order_product_id).last()
            context["order_product"] = order_product
            data['product_row'] = render_to_string(self.template_name, context, request=request)

        else:
            replace_products = ReplacementProduct.objects.filter(replacement_order__id=replacement_id)

            context['replacement_id'] = replacement_id
            context['replace_products'] = replace_products
            data['product_list']=render_to_string(self.template_name, context, request=request)

            replace_products = list(replace_products.values_list('order_product', flat=True))
            data['replace_products'] = replace_products

        return JsonResponse(data)


class TransferStockView(TemplateView):
    template_name = "order/transfer_stock.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.request.GET.get("product_id")
        order_product_stock = self.request.GET.get("order_product_stock")

        product = Product.objects.filter(id = product_id).last()
        context["product"] = product
        context["order_product_stock"] = order_product_stock
        context["company_list"] = Company.objects.filter(status='active')
        context["warehouse_list_for_cadmin"] = Warehouse.objects.filter(company__id=self.request.user.get_company_id, status=Warehouse.IS_ACTIVE)
        warehouse_stock = WarehouseProductStock.objects.filter(warehouse__name = "WAREHOUSE 2", product__id = product_id)
        
        context["stock"] = 0
        if warehouse_stock:
            total_stock = warehouse_stock.aggregate(total_stock = Sum("stock"))["total_stock"]
            context["stock"] = total_stock
        return context

    def get(self, request):
        html = render_to_string(self.template_name, self.get_context_data(), request)
        return JsonResponse({"html": html})


class StockDetailAjaxView(TemplateView):
    template_name = "order/stock_details.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.request.GET.get("product_id")
        ordered_stock = self.request.GET.get("ordered_stock")

        if ordered_stock:
            ordered_stock = int(ordered_stock)
        else:
            ordered_stock = 0
        context["ordered_stock"] = ordered_stock
        
        product = Product.objects.filter(id = product_id).last()
        context["product"] = product
        context["stock"] = 0
        context["remaining_stock"] = ordered_stock

        warehouse_stock = WarehouseProductStock.objects.filter(warehouse__name = "WAREHOUSE 1", product__id = product_id)
        if warehouse_stock:
            total_stock = warehouse_stock.aggregate(total_stock = Sum("stock"))["total_stock"]
            context["stock"] = min(total_stock, ordered_stock)

            if total_stock >= ordered_stock:
                context["remaining_stock"] = 0
            else:
                context["remaining_stock"] = ordered_stock - total_stock
        return context

    def get(self, request):
        context = self.get_context_data()
        html = render_to_string(self.template_name, context, request)
        return JsonResponse({"html": html})


class UpdateProductAjaxView(TemplateView):
    template_name = "order/update_order_product.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.request.GET.get("product_id")
        customer_id = self.request.GET.get("customer_id")
        price_type = self.request.GET.get('price_type')
        applied_product_price = self.request.GET.get('applied_product_price')
        qty = self.request.GET.get('qty')
        free_quantity = self.request.GET.get('free_quantity')
        special_rate = self.request.GET.get('special_rate')
        special_discount = self.request.GET.get('special_discount')
        primary_discount = self.request.GET.get('primary_discount')
        secondary_discount = self.request.GET.get('secondary_discount')
        is_bill_create = self.request.GET.get("is_bill_create")

        product = Product.objects.filter(id = product_id).last()
        context["product"] = product
        context["unit"] = product.unit if product.unit else ""
        context["vehicle"] = product.vehicle.name if product.vehicle else ""
        context["is_bill_create"] = True if is_bill_create == "true" else False

        customer = Customer.objects.filter(id = customer_id).last()
        context["customer_type"] = customer.customer_type

        context["price_type"] = price_type
        context["applied_product_price"] = applied_product_price
        context["qty"] = qty
        context["free_quantity"] = free_quantity
        context["special_rate"] = special_rate
        context["special_discount"] = special_discount
        context["primary_discount"] = primary_discount
        context["secondary_discount"] = secondary_discount

        context["available_stock"] = 0
        warehouse_stock = WarehouseProductStock.objects.filter(product = product)
        if warehouse_stock:
            total_stock = warehouse_stock.aggregate(total_stock = Sum("stock"))["total_stock"]
            context["available_stock"] = total_stock

        context["previous_price"] = 0
        order_product = OrderedProduct.objects.filter(order__customer__id = customer_id, product = product, order__status = Order.COMPLETED).order_by("created_at").last()
        if order_product:
            context["previous_price"] = order_product.unit_price

        return context

    def get(self, request):
        html = render_to_string(self.template_name, self.get_context_data(), request)
        return JsonResponse({"html": html})


class ReplacementProductAjaxView(LoginRequiredMixin, DataTableMixin, View):
    model = ReplacementProduct

    def get_queryset(self):
        qs = ReplacementProduct.objects.filter(replacement_order__return_type = Replacement.SETTLEMENT, replacement_order__settlement_pending = True)
        order_id = self.request.GET.get("order_id")

        if order_id:
            qs = qs.filter(replacement_order__order__id = order_id)

        if not self.request.user.is_superuser:
            qs = qs.filter(replacement_order__customer__company__id = self.request.user.get_company_id)

        return qs

    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'replacement_order__replace_id': o.replacement_order.replace_id if o.replacement_order.replace_id else "-",
                'order_product__product': o.order_product.product.name,
                'order_product__unit_price': o.order_product.unit_price,
                'replace_quantity': o.replace_quantity,
                'total_amount': float(o.get_replace_item_total),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class PrintDispatchRoutesView(View):
    def get(self, request, pk):
        assigned_routes = AssignOrderRoutes.objects.filter(driver_route__id = pk)
        driver_route = AssignDriverRoutes.objects.filter(id = pk).last()
        context = {}
        context["assigned_routes"] = assigned_routes
        context["driver_route"] = driver_route
        pdf = utils.render_to_pdf("order/print_dispatch_routes.html", context)

        return HttpResponse(pdf, content_type='application/pdf')


class SetInformAdminReplacement(View):
    def get(self, request):

        order_id = self.request.GET.get("order_id")
        inform_admin = self.request.GET.get("inform_admin")
        
        if order_id:
            order = Order.objects.filter(id = order_id).last()

            replacements = Replacement.objects.filter(order = order, return_type = Replacement.SETTLEMENT, settlement_completed = False, settlement_pending = False)
            if replacements.count() > 0:
                replacements.update(settlement_pending=True)

            if inform_admin == "true":
                order.inform_admin_for_settlement = True
            else:
                order.inform_admin_for_settlement = False
            order.save()

        return JsonResponse({"success": True})


class CompleteReplacementAjaxView(View):

    def post(self, request):
        order_id = self.request.POST.get("order_id")

        if order_id:
            order = Order.objects.filter(id = order_id).last()
            order.inform_admin_for_settlement = False
            order.save()

            replacements = Replacement.objects.filter(order = order)
            if replacements.count() > 0:
                replacements.update(settlement_pending=False, settlement_completed = True)

        return JsonResponse({"success": True})


class GenerateBillAjaxView(View):
    template_name1 = "order/bills/generate_bill_form.html"
    template_name2 = "order/bills/print_order_form.html"

    def get(self, request, *args, **kwargs):
        company_id = request.GET.get('company_id')
        customer_id = request.GET.get('customer_id')
        order_id = request.GET.get('order_id')

        billing_address = {}
        shipping_address = {}

        customer = Customer.objects.filter(id = customer_id).last()

        now = datetime.datetime.today()
        slip_no = OrderBill.objects.filter(order__company__id = company_id, created_at__date = now).count() + 1

        context = {"slip_no": slip_no}
        context['billing_address'] = billing_address
        context['shipping_address'] = shipping_address
        context["transport"] = customer.transport if customer.transport else ""

        if order_id:
            order = Order.objects.filter(id = order_id).last()
            if order:
                context["item_total"] = order.item_total
                context["grand_total"] = order.grand_total
                context["shipping_charges"] = order.shipping_charges
                context["packing_charges"] = order.packing_charges
                context["payment_method"] = order.payment_method

            order_bill = OrderBill.objects.filter(order = order).last()
            if order_bill:
                context["order_bill"] = order_bill

        data = {}
        if kwargs['type'] == "generate":
            data['html']=render_to_string(self.template_name1, context, request=request)
        else:
            data['html']=render_to_string(self.template_name2, context, request=request)
        
        return JsonResponse(data)

    def post(self, request, *args, **kwargs):
        order = request.POST.get('order')
        order = Order.objects.filter(id = order).last()

        if kwargs["type"] == "generate":
            shipping_charges = request.POST.get('shipping_charges', 0)
            packing_charges = request.POST.get('packing_charges', 0)

            shipping_charges = float(shipping_charges) if shipping_charges else 0
            packing_charges = float(packing_charges) if packing_charges else 0

            order.shipping_charges = shipping_charges
            order.packing_charges = packing_charges
            order.grand_total = order.item_total + shipping_charges + packing_charges
            # order.payment_method = request.POST.get("payment_method")

            # if order.payment_method == Order.CASH:
            #     order.paid_amount = order.grand_total
            #     Payment.objects.create(customer_name=order.customer, receive_amount=order.paid_amount)
            order.save()

            order_bill = OrderBill.objects.filter(order = order, customer = order.customer).last()
            # order_bill.slip_no = request.POST.get("slip_no")
            if not order_bill.bill_id:
                order_bill.bill_id = "{}{:05d}".format("BILL#", order_bill.id)
            order_bill.bill_amount = order.grand_total

            bill_date = request.POST.get("bill_date")
            if bill_date:
                order_bill.bill_date = datetime.datetime.strptime(bill_date, "%Y-%m-%d")

            due_date = request.POST.get("due_date")
            if due_date:
                order_bill.due_date = datetime.datetime.strptime(due_date, "%Y-%m-%d")

            local_bill = request.POST.get("local_bill", "")
            if local_bill == "true":
                order_bill.is_local_bill = True
                order_bill.gr_date = None
                order_bill.gr_number = ""
                order_bill.case_number = None
                order_bill.transporter = ""
            else:
                order_bill.is_local_bill = False
                gr_date = request.POST.get("gr_date")
                if gr_date:
                    order_bill.gr_date = datetime.datetime.strptime(gr_date, "%Y-%m-%d")
                order_bill.gr_number = request.POST.get("gr_number")
                order_bill.case_number = request.POST.get("case_number")
                order_bill.transporter = request.POST.get("transporter")

            order_bill.written_by = request.POST.get("written_by")
            order_bill.checked_by = request.POST.get("checked_by")
            order_bill.packed_by = request.POST.get("packed_by")
            order_bill.due_amount = order.grand_total - order.paid_amount
            order_bill.paid_amount = order.paid_amount

            if order_bill.due_amount == 0:
                order_bill.status = OrderBill.COMPLETE
            order_bill.save()

            order.is_bill_generated = True
            order.save()

            context = {}
            context["order_products"] = OrderedProduct.objects.filter(order=order)
            context["order"] = order
            context["order_bill"] = order_bill
            context["amount_in_words"] = num2words(order.grand_total, lang='en_IN').title()
            
            if order_bill.due_date and order_bill.bill_date and order_bill.due_date > order_bill.bill_date:
                due_days = (order_bill.due_date - order_bill.bill_date).days
                context["due_days"] = "Within " + num2words(due_days, lang='en_IN').title() + " Days"

            pdf = utils.render_to_pdf('order/bills/print_order_bill.html', context)
            pdf_name = "order-%s.pdf" % str(order.order_id)

            if pdf:
                if order_bill.bill_pdf:
                    order_bill.bill_pdf.delete()
                order_bill.bill_pdf.save(pdf_name, ContentFile(pdf))
                order_bill.save()

                return JsonResponse({"message": "Order bill generated.", "bill_pdf_url": order_bill.bill_pdf.url})

            return JsonResponse({"message": "Order bill generated.", "bill_id": order.id})

        else:
            transport = request.POST.get("transporter")
            context = {"order_id": order.id, "transport":transport, "customer_name": order.customer.customer_name, "customer_area": order.customer.area}
            return utils.generate_order_pdf(context)

            # template = get_template("order/bills/print_order.html")
            # html = template.render(context)
            
            # return JsonResponse({"html": html})

            # return utils.generate_order_bill("order/bills/print_order.html", context)

        # customer_bill = CustomerBill.objects.filter(order = order).last()
        # if customer_bill:
        #     order_bill.paid_amount = customer_bill.paid_amount
        #     order_bill.due_amount = customer_bill.due_amount

        #     if order_bill.due_amount == 0:
        #         order_bill.status = OrderBill.COMPLETE
        # order_bill.save()

        # return JsonResponse({"level": "success", "message": "Order  generated."})
class FetchShortestRouteView(View):
    def post(self, request, *args, **kwargs):
        assigned_route_obj_pk = self.request.POST.get('assigned_route_obj')

        if not assigned_route_obj_pk:
            return JsonResponse({'status': 'error', 'message': 'Object PK not provided'}, status=400)

        try:
            # Fetch the assigned route and associated orders
            assigned_route_objs = AssignOrderRoutes.objects.filter(driver_route__id=assigned_route_obj_pk)
            orders = Order.objects.filter(assined_orders__in=assigned_route_objs)
            print('orders: ', orders.values_list("id"))

            # Retrieve the start location's latitude and longitude
            assigned_route = AssignDriverRoutes.objects.get(id=assigned_route_obj_pk)
            warehouse = assigned_route.start_location
            origin = f"{warehouse.latitude},{warehouse.longitude}"

            # Group orders by unique addresses
            address_to_orders = {}
            client_lat_long_dict = {}
            customer_order_map = {}  # To map waypoints to order IDs and customer IDs

            for order in orders:
                print('order: ', order.customer.pk)
                customer_shipping_addresses = CustomerShippingAddress.objects.filter(customer=order.customer)

                for address in customer_shipping_addresses:
                    address_key = (
                        address.shipping_address_line_1,
                        address.shipping_address_line_2,
                        address.shipping_suite_apartment,
                        address.shipping_city,
                        address.shipping_state,
                        address.shipping_country,
                        address.shipping_zip_code,
                    )

                    if address_key not in address_to_orders:
                        address_to_orders[address_key] = []

                    address_to_orders[address_key].append(order.id)
                    client_lat_long_dict[order.id] = f"{address.shipping_latitude},{address.shipping_longitude}"
                    customer_order_map[f"{address.shipping_latitude},{address.shipping_longitude}"] = {
                        'customer_pk': order.customer.id,
                        'order_ids': address_to_orders[address_key]
                    }
                    
            print('customer_order_map: ', customer_order_map)

            # Remove duplicate lat-longs for best route calculation
            unique_lat_longs = list(set(client_lat_long_dict.values()))
            print('unique_lat_longs: ', unique_lat_longs)

            # Create the indexed dictionary for unique lat-longs
            indexed_customer_order_map = {i: {'customer_pk': customer_order_map[lat_long]['customer_pk'],
                                              'order_ids': customer_order_map[lat_long]['order_ids'],
                                              'let-long': lat_long}
                                          for i, lat_long in enumerate(unique_lat_longs)}

            print('indexed_customer_order_map: ', indexed_customer_order_map)

            # Fetch the best route
            try:
                best_route_data = get_best_route(unique_lat_longs, origin)
                # print('best_route_data: ', best_route_data)
            except ValueError as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

            if not isinstance(best_route_data, list) or len(best_route_data) == 0:
                return JsonResponse({'status': 'error', 'message': 'Invalid route data'}, status=500)

            best_route_data = best_route_data[0]
            waypoint_order = best_route_data.get('waypoint_order', [])
            print("waypoint_order: ", waypoint_order)

            # Assign stops based on waypoint order
            order_id_to_stop = {}
            for stop_number, waypoint_index in enumerate(waypoint_order, start=1):
                waypoint_lat_long = unique_lat_longs[waypoint_index]
                indexed_entry = next((entry for idx, entry in indexed_customer_order_map.items() if entry['let-long'] == waypoint_lat_long), None)

                if indexed_entry:
                    for order_id in indexed_entry['order_ids']:
                        order_id_to_stop[order_id] = stop_number
                        try:
                            assign_order_route = AssignOrderRoutes.objects.get(order_id=order_id, driver_route__id=assigned_route_obj_pk)
                            assign_order_route.stop = stop_number
                            assign_order_route.save()
                        except AssignOrderRoutes.DoesNotExist:
                            print(f"AssignOrderRoutes not found for order ID {order_id}.")

            # Prepare orders_data for response
            orders_data = []
            for order in orders:
                try:
                    assign_order_route = AssignOrderRoutes.objects.get(order=order, driver_route__id=assigned_route_obj_pk)
                    stop_number = order_id_to_stop.get(order.id, assign_order_route.stop)
                    orders_data.append({
                        'order': {
                            'id': order.id,
                            'order_id': order.order_id,
                            'order_date': order.order_date.strftime('%b. %-d, %Y'),
                            'shipping_address': f"{order.shipping_address_line_1},<br>{order.shipping_address_line_2},<br>{order.shipping_city},{order.shipping_state},<br>{order.shipping_country}-{order.shipping_zip_code}",
                            'payment_method': order.payment_method,
                            'status': order.status.capitalize(),
                            'status_class': 'badge bg-light-success' if order.status == 'shipped' else 'badge bg-light-danger',
                        },
                        'customer_name': order.customer.customer_name,
                        'customer_url': reverse('customer:customer_details', args=[order.customer.id]),
                        'order_url': reverse('order:order_detail', args=[order.id]),
                        'stop': stop_number
                    })
                except AssignOrderRoutes.DoesNotExist:
                    print(f"AssignOrderRoutes not found for order ID {order.id}.")

            print('orders_data: ', orders_data)
            orders_data.sort(key=lambda x: x['stop'])
            # print('orders_data: ', orders_data)
            assigned_route.synchronized_route = True
            assigned_route.save()

            return JsonResponse({'status': 'success', 'best_route': orders_data, "message": "Best Route Updated."})

        except AssignOrderRoutes.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Assigned route object not found'}, status=404)
        except AssignDriverRoutes.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Assigned driver route not found'}, status=404)
        except Exception as e:
            print(f"Exception occurred: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
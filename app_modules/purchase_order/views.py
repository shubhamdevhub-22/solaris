from django.template.loader import render_to_string
from app_modules.purchase_order.models import PurchaseOrder,PurchaseOrderProducts
from app_modules.product.models import Barcode, Product, WarehouseProductStock, WarehouseProductStockHistory,Brand 
from app_modules.vendors.models import Vendor 
from app_modules.company.models import Company, Warehouse 
from app_modules.users.models import User 
from app_modules.purchase_order.forms import PurchaseOrderFrom,PurchaseOrderProductsForm
from django.views.generic import CreateView, View, ListView, UpdateView
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.template.loader import get_template
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import HttpResponseRedirect
from django.db.models import Q
from django_datatables_too.mixins import DataTableMixin
from django.contrib import messages
from app_modules.vendors.models import VendorBill
from app_modules.base.mixins import CompanyAdminLoginRequiredMixin

# Create your views here.

class PurchaseOrderCreateView(CompanyAdminLoginRequiredMixin,CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderFrom
    template_name = "purchase_order/purchase_order_form.html"
    success_url = reverse_lazy("purchase_order:purchase_order_list")
    
    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form2"] =  PurchaseOrderProductsForm
        return context
    

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.save()
        if self.request.user.role in[User.COMPANY_ADMIN,User.SALES_REPRESENTATIVE]:
            instance.company = self.request.user.company_users.first().company
            instance.save()
            
        product_ids=self.request.POST.get('product_id_list').split(',')
        
        for product_id in product_ids:
            self.add_product_list_in_purchase_order(instance,product_id)
        new_vendor_bill = VendorBill(purchase_order=instance, vendor = instance.vendor , bill_amount = instance.total_price , due_amount = instance.total_price)
        new_vendor_bill.save()
        messages.add_message(self.request, messages.SUCCESS, "Purchase Order Created ")
        return HttpResponseRedirect(reverse("purchase_order:purchase_order_list"))

    def add_product_list_in_purchase_order(self,purchase_order,product_id):
        purchase_order = purchase_order
        product_id = product_id
        product=Product.objects.get(id=product_id)
        unit_type = self.request.POST.get(f"product_{product_id}__unit_type")
        quantity = self.request.POST.get(f"product_{product_id}__quantity")
        total_pieces = self.request.POST.get(f"product_{product_id}__totalpieces")
        cost_price = self.request.POST.get(f"product_{product_id}__costprice")
        new_purchase_order=PurchaseOrderProducts(purchase_order=purchase_order,product=product,unit_type=unit_type,quantity=quantity,total_pieces=total_pieces,cost_price=cost_price)
        
        new_purchase_order.save()
    

class GetProductFromBarcodeAjax(View):
    def post(self, request):
        barcode_number = request.POST.get('barcode_number')
        product_id = None
        barcode_product_unit_type = None
        piece = 1
       
        product = list(Barcode.objects.filter(barcode_number=barcode_number).values('product','product_type'))
        for id in product:
            barcode_product_unit_type = id['product_type']
            product_id = id['product']
        product_list = Product.objects.filter(id = int(product_id)).all()

        for product_data in product_list:
            if product_data.box and barcode_product_unit_type == 'box' :
                piece = product_data.box_piece
            if product_data.case and barcode_product_unit_type == 'case':
                piece = product_data.case_piece

        data = {
            "product_id":product_id,
            "barcode_product_unit_type":barcode_product_unit_type.capitalize(),
            "piece":piece,
            }
        return JsonResponse(data, safe=False)



class GetVendorsAndProductsByCompanyAjax(View):

    template_name = "purchase_order/get_vendors_and_products_by_company.html"

    def post(self, request, *args, **kwargs):
        context={}
        data={}
        company_id = request.POST['company_id']
        
        company_vendors = Vendor.objects.filter(company = company_id,status=Vendor.ACTIVE)
        company_products = Product.objects.filter(company = company_id,status=Product.ACTIVE,brand__status = Brand.ACTIVE)

        context['company_vendors'] = company_vendors
        data['company_vendors']=render_to_string(self.template_name,context,request=request)
        context['company_vendors'] = None

        context['company_products'] = company_products
        data['company_products']=render_to_string(self.template_name,context,request=request)
        return JsonResponse(data)

class AjaxGetProductDetails(View):
    template_name = "purchase_order/get_product_details.html"
    
    def post(self, request, *args, **kwargs):
        context={}
        data={}
        product_id = request.POST['product_id']
        product = get_object_or_404(Product,id=product_id)

        context['product'] = product
        data['product_unit_type']=render_to_string(self.template_name,context,request=request)
        data['product_cost_price'] = product.cost_price
        return JsonResponse(data)



class AddProductInPurchaseList(View):
    #use this on company select
    template_name = "purchase_order/add_product_in_purchase_list.html"

    def post(self,request,*args, **kwargs):
        context={}
        data={}
        product_id = request.POST['product_id']
        unit_type = request.POST['unit_type']
        unit_type_text = request.POST['unit_type_text']
        unit_type_pieces = int(request.POST['unit_type_pieces'])
        quantity = int(request.POST['quantity'])
        cost_price = float(request.POST['cost_price'])

        product = get_object_or_404(Product, id = product_id)
        
        
        
        context['product'] = product
        context['unit_type'] = unit_type 
        context['unit_type_text'] = unit_type_text
        context['unit_type_pieces'] = unit_type_pieces
        context['quantity'] = quantity
        total_pieces = quantity * unit_type_pieces

        context['total_pieces'] = total_pieces
        context['cost_price'] = cost_price
        total_price = cost_price * total_pieces
        context['total_price'] = f'{"%.2f" % round(total_price, 2)}' 
        data['product_row']=render_to_string(self.template_name,context,request=request)
        return JsonResponse(data)
    


class PurchaseOrderListView(CompanyAdminLoginRequiredMixin,ListView):
    template_name = "purchase_order/purchase_order_list.html"
    model = PurchaseOrder

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["purhase_order_statuses"] = PurchaseOrder.STATUS_CHOICES
        context["companies"] = Company.objects.filter(status=Company.IS_ACTIVE)
        context["vendors"] = Vendor.objects.filter(status=Vendor.ACTIVE)
        if self.request.user.role in[User.COMPANY_ADMIN,User.SALES_REPRESENTATIVE]:
            company_admin_company = self.request.user.company_users.first().company
            context["vendors"] = Vendor.objects.filter(status=Vendor.ACTIVE, company = company_admin_company)

        return context

class PurchaseOrderListAjax(DataTableMixin,View):
    model = PurchaseOrder
    
    def get_queryset(self):
        qs = PurchaseOrder.objects.all().order_by("-id")

        if self.request.user.role == User.COMPANY_ADMIN or self.request.user.role == User.SALES_REPRESENTATIVE:
            company_id = list(self.request.user.company_users.all().values_list("company_id", flat=True))
            company_list = list(Company.objects.filter(id__in=company_id).values_list("id",flat=True))
            qs = qs.filter(company__in=company_list)


        purchase_order_list_company=self.request.GET.get("purchase_order_list_company")
        if purchase_order_list_company:
            companies=list(PurchaseOrder.objects.filter(company__in = purchase_order_list_company).values_list("id",flat=True))
            qs = qs.filter(id__in = companies)
        order_statuse = self.request.GET.get("purchase_order_status")
        if order_statuse:
            order_list = list(PurchaseOrder.objects.filter(status = order_statuse).values_list("id",flat=True))
            qs = qs.filter(id__in = order_list)
        purchase_order_vendor = self.request.GET.get("purchase_order_vendor")
        if purchase_order_vendor:
            qs = qs.filter(vendor__id=purchase_order_vendor)
        purchase_order_bill_number=self.request.GET.get("purchase_order_bill_number")
        if purchase_order_bill_number:
            qs = qs.filter(bill_number=purchase_order_bill_number)
        start_date = self.request.GET.get("from_date")
        end_date = self.request.GET.get("to_date")
        if end_date:
            result_payment = PurchaseOrder.objects.filter(bill_date__range = [start_date, end_date])
            qs = qs.filter(id__in=result_payment)
            return qs.order_by("-id")

        
        
        return qs.order_by("-id")
        

    def filter_queryset(self, qs):
        if self.search:
            return qs.filter(
                Q(bill_number__icontains=self.search) |
                Q(bill_date__icontains=self.search) | 
                Q(status__icontains=self.search)
            )
        return qs
    
    def _get_actions_buttons(self,obj):

        update_url = reverse("purchase_order:purchase_order_update", kwargs={"pk": obj.id})
        return f'<center><a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a></center>'
    
    def _get_status(self,obj):
        t = get_template("purchase_order/get_purchase_order_status.html")
        return t.render(
            {"purchase_order": obj, "request": self.request}
        )
    
    def get_vendor_details(self, obj):
        t = get_template("purchase_order/po_vendor_details.html")
        return t.render(
            {"vendor_id": obj.vendor}
        )
    
        
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'company': o.company.company_name,
                'vendor': self.get_vendor_details(o),
                'bill_number': o.bill_number,
                'bill_date': f'{o.bill_date.strftime("%-d %B, %Y")}',
                
                'total_price': o.total_price,
                'status':self._get_status(o),
                'actions':self._get_actions_buttons(o),
            }
            for o in qs
        ]


class PurchaseOrderUpdateView(CompanyAdminLoginRequiredMixin,UpdateView):
    model = PurchaseOrder
    form_class = PurchaseOrderFrom
    template_name = "purchase_order/purchase_order_form.html"
    success_url = reverse_lazy("purchase_order:purchase_order_list")

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form2"] =  PurchaseOrderProductsForm
        return context
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        
        instance.save()
        if self.request.user.role == User.COMPANY_ADMIN or self.request.user.role == User.SALES_REPRESENTATIVE:
            instance.company = self.request.user.company_users.first().company
            instance.save()
        product_ids=self.request.POST.get('product_id_list').split(',')
        self.update_product_list_in_purchase_order(instance,product_ids)
        warehouse_id = self.request.POST.get("warehouse_id")
        if instance.status == PurchaseOrder.REVERTED:
            self.revert_product_stock(instance)
        if instance.status == PurchaseOrder.COMPLETED and warehouse_id:
            self.update_product_stock(instance, warehouse_id)
        messages.add_message(self.request, messages.SUCCESS, "Purchase Order Updated ")
        return HttpResponseRedirect(reverse("purchase_order:purchase_order_list"))


    def update_product_list_in_purchase_order(self,purchase_order,product_ids):
        purchase_order = purchase_order
        to_delete_products = PurchaseOrderProducts.objects.filter(purchase_order = purchase_order)
        for to_deletes_product in to_delete_products:
            to_deletes_product.delete()
        for product_id in product_ids:
            product=Product.objects.get(id=product_id)
            unit_type = self.request.POST.get(f"product_{product_id}__unit_type")
            quantity = self.request.POST.get(f"product_{product_id}__quantity")
            total_pieces = self.request.POST.get(f"product_{product_id}__totalpieces")
            cost_price = self.request.POST.get(f"product_{product_id}__costprice")
            new_purchase_order=PurchaseOrderProducts(purchase_order=purchase_order,product=product,unit_type=unit_type,quantity=quantity,total_pieces=total_pieces,cost_price=cost_price)
            new_purchase_order.save()

    def revert_product_stock(self,purchase_order):
        purchase_order_products = PurchaseOrderProducts.objects.filter(purchase_order=purchase_order)
        warehouse = purchase_order.warehouse
        if warehouse:
            for product in purchase_order_products:
                product_stock, created = WarehouseProductStock.objects.get_or_create(warehouse=warehouse, product=product.product)
                if created:
                    product_stock.stock =  product.total_pieces
                    product_stock.save()
                else:
                    product_stock.stock =  product_stock.stock - product.total_pieces
                    product_stock.save()

                last_product_stock_history = WarehouseProductStockHistory.objects.filter(warehouse=warehouse, product=product.product).last()
                if last_product_stock_history:
                        new_product_stock_history = WarehouseProductStockHistory.objects.create(warehouse=warehouse, product=product.product)
                        new_product_stock_history.stock = last_product_stock_history.stock - product.total_pieces
                        new_product_stock_history.affected_stock = product.total_pieces
                        new_product_stock_history.before_stock = last_product_stock_history.stock
                        new_product_stock_history.save()
                    
                else:
                    new_product_stock_history = WarehouseProductStockHistory.objects.create(warehouse=warehouse, product=product.product)
                    new_product_stock_history.before_stock = 0
                    new_product_stock_history.affected_stock = product.total_pieces
                    new_product_stock_history.stock = product.total_pieces
                    new_product_stock_history.save() 

                purchase_order.warehouse = None
                purchase_order.save()      

    def update_product_stock(self,purchase_order, warehouse_id):
        purchase_order_products = PurchaseOrderProducts.objects.filter(purchase_order=purchase_order)
        warehouse = Warehouse.objects.get(id=warehouse_id)
        purchase_order.warehouse = warehouse
        purchase_order.save()

        for product in purchase_order_products:
            product_stock, created = WarehouseProductStock.objects.get_or_create(warehouse=warehouse, product=product.product)
            if created:
                product_stock.stock =  product.total_pieces
                product_stock.save()
            else:
                product_stock.stock =  product_stock.stock + product.total_pieces
                product_stock.save()

            last_product_stock_history = WarehouseProductStockHistory.objects.filter(warehouse=warehouse, product=product.product).last()
            if last_product_stock_history:
                    new_product_stock_history = WarehouseProductStockHistory.objects.create(warehouse=warehouse, product=product.product)
                    new_product_stock_history.stock = last_product_stock_history.stock + product.total_pieces
                    new_product_stock_history.affected_stock = product.total_pieces
                    new_product_stock_history.before_stock = last_product_stock_history.stock
                    new_product_stock_history.save()
                
            else:
                new_product_stock_history = WarehouseProductStockHistory.objects.create(warehouse=warehouse, product=product.product)
                new_product_stock_history.before_stock = 0
                new_product_stock_history.affected_stock = product.total_pieces
                new_product_stock_history.stock = product.total_pieces
                new_product_stock_history.save()

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == User.COMPANY_ADMIN:
            qs = qs.filter(company__id=self.request.user.get_company_id)
        return qs
        

class AjaxGetUpdateProductDetails(View):
    template_name = "purchase_order/add_product_in_purchase_list.html"

    def post(self, request, *args, **kwargs):
        context={}
        data={}
        purchase_order_id = request.POST['purchase_order_id']
        purchase_order_products = PurchaseOrderProducts.objects.filter(purchase_order=purchase_order_id)
        purchase_order__product_ids = list(purchase_order_products.values_list('product',flat=True))
        context['purchase_order_products'] = purchase_order_products
        context['purchase_order_update_id'] = purchase_order_id
        data['purchase_order__product_ids'] = purchase_order__product_ids
        data['existing_product_list']=render_to_string(self.template_name,context,request=request)
        # data['product_cost_price'] = product.cost_price
        return JsonResponse(data)
    

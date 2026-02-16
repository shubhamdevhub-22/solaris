import json
from django.forms import BaseForm
from django.shortcuts import redirect, render, HttpResponseRedirect
from django.views.generic import CreateView, ListView, UpdateView, View, TemplateView,FormView
from requests import request
from app_modules.product.tasks import  import_product_from_xlsx, import_product_stock_from_xlsx
from app_modules.vendors.models import Vendor
from app_modules.product.models import CSVFile, ProductLog, Brand, Product, WarehouseProductStock, WarehouseProductStockHistory, Barcode, ProductVehicle
from app_modules.company.models import Company
from django.db.models import Q, F, Sum
from django.views.generic import View
from django_datatables_too.mixins import DataTableMixin
from app_modules.company.models import Company, Warehouse
from django.http import HttpResponse, JsonResponse
from django.urls import reverse_lazy, reverse
from django.template.loader import get_template
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from app_modules.product.forms import (
    BrandCreateForm,CreateProductCSVForm, ImportProductCSVForm, 
    ProductPriceUpdateForm,ProductCreateForm,
    UpdateStockCSVForm, WarehouseStockForms, BarcodeForm,
    ProductVehicleForm, StockCreateForm,
)
from app_modules.vendors.models import Vendor
from barcode import EAN13, Code39,Code128
from django.core.files import File
from barcode.writer import ImageWriter
import uuid
from io import BytesIO
import re
from django.template.loader import render_to_string
from app_modules.base.mixins import CompanyAdminLoginRequiredMixin, SalesAccountantLoginRequiredMixin
from django.contrib.auth import get_user_model

User = get_user_model()


# Create your views here.
"""
Brand Model Crud(Created Date:-19/06/23)
"""


class BrandCreateView(SuccessMessageMixin, CompanyAdminLoginRequiredMixin, CreateView):
    model = Brand
    form_class = BrandCreateForm
    success_message = "Brand Created Successfully!!"
    template_name = "product/form_brand.html"
    success_url = reverse_lazy("product:list_brand")

    def form_valid(self, form):
        instance = form.save(commit=False)
        if not instance.discount_a:
            instance.discount_a = 0
        if not instance.discount_b:
            instance.discount_b = 0
        instance.save()
        return HttpResponseRedirect(reverse("product:list_brand"))


class BrandUpdateView(SuccessMessageMixin, CompanyAdminLoginRequiredMixin, UpdateView):
    model = Brand
    form_class = BrandCreateForm
    success_message = "Brand Updated Successfully!!"
    template_name = "product/form_brand.html"

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role in[ User.COMPANY_ADMIN, User.SALES_REPRESENTATIVE]:
            qs = qs.filter(company__id=self.request.user.get_company_id)
        return qs

    def form_valid(self, form):
        instance = form.save(commit=False)
        if not instance.discount_a:
            instance.discount_a = 0
        if not instance.discount_b:
            instance.discount_b = 0
        instance.save()
        return HttpResponseRedirect(reverse("product:list_brand"))

class BrandListView(SuccessMessageMixin, CompanyAdminLoginRequiredMixin, ListView):
    model = Brand
    template_name = "product/list_brand.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company_list"] = Company.objects.filter(status='active')
        return context


class BrandDataTablesAjaxPagination(DataTableMixin, View):
    model = Brand

    def get_queryset(self):
        qs = Brand.objects.all()

        if self.request.user.role not in [User.SUPER_ADMIN]:
            qs = Brand.objects.filter(company__id=self.request.user.get_company_id)

        company = self.request.GET.get("company")
        if company:
            qs = qs.filter(company__id=company)

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("-id")

    def _get_actions(self, obj):
        """Get action buttons w/links."""
        update_url = reverse("product:update_brand", kwargs={"pk": obj.id})
        delete_url = reverse("product:delete_brand")
        return f'<center><a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a> <label data-title="{obj.name}" title="Delete" data-url="{delete_url}" data-id="{obj.id}" id="delete_btn" class="danger p-0 ajax-delete-btn"><i class="ft-trash font-medium-3"></i></label></center>'

    def _get_product_count(self, obj):
        return Product.objects.filter(brand=obj).count()

    def filter_queryset(self, qs):
        if self.search:
            return qs.filter(
                Q(name__icontains=self.search) |
                Q(status__icontains=self.search)
            )
        return qs

    def _get_status(self, obj):
        t = get_template("product/get_brand_status.html")
        return t.render(
            {"product": obj, "request": self.request}
        )

    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'name': o.name,
                'company': o.company.company_name,
                'status': self._get_status(o),
                'product_count': o.product_count,
                'active_product': o.active_product_count,
                'inactive_product': o.inactive_product_count,
                'discount_a': o.discount_a,
                'discount_b': o.discount_b,
                'inactive_product': o.inactive_product_count,
                'actions': self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class BrandDeleteAjaxView(View):
    def post(self, request):
        brand_id = self.request.POST.get("id")
        Brand.objects.filter(id=brand_id).delete()
        return JsonResponse({"message": "Brand Deleted Successfully."})


"""
Category Model Crud(Created Date:-19/06/23)
"""


# class CategoryCreateView(SuccessMessageMixin, LoginRequiredMixin, CreateView):
#     model = Category
#     form_class = CategoryCreateForm
#     success_message = "Category Created Successfully!!"
#     template_name = "product/form_category.html"
#     success_url = reverse_lazy("product:list_category")


# class CategoryUpdateView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
#     model = Category
#     form_class = CategoryCreateForm
#     success_message = "Category Updated Successfully!!"
#     template_name = "product/form_category.html"
#     success_url = reverse_lazy("product:list_category")

#     def get_queryset(self):
#         qs = super().get_queryset()
#         if self.request.user.role in[ User.COMPANY_ADMIN, User.SALES_REPRESENTATIVE]:
#             qs = qs.filter(company__id=self.request.user.get_company_id)
#         return qs



# class CategoryListView(SuccessMessageMixin, LoginRequiredMixin, ListView):
#     model = Category
#     template_name = "product/list_category.html"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["company_list"] = Company.objects.filter(status='active')
#         return context


# class CategoryDataTablesAjaxPagination(DataTableMixin, View):
#     model = Category
#     # queryset=Category.objects.all()

#     def get_queryset(self):
#         qs = Category.objects.all()
#         if self.request.user.role in ["company admin", "sales representative"]:
#             qs = Category.objects.filter(
#                 company__id=self.request.user.get_company_id)

#         company = self.request.GET.get("company")
#         if company:
#             qs = qs.filter(company__id=company)

#         status = self.request.GET.get("status")
#         if status:
#             qs = qs.filter(status=status)

#         return qs.order_by("-id")

#     def _get_actions(self, obj):
#         """Get action buttons w/links."""
#         update_url = reverse("product:update_category", kwargs={"pk": obj.id})
#         delete_url = reverse("product:delete_category")
#         return f'<center><a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a> <label data-title="{obj.name}" title="Delete" data-url="{delete_url}" data-id="{obj.id}" id="delete_btn" class="danger p-0 ajax-delete-btn"><i class="ft-trash font-medium-3"></i></label></center>'

#     def filter_queryset(self, qs):
#         """Return the list of items for this view."""
#         # If a search term, filter the query
#         return qs.filter(Q(name__icontains=self.search)) if self.search else qs

#     def _get_status(self, obj):
#         t = get_template("product/get_category_status.html")
#         return t.render(
#             {"product": obj, "request": self.request}
#         )

#     def _get_type_invoice(self, obj):
#         t = get_template("product/get_type_a_invoice.html")
#         return t.render(
#             {"product": obj, "request": self.request}
#         )

#     def prepare_results(self, qs):
#         return [
#             {
#                 'id': o.id,
#                 'name': o.name,
#                 'company': o.company.company_name,
#                 'status': self._get_status(o),
#                 'is_type_a_invoice': self._get_type_invoice(o),
#                 'product_count': o.product_count,
#                 'active_product': o.active_product_count,
#                 'inactive_product': o.inactive_product_count,
#                 'actions': self._get_actions(o),
#             }
#             for o in qs
#         ]

#     def get(self, request, *args, **kwargs):
#         context_data = self.get_context_data(request)
#         return JsonResponse(context_data)


# class CategoryDeleteAjaxView(View):
#     def post(self, request):
#         category_id = self.request.POST.get("id")
#         Category.objects.filter(id=category_id).delete()
#         return JsonResponse({"message": "Category Deleted Successfully ."})


# """
# SubCategory Model Crud(Created Date:-19/06/23)
# """


# class SubCategoryCreateView(SuccessMessageMixin, LoginRequiredMixin, CreateView):
#     model = SubCategory
#     form_class = SubCategoryCreateForm
#     success_message = "Subcategory Created Successfully!!"
#     template_name = "product/form_subcategory.html"
#     success_url = reverse_lazy("product:list_subcategory")

#     def get_form_kwargs(self):
#         form_kwargs = super().get_form_kwargs()
#         form_kwargs["user"] = self.request.user
#         return form_kwargs


# class SubCategoryUpdateView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
#     model = SubCategory
#     form_class = SubCategoryCreateForm
#     success_message = "Subcategory Updated Successfully!!"
#     template_name = "product/form_subcategory.html"
#     success_url = reverse_lazy("product:list_subcategory")

#     def get_form_kwargs(self):
#         form_kwargs = super().get_form_kwargs()
#         form_kwargs["user"] = self.request.user
#         return form_kwargs
    
#     def get_queryset(self):
#         qs = super().get_queryset()
#         if self.request.user.role in[ User.COMPANY_ADMIN, User.SALES_REPRESENTATIVE]:
#             qs = qs.filter(company__id=self.request.user.get_company_id)
#         return qs


# class SubCategoryListView(SuccessMessageMixin, LoginRequiredMixin, ListView):
#     model = SubCategory
#     template_name = "product/list_subcategory.html"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["company_list"] = Company.objects.filter(status='active')
#         if self.request.user.role in ["company admin", "sales representative"]:
#             context["category_list"] = Category.objects.filter(company__id=self.request.user.get_company_id)
#         else:
#             context["category_list"] = Category.objects.all()

#         return context


# class SubCategoryDataTablesAjaxPagination(DataTableMixin, View):
#     model = SubCategory

#     def get_queryset(self):
#         qs = SubCategory.objects.all()
#         if self.request.user.role in ["company admin", "sales representative"]:
#             qs = SubCategory.objects.filter(
#                 company__id=self.request.user.get_company_id)
#         category = self.request.GET.get("category")
#         if category:
#             qs = qs.filter(category__id=category)

#         company = self.request.GET.get("company")
#         if company:
#             qs = qs.filter(company__id=company)

#         status = self.request.GET.get("status")
#         if status:
#             qs = qs.filter(status=status)

#         return qs.order_by("-id")

#     def _get_actions(self, obj):
#         """Get action buttons w/links."""
#         update_url = reverse("product:update_subcategory",
#                              kwargs={"pk": obj.id})
#         delete_url = reverse("product:delete_subcategory")

#         return f'<center><a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a> <label data-title="{obj.name}" title="Delete" data-url="{delete_url}" data-id="{obj.id}" id="delete_btn" class="danger p-0 ajax-delete-btn"><i class="ft-trash font-medium-3"></i></label></center>'

#     def filter_queryset(self, qs):
#         """Return the list of items for this view."""
#         # If a search term, filter the query
#         if self.search:
#             return qs.filter(
#                 Q(name__icontains=self.search) |
#                 Q(category__name__icontains=self.search)

#             )
#         return qs

#     def _get_status(self, obj):
#         t = get_template("product/get_subcategory_status.html")
#         return t.render(
#             {"product": obj, "request": self.request}
#         )

#     def _get_type_invoice(self, obj):
#         t = get_template("product/get_type_a_invoice.html")
#         return t.render(
#             {"product": obj, "request": self.request}
#         )

#     def prepare_results(self, qs):
#         return [
#             {
#                 'id': o.id,
#                 'name': o.name,
#                 'category': o.category.name,
#                 'company': o.company.company_name,
#                 'status': self._get_status(o),
#                 'is_type_a_invoice': self._get_type_invoice(o),
#                 'product_count': o.product_count,
#                 'active_product': o.active_product_count,
#                 'inactive_product': o.inactive_product_count,
#                 'actions': self._get_actions(o),
#             }
#             for o in qs
#         ]

#     def get(self, request, *args, **kwargs):
#         context_data = self.get_context_data(request)
#         return JsonResponse(context_data)


# class SubCategoryDeleteAjaxView(View):
#     def post(self, request):
#         subcategory_id = self.request.POST.get("id")
#         SubCategory.objects.filter(id=subcategory_id).delete()
#         return JsonResponse({"message": "Subcategory Deleted Successfully."})


"""
Product Model Crud(Created Date:-19/06/23)
"""


class ProductCreateView(SuccessMessageMixin, CompanyAdminLoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductCreateForm
    success_message = "Product Created Successfully!!"
    template_name = "product/form_product.html"
    success_url = reverse_lazy("product:list_product")

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

class ProductUpdateView(SuccessMessageMixin, CompanyAdminLoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductCreateForm
    success_message = "Product Updated Successfully!!"
    template_name = "product/form_product.html"
    success_url = reverse_lazy("product:list_product")

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs
    
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role in[ User.COMPANY_ADMIN, User.SALES_REPRESENTATIVE]:
            qs = qs.filter(company__id=self.request.user.get_company_id)
        return qs

class ProductListView(SuccessMessageMixin, CompanyAdminLoginRequiredMixin, ListView):
    model = Product
    template_name = "product/list_product.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company_list"] = Company.objects.all()

        if self.request.user.role in ['company admin', 'sales representative']:
            context["brand_list"] = Brand.objects.filter(company__id= self.request.user.get_company_id)
            context["product_list"] = Product.objects.filter(company__id= self.request.user.get_company_id)
            context["vehicles"] = ProductVehicle.objects.filter(company__id= self.request.user.get_company_id)
        else:
            context["brand_list"] = Brand.objects.all()
            context["product_list"] = Product.objects.all()
        return context


class ProductDataTablesAjaxPagination(DataTableMixin, View):
    model = Product

    def get_queryset(self):
        qs = Product.objects.all()
        if self.request.user.role in ["company admin", "sales representative"]:
            qs = Product.objects.filter(
                company__id=self.request.user.get_company_id)

        brand = self.request.GET.get("brand")
        if brand:
            qs = qs.filter(brand__id=brand)

        company = self.request.GET.get("company")
        if company:
            qs = qs.filter(company__id=company)

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        
        vehicle = self.request.GET.get("vehicle")
        if vehicle:
            qs = qs.filter(vehicle__id=vehicle)

        return qs.order_by("-id")

    def _get_actions(self, obj):
        """Get action buttons w/links."""
        update_url = reverse("product:update_product", kwargs={"pk": obj.id})
        delete_url = reverse("product:delete_product")
        detail_url = reverse("product:product_detail", kwargs={"pk": obj.id})
        return f'<div class="row"><center>  <a href="{detail_url}" title="Detail"><i class="ft-eye font-medium-3 mr-2"></i></a>  <a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a>  <label data-title="{obj.name}" title="Delete" data-url="{delete_url}" data-id="{obj.id}" id="delete_btn" class="danger p-0 ajax-delete-btn"><i class="ft-trash font-medium-3"></i></label></center></div>'

    def _get_product_image(self, obj):
        t = get_template("product/get_product_image.html")
        return t.render(
            {
                "height": 30,
                "img_url": obj.product_image,
                "obj": obj,

            }
        )

    def _get_status(self, obj):
        t = get_template("product/get_product_status.html")
        return t.render(
            {"product": obj, "request": self.request}
        )

    def _get_type_invoice(self, obj):
        t = get_template("product/get_type_a_invoice.html")
        return t.render(
            {"product": obj, "request": self.request}
        )
    
    def _get_product_name(self, obj):
        # return f"<div class='product-name'>{obj.name}</div>"
        return obj.name

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        # If a search term, filter the query
        if self.search:
            return qs.filter(
                Q(name__icontains=self.search) |
                Q(code__icontains=self.search) |
                Q(brand__name__icontains=self.search)
            )
        return qs

    def prepare_results(self, products):
        return [
            {   
            'id': product.id,
            'code': product.code,
            'name': self._get_product_name(product),
            'product_image': self._get_product_image(product),
            'brand': product.brand.name,
            'company': product.company.company_name,
            'vehicle__name': product.vehicle.name if product.vehicle else "-",
            'mrp': product.mrp,
            'wholesale_rate': product.wholesale_rate,
            'retail_rate': product.retail_rate,
            'status': self._get_status(product),
            'actions': self._get_actions(product),
            }
            for product in products
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class ProductDeleteAjaxView(View):
    def post(self, request):
        product_id = self.request.POST.get("id")
        Product.objects.filter(id=product_id).delete()
        return JsonResponse({"message": "Product Deleted Successfully."})

class VehicleCreateAjaxView(SuccessMessageMixin, CreateView):
    form_class = ProductVehicleForm
    template_name = "product/form_product_vehicle.html"
    success_message = "Vehicle created successfully"

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form), status=201)

    def form_valid(self, form):
        instance = form.save()
        response = HttpResponse(status=200)
        response["HX-Trigger"] = json.dumps(
            {
                "productVehicleCreate": {
                    "option": f'<option value="{instance.id}">{instance.name}</option>',
                    "vehicle_id": instance.id,
                    "message": "Product vehicle created.",
                    "level": "success",
                }
            }
        )
        return response
    
class TransferStockView(CompanyAdminLoginRequiredMixin, TemplateView):
    template_name = "product/transfer_stock.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company_list"] = Company.objects.filter(status='active')
        company_id = self.request.user.get_company_id
        context["warehouse_list_for_cadmin"] = Warehouse.objects.filter(company__id=company_id, status=Warehouse.IS_ACTIVE)
        return context


class ProductDetailView(CompanyAdminLoginRequiredMixin, FormView):
    template_name = "product/product_detail.html"
    form_class=BarcodeForm
    success_url = reverse_lazy("product:list_product")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.kwargs.get('pk')
        product = Product.objects.filter(id=product_id).first()
        context["product"] = product
        return context
    
class BarcodeGenerateView(LoginRequiredMixin, View):

    def post(self,*args, **kwargs):
        product_name=self.request.POST.get('product_name')
        product = Product.objects.get(name=product_name)
        product_id=self.request.POST.get('product_id')
        product_type=self.request.POST.get('product_type')
        barcode_number=self.request.POST.get('barcode_number')
        

        buffer = BytesIO()
        my_code = Code128(barcode_number, writer=ImageWriter())
        my_code.write(buffer)

        def validate_code128(barcode):
            pattern = r"^(\{[A-C]\})?[\x00-\x5F\xC8-\xCF]+(\{\d{2}\})*$"
            return re.match(pattern, barcode) is not None

        if validate_code128(barcode_number):

            if Barcode.objects.filter(barcode_number=barcode_number):                
                # messages.add_message(self.request, messages.WARNING, "This Barcode Number's Barcode already Exixts")
                return JsonResponse({"error": "This Barcode Number's Barcode already Exixts."})
            
            Barcode.objects.create(product=product,product_type=product_type,barcode_number=barcode_number,barcode_code=File(buffer, name=f"{str(uuid.uuid4())}.png"))
            return JsonResponse({"message": "Barcode Created Successfully."})
        
        return JsonResponse({"error": "Please Fill Valid Barcode Number."})
        
        # messages.add_message(self.request, messages.SUCCESS, "Barcode Created Successfully.")
    
# UpdateBarcode
class ProdcutBarcodeDataTablesAjaxPagination(LoginRequiredMixin, DataTableMixin, View):
    model = Barcode

    def get_queryset(self):
        qs = Barcode.objects.all()
        product_id = self.request.GET.get("id")
        if product_id:
            qs = qs.filter(product__id=product_id)

        return qs.order_by("-id")

    def _get_actions(self, obj):
        """Get action buttons w/links."""
        delete_url = reverse("product:delete_barcode")
        return f'<center> <label  ><a class="ajax-image-btn text-primary mr-2" data-image="{obj.barcode_code}" ><i class="ft-printer font-medium-3"></i></a></label>  <label data-title="{obj.barcode_number}" title="Delete" data-url="{delete_url}" data-id="{obj.id}" id="delete_btn" class="danger p-0 ajax-delete-btn"><i class="ft-trash font-medium-3"></i></label></center>'

    def _get_barcode_image(self, obj):
        t = get_template("product/get_barcode_image.html")
        return t.render(
            {
                "height": 80,
                "width": 220,
                "img_url": obj.barcode_code,
                "obj": obj,

            }
        )


    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        # If a search term, filter the query
        if self.search:
            return qs.filter(
                Q(barcode_number__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        return [
            {
                # 'no' : index,
                'id': o.id,
                'unit':o.product_type,
                'barcode_number': o.barcode_number,
                'barcode_code': self._get_barcode_image(o),
                'action': self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)
    

class DeleteBarcodeAjaxView(View):
    def post(self, request):
        barcode_id = self.request.POST.get("id")
        Barcode.objects.filter(id=barcode_id).delete()
        return JsonResponse({"message": "Barcode Deleted Successfully."})

# same as product form but just only showing prices of products
class ProductPriceListView(SuccessMessageMixin, CompanyAdminLoginRequiredMixin, ListView):
    model = Product
    template_name = "product/list_product_price.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company_list"] = Company.objects.all()
        if self.request.user.role in ['company admin', 'sales representative']:
            context["brand_list"] = Brand.objects.filter(company__id= self.request.user.get_company_id)
            context["product_list"] = Product.objects.filter(company__id= self.request.user.get_company_id)
        else:
            context["brand_list"] = Brand.objects.all()
            context["product_list"] = Product.objects.all()
        return context


class ProductPriceDataTablesAjaxPagination(DataTableMixin, View):
    model = Product
    # queryset=Product.objects.all()

    def get_queryset(self):
        qs = Product.objects.all()
        if self.request.user.role in ["company admin", "sales representative"]:
            qs = Product.objects.filter(
                company__id=self.request.user.get_company_id)

        brand = self.request.GET.get("brand")
        if brand:
            qs = qs.filter(brand__id=brand)
    
        company = self.request.GET.get("company")
        if company:
            qs = qs.filter(company__id=company)

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        return qs.order_by("-id")

    def _get_actions(self, obj):
        """Get action buttons w/links."""
        return f'<center><a data-id="{obj.id}" class="update-price text-primary" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a><button data-id="{obj.id}" class="btn btn-primary d-none change-price">Save</button></center>'

    def _get_status(self, obj):
        t = get_template("product/get_product_status.html")
        return t.render(
            {"product": obj, "request": self.request}
        )
    
    def _get_mrp(self, obj):
        t = get_template("product/get_mrp.html")
        return t.render(
            {"product": obj, "request": self.request}
        )
    
    def _get_wholesale_price(self, obj):
        t = get_template("product/get_wholesale_price.html")
        return t.render(
            {"product": obj, "request": self.request}
        )
    
    def _get_retail_price(self, obj):
        t = get_template("product/get_retail_price.html")
        return t.render(
            {"product": obj, "request": self.request}
        )

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        # If a search term, filter the query
        return qs.filter(Q(name__icontains=self.search)) if self.search else qs

    def prepare_results(self, qs):
        return [
            {
                'code': o.code,
                'name': f"{o.name} {'('+o.vehicle.name+')' if o.vehicle else ''}  {self._get_status(o)}",
                'company': o.company.company_name,
                'brand': o.brand.name,
                'mrp': self._get_mrp(o),
                'wholesale_rate': self._get_wholesale_price(o),
                'retail_rate': self._get_retail_price(o),
                # 'purchase_price': o.purchase_price,
                'status': self._get_status(o),
                'is_type_a_invoice': o.is_type_a_invoice,
                # 'description': f'{o.description[:10]}...',
                'actions': self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


# same as product update form but only showing price fileds
class ProductPriceUpdateAjaxView(View):
    success_message = "Product Price Updated Successfully!!"

    def post(self, request, pk):
        mrp = request.POST.get("mrp")
        wholesale_rate = request.POST.get("wholesale_rate")
        retail_rate = request.POST.get("retail_rate")
        
        product = Product.objects.filter(id = pk).last()
        if mrp:
            product.mrp = mrp
        if retail_rate:
            product.retail_rate = retail_rate
        if wholesale_rate:
            product.wholesale_rate = wholesale_rate
        product.save()

        return JsonResponse({"message": "Product Price Updated Successfully !!!"})

# Add product stocks in Warehouse
class ManageProductStock(CompanyAdminLoginRequiredMixin,TemplateView):
    template_name = 'product/manage_product_stock.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company_list"] = Company.objects.filter(status='active')
        company_id = self.request.user.get_company_id
        context["product_list_for_cadmin"] = Product.objects.filter(company__id=company_id,status=Product.ACTIVE)
        context["warehouse_list_for_cadmin"] = Warehouse.objects.filter(company__id=company_id,status=Warehouse.IS_ACTIVE)
        context["vehicle_list_for_cadmin"] = ProductVehicle.objects.filter(company__id = company_id)
        return context


# Ajax call for selction of company
class LoadWarehouse(View):
    def get(self, request):
        data = {
            'products_list': list(
                Product.objects.filter(
                    company__id=request.GET.get('id_company'),
                    status=Product.ACTIVE,
                ).values('id', 'name', 'vehicle__name')
            ),
            'warehouse_list': list(
                Warehouse.objects.filter(
                    company__id=request.GET.get('id_company'),
                    status=Warehouse.IS_ACTIVE
                ).values('id', 'name')
            ),
            'vehicle_list': list(
                ProductVehicle.objects.filter(
                    company__id=request.GET.get('id_company')
                ).values('id', 'name')
            ),
        }
        return JsonResponse(data, safe=False)
    
# Ajax call for selection of warehouse and company
class LoadProduct(View):
        def get(self, request):
            id_product = request.GET.get("id_product")
            id_company = request.GET.get("id_company")
            id_warehouse = request.GET.get("id_warehouse")

            stock = 0
            warehouse_list = []
            if id_warehouse:
                warehouse_list = list(Warehouse.objects.filter(company__id = id_company, status = Warehouse.IS_ACTIVE).exclude(id = id_warehouse).values('id', 'name'))
                print('warehouse_list: ', warehouse_list)

            if id_product:
                warehouse_stock = WarehouseProductStock.objects.filter(warehouse__id = id_warehouse, product__id = id_product).last()
                if warehouse_stock:
                    stock = warehouse_stock.stock

            data = {
                'warehouse_list': warehouse_list,
                'stock': stock
            }
            return JsonResponse(data, safe=False)
        

# Ajax call for to know Product stock in particular warehouse 
class LoadAvailableStock(View):
    def get(self, request):
            warehouse_id = request.GET.get('id_warehouse')
            product_id = request.GET.get('id_product')
            data = {
                'available_stock': list(
                    WarehouseProductStock.objects.filter(warehouse__id = warehouse_id, product__id = product_id).values('id', 'stock')
                ),
            }

            return JsonResponse(data, safe=False)
    
class TransferStockAdd(View):
    def post(self, request):
        company_id = request.POST.get('company_id')
        from_warehouse_id = request.POST.get('from_warehouse_id')
        to_warehouse_id = request.POST.get('to_warehouse_id')
        product_id = request.POST.get('product_id')
        available_stock_data = request.POST.get('available_stock_data')
        transfer_stock_data = request.POST.get('transfer_stock_data')
        ordered_stock = request.POST.get('ordered_stock')

        minus_data = WarehouseProductStock.objects.get(warehouse__id = from_warehouse_id, product__id = product_id)
        final_stock = int(minus_data.stock)-int(transfer_stock_data)
        minus_data.stock = final_stock

        minus_data.save()

        WarehouseProductStockHistory.objects.create(warehouse = Warehouse.objects.get(id=from_warehouse_id), product = Product.objects.get(id=product_id), before_stock=available_stock_data, affected_stock=transfer_stock_data, stock=final_stock)

        plus_data, created = WarehouseProductStock.objects.get_or_create(product = Product.objects.get(id=product_id),warehouse = Warehouse.objects.get(id=to_warehouse_id))
        plus_data.stock += int(transfer_stock_data)
        plus_data.save()
        
        context = {"pending_stock": 0}
        if ordered_stock:
            to_warehouse_stock = WarehouseProductStock.objects.filter(product__id = product_id, warehouse__name = "WAREHOUSE 1")
            if to_warehouse_stock.count()>0:
                total_stock = to_warehouse_stock.aggregate(total_stock = Sum("stock"))["total_stock"]
                context["pending_stock"] = max(int(ordered_stock) - total_stock, 0)
        else:
            context["current_stock"] = minus_data.stock
        # plus_data_in_history, history_created = WarehouseProductStockHistory.objects.get_or_create(warehouse__id = to_warehouse_id, product__id = product_id)
        # if history_created:
        #     plus_data_in_history.stock = transfer_stock_data
        #     plus_data_in_history.save()
        # plus_data_in_history.stock = int(avl_stock_history)+int(transfer_stock_data)
        # plus_data_in_history.save()

        # WarehouseProductStockHistory.objects.create(warehouse = Warehouse.objects.get(id=to_warehouse_id), product = Product.objects.get(id=product_id), before_stock=avl_stock_history, affected_stock=transfer_stock_data, stock=final_history_stock)

        stock_history_obj=WarehouseProductStockHistory.objects.filter(product=Product.objects.get(id=product_id),warehouse=Warehouse.objects.get(id=to_warehouse_id)).last()
        stock_new_history_obj=WarehouseProductStockHistory.objects.create(product=Product.objects.get(id=product_id),warehouse=Warehouse.objects.get(id=to_warehouse_id))

        if not stock_history_obj:
            stock_new_history_obj.before_stock=0
            stock_new_history_obj.stock=transfer_stock_data
        else:
            stock_new_history_obj.before_stock=stock_history_obj.stock
            stock_new_history_obj.stock=int(stock_history_obj.stock) + int(transfer_stock_data)
        stock_new_history_obj.affected_stock=transfer_stock_data
        stock_new_history_obj.save()

        return JsonResponse(context, safe=False)

# For maintain history of Manage stock
class WarehouseProuctstockUpdateView(View):
    form_class=WarehouseStockForms
    success_url = reverse_lazy("product:list_product_price")

    def get(self, request):
        product_id=self.request.GET.get('product')
        print('product_id: ', product_id)
        warehouse_id=self.request.GET.get('warehouse')
        print('warehouse_id: ', warehouse_id)

        warehouse_stock = WarehouseProductStock.objects.none()
        context = {}
        if product_id:
            product= Product.objects.filter(id=product_id).last()
            # context["product"] = product

            if product and product.vehicle:
                context["vehicle_id"] = product.vehicle.id
            
            if product and product.product_barcode.all().count() > 0:
                context["barcode"] = product.product_barcode.last().barcode_number
            
            warehouse_stock = WarehouseProductStock.objects.filter(product__id=product_id)
        
        context["available_stock"] = 0
        if warehouse_id:
            # context["warehouse_id"] = warehouse_id
            warehouse_stock = warehouse_stock.filter(warehouse__id=warehouse_id).first()
            context["available_stock"]=warehouse_stock.stock if warehouse_stock else 0
        else:
            total_stock = warehouse_stock.aggregate(total_stock=Sum("stock"))["total_stock"] if warehouse_stock else 0
            context["available_stock"]=total_stock if total_stock else 0
        
        # html = render_to_string("product/warehouse_product_stock_update.html", context, request)
        # context["html"] = html

        # context["product"] = None
        return JsonResponse(context)
   

# Ajax call for To maintain manage stock history    
class UpdateStock(View):
    def post(self,*args, **kwargs):
        product_id=self.request.POST.get('product')
        warehouse_id=self.request.POST.get('warehouse')
        stock_type = self.request.POST.get('stock_type')

        if product_id:
            product = Product.objects.get(id=product_id)
        else:
            return JsonResponse({"error": "Please select the product !!!"})
        
        if warehouse_id:
            warehouse = Warehouse.objects.get(id=warehouse_id)
        else:
            return JsonResponse({"error": "Please select the warehouse !!!"})
        
        piece=int(self.request.POST.get('stock', 0))
        return self.manage_stock_warehouse(product, warehouse, piece, stock_type)


    def manage_stock_warehouse(self, product, warehouse, piece, stock_type):
        stock_obj, created= WarehouseProductStock.objects.get_or_create(product=product,warehouse=warehouse)
        
        if stock_type == "add":
            stock_obj.stock += piece
        else:
            # if not created:
            #     if piece < stock_obj.stock:
            #         stock_obj.ready_for_dispatch = min(stock_obj.ready_for_dispatch, piece)
            stock_obj.stock = piece
        stock_obj.save()

        stock_history_obj=WarehouseProductStockHistory.objects.filter(product=product,warehouse=warehouse).last()
        stock_new_history_obj=WarehouseProductStockHistory.objects.create(product=product,warehouse=warehouse)

        if not stock_history_obj:
            stock_new_history_obj.before_stock=0
            stock_new_history_obj.stock=piece
            affected_stock=piece
        else:
            stock_new_history_obj.before_stock=stock_history_obj.stock
            if stock_type == "add":
                affected_stock=piece
                stock_new_history_obj.stock = stock_history_obj.stock + piece
            else:
                stock_new_history_obj.stock=piece
        
                if piece > stock_history_obj.stock:
                    affected_stock=piece-stock_history_obj.stock
                else:
                    affected_stock=stock_history_obj.stock-piece
        
        stock_new_history_obj.affected_stock=affected_stock

        if product.vehicle:
            stock_new_history_obj.vehicle = product.vehicle
        
        stock_new_history_obj.save()


        # logs
        log_msg = "Product stock has been updated"
        ProductLog.objects.create(
            product=product,
            action_by=self.request.user,
            remark=log_msg,
            warehouse=warehouse,
            before_stock=stock_new_history_obj.before_stock,
            affected_stock=stock_new_history_obj.affected_stock,
            stock=stock_new_history_obj.stock,
        )

        # messages.add_message(self.request, messages.SUCCESS, "Stock Updated Successfully.")
        return JsonResponse({"message": "Stock Updated Successfully.",'stock':stock_obj.stock })
        
    

class ProductCreateFromCSVFormView(CompanyAdminLoginRequiredMixin, FormView):
    template_name = "product/import_product.html"
    form_class = ImportProductCSVForm

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def form_valid(self, form):
        csv_file = self.request.FILES["csv_file"]
        file = csv_file.read()
        csv_file_obj = CSVFile.objects.create(csv_file=csv_file)
        import_product_from_xlsx.delay(file)
        messages.add_message(self.request, messages.SUCCESS, "Product importing process is starting..")
        return HttpResponseRedirect(reverse("product:list_product"))
    
    
        # sourcery skip: extract-method, merge-dict-assign, remove-redundant-pass
        # try:
        #     csv_file = self.request.FILES["csv_file"]
        #     file_data = csv_file.read().decode("utf-8")
        #     lines = file_data.split("\n")
        #     for line in lines[1:]:
        #         fields = line.split(",")
        #         if len(fields) > 25:
        #             data_dict = {}
        #             data_dict["name"] = fields[8]
        #             company = Company.objects.get(company_name=fields[0])
        #             data_dict["company"] = company
        #             category, _ = Category.objects.get_or_create(name=fields[3], company=company)
        #             category.description = fields[4]
        #             category.is_type_a_invoice = str(fields[5]).lower() == "yes"
        #             category.save()
        #             data_dict["category"] = category
        #             sub_category, _ = SubCategory.objects.get_or_create(name=fields[6], company=company, category=category)
        #             sub_category.description = fields[7]
        #             sub_category.save()
        #             data_dict["subcategory"] = sub_category
        #             brand, _ = Brand.objects.get_or_create(name=fields[1], company=company)
        #             brand.description = fields[2]
        #             brand.save()
        #             data_dict["brand"] = brand
        #             vendor, _ = Vendor.objects.get_or_create(email=fields[9], company=company)
        #             data_dict["prefered_vendor"] = vendor
        #             data_dict["is_apply_ml_quantity"] = str(fields[10]).lower() == "yes"
        #             data_dict["ml_quantity"] = fields[11] if data_dict["is_apply_ml_quantity"] else 0
        #             data_dict["is_apply_weight"] = str(fields[12]).lower() == "yes"
        #             data_dict["weight"] = fields[13] if data_dict["is_apply_weight"] else 0
        #             data_dict["box"] = str(fields[16]).lower() == "yes"
        #             data_dict["box_piece"] = fields[17] if data_dict["box"] else 0
        #             data_dict["case"] = str(fields[19]).lower() == "yes"
        #             data_dict["case_piece"] = fields[20] if data_dict["case"] else 0
        #             data_dict["case_upc"] = fields[18]
        #             data_dict["srp"] = fields[21]
        #             data_dict["status"] = "active"
        #             data_dict["re_order_mark"] = fields[22]
        #             data_dict["product_upc"] = fields[14]
        #             data_dict["box_upc"] = fields[15]
        #             data_dict["cost_price"] = fields[23]
        #             # data_dict["box_cost_price"] = fields[25]
        #             # data_dict["case_cost_price"] = fields[24]
        #             data_dict["wholesale_min_price"] = fields[25]
        #             # data_dict["case_wholesale_min_price"] = fields[27]
        #             # data_dict["box_wholesale_min_price"] = fields[28]
        #             data_dict["wholesale_base_price"] = fields[26]
        #             # data_dict["case_wholesale_base_price"] = fields[30]
        #             # data_dict["box_wholesale_base_price"] = fields[31]
        #             data_dict["retail_min_price"] = fields[27]
        #             # data_dict["case_retail_min_price"] = fields[33]
        #             # data_dict["box_retail_min_price"] = fields[34]
        #             data_dict["retail_base_price"] = fields[28]
        #             # data_dict["case_retail_base_price"] = fields[36]
        #             # data_dict["box_retail_base_price"] = fields[37]
        #             data_dict["base_price"] = fields[24]
        #             # data_dict["case_base_price"] = fields[39]
        #             # data_dict["box_base_price"] = fields[40]
        #             product_form = CreateProductCSVForm(data_dict)
        #             if product_form.is_valid():
        #                 instance = product_form.save(commit=False)
        #                 instance.save()
        #             else:
        #                 pass

        #     messages.add_message(self.request, messages.SUCCESS, "Product Uploaded Successfully.")
        #     return HttpResponseRedirect(reverse("product:list_product"))
        # except Exception as e:
        #     import traceback
        #     print("exception::>>...", traceback.format_exc())
        #     messages.add_message(self.request, messages.WARNING, "Something went wrong, Please try again.")
        #     return HttpResponseRedirect(reverse("product:list_product"))


class AddStockFromCSVFormView(CompanyAdminLoginRequiredMixin, FormView):
    template_name = "product/add_stock.html"
    form_class = ImportProductCSVForm

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def form_valid(self, form):
        # sourcery skip: extract-method, merge-dict-assign, move-assign-in-block, remove-redundant-pass
        csv_file = self.request.FILES["csv_file"]
        file = csv_file.read()
        print("➡ file :", file)
        csv_file_obj = CSVFile.objects.create(csv_file=csv_file)
        import_product_stock_from_xlsx.delay(file)
        messages.add_message(self.request, messages.SUCCESS, "Product stock importing process is starting..")
        return HttpResponseRedirect(reverse("product:manage_stocks"))
        # try:
        #     csv_file = self.request.FILES["csv_file"]
        #     file_data = csv_file.read().decode("utf-8")
        #     lines = file_data.split("\n")
        #     for line in lines[1:]:
        #         fields = line.split(",")
        #         data_dict = {}
        #         company = Company.objects.get(company_name=fields[0])
        #         warehouse, _ = Warehouse.objects.get_or_create(name=fields[1], company=company)
        #         data_dict["warehouse"] = warehouse
        #         category = Category.objects.get(name=fields[3], company=company)
        #         product, _ = Product.objects.get_or_create(name=fields[2], company=company, category=category)
        #         data_dict["product"] = product
        #         data_dict["stock"] = fields[4]
        #         stock_form = UpdateStockCSVForm(data_dict)
        #         if stock_form.is_valid():
        #             instance = stock_form.save(commit=False)
        #             instance.save()
        #         else:
        #             pass

        #     messages.add_message(self.request, messages.SUCCESS, "Product Stock Updated Successfully.")
        #     return HttpResponseRedirect(reverse("product:manage_stocks"))
        # except Exception as e:
        #     import traceback
        #     print("exception::>>...", traceback.format_exc())
        #     messages.add_message(self.request, messages.WARNING, "Something went wrong, Please try again.")
        #     return HttpResponseRedirect(reverse("product:manage_stocks"))
    
# List view of History of MAnage stock
class ProdcutStockHistoryListView(SuccessMessageMixin, CompanyAdminLoginRequiredMixin, ListView):
    model = WarehouseProductStockHistory
    template_name = "product/product_stock_history.html"


class ProdcutStockHistoryDataTablesAjaxPagination(DataTableMixin, View):
    model = WarehouseProductStockHistory

    def get_queryset(self):
        qs = WarehouseProductStockHistory.objects.all()

        # if self.request.user.role == "company admin":
        #     qs = WarehouseProductStockHistory.objects.filter(
        #         company__id=self.request.user.get_company_id)

        company = self.request.GET.get("company")
        if company:
            qs = qs.filter(warehouse__company__id=company)
        product = self.request.GET.get("product")
        if product:
            qs = qs.filter(product__id=product)

        warehouse = self.request.GET.get("warehouse")
        if warehouse:
            qs = qs.filter(warehouse__id=warehouse)
        return qs.order_by("-id")
    
    def filter_queryset(self, qs):
        if self.search:
            return qs.filter(
                Q(product__name__icontains=self.search) |
                Q(product__code__icontains=self.search) |
                Q(warehouse__name__icontains=self.search)
            )
        return qs
    
    def _get_ready_for_dispatch(self, obj):
        """Get action buttons w/links."""
        last_stock = WarehouseProductStockHistory.objects.filter(product = obj.product, warehouse = obj.warehouse).order_by("created_at").last()
        product_stock = WarehouseProductStock.objects.filter(product = obj.product, warehouse = obj.warehouse).last()
        if last_stock and obj.id == last_stock.id:
            return f'<div class="d-flex"><input type="number" disabled data-max="{obj.stock}" data-id="{product_stock.id}" id="id_stock-{product_stock.id}" onfocusout="disableInput(this)" class="form-control w-100 update-ready-stock" value="{product_stock.ready_for_dispatch}" /><a href="javascript:void(0)" data-id="{product_stock.id}" class="my-auto ml-2 stock-update" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a></div>'
        else:
            return "-"
    
    def _get_affected_stock(self, obj):
        affected_stock = ""
        if obj.before_stock > obj.stock:
            affected_stock = "- "+str(obj.affected_stock)
        else:
            affected_stock = "+ "+str(obj.affected_stock)

        return affected_stock
    
    def prepare_results(self, qs):
        return [
            {
                'product__code': o.product.code if o.product.code else "-",
                'product': o.product.name,
                'vehicle': o.vehicle.name if o.vehicle else "-",
                'company':o.warehouse.company.company_name,
                'product__brand': o.product.brand.name,
                'warehouse': o.warehouse.name,
                'created_at': o.created_at.date(),
                'before_stock': o.before_stock,
                'affected_stock': self._get_affected_stock(o),
                'stock': o.stock,
                'ready_for_dispatch': self._get_ready_for_dispatch(o),
            }
            
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class StockUpdateAjaxView(View):
    def post(self, request, pk):
        value = request.POST.get("value")

        stock = WarehouseProductStock.objects.filter(id = pk).last()
        if stock:
            stock.ready_for_dispatch = value
            stock.save()
        else:
            return JsonResponse({"level": "error", "message": "Stock not found !!!"}, status=201)

        return JsonResponse({"level": "success", "message": "Stock updated successfully"}, status=200)


class StockFormAjaxView(View):
    template_name = "product/manage_stock_form.html"

    def get(self, request):
        context = {}

        selected_product = request.GET.get("product")
        selected_warehouse = request.GET.get("warehouse")
        stock = request.GET.get("stock")

        context["selected_product"] = json.loads(selected_product) if selected_product else ""
        context["selected_warehouse"] = json.loads(selected_warehouse) if selected_warehouse else ""
        context["stock"] = stock

        if not request.user.is_superuser:
            products = Product.objects.filter(status = Product.ACTIVE, company = request.user.get_company_id)
            warehouses = Warehouse.objects.filter(status = Warehouse.IS_ACTIVE, company = request.user.get_company_id)
        else:
            products = Product.objects.filter(status = Product.ACTIVE)
            warehouses = Warehouse.objects.filter(status = Warehouse.IS_ACTIVE)

        context["products"] = products
        context["warehouses"] = warehouses
        
        context["form"] = StockCreateForm()

        html = render_to_string(self.template_name, context, request)
        # stock = WarehouseProductStock.objects.filter(id = pk).last()

        return JsonResponse({"html": html}, status=200)


class SearchAjaxView(View):
    def get(self, request):
        if request.user.is_superuser:
            company = request.GET.get("company")
        else:
            company = request.user.get_company_id
        
        search = request.GET.get("search")
        model = request.GET.get("model")

        if model == "brand":
            qs = Brand.objects.filter(company__id = company, status = Product.ACTIVE)
        elif model == "vehicle":
            qs = ProductVehicle.objects.filter(company__id = company)
        else:
            qs = None

        if search:
            qs = qs.filter(
                Q(name__icontains = search)
            ).distinct()
            
        data = [{"id": instance.id, "text": instance.name} for instance in qs]
        return JsonResponse({"items": data})


class ProductSearchAjaxView(View):
    def get(self, request):
        company_id = self.request.GET.get("company")
        term = self.request.GET.get("search")

        queryset = Product.objects.filter(company = company_id, status = Product.ACTIVE, brand__status = Brand.ACTIVE)

        if term:
            queryset = queryset.filter(
                Q(name__icontains = term) |
                # Q(genericname__icontains = term) |
                Q(code__icontains = term)
            )

        if company_id:
            queryset = queryset.filter(company__id = company_id)
        
        data = []
        for product in queryset[0:50]:
            data.append({
                "id": product.id, 
                "text": product.name, 
                "brand" : product.brand.name,
                "code" : product.code,
                "vehicle": product.vehicle.name if product.vehicle else ""
            })

        return JsonResponse({"items": data})


class ProductPriceAjaxView(View):
    def get(self, request):
        product_id = self.request.GET.get("product_id")
        price_type = self.request.GET.get("price_type")

        product = Product.objects.filter(id = product_id).last()

        if not product:
            return JsonResponse({"error": "Product not found !!!"})
        
        data = {}
        if price_type == "wholesale":
            data["amount"] = product.wholesale_rate
        elif price_type == "retail":
            data["amount"] = product.retail_rate
        else:
            data["amount"] = product.mrp

        return JsonResponse(data)


#------for csv preview
import csv
from django.http import HttpResponse
from django.shortcuts import render

def preview_csv(request):
    if request.method == 'POST' and request.FILES['csv_file']:
        csvfile = request.FILES['csv_file']
        csv_data = csvfile.read().decode('utf-8')  # Read and decode the uploaded CSV file
        reader = csv.reader(csv_data.splitlines())  # Create a CSV reader object
        rows = list(reader)  # Convert the CSV data into a list of rows

        # Pass the rows to the template for rendering
        context = {'csv_data': rows}
        return render(request, 'preview.html', context)

    return render(request, 'upload.html')
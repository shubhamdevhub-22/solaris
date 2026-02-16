from django.http import JsonResponse
from django.shortcuts import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, TemplateView
from django.contrib.messages.views import SuccessMessageMixin
from app_modules.base.mixins import AdminLoginRequiredMixin, CompanyAdminLoginRequiredMixin
from app_modules.company.forms import CompanyForm, WarehouseForm
from app_modules.company.models import Company, Warehouse
from app_modules.product.models import WarehouseProductStock
from app_modules.company.tasks import set_geocode_for_company, set_geocode_for_warehouse
from app_modules.users.models import User
from django.template.loader import get_template
from django.db.models import Q, Sum
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django_datatables_too.mixins import DataTableMixin
from django.contrib import messages
from utils.helpers import get_geo_code_from_address
from django.template.loader import render_to_string


# Create your views here.


class HomeView(TemplateView):
    template_name = "base.html"

# -------Start------
"""View for Company all operations"""
class CompanyListView(AdminLoginRequiredMixin, ListView):
    template_name = "company/company_list.html"
    model = Company

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company_statuses"] = Company.STATUS_TYPE
        return context

class CompanyListAjax(AdminLoginRequiredMixin, DataTableMixin, View):
    model = Company
    
    def get_queryset(self):
        qs = Company.objects.all()

        company_status = self.request.GET.get("company_status")
        if company_status:
            company_list = list(Company.objects.filter(status = company_status).values_list("id",flat=True))
            qs = qs.filter(id__in = company_list)
        
        return qs.order_by("-id")
        

    def filter_queryset(self, qs):
        if self.search:
            return qs.filter(
                Q(company_name__icontains=self.search) |
                Q(contact_person__icontains=self.search) | 
                Q(email__icontains=self.search) | 
                Q(phone__icontains=self.search) |
                Q(status__icontains=self.search)
            )
        return qs
    
    def _get_actions_buttons(self,obj):

        update_url = reverse("company:update_company", kwargs={"pk": obj.id})
        delete_url = reverse("company:delete_company")
        return f'<center><a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a><a data-id="{obj.id}" data-url="{delete_url}" data-title="{obj.company_name}" class="company-delete text-danger" title="Delete"><i class="ft-trash font-medium-3 mr-2"></i></a></center>'
    
    def _get_status(self,obj):
        t = get_template("company/get_company_status.html")
        return t.render(
            {"company": obj, "request": self.request}
        )
        
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'company_name': o.company_name,
                'contact_person': o.contact_person,
                'email': o.email,
                'phone': o.phone if o.phone else "-----",
                'status':self._get_status(o),
                'actions':self._get_actions_buttons(o),
            }
            for o in qs
        ]



class CompanyCreateView(SuccessMessageMixin,AdminLoginRequiredMixin,CreateView):
    model = Company
    template_name = "company/company_form.html"
    form_class = CompanyForm
    success_message = "Company Added Successfully."
    # success_url = reverse_lazy("company:company_list")


    def form_valid(self, form):
        instance = form.save(commit=False)
        phone = form.cleaned_data['phone']
        if phone:
            instance.phone = f"+91{phone}"
        instance.save()
        latitude = form.cleaned_data["latitude"]
        longitude = form.cleaned_data["longitude"]
        if not latitude and not longitude:
            set_geocode_for_company.delay(instance.id)
        return HttpResponseRedirect(reverse("company:company_list"))
    
class CompanyUpdateView(SuccessMessageMixin,AdminLoginRequiredMixin,UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = "company/company_form.html"
    success_message = "Company Updated Successfully!"
    success_url = reverse_lazy("company:company_list")

    def form_valid(self, form):
        instance = form.save(commit=False)
        phone = form.cleaned_data['phone']
        if phone:
            instance.phone = f"+91{phone}"
        instance.save()
        latitude = form.cleaned_data["latitude"]
        longitude = form.cleaned_data["longitude"]
        if not latitude and not longitude:
            set_geocode_for_company.delay(instance.id)
        return HttpResponseRedirect(reverse("company:company_list"))


class CompanyDeleteView(SuccessMessageMixin, AdminLoginRequiredMixin, View):
    def post(self, request):
        company_id = request.POST.get("company_id")
        Company.objects.filter(id = company_id).delete()
        return JsonResponse({"message": "Company deleted successfully."})
# #--------End-----


# -------Start------
"""View for Warehouse all operations"""
class WarehouseListView(CompanyAdminLoginRequiredMixin,ListView):
    template_name = "company/warehouse_list.html"
    model = Warehouse

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["companies"] = Company.objects.all()
        context["warehouse_statuses"] = Warehouse.STATUS_TYPE
        return context

class WarehouseListAjax(DataTableMixin,View):
    model = Warehouse

    def get_queryset(self):
        qs = Warehouse.objects.all()


        if self.request.user.role == User.COMPANY_ADMIN or self.request.user.role == User.SALES_REPRESENTATIVE:
            company_id = list(self.request.user.company_users.all().values_list("company_id", flat=True))
            company_list = list(Company.objects.filter(id__in=company_id).values_list("id",flat=True))
            qs = qs.filter(company__in=company_list)

        company = self.request.GET.get("company")
        if company:
            warehouse_companies = list(Warehouse.objects.filter(company__in = company).values_list("id",flat=True))

            qs = qs.filter(id__in=warehouse_companies)

        warehouse_status = self.request.GET.get("warehouse_status")
        
        if warehouse_status:
            warehouse_list = list(Warehouse.objects.filter(status = warehouse_status).values_list("id",flat=True))
            qs = qs.filter(id__in = warehouse_list)
        
        return qs.order_by("-id")

    def _get_status(self,obj):
        t = get_template("company/get_warehouse_status.html")
        return t.render(
            {"warehouse": obj, "request": self.request}
        )
    def __get_actions_buttons(self,obj):
        update_url = reverse("company:update_warehouse", kwargs={"pk": obj.id})
        delete_url = reverse("company:warehouse_delete_ajax")
        return f'<center><a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a><label style="cursor: pointer;" data-title="{obj.name}" data-url="{delete_url}" data-id="{obj.id}" title="Delete" class="danger p-0 ajax-delete-btn"><i class="ft-trash font-medium-3"></i></label></center>'

    def filter_queryset(self, qs):
        if self.search:
            return qs.filter(
                Q(name__icontains=self.search) |
                Q(city__icontains=self.search) | 
                Q(state__icontains=self.search) |
                Q(country__icontains=self.search) |
                Q(status__icontains=self.search) |
                Q(company__company_name__icontains=self.search)
            )
        return qs
    
    
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'name': o.name,
                'company': o.company.company_name,
                'address1': o.address_line_1,
                'address2': o.address_line_2,
                'city': o.city,
                'state': o.state,
                'zip_code': o.zip_code,
                'country': o.country,
                'latitude': o.latitude,
                'longitude': o.longitude,
                'status': self._get_status(o),
                'actions':self.__get_actions_buttons(o),
            }
            for o in qs
        ]


class WarehouseCreateView(CompanyAdminLoginRequiredMixin,CreateView):
    model = Warehouse
    form_class = WarehouseForm
    # get form method and pass current user as parameter
    template_name = "company/warehouse_form.html"
    success_url = reverse_lazy("company:warehouse_list")

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.save()
        if self.request.user.role == User.COMPANY_ADMIN:
            instance.company = self.request.user.company_users.first().company
            instance.save()

        latitude = form.cleaned_data["latitude"]
        longitude = form.cleaned_data["longitude"]
        if not latitude and not longitude:
            set_geocode_for_warehouse.delay(instance.id)
            # address1 = form.cleaned_data["address_line_1"]
            # address2 = form.cleaned_data["address_line_2"]
            # city = form.cleaned_data["city"]
            # state = form.cleaned_data["state"]
            # country = form.cleaned_data["country"]
            # location = get_geo_code_from_address(address1, city, state, country)
            # if location:
            #     instance.latitude = location.latitude
            #     instance.longitude = location.longitude
            #     instance.save()
        messages.add_message(self.request, messages.SUCCESS, "Warehouse Added Successfully.")
        return HttpResponseRedirect(reverse("company:warehouse_list"))

class WarehouseUpdateView(SuccessMessageMixin,CompanyAdminLoginRequiredMixin,UpdateView):
    model = Warehouse
    form_class = WarehouseForm
    template_name = "company/warehouse_form.html"
    # success_message = "Warehouse Updated Succefully ."

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs
    
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == User.COMPANY_ADMIN:
            qs = qs.filter(company__id=self.request.user.get_company_id)
        return qs

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.save()
        latitude = form.cleaned_data["latitude"]
        longitude = form.cleaned_data["longitude"]
        if not latitude and not longitude:
            set_geocode_for_warehouse.delay(instance.id)
        # address1 = form.cleaned_data["address_line_1"]
        # address2 = form.cleaned_data["address_line_2"]
        # city = form.cleaned_data["city"]
        # state = form.cleaned_data["state"]
        # country = form.cleaned_data["country"]
        # location = get_geo_code_from_address(address1, city, state, country)
        # if location:
        #     instance.latitude = location.latitude
        #     instance.longitude = location.longitude
        #     instance.save()
        messages.add_message(self.request, messages.SUCCESS, "Warehouse Updated Successfully.")
        return HttpResponseRedirect(reverse("company:warehouse_list"))

    # success_url = reverse_lazy("company:warehouse_list")


class WarehouseDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request):
        warehouse_id = self.request.POST.get("id")
        warehouse_stocks = WarehouseProductStock.objects.filter(warehouse__id = warehouse_id)
        if warehouse_stocks:
            total_stock = warehouse_stocks.aggregate(total_stock = Sum("stock"))["total_stock"]
        else:
            total_stock = 0

        if total_stock <= 0:
            Warehouse.objects.filter(id=warehouse_id).delete()
            return JsonResponse({"level": "success", "message": "Warehouse Deleted Successfully."})
        else:
            return JsonResponse({"level": "error", "message": "Warehouse cannot delete because the stock is exists in the warehouse !!!"})


class GetCompanyWarehouseAjaxView(View):
    template_name = "company/warehouse_select.html"

    def get(self, request, *args, **kwargs):
        context={}
        data={}
        company_id = request.GET['company_id']
        warehouses = Warehouse.objects.filter(company__id=company_id)
        context['warehouse_list'] = warehouses
        data['warehouses']=render_to_string(self.template_name,context,request=request)
        return JsonResponse(data)
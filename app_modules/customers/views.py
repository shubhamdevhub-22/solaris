import json
from django.forms.models import BaseModelForm
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView, View, DetailView, TemplateView, FormView
from app_modules.order.models import Order, OrderBill
from app_modules.customers.models import Customer,CustomerLog, CustomerPaymentBill, MultipleContact, Payment, SalesRoute, PriceLevel, PriceLevelProduct, CustomerBill, CustomerBillingAddress, CustomerShippingAddress, CustomerDocuments, Zone, Discount, MultipleVendorDiscount, Replacement, ReplacementProduct
from django.urls import reverse_lazy, reverse
from app_modules.customers.forms import CustomerCreateForm, CustomerUpdateForm, ImportCustomerCSVForm, MultipleContactForm, PaymentForm, SalesRouteForm, PriceLevelForm, CustomerBillingAddressUpdateForm, CustomerBillingAddressCreateForm, CustomerShippingAddressUpdateForm, CustomerShippingAddressCreateForm, CustomerDocumentForm, CustomerContactForm, ZoneForm, DiscountForm, MultipleVendorDiscountForm, ReplacementForm, ReplacementProductForm
from extra_views import CreateWithInlinesView, InlineFormSetFactory, NamedFormsetsMixin, UpdateWithInlinesView
from django_datatables_too.mixins import DataTableMixin
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import get_template, render_to_string
from app_modules.company.models import Company, CompanyUsers
from app_modules.customers.tasks import import_customer_from_xlsx, import_zone_from_xlsx, set_geocode_for_customer_billing_address, set_geocode_for_customer_shipping_address
from app_modules.users.models import User
from app_modules.base.mixins import SalesLoginRequiredMixin, SalesAccountantLoginRequiredMixin, CompanyAdminLoginRequiredMixin, AccountantLoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from utils.helpers import get_geo_code_from_address
from django.contrib import messages
from django.shortcuts import HttpResponseRedirect
from app_modules.product.models import CSVFile, Product
from django.db.models import Sum
from app_modules.credit_memo.models import CreditMemo
from app_modules.product.models import Brand
from app_modules.utils import order_utils

from num2words import num2words


# Create your views here.

'''views for Customer list'''
class CustomerListView(CompanyAdminLoginRequiredMixin, ListView):
    template_name = "customer/customer_list.html"
    model = Customer

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["companies"] = Company.objects.filter(status='active')
        context["status_choices"] = Customer.STATUS_CHOICES
        if not self.request.user.is_superuser:
            context["customer_zones"] = Zone.objects.filter(company = self.request.user.get_company_id)
        else:
            context["customer_zones"] = Zone.objects.all()
        return context
    
    # def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    #     Customer.objects.all().delete()
    #     return super().get(request, *args, **kwargs)
    
class CustomerDetailsView(CompanyAdminLoginRequiredMixin, DetailView):
    template_name = "customer/customer_detail.html"
    model = Customer

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer_id = self.kwargs.get('pk')
        # context["contactPerson"] = MultipleContact.objects.filter(customer_obj__id=customer_id).first()
        context["due_amount"] = OrderBill.objects.filter(customer__id=customer_id).aggregate(due_amount = Sum("due_amount"))["due_amount"]
        context["store_credit"] = CreditMemo.objects.filter(customer__id=customer_id).count()

        return context


class CustomerBillingLockAjaxView(View):
    def post(self, request):
        value = request.POST.get("value", "")
        customer_id = request.POST.get("customer_id")

        if customer_id:
            customer = Customer.objects.filter(id = customer_id).last()
            if value == "true":
                customer.is_locked = True
            else:
                customer.is_locked = False
            customer.save()
        else:
            return JsonResponse({"level": "error", "message": "Customer not found !!!"})
        
        return JsonResponse({"level": "success", "message": "Customer updated."})



class CustomerAddressListView(SalesAccountantLoginRequiredMixin, ListView):
    template_name = "customer/customer-details/customer_addressinfo_list.html"
    model = CustomerBillingAddress

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        customer_id = self.kwargs.get('pk')
        context["customer_id"] = customer_id
        return context


'''view for billing address'''
class CustomerBillingAddressDataTablesAjaxPagination(DataTableMixin, View):
    model = CustomerBillingAddress

    def get_queryset(self):

        qs = CustomerBillingAddress.objects.all()
        customer_id = self.request.GET.get("id_customer")
        if customer_id:
            qs = CustomerBillingAddress.objects.filter(customer=customer_id)
            return qs.order_by("-id")
    
    def _get_status(self,obj):
        t = get_template("customer/customer-details/default_status.html")
        return t.render(
            {"customer": obj, "request": self.request}
        )
    

    def _get_actions(self, obj):
        """Get action buttons w/links."""
        customer_id = self.request.GET.get("id_customer")
        update_url = reverse("customer:customer_billing_addressinfo_update", kwargs={"pk": obj.id , "customer_id":customer_id})
        delete_url = reverse("customer:customer_billing_addressinfo_delete")
        return f'<center><a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a> <label data-title="{obj.billing_address_line_1}" data-url="{delete_url}" data-id="{obj.id}" title="Delete" id="delete_btn"  class="danger p-0 ajax-delete-btn"><i class="ft-trash font-medium-3"></i></label></center>'


    
    
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'billing_address': [o.billing_address_line_1, o.billing_city, 
                                           o.billing_state, o.billing_country, o.billing_zip_code,
                                           ],
                'is_default': self._get_status(o),
                'actions': self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)

class CustomerBillingAddressInfoCreateView(CompanyAdminLoginRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = "customer/customer-details/billing_addressinfo_create.html"
    form_class = CustomerBillingAddressCreateForm

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        customer_id = self.kwargs.get('pk')
        context["customer_id"] = customer_id
        return context
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        customer_id = self.kwargs.get('pk')
        customer = Customer.objects.get(id=customer_id)

        default = form.cleaned_data["is_default"]
        address_line1 = form.cleaned_data["billing_address_line_1"]
        address_line2 = form.cleaned_data["billing_address_line_2"]
        suite_apartment = form.cleaned_data["billing_suite_apartment"]
        city = form.cleaned_data["billing_city"]
        state = form.cleaned_data["billing_state"]
        country = form.cleaned_data["billing_country"]
        zip_code = form.cleaned_data["billing_zip_code"]
        latitude = form.cleaned_data["billing_latitude"]
        longitude = form.cleaned_data["billing_longitude"]

        if default:
            data = CustomerBillingAddress.objects.filter(customer__id=self.kwargs.get('pk'), is_default=True)
            if data.count() > 0:
                data.update(is_default = False)

        instance.save()
        if not latitude and not longitude:
            set_geocode_for_customer_billing_address.delay(instance.id)
            # if location:
            #     CustomerBillingAddress.objects.create(customer=customer,billing_address_line_1=address_line1, billing_address_line_2=address_line2,
            #                                             billing_suite_apartment=suite_apartment, billing_city=city, billing_state=state,
            #                                             billing_country=country, billing_zip_code=zip_code, billing_latitude=location.latitude,
            #                                             billing_longitude=location.longitude, is_default=default
            #                                             )
            # else:
            #     instance.save()

        messages.add_message(self.request, messages.SUCCESS, "Billing Address Created Successfully.")
        return HttpResponseRedirect(reverse("customer:customer_details", kwargs={'pk':self.kwargs["pk"]}))
        
class CustomerBillingAddressInfoUpdateView(CompanyAdminLoginRequiredMixin, SuccessMessageMixin, UpdateView):
    template_name = "customer/customer-details/billing_addressinfo_update.html"
    model = CustomerBillingAddress
    form_class = CustomerBillingAddressUpdateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["customer_id"] = self.kwargs["customer_id"]
        return context
    
    def form_valid(self, form):
        instance = form.save(commit=False)

        default = form.cleaned_data["is_default"]
        address_line1 = form.cleaned_data["billing_address_line_1"]
        address_line2 = form.cleaned_data["billing_address_line_2"]
        suite_apartment = form.cleaned_data["billing_suite_apartment"]
        city = form.cleaned_data["billing_city"]
        state = form.cleaned_data["billing_state"]
        country = form.cleaned_data["billing_country"]
        zip_code = form.cleaned_data["billing_zip_code"]
        latitude = form.cleaned_data["billing_latitude"]
        longitude = form.cleaned_data["billing_longitude"]
        
        if default:
            data = CustomerBillingAddress.objects.filter(customer=instance.customer, is_default=True)
            if data.count() > 0:
                data.update(is_default = False)

        instance.save()
        if longitude and latitude is None:
            set_geocode_for_customer_billing_address.delay(instance.id)
            # if location:
            #     CustomerBillingAddress.objects.update(customer=instance.customer,billing_address_line_1=address_line1, billing_address_line_2=address_line2,
            #                                             billing_suite_apartment=suite_apartment, billing_city=city, billing_state=state,
            #                                             billing_country=country, billing_zip_code=zip_code, billing_latitude=location.latitude,
            #                                             billing_longitude=location.longitude, is_default=default
            #                                             )
            # else:
            #     instance.save()
        

        messages.add_message(self.request, messages.SUCCESS, "Billing Address Updated Successfully.")
        return HttpResponseRedirect(reverse("customer:customer_details", kwargs={'pk':self.kwargs["customer_id"]}))
 
class CustomerBillingAddressInfoDeleteAjaxView(LoginRequiredMixin, SuccessMessageMixin, View):
    def post(self, request):
        billing_id = self.request.POST.get("id")
        if CustomerBillingAddress.objects.filter(id=billing_id, is_default=False):
            CustomerBillingAddress.objects.filter(id=billing_id).delete()
            return JsonResponse({"message": "Billing Address Deleted Successfully.", "message_type": "success"})
        return JsonResponse({"message": "Default Address does'nt Deleted.", "message_type": "error"})
        
    
'''view for shipping address'''
class CustomerShippingAddressDataTablesAjaxPagination(DataTableMixin, View):
    model = CustomerShippingAddress

    def get_queryset(self):
        qs = CustomerShippingAddress.objects.all()
        customer_id = self.request.GET.get("id_customer")
        if customer_id:
            qs = CustomerShippingAddress.objects.filter(customer=customer_id)
            return qs.order_by("-id")
    
    def _get_status(self,obj):
        t = get_template("customer/customer-details/default_status.html")
        return t.render(
            {"customer": obj, "request": self.request}
        )
    

    def _get_actions(self, obj):
        """Get action buttons w/links."""
        customer_id = self.request.GET.get("id_customer")
        update_url = reverse("customer:customer_shipping_addressinfo_update", kwargs={"pk": obj.id, "customer_id":customer_id})
        delete_url = reverse("customer:customer_shipping_addressinfo_delete")
        return f'<center><a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a> <label data-title="{obj.shipping_address_line_1}" data-url="{delete_url}" data-id="{obj.id}" title="Delete" id="delete_btn"  class="danger p-0 ajax-delete-btn"><i class="ft-trash font-medium-3"></i></label></center>'


    
    
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'shipping_address': [o.shipping_address_line_1, o.shipping_city, 
                                           o.shipping_state, o.shipping_country, o.shipping_zip_code,
                                           ],
                'is_default': self._get_status(o),
                'actions': self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)
    
class CustomerShippingAddressInfoCreateView(CompanyAdminLoginRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = "customer/customer-details/shippinging_addressinfo_create.html"
    form_class = CustomerShippingAddressCreateForm

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        customer_id = self.kwargs.get('pk')
        context["customer_id"] = customer_id
        return context
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        customer_id = self.kwargs.get('pk')
        customer = Customer.objects.get(id=customer_id)

        # get_geo_code_for_address.delay(instance)
        default = form.cleaned_data["is_default"]
        address_line1 = form.cleaned_data["shipping_address_line_1"]
        address_line2 = form.cleaned_data["shipping_address_line_2"]
        suite_apartment = form.cleaned_data["shipping_suite_apartment"]
        city = form.cleaned_data["shipping_city"]
        state = form.cleaned_data["shipping_state"]
        country = form.cleaned_data["shipping_country"]
        zip_code = form.cleaned_data["shipping_zip_code"]
        latitude = form.cleaned_data["shipping_latitude"]
        longitude = form.cleaned_data["shipping_longitude"]

        if default:
            data = CustomerShippingAddress.objects.filter(customer__id=self.kwargs.get('pk'), is_default=True)
            if data.count() > 0:
                data.update(is_default = False)

        instance.save()
        if longitude and latitude is None:
            set_geocode_for_customer_shipping_address(instance.id)
            # if location:
            #     CustomerShippingAddress.objects.create(customer=customer,shipping_address_line_1=address_line1, shipping_address_line_2=address_line2,
            #                                             shipping_suite_apartment=suite_apartment, shipping_city=city, shipping_state=state,
            #                                             shipping_country=country, shipping_zip_code=zip_code, shipping_latitude=location.latitude,
            #                                             shipping_longitude=location.longitude, is_default=default
            #                                             )
            # else:
            #     instance.save()

        messages.add_message(self.request, messages.SUCCESS, "Shipping Address Created Successfully.")
        return HttpResponseRedirect(reverse("customer:customer_details", kwargs={'pk':self.kwargs["pk"]}))
        
class CustomerShippingAddressInfoUpdateView(CompanyAdminLoginRequiredMixin, SuccessMessageMixin, UpdateView):
    template_name = "customer/customer-details/shipping_addressinfo_update.html"
    model = CustomerShippingAddress
    form_class = CustomerShippingAddressUpdateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["customer_id"] = self.kwargs["customer_id"]
        return context
    
    def form_valid(self, form):
        instance = form.save(commit=False)

        default = form.cleaned_data["is_default"]
        address_line1 = form.cleaned_data["shipping_address_line_1"]
        address_line2 = form.cleaned_data["shipping_address_line_2"]
        suite_apartment = form.cleaned_data["shipping_suite_apartment"]
        city = form.cleaned_data["shipping_city"]
        state = form.cleaned_data["shipping_state"]
        country = form.cleaned_data["shipping_country"]
        zip_code = form.cleaned_data["shipping_zip_code"]
        latitude = form.cleaned_data["shipping_latitude"]
        longitude = form.cleaned_data["shipping_longitude"]
        
        if default:
            data = CustomerShippingAddress.objects.filter(customer=instance.customer, is_default=True)
            if data.count() > 0:
                data.update(is_default = False)
        
        instance.save()    
        if longitude and latitude is None:
            set_geocode_for_customer_shipping_address(instance.id)
            # if location:
            #     CustomerShippingAddress.objects.update(customer=instance.customer,shipping_address_line_1=address_line1, shipping_address_line_2=address_line2,
            #                                             shipping_suite_apartment=suite_apartment, shipping_city=city, shipping_state=state,
            #                                             shipping_country=country, shipping_zip_code=zip_code, shipping_latitude=location.latitude,
            #                                             shipping_longitude=location.longitude, is_default=default
            #                                             )
            # else:
            #     instance.save()

        messages.add_message(self.request, messages.SUCCESS, "Shipping Address Updated Successfully.")
        return HttpResponseRedirect(reverse("customer:customer_details", kwargs={'pk':self.kwargs["customer_id"]}))
    
class CustomerShippingAddressInfoDeleteAjaxView(LoginRequiredMixin, SuccessMessageMixin, View):
    def post(self, request):
        shipping_id = self.request.POST.get("id")
        if CustomerShippingAddress.objects.filter(id=shipping_id, is_default=False):
            CustomerShippingAddress.objects.filter(id=shipping_id).delete()
            return JsonResponse({"message": "Shipping Address Deleted Successfully.", "message_type": "success"})
        return JsonResponse({"message": "Default Address does'nt Deleted.", "message_type": "error"})
        

'''view for documents'''
class UploadDocumentsCreateView(SuccessMessageMixin, SalesAccountantLoginRequiredMixin, CreateView):
    template_name="customer/customer-details/upload_document.html"
    form_class = CustomerDocumentForm

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        customer_id = self.kwargs.get('pk')
        context["customer_id"] = customer_id
        return context
    
    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["id_customer"] = self.kwargs["pk"]
        return form_kwargs    
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.save()
        messages.add_message(self.request, messages.SUCCESS, "Document Upload Successfully.")
        return HttpResponseRedirect(reverse("customer:customer_details", kwargs={'pk':self.kwargs["pk"]}))
    
class UploadDocumentsUpdateView(SuccessMessageMixin, SalesAccountantLoginRequiredMixin, UpdateView):
    template_name = "customer/customer-details/upload_document.html"
    model = CustomerDocuments
    form_class = CustomerDocumentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["customer_id"] = self.kwargs["customer_pk"]
        return context

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["id_customer"] = self.kwargs["customer_pk"]
        return form_kwargs 
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.save()
        messages.add_message(self.request, messages.SUCCESS, "Document Update Successfully.")
        return HttpResponseRedirect(reverse("customer:customer_details", kwargs={'pk':self.kwargs["customer_pk"]}))

class CustomerDocumentsListView(SalesAccountantLoginRequiredMixin, ListView):
    template_name = "customer/customer-details/customer_documentsinfo_list.html"
    model = CustomerDocuments

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        customer_id = self.kwargs.get('pk')
        context["customer_id"] = customer_id
        return context

class CustomerDocumentsDataTablesAjaxPagination(DataTableMixin, View):
    model = CustomerDocuments

    def get_queryset(self):

        qs = CustomerDocuments.objects.all()
        customer_id = self.request.GET.get("id_customer")
        if customer_id:
            qs = CustomerDocuments.objects.filter(customer__id=customer_id)
            return qs.order_by("-id")
        
    def _get_document(self, obj):
        t = get_template("customer/customer-details/document_file_view.html")
        return t.render(
            {"document": obj.document, "request": self.request}
        )

    def _get_actions(self, obj):
        """Get action buttons w/links."""
        customer_id = self.request.GET.get("id_customer")
        update_url = reverse("customer:customer_document_update", kwargs={'pk':obj.id, 'customer_pk':customer_id})
        delete_url = reverse("customer:customer_document_delete")
        return f'<center>  <a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a>  <label data-title="{obj.document_name}" data-url="{delete_url}" data-id="{obj.id}" title="Delete" class="danger p-0 ajax-document-delete-btn cursor-pointer"><i class="ft-trash font-medium-3"></i></label></center>'

    
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'docuemnt_name':o.document_name,
                'document': self._get_document(o),
                'actions': self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)
    
class CustomerDocumentDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request):
        document_id = request.POST.get("id")
        CustomerDocuments.objects.filter(id=document_id).delete()
        return JsonResponse({"message": "Document Deleted Successfully."})


'''view for contact'''
class CustomerContactCreateView(SalesAccountantLoginRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = "customer/customer-details/contact.html"
    form_class = CustomerContactForm

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        customer_id = self.kwargs.get('pk')
        context["customer_id"] = customer_id
        return context

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["id_customer"] = self.kwargs["pk"]
        return form_kwargs    
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        
        default = form.cleaned_data["is_default"]
        if default:
            data = MultipleContact.objects.filter(customer_obj__id=self.kwargs.get('pk'), is_default=True).first()
            if data:
                if data.is_default:
                    data.is_default = False
                    data.save()

        instance.save()
        messages.add_message(self.request, messages.SUCCESS, "Contact details Added Successfully.")
        return HttpResponseRedirect(reverse("customer:customer_details", kwargs={'pk':self.kwargs["pk"]}))

class CustomerContactUpdateView(SalesAccountantLoginRequiredMixin, SuccessMessageMixin, UpdateView):
    template_name = "customer/customer-details/contact.html"
    model = MultipleContact
    form_class = CustomerContactForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["customer_id"] = self.kwargs["customer_pk"]
        return context

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["id_customer"] = self.kwargs["customer_pk"]
        return form_kwargs 
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        phone = form.cleaned_data['mobile_no']
        instance.mobile_no = f"+91{phone}" if phone else ""
        
        default = form.cleaned_data["is_default"]
        if default:
            data = MultipleContact.objects.filter(customer_obj=instance.customer_obj, is_default=True).first()
            if data:
                if data.is_default:
                    data.is_default = False
                    data.save()

        instance.save()
        messages.add_message(self.request, messages.SUCCESS, "Contact details Update Successfully.")
        return HttpResponseRedirect(reverse("customer:customer_details", kwargs={'pk':self.kwargs["customer_pk"]}))
    
class CustomerContactListView(SalesAccountantLoginRequiredMixin, SuccessMessageMixin, ListView):
    template_name = "customer/customer-details/customer_contactsinfo_list.html"
    model = MultipleContact

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        customer_id = self.kwargs.get('pk')
        context["customer_id"] = customer_id
        return context
    
class CustomerContactDataTableAjaxPagination(DataTableMixin, View):
    model = MultipleContact

    def get_queryset(self):
        qs = MultipleContact.objects.all()
        customer_id = self.request.GET.get("id_customer")
        if customer_id:
            qs = MultipleContact.objects.filter(customer_obj__id=customer_id)
            return qs.order_by("-id")
        
    def _get_actions(self, obj):
        """Get action buttons w/links."""
        customer_id = self.request.GET.get("id_customer")
        update_url = reverse("customer:customer_contact_update", kwargs={'pk':obj.id, 'customer_pk':customer_id})
        delete_url = reverse("customer:customer_contact_delete")
        return f'<center>  <a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a>  <label data-title="{obj.contact_person}" data-url="{delete_url}" data-id="{obj.id}" title="Delete" id="delete_btn"  class="danger p-0 ajax-contact-delete-btn"><i class="ft-trash font-medium-3"></i></label></center>'

    def _get_status(self, obj):
        t = get_template("customer/customer_status.html")
        return t.render(
            {"default": obj.is_default, "request": self.request}
        )
        
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'contact_person': o.contact_person,
                'email': o.email,
                'mobile_no': o.mobile_no,
                'is_default': self._get_status(o),
                'actions': self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)

class CustomerContactDeleteAjaxView(LoginRequiredMixin, SuccessMessageMixin, View):
     def post(self, request):
        contact_id = request.POST.get("id")
        MultipleContact.objects.filter(id=contact_id).delete()
        return JsonResponse({"message": "Contact details Deleted Successfully."})

'''view for credit memo'''
class CustomerCreditMemoListView(CompanyAdminLoginRequiredMixin, SuccessMessageMixin, ListView):
    template_name = "customer/customer-details/customer_creditmemo_list.html"
    model = CreditMemo

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        customer_id = self.kwargs.get('pk')
        context["customer_id"] = customer_id
        return context
    
class CustomerCreditMemoDataTableAjaxPagination(DataTableMixin, View):
    model = CreditMemo

    def get_queryset(self):
        qs = CreditMemo.objects.all()
        customer_id = self.request.GET.get("id_customer")
        if customer_id:
            qs = CreditMemo.objects.filter(customer__id=customer_id)
            return qs.order_by("-id")
        
    def _get_actions(self, obj):
        """Get action buttons w/links."""
        customer_id = self.request.GET.get("id_customer")
        detail_url = reverse("credit_memo:credit_memo_detail", kwargs={'pk':obj.id,})
        return f'<center>  <a href="{detail_url}" title="Detail"><i class="ft-eye font-medium-3 mr-2"></i></a></center>'

    def _get_status(self, obj):
        t = get_template("customer/customer_status.html")
        return t.render(
            {"status": obj.status, "request": self.request}
        )

        
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'credit_type': o.credit_type,
                'date': f'{o.date.strftime("%-d %B, %Y")}',
                'status': self._get_status(o),
                'grand_total': o.grand_total,
                'added_by':str(o.added_by),
                'actions': self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)

'''view for order'''
class CustomerOrderListView(SalesAccountantLoginRequiredMixin, SuccessMessageMixin, ListView):
    template_name = "customer/customer-details/customer_order_list.html"
    model = Order

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        customer_id = self.kwargs.get('pk')
        context["customer_id"] = customer_id
        return context
    
class CustomerOrderDataTableAjaxPagination(DataTableMixin, View):
    model = Order

    def get_queryset(self):
        customer_id = self.request.GET.get("id_customer")
        if customer_id:
            qs = Order.objects.filter(customer__id=customer_id)
            return qs.order_by("-id")
        
    def _get_actions(self, obj):
        """Get action buttons w/links."""
        customer_id = self.request.GET.get("id_customer")
        detail_url = reverse("order:order_detail", kwargs={'pk':obj.id})
        return f'<center>  <a href="{detail_url}" title="Detail"><i class="ft-eye font-medium-3 mr-2"></i></a></center>'
    
    def _get_status(self, obj):
        t = get_template("customer/customer_status.html")
        return t.render(
            {"status": obj.status, "request": self.request}
        )
        
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'order_date': f'{o.order_date.strftime("%-d %B, %Y")}',
                'status': self._get_status(o),
                'item_total': o.get_item_count,
                'total_amount': o.get_total_amount,
                'paid_amount': o.get_paid_amount,
                'due_amount': o.get_due_amount,
                'actions': self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


'''view for replacement'''
class CustomerReplacementListView(SalesAccountantLoginRequiredMixin, SuccessMessageMixin, ListView):
    template_name = "customer/customer-details/customer_replacement_list.html"
    model = Replacement

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        customer_id = self.kwargs.get('pk')
        context["customer_id"] = customer_id
        return context


class CustomerReplacementDataTableAjaxPagination(DataTableMixin, View):
    model = Replacement

    def get_queryset(self):
        customer_id = self.request.GET.get("id_customer")
        if customer_id:
            qs = Replacement.objects.filter(customer__id=customer_id)
            return qs.order_by("-id")
        
    def _get_actions(self, obj):
        """Get action buttons w/links."""
        
        detail_url = reverse("customer:replacement_update", kwargs={'pk':obj.id})
        return f'<center>  <a href="{detail_url}" title="Detail"><i class="ft-eye font-medium-3 mr-2"></i></a></center>'
        
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'replace_id': o.replace_id if o.replace_id else "-",
                'created_at': f'{o.created_at.strftime("%-d %B, %Y")}',
                'return_type': o.return_type,
                'replacement_total': float(o.get_replacement_total),
                'actions': self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class LedgerDataTableAjaxPagination(LoginRequiredMixin, DataTableMixin,View):
    model= OrderBill
    
    def get_queryset(self):
        customer = self.request.GET.get("customer")
        
        qs = OrderBill.objects.all()

        company_obj = self.request.user.company
        if not self.request.user.role == User.COMPANY_ADMIN:
            qs = qs.filter(customer__company = company_obj)

        elif self.request.user.role == User.SALES_REPRESENTATIVE:
            qs = qs.filter(customer__sales_rep__id = self.request.user.id)
        
        if customer:
            qs = qs.filter(customer__id=customer)
            
        return qs.order_by("-id")

    def _get_status(self,obj):
        t = get_template("customer/customer_status.html")
        return t.render(
            {"status": obj.status , "request": self.request}
        )

    def filter_queryset(self, qs):
        if self.search:
            return qs.filter(
                Q(bill_amount__icontains=self.search) |
                Q(bill_no__icontains=self.search)
            )
        return qs
    
    def get_customer_details(self, obj):
        t = get_template("reports/report_customer_details.html")
        return t.render(
            {"customer_id": obj.customer}
        )
    
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'bill_id': o.bill_id,
                'company': str(o.customer.company),
                'bill_date': o.bill_date.strftime("%d %B, %Y") if o.bill_date else "-",
                'bill_amount': o.bill_amount,
                'paid_amount': o.paid_amount,
                'due_amount': o.due_amount,
                'status': self._get_status(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class CustomerLedgerListView(AccountantLoginRequiredMixin, SuccessMessageMixin, ListView):
    template_name = "customer/customer-details/customer_ledger_list.html"
    model = Payment

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        customer_id = self.kwargs.get('pk')
        context["customer_id"] = customer_id
        return context


'''view for payment history'''    
class CustomerPaymentHistoryListView(AccountantLoginRequiredMixin, SuccessMessageMixin, ListView):
    template_name = "customer/customer-details/customer_payment_history_list.html"
    model = Payment

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        customer_id = self.kwargs.get('pk')
        context["customer_id"] = customer_id
        return context
    

class CustomerPaymentHistoryDataTableAjaxPagination(DataTableMixin, View):
    model = CustomerPaymentBill

    def get_queryset(self):
        customer_id = self.request.GET.get("id_customer")
        if customer_id:
            qs = CustomerPaymentBill.objects.filter(customer_bill__customer__id=customer_id)
            return qs.order_by("-id")
        
    def _get_actions(self, obj):
        """Get action buttons w/links."""
        customer_id = self.request.GET.get("id_customer")
        detail_url = reverse("customer:payment_history_detail", kwargs={'pk':obj.customer_payment.id})
        return f'<center>  <a href="{detail_url}" title="Detail"><i class="ft-eye font-medium-3 mr-2"></i></a></center>'
        
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'entry_date': f'{o.customer_payment.entry_date.strftime("%-d %B, %Y")}',
                'payment_mode': o.customer_payment.payment_mode.title(),
                'count': o.customer_payment.get_order_count,
                'amount': o.amount,
                'actions': self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)
    
class PaymentHistoryDetailsView(AccountantLoginRequiredMixin, DetailView):
    model = Payment
    template_name="customer/customer-details/payment_history_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment_history_id=self.kwargs['pk']
        customer_id = Payment.objects.filter(id=payment_history_id).values('customer_name').first()
        due_amount = OrderBill.objects.filter(customer__id=customer_id['customer_name']).aggregate(total_due_amount=Sum("due_amount"))
        total_due_amount = due_amount ['total_due_amount']
        context["total_due_amount"] = total_due_amount

        paid_amount = OrderBill.objects.filter(customer__id=customer_id['customer_name']).aggregate(total_paid_amount=Sum("paid_amount"))
        total_paid_amount = paid_amount ['total_paid_amount']
        context["total_paid_amount"] = total_paid_amount


        return context

'''views for customer'''
class CustomerDataTablesAjaxPagination(DataTableMixin,View):
    model= Customer
    
    def get_queryset(self):  # sourcery skip: extract-duplicate-method

        #----- dropdown filteration -----
        company = self.request.GET.get("company")
        status_choice = self.request.GET.get("status")
        zone = self.request.GET.get("zone")
        
        if self.request.user.is_superuser:
            qs = Customer.objects.all()
        else:
            company_id = self.request.user.get_company_id
            if self.request.user.role == User.SALES_REPRESENTATIVE:
                qs = Customer.objects.filter(company__id=company_id, sales_rep__id=self.request.user.id)
            else:
                qs = Customer.objects.filter(company__id=company_id)
        
        if zone:
            qs = qs.filter(zone__id = zone)

        if company:
            company_users = Customer.objects.filter(company__company_name=company)
            qs = qs.filter(id__in=company_users)
            if status_choice:
                status_customer = Customer.objects.filter(status=status_choice)
                qs = qs.filter(id__in=status_customer)
                return qs.order_by("-id")
            return qs
        if status_choice:
            status_customer = Customer.objects.filter(status=status_choice)
            qs = qs.filter(id__in=status_customer)
            return qs.order_by("-id")
        # ---end---

        return qs.order_by("-id")
    
    def _get_status(self,obj):
        t = get_template("customer/customer_status.html")
        return t.render(
            {"status": obj.status , "request": self.request}
        )
    
    

    def _get_actions(self, obj):
        """Get action buttons w/links."""
        update_url = reverse("customer:customer_update", kwargs={"pk": obj.id})
        delete_url = reverse("customer:customer_delete")
        detail_url = reverse("customer:customer_details", kwargs={"pk": obj.id})
        logs_url = reverse("customer:customer_log_ajax", kwargs={"pk": obj.id})
        return f'<div class="row"><center> <label data-title="{obj.customer_name}" data-id="{obj.id}" data-url="{logs_url}" title="Delete" data-toggle="modal" data-target="#default" class="danger p-0 mr-2 customer-log-history-btn"><i class="ft-clock font-medium-3" style="color: #975AFF;"></i></label> <a href="{detail_url}" title="Detail" class="customer-detail-btn" ><i class="ft-eye font-medium-3 mr-2" ></i></a> <a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a>  <label data-title="{obj.customer_name}" data-url="{delete_url}" data-id="{obj.id}" title="Delete" id="delete_btn"  class="danger p-0 ajax-delete-btn"><i class="ft-trash font-medium-3"></i></label></center></div>'


    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        # If a search term, filter the query
        if self.search:
            return qs.filter(
                Q(customer_name__icontains=self.search) |
                Q(customer_type__icontains=self.search)
            )
        return qs
    
    def _get_billing_block(self, obj):
        if obj.is_locked:
            return f'<div class="text-center"><label class="switch"><input type="checkbox" checked data-id="{obj.id}" class="lock-switch"><span class="slider round"></span></label></div>'
        else:
            return f'<div class="text-center"><label class="switch"><input type="checkbox" data-id="{obj.id}" class="lock-switch"><span class="slider round"></span></label></div>'

    def _get_due_amount(self, obj):
        customer_bills = OrderBill.objects.filter(customer__id=obj.id)
        total_due_amount = 0

        if customer_bills:
            total_due_amount = customer_bills.aggregate(total_due_amount=Sum("due_amount"))['total_due_amount']
        return total_due_amount

    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'customer_name': o.customer_name ,
                'area': o.area.title() if o.area else "-",
                'zone': o.zone.zone_code if o.zone else "-",
                'due_amount': self._get_due_amount(o),
                'customer_type': o.customer_type.title() if o.customer_type else "-",
                'is_locked': self._get_billing_block(o),
                # 'company': str(o.company), 
                'status': self._get_status(o),
                'actions': self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)    
    
class MultipleContactInline(InlineFormSetFactory):
    model = MultipleContact
    form_class = MultipleContactForm
    factory_kwargs = {"extra": 1, "min_num": 0, "validate_min": False}

class MultipleVendorDiscountInline(InlineFormSetFactory):
    model = MultipleVendorDiscount
    form_class = MultipleVendorDiscountForm
    factory_kwargs = {"extra": 1, "min_num": 0, "validate_min": False}

class CustomerCreateView(SuccessMessageMixin, CompanyAdminLoginRequiredMixin, NamedFormsetsMixin, CreateView):
    template_name = "customer/customer_create.html"
    model = Customer
    form_class = CustomerCreateForm

    # inlines = [MultipleContactInline, MultipleVendorDiscountInline]    
    # inlines_names = ["multiplecontacts", "multipleVendorDiscounts"]

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.request.user.is_superuser:
            context["brands"] = Brand.objects.filter(company__id = self.request.user.get_company_id).order_by("id")
            context["discounts"] = Discount.objects.filter(company__id = self.request.user.get_company_id)
        return context
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        phone_1 = form.cleaned_data['phone_1']
        instance.phone_1 = f"{phone_1}" if phone_1 else ""
        phone_2 = form.cleaned_data['phone_2']
        instance.phone_2 = f"{phone_2}" if phone_2 else ""
        mobile = form.cleaned_data['mobile']
        instance.mobile = f"{mobile}"
        instance.save()

        is_locked = form.data["is_locked"]
        if is_locked == "lock":
            instance.is_locked = True
        else:
            instance.is_locked = False
        instance.save()

        if self.request.user.role == User.SALES_REPRESENTATIVE:
            instance.sales_rep=self.request.user
            instance.company = self.request.user.company_users.first().company
            instance.save()
        
        order_utils.add_customer_discounts(form, instance)

        # for formset in inlines:
        #     formset.save()

        # document_name = form.cleaned_data["document_name"]
        # document = form.cleaned_data["document"]
        # CustomerDocuments.objects.create(customer=instance, document_name=document_name, document=document)

        billing_address1 = form.cleaned_data["billing_address_line_1"]
        billing_address2 = form.cleaned_data["billing_address_line_2"]
        billing_suite_apartment = form.cleaned_data["billing_suite_apartment"]

        shipping_address1 = form.cleaned_data["shipping_address_line_1"]
        shipping_address2 = form.cleaned_data["shipping_address_line_2"]
        shipping_suite_apartment = form.cleaned_data["shipping_suite_apartment"]

        billing_city = form.cleaned_data["billing_city"]
        billing_state = form.cleaned_data["billing_state"]
        billing_country = form.cleaned_data["billing_country"]
        billing_zip_code = form.cleaned_data["billing_zip_code"]
        
        shipping_city = form.cleaned_data["shipping_city"]
        shipping_state = form.cleaned_data["shipping_state"]
        shipping_country = form.cleaned_data["shipping_country"]
        shipping_zip_code = form.cleaned_data["shipping_zip_code"]
        
        billing_location = get_geo_code_from_address(billing_address1, billing_city, billing_state, billing_country)
        if billing_location:
            CustomerBillingAddress.objects.create(customer=instance, billing_address_line_1=billing_address1, 
                                                billing_address_line_2=billing_address2, billing_address_line_3=billing_suite_apartment,
                                                billing_city=billing_city, billing_state=billing_state, billing_country=billing_country, 
                                                billing_zip_code=billing_zip_code, billing_latitude=billing_location.get("lat"), billing_longitude=billing_location.get("lng"), is_default = True
                                                )
        billing_address =  CustomerBillingAddress.objects.create(customer=instance, billing_address_line_1=billing_address1, 
            billing_address_line_2=billing_address2, billing_address_line_3=billing_suite_apartment,
            billing_city=billing_city, billing_state=billing_state, billing_country=billing_country, 
            billing_zip_code=billing_zip_code, is_default = True
        )
        set_geocode_for_customer_billing_address.delay(billing_address.id)
            
            
        shipping_location = get_geo_code_from_address(shipping_address1, shipping_city, shipping_state, shipping_country)
        if shipping_location:
            CustomerShippingAddress.objects.create(customer=instance, shipping_address_line_1=shipping_address1, shipping_address_line_2=shipping_address2, 
                                                shipping_address_line_3=shipping_suite_apartment, shipping_city=shipping_city, shipping_state=shipping_state,
                                                shipping_country=shipping_country, shipping_zip_code=shipping_zip_code, shipping_latitude=shipping_location.get("lat"), shipping_longitude=shipping_location.get("lng"), is_default = True)
        
        shipping_address = CustomerShippingAddress.objects.create(customer=instance, shipping_address_line_1=shipping_address1, shipping_address_line_2=shipping_address2, 
            shipping_address_line_3=shipping_suite_apartment, shipping_city=shipping_city, shipping_state=shipping_state,
            shipping_country=shipping_country, shipping_zip_code=shipping_zip_code, is_default = True
        )
        set_geocode_for_customer_shipping_address.delay(shipping_address.id)

        messages.add_message(self.request, messages.SUCCESS, "Customer Created Successfully.")
        return HttpResponseRedirect(reverse("customer:customer_list"))
    

    def form_invalid(self, form):
        return super().form_invalid(form)


class UpdateMultipleContactInline(InlineFormSetFactory):
    model = MultipleContact
    form_class = MultipleContactForm
    factory_kwargs = {"extra": 1, "min_num": 0, "validate_min": False}

class UpdateMultipleVendorDiscountInline(InlineFormSetFactory):
    model = MultipleVendorDiscount
    form_class = MultipleVendorDiscountForm
    factory_kwargs = {"extra": 1, "min_num": 0, "validate_min": False}


class CustomerUpdateView(SuccessMessageMixin, CompanyAdminLoginRequiredMixin, NamedFormsetsMixin, UpdateView):
    template_name = "customer/customer_update.html"
    model = Customer
    form_class = CustomerUpdateForm

    # inlines = [UpdateMultipleContactInline, UpdateMultipleVendorDiscountInline]    
    # inlines_names = ["multiplecontacts", "multipleVendorDiscounts"]

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        form_kwargs["customer_id"] = self.object.id
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["companies"] = Company.objects.filter(status='active')

        if not self.request.user.is_superuser:
            context["brands"] = Brand.objects.filter(company__id = self.request.user.get_company_id)
            context["discounts"] = Discount.objects.filter(company__id = self.request.user.get_company_id)

        customer_discounts = MultipleVendorDiscount.objects.filter(customer = self.object).order_by("brand__id")

        data = {}
        data["customer_discounts"] = customer_discounts

        if not self.request.user.is_superuser:
            discounts = Discount.objects.filter(company = self.request.user.get_company_id)
            data["discounts"] = discounts

        context["discount_table"] = render_to_string("customer/discount/customer-discount-table.html", data, self.request)
        return context

    def form_valid(self, form):
        instance = form.save(commit=False)
        # phone_1 = form.cleaned_data['phone_1']
        # instance.phone_1 = f"+91{phone_1}"  if phone_1 else ""
        # phone_2 = form.cleaned_data['phone_2']
        # instance.phone_2 = f"+91{phone_2}"  if phone_2 else ""
        # mobile = form.cleaned_data['mobile']
        # instance.mobile = f"+91{mobile}"

        phone_1 = form.cleaned_data['phone_1']
        instance.phone_1 = f"{phone_1}"  if phone_1 else ""
        phone_2 = form.cleaned_data['phone_2']
        instance.phone_2 = f"{phone_2}"  if phone_2 else ""
        mobile = form.cleaned_data['mobile']
        instance.mobile = f"{mobile}"

        is_locked = form.data["is_locked"]
        if is_locked == "lock":
            instance.is_locked = True
        else:
            instance.is_locked = False
        instance.save()

        if self.request.user.role == User.SALES_REPRESENTATIVE:
            instance.sales_rep=User.objects.get(id=self.request.user.id)
            instance.company = self.request.user.company_users.first().company
            instance.save()
        
        MultipleVendorDiscount.objects.filter(customer = instance).delete()
        order_utils.add_customer_discounts(form, instance)
        # for formset in inlines:
        #     formset.save()

        billing_address_id = form.cleaned_data["billing_address"]
        billing_address1 = form.cleaned_data["billing_address_line_1"]
        billing_address2 = form.cleaned_data["billing_address_line_2"]
        billing_suite_apartment = form.cleaned_data["billing_suite_apartment"]

        shipping_address_id = form.cleaned_data["shipping_address"]
        shipping_address1 = form.cleaned_data["shipping_address_line_1"]
        shipping_address2 = form.cleaned_data["shipping_address_line_2"]
        shipping_suite_apartment = form.cleaned_data["shipping_suite_apartment"]

        billing_city = form.cleaned_data["billing_city"]
        billing_state = form.cleaned_data["billing_state"]
        billing_country = form.cleaned_data["billing_country"]
        billing_zip_code = form.cleaned_data["billing_zip_code"]
        
        shipping_city = form.cleaned_data["shipping_city"]
        shipping_state = form.cleaned_data["shipping_state"]
        shipping_country = form.cleaned_data["shipping_country"]
        shipping_zip_code = form.cleaned_data["shipping_zip_code"]
        
        billing_location = get_geo_code_from_address(billing_address1, billing_city, billing_state, billing_country)
        if billing_location:
            CustomerBillingAddress.objects.filter(id = billing_address_id).update(billing_address_line_1=billing_address1, 
                                                billing_address_line_2=billing_address2, billing_address_line_3=billing_suite_apartment,
                                                billing_city=billing_city, billing_state=billing_state, billing_country=billing_country, 
                                                billing_zip_code=billing_zip_code, billing_latitude=billing_location.get("lat"), billing_longitude=billing_location.get("lng")
                                                )
        CustomerBillingAddress.objects.filter(id = billing_address_id).update(customer=instance, billing_address_line_1=billing_address1, 
            billing_address_line_2=billing_address2, billing_address_line_3=billing_suite_apartment,
            billing_city=billing_city, billing_state=billing_state, billing_country=billing_country, 
            billing_zip_code=billing_zip_code
        )
        set_geocode_for_customer_billing_address.delay(billing_address_id)
            
            
        shipping_location = get_geo_code_from_address(shipping_address1, shipping_city, shipping_state, shipping_country)
        if shipping_location:
            CustomerShippingAddress.objects.filter(id = shipping_address_id).update(customer=instance, shipping_address_line_1=shipping_address1, shipping_address_line_2=shipping_address2, 
                                                shipping_address_line_3=shipping_suite_apartment, shipping_city=shipping_city, shipping_state=shipping_state,
                                                shipping_country=shipping_country, shipping_zip_code=shipping_zip_code, shipping_latitude=shipping_location.get("lat"), shipping_longitude=shipping_location.get("lng"))

        CustomerShippingAddress.objects.filter(id = shipping_address_id).update(customer=instance, shipping_address_line_1=shipping_address1, shipping_address_line_2=shipping_address2, 
            shipping_address_line_3=shipping_suite_apartment, shipping_city=shipping_city, shipping_state=shipping_state,
            shipping_country=shipping_country, shipping_zip_code=shipping_zip_code
        )
        set_geocode_for_customer_shipping_address.delay(shipping_address_id)

        messages.add_message(self.request, messages.SUCCESS, "Customer Updated Successfully.")
        return HttpResponseRedirect(reverse("customer:customer_list"))


    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == User.COMPANY_ADMIN:
            qs = qs.filter(company__id=self.request.user.get_company_id)
        return qs

        # documents = self.request.FILES.getlist("documents")
        # for document in documents:
        #     CustomerDocuments.objects.create(customer=instance, document=document)
        

        # billing_address1 = form.cleaned_data["billing_address_line_1"]
        # billing_address2 = form.cleaned_data["billing_address_line_2"]
        # billing_suite_apartment = form.cleaned_data["billing_suite_apartment"]

        # shipping_address1 = form.cleaned_data["shipping_address_line_1"]
        # shipping_address2 = form.cleaned_data["shipping_address_line_2"]
        # shipping_suite_apartment = form.cleaned_data["shipping_suite_apartment"]

        # billing_city = form.cleaned_data["billing_city"]
        # billing_state = form.cleaned_data["billing_state"]
        # billing_country = form.cleaned_data["billing_country"]
        # billing_zip_code = form.cleaned_data["billing_zip_code"]
        
        # shipping_city = form.cleaned_data["shipping_city"]
        # shipping_state = form.cleaned_data["shipping_state"]
        # shipping_country = form.cleaned_data["shipping_country"]
        # shipping_zip_code = form.cleaned_data["shipping_zip_code"]

        # get_geo_code_for_address.delay(billing_address1, billing_address2, billing_suite_apartment,  billing_city, billing_state, billing_country, billing_zip_code,
        #                                shipping_address1, shipping_address2, shipping_suite_apartment, shipping_city, shipping_state, shipping_country, shipping_zip_code
        #                                )
        
        # billing_location = get_geo_code_from_address(billing_address1, billing_city, billing_state, billing_country)
        # if billing_location:
        #     CustomerBillingAddress.objects.update(customer=instance, billing_address_line_1=billing_address1, 
        #                                         billing_address_line_2=billing_address2, billing_suite_apartment=billing_suite_apartment,
        #                                         billing_city=billing_city, billing_state=billing_state, billing_country=billing_country, 
        #                                         billing_zip_code=billing_zip_code, billing_latitude=billing_location.latitude, billing_longitude=billing_location.longitude
        #                                         )
        # CustomerBillingAddress.objects.update(customer=instance, billing_address_line_1=billing_address1, 
        #                                         billing_address_line_2=billing_address2, billing_suite_apartment=billing_suite_apartment,
        #                                         billing_city=billing_city, billing_state=billing_state, billing_country=billing_country, 
        #                                         billing_zip_code=billing_zip_code
        #                                         )
            
            
        # shipping_location = get_geo_code_from_address(shipping_address1, shipping_city, shipping_state, shipping_country)
        # if shipping_location:
        #     CustomerShippingAddress.objects.update(customer=instance, shipping_address_line_1=shipping_address1, shipping_address_line_2=shipping_address2, 
        #                                         shipping_suite_apartment=shipping_suite_apartment, shipping_city=shipping_city, shipping_state=shipping_state,
        #                                         shipping_country=shipping_country, shipping_zip_code=shipping_zip_code, shipping_latitude=instance.latitude, shipping_longitude=instance.longitude)
        # CustomerShippingAddress.objects.update(customer=instance, shipping_address_line_1=shipping_address1, shipping_address_line_2=shipping_address2, 
        #                                         shipping_suite_apartment=shipping_suite_apartment, shipping_city=shipping_city, shipping_state=shipping_state,
        #                                         shipping_country=shipping_country, shipping_zip_code=shipping_zip_code)


class CustomerDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request):
        customer_id = self.request.POST.get("id")
        Customer.objects.filter(id=customer_id).delete()
        return JsonResponse({"message": "Customer Deleted Successfully."})

class LoadSalesRep(LoginRequiredMixin, View):
    def get(self, request):

        user_id = CompanyUsers.objects.filter(company__id=request.GET.get('company_id'), user__role = User.SALES_REPRESENTATIVE).values('user_id')
        sales_rep_list=[]
        price_level_list=[]
        for data in user_id:
            sales_rep = list(User.objects.filter(id=data['user_id']).values('id','full_name'))
            sales_rep_list.append(sales_rep)
        # price_level = list(PriceLevel.objects.filter(company__id=request.GET.get('company_id'),customer_type=request.GET.get('customer_type_id'), status=PriceLevel.ACTIVE).values('id','price_level'))
        # price_level_list.append(price_level)
        data = {
            'sales_rep_list' : sales_rep_list,
            # 'price_level_list' : price_level_list,
        }
        
        return JsonResponse(data, safe=False)

class CustomerDiscountAjaxView(View):
    template_name = "customer/discount/customer-discount-table.html"

    def post(self, request):
        return JsonResponse()

'''views for payment'''
class PaymentListView(AccountantLoginRequiredMixin, ListView):
     template_name = "customer/payment_list.html"
     model = Payment

     def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_obj = self.request.user.company

        if self.request.user.role == 'sales representative':
            context["customers"] = Customer.objects.filter(sales_rep__id=self.request.user.id, status=Customer.ACTIVE)
            return context

        elif company_obj is not None:
            context["customers"] = Customer.objects.filter(company__company_name=company_obj, status=Customer.ACTIVE)
            return context
        
        context["customers"] = Customer.objects.filter(status='active')
        return context

class PaymentDataTablesAjaxPagination(LoginRequiredMixin, DataTableMixin,View):
    model= OrderBill
    
    def get_queryset(self):
        """Get queryset."""
        #----- dropdown filteration -----
        customer = self.request.GET.get("customer")
        start_date = self.request.GET.get("from_date")
        end_date = self.request.GET.get("to_date")
        
        qs = OrderBill.objects.all()

        company_obj = self.request.user.company

        if self.request.user.role == 'sales representative':
            qs = OrderBill.objects.filter(customer__sales_rep__id=self.request.user.id)

        elif company_obj is not None:
            qs = OrderBill.objects.filter(customer__company__company_name=company_obj)
        
        if customer:
            customer_users = OrderBill.objects.filter(customer__customer_name=customer)
            qs = qs.filter(id__in=customer_users)
            if end_date:
                result_payment = OrderBill.objects.filter(customer_bill__customer_payment__receive_date__range = [start_date, end_date])
                qs = qs.filter(id__in=result_payment)
                return qs.order_by("-id")
            return qs.order_by("-id")
        if end_date:
            result_payment = OrderBill.objects.filter(customer_bill__customer_payment__receive_date__range = [start_date, end_date])
            qs = qs.filter(id__in=result_payment)
            return qs.order_by("-id")
        # ---end---
        return qs.order_by("-id")
    
    def _get_actions(self, obj):
        """Get action buttons w/links."""
        details_url = reverse("customer:payment_model_ajax", kwargs={"pk": obj.id})
        return f'<center> <label data-id="{obj.id}" data-url="{details_url}" title="Details" data-toggle="modal" data-target="#default" class="danger p-0 mr-2 payment-history-btn"><i class="ft-eye font-medium-3" style="color: #975AFF;"></i></label> </center>'

    

    def _get_status(self,obj):
        t = get_template("customer/customer_status.html")
        return t.render(
            {"status": obj.status , "request": self.request}
        )

    def filter_queryset(self, qs):
        # sourcery skip: assign-if-exp, reintroduce-else
        """Return the list of items for this view."""
        # If a search term, filter the query
        if self.search:
            return qs.filter(
                Q(bill_amount__icontains=self.search)
            )
        return qs
    
    def get_customer_details(self, obj):
        t = get_template("reports/report_customer_details.html")
        return t.render(
            {"customer_id": obj.customer}
        )
    
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'customer_name': self.get_customer_details(o),
                'company': str(o.customer.company),
                'entry_date': f'{o.created_at.strftime("%-d %B, %Y")}',
                'bill_amount': o.bill_amount,
                'paid_amount': o.paid_amount,
                'due_amount': o.due_amount,
                'status': self._get_status(o),
                'actions': self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)
    
class PaymentAjaxView(CompanyAdminLoginRequiredMixin, ListView):
    template_name = "customer/payment_details.html"
    model = CustomerPaymentBill

    def get_queryset(self):
        qs = CustomerPaymentBill.objects.all()
        pk = self.kwargs.get("pk")
        if pk:
            qs = qs.filter(customer_bill__id=pk)
            return qs
        return super().get_queryset()
    
class PaymentCreateView(AccountantLoginRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = "customer/payment_form.html"
    form_class = PaymentForm

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company"] = Company.objects.filter(status='active')
        return context

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.save()

        customer_bill_id_list = self.request.POST.get('customer_bill_id_list').split(',')

        customer_past_due_paid_amount = self.request.POST.get('customer__paid_amount') or 0

        customer_id = self.request.POST.get('customer_name')
        use_credit = self.request.POST.get('use_credit')
        credit_amount = self.request.POST.get('credit_amount') or 0

        if customer_id:
            customer_obj = Customer.objects.filter(id = customer_id).last()
            customer_obj.past_due_amount -= float(customer_past_due_paid_amount)
            if use_credit:
                customer_obj.credit_amount = float(credit_amount)
            else:
                customer_obj.credit_amount += float(credit_amount)
            customer_obj.save()

        for customer_bill_id in customer_bill_id_list:
            if customer_bill_id != "":
                paid_amount = self.request.POST.get(f"customer_{customer_bill_id}__paid_amount", 0)
                due_balance = self.request.POST.get(f"customer_{customer_bill_id}__due_balance", 0)
                
                if float(paid_amount) <= 0:
                    continue

                order_bill = OrderBill.objects.filter(id = customer_bill_id).last()
                if order_bill:
                    order_bill.paid_amount += float(paid_amount)
                    order_bill.due_amount = due_balance
                    if order_bill.due_amount == 0:
                        order_bill.status = OrderBill.COMPLETE
                    
                    order_bill.save()

                CustomerPaymentBill.objects.create(customer_payment=instance, customer_bill=order_bill, amount=float(paid_amount))
            else:
                pass
            # return self.render_to_response(self.get_context_data(form=form))
        messages.add_message(self.request, messages.SUCCESS, "Customer payment completed")

        return HttpResponseRedirect(reverse("customer:payment_list"))
    
    def form_invalid(self, form):
        print('form: ', form.errors)
        return super().form_invalid(form)


class PaymentUpdateView(AccountantLoginRequiredMixin, SuccessMessageMixin, UpdateView):
    template_name = "customer/payment_form.html"
    model = Payment
    form_class =PaymentForm

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    success_message = "Payment Updated Successfully"

    success_url = reverse_lazy('customer:payment_list')

class PaymentDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request):
        payment_id = self.request.POST.get("id")
        Payment.objects.filter(id=payment_id).delete()
        return JsonResponse({"message": "Payment Deleted Successfully."})
    
class LoadCustomerForPaymentAjax(LoginRequiredMixin, View):
    def get(self, request):
        company = request.GET.get("company_name")
        data = {
            'customer_data' : list(Customer.objects.filter(status=Customer.ACTIVE, company__company_name=company).values('id','customer_name'))
        }
        return JsonResponse(data, safe=True)

class CustomerBillListView(View):
    template_name = "customer/customer_bill_list.html"

    def get(self, request):
        customer_id = self.request.GET.get('customer_id')
        receive_amount = self.request.GET.get("receive_amount")
        receive_amount = float(receive_amount) if receive_amount else 0
        is_credit_used = self.request.GET.get("is_credit_used")

        queryset = OrderBill.objects.filter(status = OrderBill.INCOMPLETE)

        data = {}
        context = {}

        if customer_id:
            queryset = queryset.filter(customer__id=customer_id)
        
            context["object_list"] = queryset.order_by("created_at")
            due_amount = OrderBill.objects.filter(customer__id=customer_id).aggregate(total_due_amount=Sum("due_amount"))
            total_due_amount = due_amount ['total_due_amount'] or 0
            customer =  Customer.objects.get(id=customer_id)
            if customer.past_due_amount > 0:
                context['customer'] =  customer
                total_due_amount += customer.past_due_amount
            context["total_due_amount"] = total_due_amount
            context["available_credit"] = customer.credit_amount

            credit_amount = receive_amount
            if is_credit_used == "true":
                credit_amount += customer.credit_amount
                context["credit_amount"] = credit_amount
            else:
                context["credit_amount"] = credit_amount

            data["html"] = render_to_string(self.template_name, context, request)
        else:
            context["credit_amount"] = 0.0
            data["html"] = render_to_string(self.template_name, context, request)

        if receive_amount > 0:
            data["amount_in_words"] = num2words(receive_amount, lang='en_IN').title()

        return JsonResponse(data)
    
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     customer_id = self.kwargs.get("id_customer")

'''views for Sales Route'''
class SalesRouteListView(CompanyAdminLoginRequiredMixin, ListView):
    template_name = "customer/sales_route_list.html"
    model = SalesRoute
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_obj = self.request.user.company
        if company_obj is not None:
            context["sales_rep"] = CompanyUsers.objects.filter(company__company_name=company_obj, user__role=User.SALES_REPRESENTATIVE)
        else:
            context["sales_rep"] = User.objects.filter(role='sales representative')
        context["status_choices"] = SalesRoute.STATUS_CHOICES
        return context

class SalesRouteDataTablesAjaxPagination(LoginRequiredMixin, DataTableMixin, View):
    model = SalesRoute

    def get_queryset(self):  
    #----- dropdown filteration -----
        sales_rep = self.request.GET.get("sales_rep")
        status_choice = self.request.GET.get("status")
        qs = SalesRoute.objects.all()

        company_obj = self.request.user.company

        if self.request.user.role == 'sales representative':
            qs = SalesRoute.objects.filter(sales_rep__id=self.request.user.id, company__company_name=company_obj)

        elif company_obj is not None:
            qs = SalesRoute.objects.filter(company__company_name=company_obj)

        if sales_rep:
            sales_rep_users = SalesRoute.objects.filter(sales_rep__username=sales_rep)
            qs = qs.filter(id__in=sales_rep_users)
            if status_choice:
                status_salesroute = SalesRoute.objects.filter(status=status_choice)
                qs = qs.filter(id__in=status_salesroute)
                return qs.order_by("-id")
            return qs.order_by("-id")
        if status_choice:
            status_salesroute = SalesRoute.objects.filter(status=status_choice)
            qs = qs.filter(id__in=status_salesroute)
            return qs.order_by("-id")
        return qs.order_by("-id")
        # ---end---
    
    def _get_actions(self, obj):
        update_url = reverse("customer:sales_route_update", kwargs={"pk":obj.id})
        delete_url = reverse("customer:sales_route_delete")
        return f'<center><a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a> <label data-title="{obj.route_name}" data-url="{delete_url}" data-url="{delete_url}" data-id="{obj.id}" title="Delete" id="delete_btn"  class="danger p-0 ajax-delete-btn"><i class="ft-trash font-medium-3"></i></label></center>'
    
    def filter_queryset(self, qs):
        # sourcery skip: assign-if-exp, reintroduce-else
        if self.search:
            return qs.filter(
                Q(route_name__icontains=self.search) 
            )
        return qs
    
    def _get_status(self,obj):
        t = get_template("customer/customer_status.html")
        return t.render(
            {"status": obj.status, "request": self.request}
        )
    
    def prepare_results(self, qs):
        return [
            {
                'id' : o.id,
                'route_name' : o.route_name,
                'sales_rep' : str(o.sales_rep) if o.sales_rep else "-----",
                'status' : self._get_status(o),
                'actions' : self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)    
    
class SalesRouteCreateView(CompanyAdminLoginRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = "customer/sales_route_form.html"
    form_class = SalesRouteForm

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs
    
    success_message = "Sales Route Created Successfully"
    
    success_url = reverse_lazy('customer:sales_route_list')

class SalesRouteUpdateView(CompanyAdminLoginRequiredMixin, SuccessMessageMixin, UpdateView):
    template_name = "customer/sales_route_form.html"
    model = SalesRoute
    form_class = SalesRouteForm

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs
    
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == User.COMPANY_ADMIN:
            qs = qs.filter(company__id=self.request.user.get_company_id)
        return qs

    success_message = "Sales Route Updated Successfully"

    success_url = reverse_lazy('customer:sales_route_list')

class SalesRouteDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request):
        sales_route_id = self.request.POST.get("id")
        SalesRoute.objects.filter(id=sales_route_id).delete()
        return JsonResponse({"message": "Sales Route Deleted Successfully."})

class LoadCustomerSalesrepAjax(LoginRequiredMixin, View):
     def get(self, request):

        user_id = CompanyUsers.objects.filter(company__id=request.GET.get('company_id'), user__role = User.SALES_REPRESENTATIVE).values('user_id')
        sales_rep_list=[]
        for data in user_id:
            sales_rep = list(User.objects.filter(id=data['user_id']).values('id','full_name'))
            sales_rep_list.append(sales_rep)
        data = {
            'sales_rep_list' : sales_rep_list,
            'customer_list' : list(Customer.objects.filter(company__id=request.GET.get('company_id'), status=Customer.ACTIVE).values('id','customer_name'))
        }
        return JsonResponse(data, safe=True)

'''views for Price Level'''
class PricelevelListView(SalesLoginRequiredMixin, ListView):
    template_name = "customer/price_level_list.html"
    model = PriceLevel

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["customer_type"] = PriceLevel.TYPE_CHOICES
        context["status_choices"] = PriceLevel.STATUS_CHOICES
        context["company"] = Company.objects.filter(status='active')
        return context

class PricelevelDataTablesAjaxPagination(LoginRequiredMixin, DataTableMixin, View):
    model = PriceLevel

    def get_queryset(self):  # sourcery skip: extract-duplicate-method
        #----- dropdown filteration -----
        customer_type = self.request.GET.get("customer_type")
        status_choice = self.request.GET.get("status")
        company_choice = self.request.GET.get("company")

        # company_obj = self.request.user.company
        # if company_obj is not None:
        #     if self.request.user.role == 'sales representative':
        #         qs = PriceLevel.objects.filter(company__company_name=company_obj)
        #     qs = PriceLevel.objects.filter(company__company_name=company_obj)

        
        qs = PriceLevel.objects.all()

        if self.request.user.role == User.COMPANY_ADMIN or self.request.user.role == User.SALES_REPRESENTATIVE:
            company = self.request.user.company_users.first().company
            qs = qs.filter(company=company)

        if customer_type:
            customer_type_pricelevel = PriceLevel.objects.filter(customer_type=customer_type)
            qs = qs.filter(id__in=customer_type_pricelevel)
            if status_choice:
                status_pricelevel = PriceLevel.objects.filter(status=status_choice)
                qs = qs.filter(id__in=status_pricelevel)
                return qs.order_by("-id")
            if company_choice:
                company_pricelevel = PriceLevel.objects.filter(company__company_name=company_choice)
                qs = qs.filter(id__in=company_pricelevel)
                return qs.order_by("-id")
            return qs.order_by("-id")
        if status_choice:
            status_pricelevel = PriceLevel.objects.filter(status=status_choice)
            qs = qs.filter(id__in=status_pricelevel)
            if company_choice:
                company_pricelevel = PriceLevel.objects.filter(company__company_name=company_choice)
                qs = qs.filter(id__in=company_pricelevel)
                return qs.order_by("-id")
            return qs.order_by("-id")
        if company_choice:
            company_pricelevel = PriceLevel.objects.filter(company__company_name=company_choice)
            qs = qs.filter(id__in=company_pricelevel)
            return qs.order_by("-id")
        
        return qs.order_by("-id")
        # ---end---
    
    def _get_actions(self, obj):
        update_url = reverse("customer:price_level_update", kwargs={"pk":obj.id})
        delete_url = reverse("customer:price_level_delete")
        return f'<center><a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a> <label data-title="{obj.price_level}" data-url="{delete_url}" data-url="{delete_url}" data-id="{obj.id}" title="Delete" id="delete_btn"  class="danger p-0 ajax-delete-btn"><i class="ft-trash font-medium-3"></i></label></center>'
    
    def filter_queryset(self, qs):
        # sourcery skip: assign-if-exp, reintroduce-else
        if self.search:
            return qs.filter(
                Q(price_level__icontains=self.search) 
            )
        return qs
    
    def _get_status(self,obj):
        t = get_template("customer/customer_status.html")
        return t.render(
            {"status": obj.status, "request": self.request}
        )
    
    
    def prepare_results(self, qs):
        return [
            {
                'id' : o.id,
                'price_level' : o.price_level,
                'customer_type' : o.customer_type.title(),
                'company' : str(o.company),
                'status' : self._get_status(o),
                'actions' : self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)    
   
class PricelevelCreateView(SalesLoginRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = "customer/price_level_form.html"
    form_class = PriceLevelForm

    success_message = "Price Level Created Successfully"
    

    # def form_valid(self, form):  # sourcery skip: use-named-expression
    #     instance = form.save(commit=False)
    #     if self.request.user.role == User.COMPANY_ADMIN:
    #         company = self.request.user.company_users.first().company
    #         PriceLevel.objects.create(
    #             company = company,
    #             user = instance
    #         )
    #     else:
    #         company_id = form.data.get("company")
    #         if company_id:
    #             company = Company.objects.get(id=company_id)
    #             PriceLevel.objects.create(
    #                 company = company,
    #                 customer_type = instance.customer_type,
    #                 price_level = instance,
    #                 status = instance.status,
    #             )
    #     messages.add_message(self.request, messages.SUCCESS, "Price Level Created Successfully.")
    #     return HttpResponseRedirect(reverse("customer:price_level_list"))

    success_url = reverse_lazy('customer:price_level_list')

class PricelevelUpdateView(SalesLoginRequiredMixin, SuccessMessageMixin, UpdateView):
    template_name = "customer/price_level_form.html"
    model = PriceLevel
    form_class = PriceLevelForm

    success_message = "Price Level Updated Successfully"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product"] = Product.objects.all()
        return context

    success_url = reverse_lazy('customer:price_level_list')


    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == User.COMPANY_ADMIN:
            qs = qs.filter(company__id=self.request.user.get_company_id)
        return qs

class PricelevelDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request):
        price_level_id = self.request.POST.get("id")
        PriceLevel.objects.filter(id=price_level_id).delete()
        return JsonResponse({"message": "Price Level Deleted Successfully."})

'''views for custom price of product'''
class PricelevelProductDataTablesAjaxPagination(LoginRequiredMixin, DataTableMixin, View):
    model = PriceLevelProduct

    def get_queryset(self):
        qs = PriceLevelProduct.objects.all()
        price_level = self.request.GET.get("price_level")
        if price_level:
            qs = qs.filter(price_level__id=price_level)
        return qs.order_by("-id")
    
    def _get_input(self, obj):
        t = get_template("customer/custom_input.html")
        return t.render(
            {"price_level_product": obj}
        )
    
    def _get_actions(self, obj):
        save_url = reverse("customer:price_level_product_update")
        customer_type = self.request.GET.get("customer_type")
        return f'<button data-url="{save_url}" data-id="{obj.id}" data-customertype="{customer_type}" class="btn btn-primary submit-customer-price" >Save</button>'
 

    def filter_queryset(self, qs):
        # sourcery skip: assign-if-exp, reintroduce-else
        if self.search:
            return qs.filter(
                Q(unit_type__icontains=self.search) |
                Q(product__name__icontains=self.search) 
            )
        return qs
    
    

    def prepare_results(self, qs):
        customer_type = self.request.GET.get("customer_type")
        data=[]
        for o in qs:
                if customer_type == "wholesale":
                    if o.unit_type == "piece":
                        data.append(
                            {
                                'id' : o.id,
                                'product' : str(o.product),
                                'unit_type' : o.unit_type.title(),
                                # 'min_price' : o.product.wholesale_min_price,
                                'base_price': o.product.wholesale_base_price,
                                'custom_price' : self._get_input(o),
                                'action' : self._get_actions(o),
                            }
                        )
                    else:
                        data.append(
                            {
                                'id' : o.id,
                                'product' : str(o.product),
                                'unit_type' : o.unit_type.title(),
                                # 'min_price' : o.product.get_wholesale_min_price,
                                'base_price': o.product.get_wholesale_base_price,
                                'custom_price' : self._get_input(o),
                                'action' : self._get_actions(o),
                            }
                        )
                elif customer_type == "retail":
                    if o.unit_type == "piece":
                        data.append(
                            {
                                'id' : o.id,
                                'product' : str(o.product),
                                'unit_type' : o.unit_type,
                                # 'min_price' : o.product.get_retail_min_price,
                                'base_price': o.product.get_retail_base_price,
                                'custom_price' : self._get_input(o),
                                'action' : self._get_actions(o),
                            }
                        )
                    else:
                        data.append(
                            {
                                'id' : o.id,
                                'product' : str(o.product),
                                'unit_type' : o.unit_type,
                                # 'min_price' : o.product.get_retail_min_price,
                                'base_price': o.product.get_retail_base_price,
                                'custom_price' : self._get_input(o),
                                'action' : self._get_actions(o),
                            }
                        )

                elif customer_type == "distributor":
                    if o.unit_type == "piece":
                        data.append(
                            {
                                'id' : o.id,
                                'product' : str(o.product),
                                'unit_type' : o.unit_type,
                                # 'min_price' : o.product.cost_price,
                                'base_price': o.product.cost_price,
                                'custom_price' : self._get_input(o),
                                'action' : self._get_actions(o),
                            }
                        )
                    else:
                         data.append(
                            {
                                'id' : o.id,
                                'product' : str(o.product),
                                'unit_type' : o.unit_type,
                                # 'min_price' : o.product.get_distributor_min_price,
                                'base_price': o.product.get_distributor_base_price,
                                'custom_price' : self._get_input(o),
                                'action' : self._get_actions(o),
                            }
                        )       
        return data
    
    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)
    
class PricelevelProductUpdateDataTablesAjaxPagination(LoginRequiredMixin, View):
    def post(self, request):

        custom_price = self.request.POST.get("custom_price")
        price_level_product_id = self.request.POST.get("id")
        customer_type = self.request.POST.get("customertype")
        
        if price_level_product_id:
            object = PriceLevelProduct.objects.get(id=price_level_product_id)
            
            if customer_type == "wholesale":
                if object.unit_type == "piece":
                    if float(custom_price) < int(object.product.wholesale_rate):
                        return JsonResponse({"error": "Custom Price must be greated than min price."})
                    else:
                        object.custom_price = custom_price
                        object.save()
                        return JsonResponse({"message": "Custom Price Updated Successfully."})
                elif object.unit_type == "box" or object.unit_type == "case":
                    if float(custom_price) < int(object.product.wholesale_rate):
                        return JsonResponse({"error": "Custom Price must be greated than min price."})
                    else:
                        object.custom_price = custom_price
                        object.save()
                        return JsonResponse({"message": "Custom Price Updated Successfully."})
                else:
                    object.custom_price = custom_price
                    object.save()
                    return JsonResponse({"message": "Custom Price Updated Successfully."})
            elif customer_type == "retail":
                if object.unit_type == "piece":
                    if float(custom_price) < int(object.product.retail_rate):
                        return JsonResponse({"error": "Custom Price must be greated than min price."})
                    else:
                        object.custom_price = custom_price
                        object.save()
                        return JsonResponse({"message": "Custom Price Updated Successfully."})
                elif object.unit_type == "box" or object.unit_type == "case":
                    if float(custom_price) < int(object.product.retail_rate):
                        return JsonResponse({"error": "Custom Price must be greated than min price."})
                    else:
                        object.custom_price = custom_price
                        object.save()
                        return JsonResponse({"message": "Custom Price Updated Successfully."})
                else:
                    object.custom_price = custom_price
                    object.save()
                    return JsonResponse({"message": "Custom Price Updated Successfully."})
            elif customer_type == "distributor":
                if object.unit_type == "piece":
                    if float(custom_price) < int(object.product.purchase_price):
                        return JsonResponse({"error": "Custom Price must be greated than min price."})
                    else:
                        object.custom_price = custom_price
                        object.save()
                        return JsonResponse({"message": "Custom Price Updated Successfully."})
                elif object.unit_type == "box" or object.unit_type == "case":
                    if float(custom_price) < int(object.product.get_distributor_min_price):
                        return JsonResponse({"error": "Custom Price must be greated than min price."})
                    else:
                        object.custom_price = custom_price
                        object.save()
                        return JsonResponse({"message": "Custom Price Updated Successfully."})
                else:
                    object.custom_price = custom_price
                    object.save()
                    return JsonResponse({"message": "Custom Price Updated Successfully."})                
            object.custom_price = custom_price
            object.save()
            return JsonResponse({"message": "Custom Price Updated Successfully."})


class CustomerLogAjaxView(LoginRequiredMixin, ListView):
    template_name = "customer/customer_log_list.html"
    model = CustomerLog

    def get_queryset(self):
        qs = CustomerLog.objects.all()
        pk = self.kwargs.get("pk")
        if pk:
            qs = qs.filter(customer__id=pk)
        return super().get_queryset()
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["customer_id"] = self.kwargs.get("pk")
        return context


class CustomerLogDatatableAjaxView(DataTableMixin,View):
    model= CustomerLog
    
    def get_queryset(self):
        """Get queryset."""
        qs = CustomerLog.objects.all()
        customer_id = self.request.GET.get("customer_id")
        if customer_id:
            qs = qs.filter(customer__id=customer_id)

        return qs.order_by("-id")

    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'action_by': o.action_by.full_name if o.action_by else "-----",
                'remark': o.remark,
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)



class CustomerCreateFromCSVFormView(CompanyAdminLoginRequiredMixin, FormView):
    template_name = "customer/import_customer.html"
    form_class = ImportCustomerCSVForm

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def form_valid(self, form):
        csv_file = self.request.FILES["csv_file"]
        file = csv_file.read()
        csv_file_obj = CSVFile.objects.create(csv_file=csv_file)
        import_customer_from_xlsx.delay(file)
        messages.add_message(self.request, messages.SUCCESS, "Customer Details importing process is starting..")
        return HttpResponseRedirect(reverse("customer:customer_list"))
    
class ZoneCreateFromCSVFormView(CompanyAdminLoginRequiredMixin, FormView):
    template_name = "customer/import_zone.html"
    form_class = ImportCustomerCSVForm

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def form_valid(self, form):
        csv_file = self.request.FILES["csv_file"]
        file = csv_file.read()
        csv_file_obj = CSVFile.objects.create(csv_file=csv_file)
        import_zone_from_xlsx.delay(file, self.request.user.id)
        messages.add_message(self.request, messages.SUCCESS, "Zone Details importing process is starting..")
        return HttpResponseRedirect(reverse("customer:zone_list"))
    
class ZoneListView(CompanyAdminLoginRequiredMixin, ListView):
    model = Zone
    template_name = "customer/zone_list.html"

    # def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    #     Zone.objects.all().delete()
    #     return super().get(request, *args, **kwargs)
    

class ZoneDataTablesAjaxPagination(DataTableMixin, View):
    model = Zone

    def get_queryset(self):
        if self.request.user.is_superuser:
            qs = Zone.objects.all()
        else:
            qs = Zone.objects.filter(company__id = self.request.user.get_company_id)
        return qs

    def filter_queryset(self, qs):
        # sourcery skip: assign-if-exp, reintroduce-else
        if self.search:
            return qs.filter(
                Q(zone_code__icontains=self.search)
            )
        return qs
    
    def _get_actions(self, obj):
        update_url = reverse("customer:zone_update", kwargs={"pk":obj.id})
        delete_url = reverse("customer:zone_delete")
        return f'<center><a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a> <label data-title="{obj.zone_code}" data-url="{delete_url}" data-id="{obj.id}" title="Delete" id="delete_btn"  class="danger p-0 ajax-delete-btn"><i class="ft-trash font-medium-3"></i></label></center>'
    
    
    def prepare_results(self, qs):
        return [
            {
                'id' : o.id,
                'zone_code' : o.zone_code,
                'zone_description' : o.zone_description,
                'actions' : self._get_actions(o),
            }
            for o in qs
        ]
    
    
    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)
    

class ZoneCreateView(CompanyAdminLoginRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = "customer/zone_form.html"
    form_class = ZoneForm
    success_message = "Zone Created Successfully"

    def form_valid(self, form):
        instance = form.save(commit=False)

        if not self.request.user.is_superuser:
            company_id = self.request.user.get_company_id
            instance.company = Company.objects.filter(id = company_id).last()

        instance.save()
        return HttpResponseRedirect(reverse("customer:zone_list"))

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        return super().form_invalid(form)
    
class ZoneUpdateView(CompanyAdminLoginRequiredMixin, SuccessMessageMixin, UpdateView):
    template_name = "customer/zone_form.html"
    form_class = ZoneForm
    success_message = "Zone Updated Successfully"
    model=Zone
    success_url = reverse_lazy("customer:zone_list")

class ZoneDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request):
        zone_id = self.request.POST.get("id")
        Zone.objects.filter(id=zone_id).delete()
        return JsonResponse({"message": "Zone Deleted Successfully."})
    
class AllCustomerDeleteView(View):
      def post(self, request):
        Customer.objects.all().delete()
        return JsonResponse({"message": "All customers are deleted."})

class AllZoneDeleteView(View):
      def post(self, request):
        Zone.objects.all().delete()
        return JsonResponse({"message": "All zones are deleted."})


class DiscountListView(CompanyAdminLoginRequiredMixin, ListView):
    template_name = "customer/discount_list.html"
    model = Discount

class DiscountListAjaxView(LoginRequiredMixin, DataTableMixin, View):
    model = Discount

    def get_queryset(self):
        qs = Discount.objects.all()

        if not self.request.user.is_superuser:
            qs = qs.filter(company__id = self.request.user.get_company_id)

        return qs

    def _get_actions(self, obj):
        """Get action buttons w/links."""
        update_url = reverse("customer:discount_update", kwargs={"pk": obj.id})
        delete_url = reverse("customer:discount_delete")
        return f'<center><a data-url="{update_url}" class="update-discount text-primary" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a> <label data-title="category ({obj.category})" data-url="{delete_url}" data-id="{obj.id}" title="Delete" id="delete_btn"  class="danger p-0 ajax-delete-btn"><i class="ft-trash font-medium-3"></i></label></center>'
    
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'category': o.category,
                'company': o.company.company_name,
                # 'type': o.type.title() if o.type else "-",
                # 'brand__name': o.brand.name,
                'discount': o.discount,
                'actions': self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class DiscountCreateView(CompanyAdminLoginRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = DiscountForm
    template_name = "customer/discount_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form), status=201)

    def form_valid(self, form):
        instance = form.save(commit=False)
        
        # primary = form.data.get("primary")
        # secondary = form.data.get("secondary")

        # if primary:
        #     instance.type = Discount.PRIMARY
        #     brand_discounts = Discount.objects.filter(brand = instance.brand, type = Discount.PRIMARY)
        #     for brand_discount in brand_discounts:
        #         brand_discount.type = None
        #         brand_discount.save()
        # elif secondary:
        #     instance.type = Discount.SECONDARY
        #     brand_discounts = Discount.objects.filter(brand = instance.brand, type = Discount.SECONDARY)
        #     for brand_discount in brand_discounts:
        #         brand_discount.type = None
        #         brand_discount.save()

        # if not self.request.user.is_superuser:
        #     company = Company.objects.filter(id = self.request.user.get_company_id).last()
        #     instance.company = company
        instance.save()

        response = HttpResponse(status=200)
        response["HX-Trigger"] = json.dumps(
            {
                "customerDiscountCreate": {
                    "message": "Discount created.",
                    "level": "success",
                }
            }
        )
        return response


class DiscountUpdateView(CompanyAdminLoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = DiscountForm
    model = Discount
    template_name = "customer/discount_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form), status=201)

    def form_valid(self, form):
        instance = form.save(commit=False)

        # primary = form.data.get("primary")
        # secondary = form.data.get("secondary")

        # if primary:
        #     instance.type = Discount.PRIMARY
        #     brand_discounts = Discount.objects.filter(brand = instance.brand, type = Discount.PRIMARY)
        #     for brand_discount in brand_discounts:
        #         brand_discount.type = None
        #         brand_discount.save()
        # elif secondary:
        #     instance.type = Discount.SECONDARY
        #     brand_discounts = Discount.objects.filter(brand = instance.brand, type = Discount.SECONDARY)
        #     for brand_discount in brand_discounts:
        #         brand_discount.type = None
        #         brand_discount.save()

        # if not self.request.user.is_superuser:
        #     company = Company.objects.filter(id = self.request.user.get_company_id).last()
        #     instance.company = company
        instance.save()

        response = HttpResponse(status=200)
        response["HX-Trigger"] = json.dumps(
            {
                "customerDiscountCreate": {
                    "message": "Discount updated.",
                    "level": "success",
                }
            }
        )
        return response
    

class DiscountDeleteView(View):
    def post(self, request):
        id = self.request.POST.get("id")
        Discount.objects.filter(id = id).delete()
        return JsonResponse({"message": "Discount deleted successfully."})

class DiscountSearchAjaxView(View):
    def get(self, request):
        company = self.request.GET.get("company")
        term = self.request.GET.get("search")
        brand_id = self.request.GET.get("brand_id")
        discount_type = self.request.GET.get("discount_type")
        
        queryset = Discount.objects.filter(company__id = company)

        if term:
            queryset = queryset.filter(category__icontains = term)

        data = [{"id": discount.id, "text": discount.category, "discount": discount.discount} for discount in queryset]
        if brand_id:
            brand = Brand.objects.filter(id = brand_id).last()
            if brand:
                if discount_type == "primary":
                    data.insert(0, {"id": 0, "text": "Discount A", "discount": brand.discount_a})
                else:
                    data.insert(0, {"id": 0, "text": "Discount B", "discount": brand.discount_b})
        
        return JsonResponse({"items": data})


class CustomerSearchAjaxView(View):
    def get(self, request):
        company_id = self.request.GET.get("company")
        term = self.request.GET.get("search")
        is_update = request.POST.get('is_update')
        
        if self.request.user.role == User.SALES_REPRESENTATIVE:
            queryset = Customer.objects.filter(company__id = company_id, sales_rep__id = self.request.user.id, status = Customer.ACTIVE)
        else:
            queryset = Customer.objects.filter(company__id = company_id, status = Customer.ACTIVE)

        if is_update == "false":
            queryset = queryset.filter(is_locked = False)

        if term:
            queryset = queryset.filter(
                Q(customer_name__icontains = term) |
                Q(area__icontains = term)
            )

        data = [{"id": customer.id, "text": customer.customer_name+" ["+customer.customer_type.title()+"]", "code": customer.code, "zone": customer.zone.zone_code, "area": customer.area, "type": customer.customer_type} for customer in queryset]
        
        return JsonResponse({"items": data})


class ReplacementListView(CompanyAdminLoginRequiredMixin, ListView):
    template_name = "customer/replacement/replacement_list.html"
    model = Replacement


class ReplacementListAjaxView(LoginRequiredMixin, DataTableMixin, View):
    model = Replacement

    def get_queryset(self):
        qs = Replacement.objects.all()

        if not self.request.user.is_superuser:
            qs = qs.filter(customer__company__id = self.request.user.get_company_id)

        return qs
    
    def _get_customer(self, obj):
        template = get_template("reports/report_customer_details.html")
        return template.render({'customer_id': obj.customer})

    def _get_actions(self, obj):
        """Get action buttons w/links."""
        update_url = reverse("customer:replacement_update", kwargs={"pk": obj.id})
        delete_url = reverse("customer:replacement_delete")
        return f'<center><a href="{update_url}" class="text-primary" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a> <label data-title="{obj.replace_id}" data-url="{delete_url}" data-id="{obj.id}" title="Delete" id="delete_btn" class="danger p-0 ajax-delete-btn"><i class="ft-trash font-medium-3"></i></label></center>'
    
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'replace_id': o.replace_id if o.replace_id else "-",
                'order': o.order.order_id if o.order else "-",
                'customer__customer_name': self._get_customer(o),
                'created_by__full_name': o.created_by.full_name if o.created_by else "-",
                'return_type': o.return_type.title(),
                'total_amount': float(o.get_replacement_total),
                'actions': self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class ReplacementCreateView(CompanyAdminLoginRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = ReplacementForm
    template_name = "customer/replacement/replacement_form.html"

    def form_valid(self, form):
        products_list = self.request.POST.get('product_id_list').split(',')
        instance = form.save(commit=False)
        instance.created_by = self.request.user

        if not self.request.user.is_superuser:
            company = Company.objects.filter(id = self.request.user.get_company_id).last()
            instance.company = company
        instance.save()

        instance.replace_id = "{}{:05d}".format("RPL#", instance.id)
        instance.save()

        for product_id in products_list:
            order_utils.add_product_list_in_replacement(self, instance, product_id)
        
        if instance.return_type == Replacement.CREDIT:
            customer = Customer.objects.filter(id = instance.customer.id).last()
            customer.credit_amount += float(instance.get_replacement_total)
            customer.save()

            instance.settlement_completed = True
            instance.save()

        messages.add_message(self.request, messages.SUCCESS, "Replacement order created")
        return HttpResponseRedirect(reverse("customer:replacement_list"))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form), status=201)


class ReplacementUpdateView(CompanyAdminLoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = ReplacementForm
    model = Replacement
    template_name = "customer/replacement/replacement_form.html"

    def form_valid(self, form):
        old_replacement = Replacement.objects.filter(id = self.kwargs["pk"]).last()
        products_list = self.request.POST.get('product_id_list').split(',')
        instance = form.save(commit=False)

        if not self.request.user.is_superuser:
            company = Company.objects.filter(id = self.request.user.get_company_id).last()
            instance.company = company
        instance.save()

        if old_replacement.return_type == Replacement.CREDIT:
            customer = Customer.objects.filter(id = instance.customer.id).last()
            customer.credit_amount -= float(instance.get_replacement_total)
            customer.save()

        order_utils.update_product_list_in_replacement(self, instance, products_list)

        # if instance.return_type == Replacement.CREDIT:
        #     customer = Customer.objects.filter(id = instance.customer.id).last()
        #     customer.credit_amount += float(instance.get_replacement_total)
        #     customer.save()
            
        #     instance.settlement_completed = True
        #     instance.save()

        messages.add_message(self.request, messages.SUCCESS, "Replacement order updated")
        return HttpResponseRedirect(reverse("customer:replacement_list"))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form), status=201)
    

class ReplacementDeleteView(View):
    def post(self, request):
        id = self.request.POST.get("id")
        Replacement.objects.filter(id = id).delete()
        return JsonResponse({"message": "Replacement deleted successfully."})
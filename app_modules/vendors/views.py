from typing import Any, Dict
from django.forms.forms import BaseForm
from django.forms.models import BaseModelForm
from django.http.response import HttpResponse
from django.shortcuts import render, HttpResponseRedirect
from django.views.generic import CreateView, UpdateView, ListView,View, DetailView
from django.urls import reverse_lazy, reverse
from app_modules.company.models import Company
from app_modules.purchase_order.models import PurchaseOrder
from app_modules.vendors.forms import VendorCreateForm, VendorUpdateForm,VendorDocumentCreateForm,VendorPaymentCreateForm
from app_modules.vendors.models import Vendor,VendorDocument,VendorBill,VendorPayment,VendorPaymentBill
from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from django_datatables_too.mixins import DataTableMixin
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.template.loader import get_template
from django.db.models import Sum
from django.contrib.messages.views import SuccessMessageMixin
from app_modules.base.mixins import CompanyAdminLoginRequiredMixin



User = get_user_model()

# Create your views here.
class VendorListView(CompanyAdminLoginRequiredMixin, ListView):
    template_name = "vendors/vendor_list.html"
    model = Vendor
    context_object_name = "vendor_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["companies"] = Company.objects.all()
        return context


class VendorCreateView(CompanyAdminLoginRequiredMixin, CreateView):
    template_name = "vendors/vendor_create.html"
    model = Vendor
    form_class = VendorCreateForm

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def form_valid(self, form):
        instance = form.save(commit=False)
        phone = form.cleaned_data['phone']
        if phone:
            instance.phone = f"+91{phone}"
        instance.save()

        messages.add_message(self.request, messages.SUCCESS, "Vendor Created Successfully.")
        return HttpResponseRedirect(reverse("vendors:vendor_list"))
    

class VendorUpdateView(CompanyAdminLoginRequiredMixin, UpdateView):
    template_name = "vendors/vendor_update.html"
    model = Vendor
    form_class = VendorUpdateForm

    def form_valid(self, form):
        instance = form.save(commit=False)
        phone = form.cleaned_data['phone']
        if phone:
            instance.phone = f"+91{phone}"
        instance.save()

        messages.add_message(self.request, messages.SUCCESS, "Vendor Updated Successfully.")
        return HttpResponseRedirect(reverse("vendors:vendor_list"))
    
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == User.COMPANY_ADMIN:
            qs = qs.filter(company__id=self.request.user.get_company_id)
        return qs
    

class VendorDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request):
        vendor_id = self.request.POST.get("id")
        Vendor.objects.filter(id=vendor_id).delete()
        return JsonResponse({"message": "Vendor Deleted Successfully."})


class VendorDataTablesAjaxPagination(DataTableMixin,View):
    model= Vendor
    
    def get_queryset(self):
        """Get queryset."""
        qs = Vendor.objects.all()
        if self.request.user.role == User.COMPANY_ADMIN or self.request.user.role == User.SALES_REPRESENTATIVE:
            company = self.request.user.company_users.first().company
            qs = qs.filter(company=company)

        company = self.request.GET.get("company")
        if company:
            qs = qs.filter(company__id=company)
        return qs.order_by("-id")

    def _get_actions(self, obj):
        """Get action buttons w/links."""
        # update_url = reverse("users: user_update", kwargs={"pk": obj.id})
        update_url = reverse("vendors:vendor_update", kwargs={"pk": obj.id})
        delete_url = reverse("vendors:vendor_delete")
        detail_url = reverse("vendors:vendor_details", kwargs={"pk": obj.id})
        return f'<div class="row"><center><a href="{detail_url}" class="vendor-details-btn" data-id="{obj.id}" title="Edit"><i class="ft-eye font-medium-3 mr-2"></i></a><a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a> <label style="cursor: pointer;" data-title="{obj.first_name} {obj.last_name}" data-url="{delete_url}" data-id="{obj.id}" title="Delete" class="danger p-0 ajax-delete-btn"><i class="ft-trash font-medium-3"></i></label></center></div>'


    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        # If a search term, filter the query
        if self.search:
            return qs.filter(
                Q(first_name__icontains=self.search) |
                Q(last_name=self.search) |
                Q(email__icontains=self.search)
            )
        return qs
    
    def _get_status(self,obj):
        t = get_template("vendors/get_vendor_status.html")
        return t.render(
            {"vendor": obj, "request": self.request}
        )

    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'email': o.email if o.email else "-",
                'first_name': o.first_name +" "+ o.last_name,
                'phone': o.phone if o.phone else "-",
                'company': o.company.company_name,
                'city': o.city,
                'status': self._get_status(o),
                'actions': self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)
    

class VendorDetailsView(CompanyAdminLoginRequiredMixin, DetailView):
    template_name='vendors/vendor_details.html'
    model = Vendor

class VendorReceviedListView(CompanyAdminLoginRequiredMixin, ListView):
    model = PurchaseOrder
    template_name = "vendors/vendor_recevied_bill_list.html"
    context_object_name = "vendor_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor_id= self.kwargs.get('pk')
        context["vendor_id"] = vendor_id
        return context


class VendorReceivedBillDataTablesAjaxPagination(DataTableMixin,View):
    model = PurchaseOrder
    
    def get_queryset(self):
        qs = PurchaseOrder.objects.all()
        id_vendor=self.request.GET.get("id_vendor")
        if id_vendor:
            qs=qs.filter(vendor__id=id_vendor)
        return qs.order_by("-id")

    def filter_queryset(self, qs):
        if self.search:
            return qs.filter(
                Q(bill_number__icontains=self.search) |
                Q(bill_date__icontains=self.search) 
            )
        return qs
    
    def get_paid_amount(self,obj):
        id_vendor=self.request.GET.get("id_vendor")
        paid_amount = None
        try:
            paid_amount = VendorBill.objects.get(vendor__id=id_vendor,purchase_order__id=obj.id)
            return paid_amount.paid_amount if obj.id else 0.00
        except Exception:
            paid_amount = 0
            return paid_amount
        
    def get_due_amount(self,obj):
        id_vendor=self.request.GET.get("id_vendor")
        due_amount = None
        try:
            due_amount = VendorBill.objects.get(vendor__id=id_vendor,purchase_order__id=obj.id)
            return due_amount.due_amount if obj.id else 0.00
        except Exception:
            due_amount = 0
            return due_amount
    

    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'company': o.company.company_name,
                'vendor': o.vendor.first_name,
                'bill_number': o.bill_number,
                'bill_date': o.bill_date.strftime("%-d %B, %Y"),
                'total_price': o.total_price,
                'item_count': o.get_product_item_count,
                'paid_amount': self.get_paid_amount(o),
                'due_amount': self.get_due_amount(o),
                # 'received_date': o.bill_number,
                
            }
            for o in qs
        ]
    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)

class VendorDocumentCreateView(CompanyAdminLoginRequiredMixin, CreateView):
    template_name = "vendors/vendor_document_create.html"
    form_class = VendorDocumentCreateForm
    # success_url=reverse("vendors:vendor_list")

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["vendor_pk"] = self.kwargs["vendor_pk"]
        return form_kwargs
    

    def get_context_data(self, **kwargs):
        context= super().get_context_data(**kwargs)
        context['vendor_pk']=self.kwargs["vendor_pk"]
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.add_message(self.request, messages.SUCCESS, "Vendor Document Created Successfully.")
        # return self.render_to_response(self.get_context_data(form=form))
        return HttpResponseRedirect(reverse("vendors:vendor_details", kwargs={'pk': self.kwargs["vendor_pk"]}))


class VendorDocumentsListView(CompanyAdminLoginRequiredMixin,ListView):
    model = VendorDocument
    template_name = "vendors/vendor_documents_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor_id= self.kwargs.get('pk')
        context["vendor_id"] = vendor_id
        return context
    
class VendorDocumentDataTablesAjaxPagination(DataTableMixin,View):
    
    model = VendorDocument

    def get_queryset(self):
        qs = VendorDocument.objects.all()

        id_vendor=self.request.GET.get("id_vendor")
        if id_vendor:
            qs=qs.filter(vendor__id=id_vendor)

        return qs.order_by("-id")
    

    def _get_actions(self, obj):
        id_vendor=self.request.GET.get("id_vendor")

        t = get_template("vendors/get_vendor_upload_document_form.html")
        update_url = reverse("vendors:vendor_document_update", kwargs={"pk": obj.id, "vendor_pk":id_vendor})
        delete_url = reverse("vendors:vendor_document_delete" )
        return f'<div class="row"><center><a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a> <label style="cursor: pointer;" data-title="{obj.document_name}" data-url="{delete_url}" data-id="{obj.id}" title="Delete" class="danger p-0 ajax-delete-btn"><i class="ft-trash font-medium-3"></i></label></center></div>'

    
    def _get_vendor_document(self,obj):
        t = get_template("vendors/get_vendor_document.html")
        return t.render(
            {
                'document':obj.document,
                "obj": obj,

            }
        )


    def filter_queryset(self, qs):
        if self.search:
            return qs.filter(
                Q(document_name__icontains=self.search) 
            )
        return qs
    
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'vendor': o.vendor.email,
                'document_name': o.document_name,
                'document': self._get_vendor_document(o),
                'action': self._get_actions(o),
            }
            for o in qs
        ]
    
    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)
    

class VendorDocumentUpdateView(CompanyAdminLoginRequiredMixin, UpdateView):
    model= VendorDocument
    template_name = "vendors/vendor_document_create.html"
    form_class = VendorDocumentCreateForm
    success_url=reverse_lazy("vendors:vendor_details")

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["vendor_pk"] = self.kwargs["vendor_pk"]
        return form_kwargs
    
    def get_context_data(self, **kwargs):
        context= super().get_context_data(**kwargs)
        context['vendor_pk']=self.kwargs["vendor_pk"]
        return context

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.save()
        messages.add_message(self.request, messages.SUCCESS, "Vendor Document Updated Successfully.")
        return HttpResponseRedirect(reverse("vendors:vendor_details", kwargs={'pk': self.kwargs["vendor_pk"]}))
    

class VendorDocumentDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request):
        vendor_id = self.request.POST.get("id")
        VendorDocument.objects.filter(id=vendor_id).delete()
        return JsonResponse({"message": "Vendor Document Deleted Successfully."})
    
class VendorPaymentCreateView(CompanyAdminLoginRequiredMixin, CreateView):
    model= VendorPayment
    form_class= VendorPaymentCreateForm
    template_name='vendors/vendor_payment_form.html'
    # success_url=reverse_lazy("vendors:vendor_list")


    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company_list"] = Company.objects.filter(status=Company.IS_ACTIVE)
        # print("➡VendorBill.objects.all():", VendorBill.objects.all().aggregate(due_amount = Sum("due_amount")))
        return context
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.save()
        # if self.request.user.role == User.COMPANY_ADMIN:
        #     instance.company = self.request.user.company_users.first().company
        #     instance.save()
        vendor_bill_id_list = self.request.POST.get('vendor_bill_id_list').split(',')

        for vendor_bill_id in vendor_bill_id_list:
            vendor_bill_obj= VendorBill.objects.get(id=vendor_bill_id)
            paid_amount = self.request.POST.get(f"vendor_{vendor_bill_id}__paid_amount")
            # print("➡ paid_amount :", paid_amount)
            due_balance = self.request.POST.get(f"vendor_{vendor_bill_id}__due_balance")
            vendor_bill_obj.paid_amount += float(paid_amount) 
            vendor_bill_obj.due_amount = due_balance
            if int(vendor_bill_obj.due_amount) == 0:
                vendor_bill_obj.status = VendorBill.COMPLETE
            vendor_bill_obj.save()

            VendorPaymentBill.objects.create(vendor_payment=instance, vendor_bill=vendor_bill_obj, amount=paid_amount)
        # return self.render_to_response(self.get_context_data(form=form))
        messages.add_message(self.request, messages.SUCCESS, "Vendor Payment Has Been Successfully")
        return HttpResponseRedirect(reverse("vendors:payment_history_vendors"))

            

class LoadVendorAjax(View):
    def get(self, request):
        data = {
            'vendor_list' : list(Vendor.objects.filter(company__id=request.GET.get('company_id')).values('id', 'first_name')),
        }
        return JsonResponse(data , safe=False)
    

class VendorBillListView(CompanyAdminLoginRequiredMixin, ListView):
    model = VendorBill
    template_name = 'vendors/vendor_bill_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset =  VendorBill.objects.filter(vendor__id =  self.request.GET.get("vendor_id"), status = VendorBill.INCOMPLETE)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        due_amount = VendorBill.objects.filter(vendor__id =  self.request.GET.get("vendor_id")).aggregate(total_due_amount = Sum("due_amount"))
        total_due_amount = due_amount ['total_due_amount']
        context["total_due_amount"] = total_due_amount
        return context
    
class VendorDetailsPaymentListView(CompanyAdminLoginRequiredMixin,ListView):
    model = VendorPayment
    template_name = "vendors/vendor_details_payment_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor_id= self.kwargs.get('pk')
        context["vendor_id"] = vendor_id
        return context
    

class VendorDetailsPaymentDataTablesAjaxPagination(DataTableMixin,View):
    
    model = VendorPayment
    def get_queryset(self):
        qs = VendorPayment.objects.all()
        id_vendor=self.request.GET.get("id_vendor")
        if id_vendor:
            qs=qs.filter(vendor__id=id_vendor)
        return qs.order_by("-id")
    

    # def _get_actions(self, obj):

    #     detail_url = reverse("vendors:vendor_po_detailview")
    #     return f'<div class="row"><center><a href="{detail_url}" title="Detail"><i class="ft-eye font-medium-3 mr-2"></i></a>'
    
    def _get_actions(self, obj):
        """Get action buttons w/links."""
        detail_url = reverse("vendors:payment_history_detail", kwargs={'pk':obj.id})
        return f'<center>  <a href="{detail_url}" title="Detail" ><i class="ft-eye font-medium-3 mr-2 details-btn"></i></a></center>'

    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'vendor': o.vendor.email,
                'reference_number': o.reference_number if o.reference_number else "-----", 
                'payment_mode': o.payment_mode,
                'payment_date': o.payment_date.strftime("%-d %B, %Y"),
                'payment_amount': o.payment_amount,
                'get_no_of_bills':o.get_no_of_bills,
                # 'get_paid_amount':self.get_paid_amount(o),
                'remark': o.remark if o.remark else "-----",
                'actions': self._get_actions(o),
            }
            for o in qs
        ]
    
    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)
    

class VendorPaymentListView(CompanyAdminLoginRequiredMixin,ListView):
    model = VendorBill
    template_name = "vendors/vendor_payment_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor_id= self.kwargs.get('pk')
        context["vendor_id"] = vendor_id
        context['company_list'] = Company.objects.filter(status = Company.IS_ACTIVE)
        return context
    

class VendorPaymentDataTablesAjaxPagination(DataTableMixin,View):
    
    model = VendorBill

    def get_queryset(self):
        qs = VendorBill.objects.all()

        if self.request.user.role == "company admin" or self.request.user.role == "sales representative":
            qs = VendorBill.objects.filter(
                vendor__company__id=self.request.user.get_company_id)

        company = self.request.GET.get("company")
        if company:
            qs = qs.filter(vendor__company__id=company)

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        return qs.order_by("id")
    

    def _get_status(self, obj):
        t = get_template("vendors/get_vendor_payment_status.html")
        return t.render(
            {"vendor": obj, "request": self.request}
        )
    
    def _get_actions(self, obj):
        """Get action buttons w/links."""
        details_url = reverse("vendors:payment_model_ajax", kwargs={"pk": obj.id})
        return f'<center> <label data-id="{obj.id}" data-url="{details_url}" title="Details" data-toggle="modal" data-target="#default" class="danger p-0 mr-2 vendor-payment-history-btn details-btn"><i class="ft-eye font-medium-3" style="color: #975AFF;"></i></label> </center>'


    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'bill_date': f'{o.purchase_order.bill_date.strftime("%-d %B, %Y")}',
                'vendor': o.vendor.first_name,
                'company': o.vendor.company.company_name,
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
    

class VendorPaymentAjaxView(LoginRequiredMixin, ListView):
    template_name = "vendors/payment_details.html"
    model = VendorPaymentBill

    def get_queryset(self):
        qs = VendorPaymentBill.objects.all()
        pk = self.kwargs.get("pk")
        if pk:
            qs = qs.filter(vendor_bill__id=pk)
            return qs
        return super().get_queryset()

class VendorPaymentHistoryDetailsView(CompanyAdminLoginRequiredMixin, DetailView):
    template_name = "vendors/payment_history_details.html"
    model = VendorPayment

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor_id = VendorPayment.objects.get(id=self.kwargs["pk"])
        #print("➡ vendor_id :", vendor_id.id)
        due_amount = VendorBill.objects.filter(vendor__id = vendor_id.id).aggregate(total_due_amount = Sum("due_amount"))
        #print("➡ due_amount :", due_amount)
        total_due_amount = due_amount ['total_due_amount']
        context["total_due_amount"] = total_due_amount if total_due_amount else 0
        return context    
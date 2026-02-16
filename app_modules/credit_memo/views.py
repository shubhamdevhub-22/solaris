from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, View, ListView, UpdateView, DetailView
from app_modules.company.models import Company
from app_modules.credit_memo.forms import CreditMemoForm, CreditMemoProductForm, CreditMemoUpdateForm
from django.urls import reverse, reverse_lazy
from app_modules.credit_memo.models import CreditMemo, CreditMemoLog, CreditMemoProduct
from app_modules.customers.models import Customer
from app_modules.product.models import Product
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, HttpResponseRedirect
from django.contrib import messages
from django_datatables_too.mixins import DataTableMixin
from django.template.loader import get_template
from django.db.models import Q
User = get_user_model()


# Create your views here.

class CreditMemoCreateView(LoginRequiredMixin, CreateView):
    model = CreditMemo
    form_class = CreditMemoForm
    template_name = "credit_memo/credit_memo_create.html"
    
    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form2"] =  CreditMemoProductForm
        return context

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.save()
        if self.request.user.role == User.COMPANY_ADMIN or self.request.user.role == User.SALES_REPRESENTATIVE:
            instance.company = self.request.user.company_users.first().company
            instance.save()
        instance.added_by = self.request.user
        instance.save()
            
        product_ids=self.request.POST.get('product_id_list').split(',')
        
        for product_id in product_ids:
            self.add_product_list_in_credit_memo(instance,product_id)
        messages.add_message(self.request, messages.SUCCESS, "Credit memo created")
        log_msg = "New Credit memo has been Generated"
        CreditMemoLog.objects.create(credit_memo=instance, user=self.request.user, remark=log_msg)
        return HttpResponseRedirect(reverse("credit_memo:credit_memo_list"))

    def add_product_list_in_credit_memo(self,credit_memo,product_id):
        credit_memo = credit_memo
        product_id = product_id
        product=Product.objects.get(id=product_id)
        unit_type = self.request.POST.get(f"product_{product_id}__unit_type")
        quantity = self.request.POST.get(f"product_{product_id}__quantity")
        fresh_quantity = self.request.POST.get(f"product_{product_id}__fresh_quantity")
        damage_quantity = self.request.POST.get(f"product_{product_id}__damage_quantity")
        total_price = self.request.POST.get(f"product_{product_id}__totalprice")
        unit_price = self.request.POST.get(f"product_{product_id}__unitprice")
        new_credit_memo_product=CreditMemoProduct(credit_memo=credit_memo, product=product, unit_type=unit_type, return_quantity=quantity, fresh_return_quantity=fresh_quantity, damage_return_quantity=damage_quantity, total_price=float(total_price), unit_price=float(unit_price))
        new_credit_memo_product.save()


class CreditMemoUpdateView(LoginRequiredMixin, UpdateView):
    model = CreditMemo
    form_class = CreditMemoUpdateForm
    template_name = "credit_memo/credit_memo_update.html"
    
    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form2"] =  CreditMemoProductForm
        return context

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.save()
        if self.request.user.role == User.COMPANY_ADMIN or self.request.user.role == User.SALES_REPRESENTATIVE:
            instance.company = self.request.user.company_users.first().company
            instance.save()
        instance.added_by = self.request.user
        instance.save()

        if instance.status == CreditMemo.APPROVED:
            customer = Customer.objects.filter(id = instance.customer.id).first()
            total_credit = customer.total_credit_amount + instance.grand_total
            customer.total_credit_amount = total_credit
            customer.save()
            
            
            
        product_ids=self.request.POST.get('product_id_list').split(',')
        
        for product_id in product_ids:
            self.add_product_list_in_credit_memo(instance,product_id)
        messages.add_message(self.request, messages.SUCCESS, "Credit memo updated")
        log_msg = "Credit memo has been Updated"
        CreditMemoLog.objects.create(credit_memo=instance, user=self.request.user, remark=log_msg)
        return HttpResponseRedirect(reverse("credit_memo:credit_memo_list"))
    

    def add_product_list_in_credit_memo(self,credit_memo,product_id):
        credit_memo = credit_memo
        product_id = product_id
        product=Product.objects.get(id=product_id)

        to_delete_products = CreditMemoProduct.objects.filter(credit_memo = credit_memo, product=product)
        for to_delete_product in to_delete_products:
            to_delete_product.delete()
        
        unit_type = self.request.POST.get(f"product_{product_id}__unit_type")
        quantity = self.request.POST.get(f"product_{product_id}__quantity")
        fresh_quantity = self.request.POST.get(f"product_{product_id}__fresh_quantity")
        damage_quantity = self.request.POST.get(f"product_{product_id}__damage_quantity")
        total_price = self.request.POST.get(f"product_{product_id}__totalprice")
        unit_price = self.request.POST.get(f"product_{product_id}__unitprice")
        new_credit_memo_product=CreditMemoProduct(credit_memo=credit_memo, product=product, unit_type=unit_type, return_quantity=quantity, fresh_return_quantity=fresh_quantity, damage_return_quantity=damage_quantity, total_price=float(total_price), unit_price=float(unit_price))
        new_credit_memo_product.save()

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == User.COMPANY_ADMIN:
            qs = qs.filter(company__id=self.request.user.get_company_id)
        return qs


class GetCustomersAndProductsByCompanyAjaxView(View):

    template_name = "credit_memo/get_customers_and_products_by_company.html"

    def get(self, request, *args, **kwargs):

        context={}
        data={}
        company_id = request.GET.get("company_id")
        if self.request.user.role == User.SALES_REPRESENTATIVE:
            company_customers = Customer.objects.filter(company = company_id, sales_rep__id = self.request.user.id ,status = Customer.ACTIVE)
        else:
            company_customers = Customer.objects.filter(company = company_id, status = Customer.ACTIVE)
        # company_customers = Customer.objects.filter(company = company_id)
        company_products = Product.objects.filter(company = company_id)

        context['company_customers'] = company_customers
        data['company_customers']=render_to_string(self.template_name,context,request=request)
        context['company_customers'] = None

        context['company_products'] = company_products
        data['company_products']=render_to_string(self.template_name,context,request=request)
        return JsonResponse(data)


class GetProductDetailsAjaxView(View):
    template_name = "credit_memo/get_product_details.html"
    
    def get(self, request, *args, **kwargs):
        context={}
        data={}
        product_id = request.GET['product_id']
        product = get_object_or_404(Product,id=product_id)

        context['product'] = product
        data['product_unit_type']=render_to_string(self.template_name,context,request=request)
        data['product_cost_price'] = product.cost_price
        return JsonResponse(data)


class AddProductInCreditMemoListAjaxView(View):
    #use this on company select
    template_name = "credit_memo/add_product_in_credit_memo_list.html"

    def post(self,request,*args, **kwargs):
        context={}
        data={}
        product_id = request.POST['product_id']
        unit_type = request.POST['unit_type']
        unit_type_text = request.POST['unit_type_text']
        unit_type_pieces = int(request.POST['unit_type_pieces'])
        quantity = int(request.POST['quantity'])
        product = get_object_or_404(Product, id = product_id)
        
        
        
        context['product'] = product
        context['unit_type'] = unit_type 
        context['unit_type_text'] = unit_type_text
        context['unit_type_pieces'] = unit_type_pieces
        context['quantity'] = quantity
        total_pieces = quantity * unit_type_pieces

        context['total_pieces'] = total_pieces
        context['unit_price'] = product.base_price
        total_price = product.base_price * total_pieces
        context['total_price'] = f'{"%.2f" % round(total_price, 2)}' 
        data['product_row']=render_to_string(self.template_name,context,request=request)
        return JsonResponse(data)


class CreditMemoListView(LoginRequiredMixin, ListView):
    template_name = "credit_memo/credit_memo_list.html"
    model = CreditMemo
    context_object_name = "user_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["companies"] = Company.objects.all()
        return context


class CreditMemoDataTablesAjaxPagination(DataTableMixin,View):
    model= CreditMemo
    
    def get_queryset(self):
        """Get queryset."""
        qs = CreditMemo.objects.all()
        if self.request.user.role == User.COMPANY_ADMIN :        
            company = self.request.user.company_users.first().company
            qs = qs.filter(company=company)

        if self.request.user.role == User.SALES_REPRESENTATIVE:
            company = self.request.user.company_users.first().company
            qs = qs.filter(company=company,customer__sales_rep__id=self.request.user.id)

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        company = self.request.GET.get("company")
        if company:
            qs = qs.filter(company__id=company)
        return qs.order_by("-id")

    def _get_actions(self, obj):
        """Get action buttons w/links."""
        detail_url = reverse("credit_memo:credit_memo_detail", kwargs={"pk": obj.id})
        update_url = reverse("credit_memo:credit_memo_update", kwargs={"pk": obj.id})
        logs_url = reverse("credit_memo:credit_memo_log_ajax", kwargs={"pk": obj.id})
        return f'<center><label data-id="{obj.id}" data-url="{logs_url}" title="Delete" data-toggle="modal" data-target="#default" class="danger p-0 mr-2 credit-memo-log-history-btn"><i class="ft-clock font-medium-3" style="color: #975AFF;"></i></label><a href="{detail_url}" title="View"><i class="ft-eye font-medium-3 mr-2"></i></a><a href="{update_url}" title="View"><i class="ft-edit font-medium-3 mr-2"></i></a></center>'

    def _get_status(self, obj):
        t = get_template("credit_memo/get_credit_memo_status.html")
        return t.render(
            {"obj": obj, "request": self.request}
        )

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        # If a search term, filter the query

        if self.search:
            return qs.filter(
                Q(full_name__icontains=self.search) |
                Q(email__icontains=self.search)
            )
        return qs
    
    def get_customer_details(self, obj):
        t = get_template("reports/report_customer_details.html")
        return t.render(
            {"customer_id": obj.customer}
        )
    
    def prepare_results(self, qs):
        # if self.request.user.role == User.COMPANY_ADMIN:
        #     return [
        #         {
        #             'id': o.id,
        #             'email': o.email,
        #             'full_name': o.full_name,
        #             'phone': o.phone,
        #             'role': o.role.title(),
        #             'actions': self._get_actions(o),
        #         }
        #         for o in qs
        #     ]
        # else:
        return [
            {
                'id': o.id,
                'company': o.company.company_name,
                'date': o.date,
                'credit_type': o.credit_type,
                'customer': self.get_customer_details(o),
                'amount': o.grand_total,
                'items': o.item_count,
                'status': self._get_status(o),
                'actions': self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class CreditMemoDetailView(DetailView):
    template_name='credit_memo/credit_memo_details.html'
    model = CreditMemo

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["credit_memo_products"] = CreditMemoProduct.objects.filter(credit_memo__id=self.kwargs["pk"])
        return context
    

class AjaxGetUpdateProductDetailsCreditMemo(View):
    template_name = "credit_memo/add_product_in_credit_memo_list.html"

    def get(self, request, *args, **kwargs):
        context={}
        data={}
        credit_memo_id = request.GET['credit_memo_id']
        credit_memo_products = CreditMemoProduct.objects.filter(credit_memo=credit_memo_id)
        credit_memo_products_ids = list(credit_memo_products.values_list('product',flat=True))
        context['credit_memo_products'] = credit_memo_products
        context['credit_memo_update_id'] = credit_memo_id
        data['credit_memo__product_ids'] = credit_memo_products_ids
        data['existing_product_list']=render_to_string(self.template_name,context,request=request)
        return JsonResponse(data)


class CreditMemoLogAjaxView(LoginRequiredMixin, ListView):
    template_name = "credit_memo/credit_memo_log_list.html"
    model = CreditMemoLog

    def get_queryset(self):
        qs = CreditMemoLog.objects.all()
        pk = self.kwargs.get("pk")
        if pk:
            qs = qs.filter(credit_memo__id=pk)
        return super().get_queryset()
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["credit_memo_id"] = self.kwargs.get("pk")
        return context


class CreditMemoLogDatatableAjaxView(DataTableMixin,View):
    model= CreditMemoLog
    
    def get_queryset(self):
        """Get queryset."""
        qs = CreditMemoLog.objects.all()
        credit_memo_id = self.request.GET.get("credit_memo_id")
        if credit_memo_id:
            qs = qs.filter(credit_memo__id=credit_memo_id)

        return qs.order_by("-id")

    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'action_by': o.user.full_name,
                'remark': o.remark,
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)
import random
import string
from typing import Any, Dict
import uuid
from django.forms.models import BaseModelForm 
from django.shortcuts import render, redirect, HttpResponse, HttpResponseRedirect
from django.views.generic import CreateView, UpdateView, ListView, DeleteView, TemplateView, View, DetailView
from django.urls import reverse_lazy, reverse
from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from app_modules.base.mixins import AdminLoginRequiredMixin, CompanyAdminLoginRequiredMixin, SalesLoginRequiredMixin
from app_modules.company.models import Company, CompanyUsers
from app_modules.users.forms import AddRoleForm, PasswordResetForm, UserCreateForm, UserUpdateForm, ProfileManageForm 
from django_datatables_too.mixins import DataTableMixin
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from app_modules.users.models import WorkingHours
from app_modules.users.tasks import send_email_notifications
from app_modules.order.models import Order
from app_modules.purchase_order.models import PurchaseOrder
from app_modules.customers.models import Customer, CustomerPaymentBill, Payment
from app_modules.credit_memo.models import CreditMemo
from django.contrib.auth.models import Group
import datetime
from datetime import date, timedelta
from django.conf import settings
from allauth.account.views import PasswordChangeView
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError



User = get_user_model()
def handler404(request, args, *argv):
    return render(request, "404.html", status=404)
def handler403(request, args, *argv):
    return render(request, "403.html", status=403)

# Create your views here.

class DasboardTemplateView(CompanyAdminLoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        company_obj = self.request.user.get_company_id
        if company_obj is not None:
            presentdate = datetime.date.today()
            afterdate = datetime.date.today() - datetime.timedelta(days=7)

            context["total_week_sales_orders"] = Order.objects.filter(company__id = company_obj, order_date__range = [afterdate, presentdate]).count()

            context["total_week_purchase_orders"] = PurchaseOrder.objects.filter(company__id=company_obj, bill_date__range = [afterdate,presentdate]).count()

            units_orders = Order.objects.filter(company__id = company_obj,order_date__range = [afterdate, presentdate], status= Order.SHIPPED)
            # print("➡ units_orders :", units_orders)
            unit_sold_count = 0
            for units_order in units_orders:
                unit_order = units_order.orders.all()
                for unit in unit_order:
                    unit_value = unit.get_total_pieces
                    unit_sold_count+=unit_value
                    # print("➡ unit_sold_count :", unit_sold_count)
            context["unit_sold_count"] = unit_sold_count
            # week_customers_data = CustomerPaymentBill.objects.filter(customer_payment__customer_name__company__id= company_obj,created_at__range = [afterdate, presentdate])
            # total_earning = 0
            # for week_customer_data in week_customers_data:
            #     total_earning = int(total_earning)+int(week_customer_data.amount)
            # context["total_week_earning"] = total_earning

            # units_orders = Order.objects.filter(company__id = company_obj, order_date__range = [afterdate, presentdate]).count()
            # print("➡ units_orders :", units_orders)

            orders = Order.objects.filter(company__id=company_obj, order_date__range = [afterdate, presentdate])
            total_sales = 0
            for order in orders:
                total_sales = int(total_sales)+int(order.item_total)
            context["total_week_order_sales"] = total_sales

            context["last_5_orders"] = Order.objects.filter(company__id=company_obj).order_by('-id')[:5]

            # company_xyz=Company.objects.filter(id=company_obj)
            # customer_xyz = Customer.objects.filter(company__in=company_xyz).values_list("id",flat=True)

            # print("➡ company_xyz :", company_xyz)
            # print("➡ customer_xyz :", customer_xyz)
            # print("➡ last_5_customers_payment :", Payment.objects.filter(customer_name__id__in = company_xyz).order_by('-id')[:5])
            context["last_5_customers_payment"] = Payment.objects.filter(customer_name__company=Company.objects.get(id=company_obj)).order_by('-id')[:5]

            context["last_5_credit_memo"] = CreditMemo.objects.filter(company__id=company_obj).order_by('-id')[:5]

            first_day_of_current_month = date.today().replace(day=1)
            last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
            last_day_of_previous_6_month = first_day_of_current_month - timedelta(days=180)
            static_orders = Order.objects.filter(company__id=company_obj,status=Order.SHIPPED, order_date__range = [last_day_of_previous_6_month, last_day_of_previous_month])

            return self.get_chart_bar_calculation(
                first_day_of_current_month, static_orders, context
            )
        
        presentdate = datetime.date.today()
        afterdate = datetime.date.today() - datetime.timedelta(days=7)
        context["total_week_sales_orders"] = Order.objects.filter(order_date__range = [afterdate, presentdate]).count()

        context["total_week_purchase_orders"] = PurchaseOrder.objects.filter(bill_date__range = [afterdate,presentdate]).count()

        # week_customers_data = CustomerPaymentBill.objects.filter(created_at__range = [afterdate, presentdate])
        # total_earning = 0
        # for week_customer_data in week_customers_data:
        #     total_earning = int(total_earning)+int(week_customer_data.amount)
        # context["total_week_earning"] = total_earning

        units_orders = Order.objects.filter(order_date__range = [afterdate, presentdate], status= Order.SHIPPED)
        # print("➡ units_orders :", units_orders)
        unit_sold_count = 0
        for units_order in units_orders:
            unit_order = units_order.orders.all()
            for unit in unit_order:
                unit_value = unit.get_total_pieces
                unit_sold_count+=unit_value
                # print("➡ unit_sold_count :", unit_sold_count)
        context["unit_sold_count"] = unit_sold_count

        orders = Order.objects.filter(order_date__range = [afterdate, presentdate])
        total_sales = 0
        for order in orders:
            total_sales = int(total_sales)+int(order.item_total)
        context["total_week_order_sales"] = total_sales

        context["last_5_orders"] = Order.objects.all().order_by('-id')[:5]

        context["last_5_customers_payment"] = Payment.objects.all().order_by('-id')[:5]

        context["last_5_credit_memo"] = CreditMemo.objects.all().order_by('-id')[:5]

        first_day_of_current_month = date.today().replace(day=1)
        last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
        last_day_of_previous_6_month = first_day_of_current_month - timedelta(days=180)
        static_orders = Order.objects.filter(status=Order.SHIPPED, order_date__range = [last_day_of_previous_6_month, last_day_of_previous_month])

        return self.get_chart_bar_calculation(
            first_day_of_current_month, static_orders, context
        )

    def get_chart_bar_calculation(self, first_day_of_current_month, static_orders, context):
        end_day_of_1st_last_month = first_day_of_current_month - timedelta(days=1)
        start_day_of_1st_last_month = date.today().replace(day=1) - timedelta(days=end_day_of_1st_last_month.day)
        last1stmonth=static_orders.filter(order_date__range = [start_day_of_1st_last_month, end_day_of_1st_last_month]).count()
        # print("➡ last1stmonth :", last1stmonth)
        context["last_1st_month"] = last1stmonth

        end_day_of_2nd_last_month = start_day_of_1st_last_month - timedelta(days=1)
        start_day_of_2nd_last_month = start_day_of_1st_last_month - timedelta(days=end_day_of_2nd_last_month.day)
        last2ndmonth=static_orders.filter(order_date__range = [start_day_of_2nd_last_month, end_day_of_2nd_last_month]).count()
        # print("➡ last2ndmonth :", last2ndmonth)
        context["last_2nd_month"] = last2ndmonth

        end_day_of_3rd_last_month = start_day_of_2nd_last_month - timedelta(days=1)
        start_day_of_3rd_last_month = start_day_of_2nd_last_month - timedelta(days=end_day_of_3rd_last_month.day)
        last3rdmonth=static_orders.filter(order_date__range = [start_day_of_3rd_last_month, end_day_of_3rd_last_month]).count()
        # print("➡ last3rdmonth :", last3rdmonth)
        context["last_3rd_month"] = last3rdmonth

        end_day_of_4th_last_month = start_day_of_3rd_last_month - timedelta(days=1)
        start_day_of_4th_last_month = start_day_of_3rd_last_month - timedelta(days=end_day_of_4th_last_month.day)
        last4thmonth=static_orders.filter(order_date__range = [start_day_of_4th_last_month, end_day_of_4th_last_month]).count()
        # print("➡ last4thmonth :", last4thmonth)
        context["last_4th_month"] = last4thmonth

        end_day_of_5th_last_month = start_day_of_4th_last_month - timedelta(days=1)
        start_day_of_5th_last_month = start_day_of_4th_last_month - timedelta(days=end_day_of_5th_last_month.day)
        last5thmonth=static_orders.filter(order_date__range = [start_day_of_5th_last_month, end_day_of_5th_last_month]).count()
        # print("➡ last5thmonth :", last5thmonth)
        context["last_5th_month"] = last5thmonth

        end_day_of_6th_last_month = start_day_of_5th_last_month - timedelta(days=1)
        start_day_of_6th_last_month = start_day_of_5th_last_month - timedelta(days=end_day_of_6th_last_month.day)
        last6thmonth=static_orders.filter(order_date__range = [start_day_of_6th_last_month, end_day_of_6th_last_month]).count()
        # print("➡ last6thmonth :", last6thmonth)
        context["last_6th_month"] = last6thmonth

        return context
    
class UserListView(CompanyAdminLoginRequiredMixin, ListView):
    template_name = "users/user_list.html"
    model = User
    context_object_name = "user_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["companies"] = Company.objects.all()
        if self.request.user.is_authenticated:
            user_id = self.request.user.id
            user = User.objects.filter(id=user_id).first()
            image = user.image 
            if image:
                context["image"] = image.url
        return context
    
    # def get_context_data(self, **kwargs):
    #     context =  super().get_context_data(**kwargs)
    #     if self.request.user.is_authenticated:
    #         user_id = self.request.user.id
    #         user = User.objects.filter(id=user_id).first()
    #         image = user.image 
    #         if image:
    #             context["image"] = image.url
    #     return context
    
class RoleCreateView(CompanyAdminLoginRequiredMixin, CreateView):
    template_name = "users/role_create.html"
    model = Group
    form_class = AddRoleForm
    success_url = reverse_lazy("users:user_list")

class UserCreateView(CompanyAdminLoginRequiredMixin, CreateView):
    template_name = "users/user_create.html"
    model = User
    form_class = UserCreateForm

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    # def get_form(self, form_class=None):
    #     form = super(UserCreateView, self).get_form(form_class)
    #     for visible in form.visible_fields():
    #         visible.field.widget.attrs.update({'class': 'form-control'})
    #     return form
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.username = form.cleaned_data['username']
        instance.email = form.cleaned_data['email']
        instance.save()
        password = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        instance.set_password(password)
        phone = form.cleaned_data['phone']
        if phone:
            instance.phone = f"+91{phone}"
        instance.save()

        if instance.role in [User.SUPER_ADMIN, User.COMPANY_ADMIN, User.SALES_REPRESENTATIVE, User.ACCOUNTANT] and form.cleaned_data['email']:
            target_link = self.request.build_absolute_uri(reverse('account_login'))
            context = {
                "email" : instance.email,
                "username" : instance.username,
                "password" : password,
                "target_link" : target_link,
            }
            print("➡ context :", context)
            send_email_notifications.delay(
                subject = "Welcome to Solaris",
                template="users/user_email.html",
                context = context,
                to_emails = [instance.email],
            )
        if self.request.user.role == User.COMPANY_ADMIN:
            company = self.request.user.company_users.first().company
            CompanyUsers.objects.create(
                company = company,
                user = instance
            )
        else:
            company_id = form.data.get("company")
            if company_id:
                company = Company.objects.get(id=company_id)
                CompanyUsers.objects.create(
                    company = company,
                    user = instance
                )
        if instance.role not in [User.SUPER_ADMIN, User.COMPANY_ADMIN, User.COMPANY_SUPER_ADMIN]:
            self.create_default_working_hours(instance)

        messages.add_message(self.request, messages.SUCCESS, "User Created Successfully.")
        return HttpResponseRedirect(reverse("users:user_list"))

    def create_default_working_hours(self, user):
        for week_day, day_name in WorkingHours.DAYS_OF_WEEK:
            WorkingHours.objects.create(
                user=user,
                week_day=week_day,
                start_time=datetime.time(9, 0),
                end_time=datetime.time(18, 0)
            )

class UserUpdateView(CompanyAdminLoginRequiredMixin, UpdateView):
    template_name = "users/user_update.html"
    model = User
    form_class = UserUpdateForm

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs
    
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == User.COMPANY_ADMIN:
            company = list(self.request.user.company_users.all().values_list("company_id", flat=True))
            company_users = list(CompanyUsers.objects.filter(company__id__in=company).values_list("user__id", flat=True))
            qs = qs.filter(id__in=company_users)
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('pk')
        print('user_id: ', user_id)
        if user_id:
            user = User.objects.get(id=user_id)
            working_hours = WorkingHours.objects.filter(user=user)
            print('working_hours: ', working_hours)
            context['working_hours'] = working_hours
            # context['user_pk'] = user_id
            context['user_obj'] = user
        context['user_password_reset_form'] = PasswordResetForm()
        return context
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        phone = form.cleaned_data['phone']
        if phone:
            instance.phone = f"+91{phone}"
        instance.save()

        company_id = form.data.get("company")
        if company_id:
            company = Company.objects.get(id=company_id)
            if 'company' in form.changed_data:
                company_user = CompanyUsers.objects.filter(user=instance).first()
                if company_user:
                    company_user.company = company
                    company_user.save()
                else:
                    CompanyUsers.objects.create(
                        company = company,
                        user = instance
                    )
        else:
            CompanyUsers.objects.filter(user=instance).delete()

        messages.add_message(self.request, messages.SUCCESS, "User Updated Successfully.")
        return HttpResponseRedirect(reverse("users:user_list"))

class HomeView(View):
    def get(self, request, *args, **kwargs):
        return redirect(reverse("dashboard"))

class UserDataTablesAjaxPagination(DataTableMixin,View):
    model= User
    
    def get_queryset(self):
        """Get queryset."""
        qs = User.objects.all()
        if self.request.user.role == User.COMPANY_ADMIN:
            company = list(self.request.user.company_users.all().values_list("company_id", flat=True))
            company_users = list(CompanyUsers.objects.filter(company__id__in=company).values_list("user__id", flat=True))
            qs = qs.filter(id__in=company_users)

        role = self.request.GET.get("role")
        if role:
            qs = qs.filter(role=role)

        company = self.request.GET.get("company")
        if company:
            company_users = list(CompanyUsers.objects.filter(company__id=company).values_list("user_id", flat=True))
            qs = qs.filter(id__in=company_users)
        return qs.order_by("-id")

    def _get_actions(self, obj):
        """Get action buttons w/links."""
        # update_url = reverse("users: user_update", kwargs={"pk": obj.id})
        update_url = reverse("users:user_update", kwargs={"pk": obj.id})
        delete_url = reverse("users:user_delete")
        return f'<center><a href="{update_url}" title="Edit"><i class="ft-edit font-medium-3 mr-2"></i></a> <label data-title="{obj.full_name}" style="cursor: pointer;" data-url="{delete_url}" data-id="{obj.id}" title="Delete" class="danger p-0 ajax-delete-btn"><i class="ft-trash font-medium-3"></i></label></center>'


    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        # If a search term, filter the query

        if self.search:
            return qs.filter(
                Q(full_name__icontains=self.search) |
                Q(email__icontains=self.search)
            )
        return qs
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
                'email': o.email,
                'full_name': o.full_name,
                'username': o.username,
                'phone': o.phone if o.phone else "-",
                'role': o.role.title() if o.role else "-",
                'company': o.company,
                'actions': self._get_actions(o),
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)

class UserDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request):
        user_id = self.request.POST.get("id")
        User.objects.filter(id=user_id).delete()
        return JsonResponse({"message": "User Deleted Successfully."})

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "users/profile_manage.html"
    model = User
    form_class = ProfileManageForm

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            user_id = self.request.user.id
            user = User.objects.filter(id=user_id).first()
            image = user.image 
            if image:
                context["image"] = image.url
        return context
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        # form.cleaned_data["phone"]
        # print("➡ form.cleaned_data :", form.cleaned_data["image"])
        image= self.request.FILES.get("image")

        if image:

            user = User.objects.get(id=instance.id)
            user.image = image
            user.save()
        # else:
        #     user = User.objects.get(id=instance.id)
        #     user.image = "none"
        #     user.save()

        instance.save()
        # print("➡ image :", image)

        messages.add_message(self.request, messages.SUCCESS, "User Updated Successfully.")
        if self.request.user.role != User.SALES_REPRESENTATIVE:
            return HttpResponseRedirect(reverse("dashboard"))
        else:
            return HttpResponseRedirect(reverse("order:order_list"))

    success_url = reverse_lazy("dashboard")


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """
    Overriding Allauth view so we can redirect to profile home.
    """
    def get_success_url(self):
        """
        Return the URL to redirect to after processing a valid form.

        Using this instead of just defining the success_url attribute
        because our url has a dynamic element.
        """
        success_url = reverse("account_logout")
        return success_url
    
class UpdateWorkingHoursView(View):
    def post(self, request, *args, **kwargs):
        week_day = request.POST.get('week_day')
        update_user_id = request.POST.get('update_user_id')
        day_status = request.POST.get('day_status') == 'true'
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        user_obj = User.objects.get(id=update_user_id)
        print('week_day: ', week_day)
        if week_day is not None:    
            # Fetch or create the WorkingHours object
            working_hours, created = WorkingHours.objects.update_or_create(
                user=user_obj,
                week_day=week_day,
                defaults={
                    'day_status': day_status,
                    'start_time': start_time,
                    'end_time': end_time
                }
            )
            return JsonResponse({'success': True,"message": "Working Hours Updated Successfully."})
        return JsonResponse({'success': False}, status=400)

class UserPasswordResetView(View):
    def post(self, request, *args, **kwargs):
        form = PasswordResetForm(request.POST)
        
        if form.is_valid():
            user_id = request.POST.get('user_id')
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']

            # Check if passwords match
            if password1 != password2:
                return JsonResponse({
                    'success': False,
                    'message': {
                        '__all__': [{'message': 'Passwords do not match'}]
                    }
                })
            
            # Validate password using Django's password validators
            try:
                validate_password(password1)
            except ValidationError as e:
                return JsonResponse({
                    'success': False,
                    'message': {
                        '__all__': [{'message': ' '.join(e.messages)}]
                    }
                })

            # Retrieve user and update password
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': {
                        '__all__': [{'message': 'User not found'}]
                    }
                })

            user.password = make_password(password1)
            user.save()

            return JsonResponse({'success': True, 'message': 'Password has been updated successfully.'})

        # Handle form validation errors
        return JsonResponse({'success': False, 'message': form.errors.as_json()})


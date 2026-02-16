import csv
from typing import Any, Dict
from django.shortcuts import render
from django.views.generic import ListView, View, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django_datatables_too.mixins import DataTableMixin
from app_modules.base.mixins import CompanyAdminLoginRequiredMixin, AccountantLoginRequiredMixin
from app_modules.company.models import CompanyUsers
from app_modules.customers.models import Customer, CustomerBill, Zone, CustomerPaymentBill
from app_modules.order.models import Order, OrderBill
from app_modules.reports.models import SalesRepCommissionCodeReport
from app_modules.users.models import User
from django.template.loader import get_template
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Sum, F, ExpressionWrapper, FloatField
from django.utils.dateparse import parse_date

from app_modules.order import utils
from datetime import datetime, timedelta
from num2words import num2words

# Create your views here.

class ZoneWiseCollectionReport(AccountantLoginRequiredMixin, ListView):
    template_name = "reports/collection-report/zone_wise_collection_report.html"
    model = OrderBill

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.role in [User.COMPANY_ADMIN, User.ACCOUNTANT]:
            context["sales_rep"] = CompanyUsers.objects.filter(company__id=self.request.user.get_company_id,user__role=User.SALES_REPRESENTATIVE)
            context["customer_list"] = Customer.objects.filter(company__id=self.request.user.get_company_id,status=Customer.ACTIVE)
            context["zone_list"] = Zone.objects.filter(company__id=self.request.user.get_company_id)
        else:
            context["sales_rep"] = CompanyUsers.objects.filter(user__role=User.SALES_REPRESENTATIVE)
            context["customer_list"] = Customer.objects.filter(status=Customer.ACTIVE)
            context["zone_list"] = Zone.objects.all()
        return context


class ZoneWiseCollectionReportAjax(LoginRequiredMixin, DataTableMixin, View):
    model = OrderBill

    def get_queryset(self):
        qs = OrderBill.objects.all()
        
        if self.request.user.role in [User.COMPANY_ADMIN, User.ACCOUNTANT]:
            qs = qs.filter(customer__company__id = self.request.user.get_company_id)
        
        zone = self.request.GET.get("zone")
        start_date = self.request.GET.get("from_date")
        end_date = self.request.GET.get("to_date")
        
        # if start_date and end_date:
        #     qs =qs.filter(created_at__range=[start_date, end_date]).distinct()
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            qs = qs.filter(bill_date__gte = start_date_obj).distinct()

        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            qs = qs.filter(bill_date__lte = end_date_obj).distinct()

        if zone:
            qs = qs.filter(customer__zone__id=zone).distinct()
        
        return qs.order_by("-id")

    def filter_queryset(self, qs):
        if self.search:
            return qs.filter(
                Q(customer__customer_name__icontains = self.search)
            )
        return qs
    
    def get_order_details(self, obj):
        t = get_template("reports/report_order_details.html")
        return t.render(
            {"order": obj.order }
        )
    
    def get_customer_details(self, obj):
        t = get_template("reports/report_customer_details.html")
        return t.render(
            {"customer_id": obj.customer}
        )
    
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'bill_date': f'{o.bill_date.strftime("%-d %B, %Y")}',
                'customer': self.get_customer_details(o),
                'customer__zone': o.customer.zone.zone_code if o.customer.zone else "-",
                'slip_no': o.slip_no if o.slip_no else "-",
                'bill_amount': o.bill_amount,
                'paid_amount': o.paid_amount,
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class ExportCollectionReport(ListView):
    template_name = "reports/collection-report/export-collection-report.html"
    model = OrderBill

    def get(self, request, type):
        zone = self.request.GET.get("zone")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        queryset = OrderBill.objects.all()
        context = {}

        if self.request.user.role in [User.COMPANY_ADMIN, User.ACCOUNTANT]:
            queryset = queryset.filter(customer__company__id=self.request.user.get_company_id)

        if zone:
            queryset = queryset.filter(customer__zone__id = zone)
            zone = Zone.objects.filter(id = zone).last()
            context["zone"] = zone.zone_code
        
        backup_queryset = queryset

        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            queryset = queryset.filter(bill_date__gte = start_date_obj).distinct()
            before_start_date = start_date_obj - timedelta(days=1)
            context["start_date"] = start_date_obj
        else:
            before_start_date = ""

        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            queryset = queryset.filter(bill_date__lte = end_date_obj).distinct()
            context["end_date"] = end_date_obj
        else:
            end_date_obj = datetime.today().date()
            context["end_date"] = end_date_obj

        if type == "balance":
            customer_list = list(queryset.values_list("customer", flat=True).distinct())
            customers = Customer.objects.filter(status = Customer.ACTIVE, id__in = customer_list)
        else:
            customers = Customer.objects.filter(status = Customer.ACTIVE)

        collection_list = {}
        for customer in customers:
            customer_bills = queryset.filter(customer = customer)
            backup_customer_bills = backup_queryset.filter(customer = customer)

            total_payment_amount = 0
            total_bill_amount = 0
            before_start_date_bill_total = 0
            before_start_date_payment_total = 0
            bill_list = {}

            if start_date:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                before_start_date_payment_list = backup_customer_bills.filter(bill_date__lt = start_date_obj)

                if before_start_date_payment_list.count() > 0:
                    before_start_date_bill_total = before_start_date_payment_list.aggregate(total_bill_amount = Sum("bill_amount"))["total_bill_amount"]
                    before_start_date_payment_total = before_start_date_payment_list.aggregate(total_payment = Sum("paid_amount"))["total_payment"]

            before_end_date_payments = backup_customer_bills.filter(bill_date__lte = end_date_obj)
            
            if before_end_date_payments.count() > 0:
                total_bill_amount = before_end_date_payments.aggregate(total_bill_amount = Sum("bill_amount"))["total_bill_amount"]
                total_payment_amount = before_end_date_payments.aggregate(total_payment = Sum("paid_amount"))["total_payment"]

            else:
                if customer_bills.count() > 0:
                    total_bill_amount = customer_bills.aggregate(total_bill_amount = Sum("bill_amount"))["total_bill_amount"]
                    total_payment_amount = customer_bills.aggregate(total_payment = Sum("paid_amount"))["total_payment"]

            bill_list["customer_bills"] = customer_bills
            bill_list["before_start_date"] = before_start_date
            bill_list["before_start_date_bill_total"] = before_start_date_bill_total
            bill_list["before_start_date_payment_total"] = before_start_date_payment_total
            bill_list["total_payment_amount"] = total_payment_amount
            bill_list["total_bill_amount"] = total_bill_amount
            bill_list["total_pending_amount"] = total_bill_amount - total_payment_amount
            collection_list[customer] = bill_list

        context["collection_list"] = collection_list
        pdf = utils.render_to_pdf(self.template_name, context)

        return HttpResponse(pdf, content_type='application/pdf')

class ExportDailyBillReport(ListView):
    template_name = "reports/daily-bill-report/export_daily_bill_report.html"
    model = OrderBill

    def get(self, request):
        qs = OrderBill.objects.all()        
        if self.request.user.role in [User.COMPANY_ADMIN, User.ACCOUNTANT]:
            qs = qs.filter(customer__company__id = self.request.user.get_company_id)
        
        zone = self.request.GET.get("zone")
        start_date = self.request.GET.get("start_date")
        context = {}

        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            # end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            # qs =qs.filter(created_at__date__range=[start_date, end_date]).distinct()
            qs=qs.filter(created_at__date=start_date).distinct()
            context["start_date"]= start_date

        if zone:
            qs = qs.filter(customer__zone__id=zone).distinct()
            zone_obj = Zone.objects.filter(id = zone).last()
            if zone_obj:
                context["zone"] = zone_obj.zone_code
        
        context["order_bills"] = qs
        paid_total = qs.filter(status = OrderBill.COMPLETE)

        if paid_total:
            context["paid_total"] = paid_total.aggregate(total=Sum("paid_amount"))["total"]
        else:
            context["paid_total"] = 0.0
        
        unpaid_total = qs.filter(status = OrderBill.INCOMPLETE)
        if unpaid_total:
            context["unpaid_total"] = unpaid_total.aggregate(total=Sum("due_amount"))["total"]
        else:
            context["unpaid_total"] = 0.0
        pdf = utils.render_to_pdf(self.template_name, context)

        return HttpResponse(pdf, content_type='application/pdf')


class ExportBillSummaryReport(ListView):
    template_name = "reports/bill-summary-report/export-bill-summary-report.html"
    model = OrderBill

    def get(self, request):
        zone = self.request.GET.get("zone")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        queryset = self.get_queryset().annotate(
                remaining_amount = ExpressionWrapper(
                    F("bill_amount") - F("customer__credit_amount"), output_field=FloatField()
                )
            ).filter(remaining_amount__gt = 0)
        context = {}

        if self.request.user.role in [User.COMPANY_ADMIN, User.ACCOUNTANT]:
            queryset = queryset.filter(customer__company__id = self.request.user.get_company_id)

        if zone:
            queryset = queryset.filter(customer__zone__id = zone)
            zone = Zone.objects.filter(id = zone).last()
            context["zone"] = zone.zone_code

        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            queryset = queryset.filter(bill_date__gte = start_date_obj)
            context["start_date"] = start_date_obj

        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            queryset = queryset.filter(bill_date__lte = end_date_obj)
            context["end_date"] = end_date_obj
        else:
            end_date_obj = datetime.today().date()
            context["end_date"] = end_date_obj
        
        context["order_bills"] = queryset
        context["total_amount"] = queryset.aggregate(total_amount = Sum("bill_amount"))["total_amount"]

        pdf = utils.render_to_pdf(self.template_name, context)
        return HttpResponse(pdf, content_type='application/pdf')


class ExportLedgerReport(ListView):
    template_name = "reports/ledger/export-ledger-report.html"
    model = OrderBill

    def get(self, request):
        zone = self.request.GET.get("zone")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        queryset = self.get_queryset()
        context = {}

        if self.request.user.role in [User.COMPANY_ADMIN, User.ACCOUNTANT]:
            queryset = queryset.filter(customer__company__id = self.request.user.get_company_id)

        if zone:
            queryset = queryset.filter(customer__zone__id = zone)
            zone = Zone.objects.filter(id = zone).last()
            context["zone"] = zone.zone_code
        
        backup_queryset = queryset

        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            queryset = queryset.filter(bill_date__gte = start_date_obj).distinct()
            before_start_date = start_date_obj - timedelta(days=1)
            context["start_date"] = start_date_obj
        else:
            before_start_date = ""

        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            queryset = queryset.filter(bill_date__lte = end_date_obj).distinct()
            context["end_date"] = end_date_obj
        else:
            end_date_obj = datetime.today().date()
            context["end_date"] = end_date_obj

        customers = Customer.objects.filter(status = Customer.ACTIVE)

        collection_list = {}

        for customer in customers:
            customer_bills = queryset.filter(customer = customer)
            backup_customer_bills = backup_queryset.filter(customer = customer)

            total_payment_amount = 0
            total_bill_amount = 0
            before_start_date_bill_total = 0
            before_start_date_payment_total = 0
            bill_list = {}

            if start_date:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                before_start_date_payment_list = backup_customer_bills.filter(bill_date__lt = start_date_obj)

                if before_start_date_payment_list.count() > 0:
                    before_start_date_bill_total = before_start_date_payment_list.aggregate(total_bill_amount = Sum("bill_amount"))["total_bill_amount"]
                    before_start_date_payment_total = before_start_date_payment_list.aggregate(total_payment = Sum("paid_amount"))["total_payment"]

            before_end_date_payments = backup_customer_bills.filter(bill_date__lte = end_date_obj)
            
            if before_end_date_payments.count() > 0:
                total_bill_amount = before_end_date_payments.aggregate(total_bill_amount = Sum("bill_amount"))["total_bill_amount"]
                total_payment_amount = before_end_date_payments.aggregate(total_payment = Sum("paid_amount"))["total_payment"]

            else:
                if customer_bills.count() > 0:
                    total_bill_amount = customer_bills.aggregate(total_bill_amount = Sum("bill_amount"))["total_bill_amount"]
                    total_payment_amount = customer_bills.aggregate(total_payment = Sum("paid_amount"))["total_payment"]

            bill_list["customer_bills"] = customer_bills
            bill_list["before_start_date"] = before_start_date
            bill_list["before_start_date_bill_total"] = before_start_date_bill_total
            bill_list["before_start_date_payment_total"] = before_start_date_payment_total
            bill_list["total_payment_amount"] = total_payment_amount
            bill_list["total_bill_amount"] = total_bill_amount
            bill_list["total_pending_amount"] = total_bill_amount - total_payment_amount
            collection_list[customer] = bill_list

        context["collection_list"] = collection_list
        pdf = utils.render_to_pdf(self.template_name, context)

        return HttpResponse(pdf, content_type='application/pdf')


class DailyBillReport(AccountantLoginRequiredMixin, ListView):
    template_name = "reports/daily-bill-report/daily_bill_report.html"
    model = OrderBill

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.role in [User.COMPANY_ADMIN, User.ACCOUNTANT]:
            context["sales_rep"] = CompanyUsers.objects.filter(company__id=self.request.user.get_company_id,user__role=User.SALES_REPRESENTATIVE)
            context["customer_list"] = Customer.objects.filter(company__id=self.request.user.get_company_id,status=Customer.ACTIVE)
            context["zone_list"] = Zone.objects.filter(company__id=self.request.user.get_company_id)
        else:
            context["sales_rep"] = CompanyUsers.objects.filter(user__role=User.SALES_REPRESENTATIVE)
            context["customer_list"] = Customer.objects.filter(status=Customer.ACTIVE)
            context["zone_list"] = Zone.objects.all()
        return context


class DailyBillReportAjax(LoginRequiredMixin, DataTableMixin, View):
    model = OrderBill

    def get_queryset(self):
        qs = OrderBill.objects.all()
        
        if self.request.user.role in [User.COMPANY_ADMIN, User.ACCOUNTANT]:
            qs = qs.filter(customer__company__id = self.request.user.get_company_id)
        
        zone = self.request.GET.get("zone")
        start_date = self.request.GET.get("from_date")
        # end_date = self.request.GET.get("to_date")
        
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            # end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            # qs =qs.filter(created_at__date__range=[start_date, end_date]).distinct()
            qs =qs.filter(created_at__date=start_date).distinct()

        if zone:
            qs = qs.filter(customer__zone__id=zone).distinct()
        
        return qs.order_by("-id")

    def filter_queryset(self, qs):
        if self.search:
            return qs.filter(
                Q(customer__customer_name__icontains = self.search)
            )
        return qs
    
    def get_order_details(self, obj):
        t = get_template("reports/report_order_details.html")
        return t.render(
            {"order": obj.order }
        )
    
    def get_customer_details(self, obj):
        t = get_template("reports/report_customer_full_detail.html")
        return t.render(
            {"customer": obj.customer}
        )
    
    def prepare_results(self, qs):
        return [
            {
                # 'id': o.id,
                'slip_no': o.slip_no,
                'created_at': f'{o.created_at.strftime("%-d %B, %Y")}',
                'customer': self.get_customer_details(o),
                'order__order_id': self.get_order_details(o),
                'payment_status': "Paid" if o.status == OrderBill.COMPLETE else "Unpaid",
                'bill_amount': o.bill_amount,
                'updated_at': f'{o.updated_at.strftime("%d-%b-%y %I:%M %p")}' if o.updated_at.strftime("%d-%b-%y %I:%M %p") != o.created_at.strftime("%d-%b-%y %I:%M %p") else "",
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class BillSummaryReport(AccountantLoginRequiredMixin, ListView):
    template_name = "reports/bill-summary-report/bill_summary_report.html"
    model = OrderBill

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.role in [User.COMPANY_ADMIN, User.ACCOUNTANT]:
            context["sales_rep"] = CompanyUsers.objects.filter(company__id=self.request.user.get_company_id,user__role=User.SALES_REPRESENTATIVE)
            context["customer_list"] = Customer.objects.filter(company__id=self.request.user.get_company_id,status=Customer.ACTIVE)
            context["zone_list"] = Zone.objects.filter(company__id=self.request.user.get_company_id)
        else:
            context["sales_rep"] = CompanyUsers.objects.filter(user__role=User.SALES_REPRESENTATIVE)
            context["customer_list"] = Customer.objects.filter(status=Customer.ACTIVE)
            context["zone_list"] = Zone.objects.all()
        return context


class BillSummaryReportAjax(LoginRequiredMixin, DataTableMixin, View):
    model = OrderBill

    def get_queryset(self):
        qs = OrderBill.objects.all()
        
        if self.request.user.role in [User.COMPANY_ADMIN, User.ACCOUNTANT]:
            qs = qs.filter(customer__company__id = self.request.user.get_company_id)
        
        zone = self.request.GET.get("zone")
        start_date = self.request.GET.get("from_date")
        end_date = self.request.GET.get("to_date")
        
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            qs =qs.filter(created_at__date__gte=start_date).distinct()
        
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            qs =qs.filter(created_at__date__lte=end_date).distinct()

        if zone:
            qs = qs.filter(customer__zone__id=zone).distinct()

        return qs.order_by("-id")

    def filter_queryset(self, qs):
        if self.search:
            return qs.filter(
                Q(customer__customer_name__icontains = self.search) |
                Q(customer__area__icontains = self.search)
            )
        return qs
    
    def get_customer_details(self, obj):
        t = get_template("reports/customer_details.html")
        return t.render(
            {"customer": obj.customer}
        )
    
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'customer': self.get_customer_details(o),
                'bill_amount': o.bill_amount,
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class LedgerReport(AccountantLoginRequiredMixin, ListView):
    template_name = "reports/ledger/ledger_report.html"
    model = CustomerPaymentBill

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.role in [User.COMPANY_ADMIN, User.ACCOUNTANT]:
            context["sales_rep"] = CompanyUsers.objects.filter(company__id=self.request.user.get_company_id,user__role=User.SALES_REPRESENTATIVE)
            context["customer_list"] = Customer.objects.filter(company__id=self.request.user.get_company_id,status=Customer.ACTIVE)
            context["zone_list"] = Zone.objects.filter(company__id=self.request.user.get_company_id)
        else:
            context["sales_rep"] = CompanyUsers.objects.filter(user__role=User.SALES_REPRESENTATIVE)
            context["customer_list"] = Customer.objects.filter(status=Customer.ACTIVE)
            context["zone_list"] = Zone.objects.all()
        return context


class LedgerReportAjax(LoginRequiredMixin, DataTableMixin, View):
    model = OrderBill

    def get_queryset(self):
        qs = OrderBill.objects.all()
        
        if self.request.user.role in [User.COMPANY_ADMIN, User.ACCOUNTANT]:
            qs = qs.filter(customer__company__id=self.request.user.get_company_id)
        
        zone = self.request.GET.get("zone")
        start_date = self.request.GET.get("from_date")
        end_date = self.request.GET.get("to_date")
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            qs = qs.filter(bill_date__gte = start_date_obj).distinct()

        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            qs = qs.filter(bill_date__lte = end_date_obj).distinct()

        if zone:
            qs = qs.filter(customer__zone__id=zone).distinct()
        
        return qs.order_by("-id")

    def filter_queryset(self, qs):
        if self.search:
            return qs.filter(
                Q(customer__customer_name__icontains = self.search)
            )
        return qs
    
    def get_order_details(self, obj):
        t = get_template("reports/report_order_details.html")
        return t.render(
            {"order": obj.order }
        )
    
    def get_customer_details(self, obj):
        t = get_template("reports/report_customer_details.html")
        return t.render(
            {"customer_id": obj.customer}
        )
    
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'bill_date': f'{o.bill_date.strftime("%-d %B, %Y")}',
                'customer': self.get_customer_details(o),
                'customer__zone': o.customer.zone.zone_code if o.customer.zone else "-",
                'slip_no': o.slip_no if o.slip_no else "-",
                'bill_amount': o.bill_amount,
                'paid_amount': o.paid_amount,
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)

class ReportByDuePaymentListView(AccountantLoginRequiredMixin, ListView):
    template_name = "reports/by_due_list.html"
    model = OrderBill

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.role in [User.COMPANY_ADMIN, User.ACCOUNTANT]:
            context["sales_rep"] = CompanyUsers.objects.filter(company__id=self.request.user.get_company_id,user__role=User.SALES_REPRESENTATIVE)
            context["customer_list"] = Customer.objects.filter(company__id=self.request.user.get_company_id,status=Customer.ACTIVE)
        else:
            context["sales_rep"] = CompanyUsers.objects.filter(user__role=User.SALES_REPRESENTATIVE)
            context["customer_list"] = Customer.objects.filter(status=Customer.ACTIVE)
            context["zone_list"] = Zone.objects.all()
        return context

class ReportByDuePaymentDataTableAjaxPagination(LoginRequiredMixin, DataTableMixin, View):
    model = OrderBill

    def get_queryset(self):

        qs = OrderBill.objects.filter(status=OrderBill.INCOMPLETE).distinct()
        if self.request.user.role in [User.COMPANY_ADMIN, User.ACCOUNTANT]:
            qs = qs.filter(status=OrderBill.INCOMPLETE, customer__company__id=self.request.user.get_company_id).distinct()
            
        sales_rep = self.request.GET.get("sales_rep")
        customer = self.request.GET.get("customer")
        zone = self.request.GET.get("zone")
        start_date = self.request.GET.get("from_date")
        end_date = self.request.GET.get("to_date")
        
        if sales_rep:
            if customer:        
                qs = qs.filter(customer__sales_rep__username=sales_rep, customer=customer).distinct()
                if end_date:
                    qs =qs.filter(customer__sales_rep__username=sales_rep, customer=customer,order__order_date__range=[start_date, end_date]).distinct()
            if end_date:
                qs =qs.filter(customer__sales_rep__username=sales_rep,order__order_date__range=[start_date, end_date]).distinct()
            qs = qs.filter(customer__sales_rep__username=sales_rep).distinct()
        
        if customer:
            if end_date:
                qs =qs.filter(customer=customer,order__order_date__range=[start_date, end_date]).distinct()        
            qs = qs.filter(customer=customer).distinct()

        if end_date:
            qs =qs.filter(order__order_date__range=[start_date, end_date]).distinct()

        if zone:
            qs = qs.filter(customer__zone=zone).distinct()
        
        return qs.order_by("-id")

    def filter_queryset(self, qs):
        # sourcery skip: assign-if-exp, reintroduce-else
        if self.search:
            return qs.filter(
                Q(customer__customer_name__icontains=self.search) 
            )
        return qs
    
    def get_order_details(self, obj):
        t = get_template("reports/report_order_details.html")
        return t.render(
            {"order_id": obj.order.id }
        )
    
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
                'sales_rep': str(o.customer.sales_rep) if o.customer.sales_rep else "-----",
                'order_no': self.get_order_details(o),
                'total_amount': o.bill_amount,
                'total_paid': o.paid_amount,
                'total_due': o.due_amount,
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)
    

class ReportByDueTableCsvAjaxView(LoginRequiredMixin, View):
    
    def get(self, request):
        sales_rep = self.request.GET.get("sales_rep")
        customer = self.request.GET.get("customer")

        response = HttpResponse(content_type='text/csv')  
        response['Content-Disposition'] = 'attachment; filename="Report by due payment file.csv"'

        qs_due_bills_customer = OrderBill.objects.filter(status=OrderBill.INCOMPLETE).distinct()
        if self.request.user.role in [User.COMPANY_ADMIN, User.ACCOUNTANT]:
            qs_due_bills_customer= qs_due_bills_customer.filter(status=OrderBill.INCOMPLETE, customer__company__id=self.request.user.get_company_id)
        
            
        writer = csv.writer(response)  
        writer.writerow(['Customer', 'Sales Rep', 'Order Id',  'Total Amount', 'Total Paid', 'Total Due']) 
        writer.writerow(['', '', '', '', '', '']) 

        if sales_rep:
            if customer:
                qs_due_bills_customer=qs_due_bills_customer.filter(customer__sales_rep__username=sales_rep,customer=customer)
            qs_due_bills_customer=qs_due_bills_customer.filter(customer__sales_rep__username=sales_rep)

        if customer:
            if sales_rep:
                qs_due_bills_customer=qs_due_bills_customer.filter(customer__sales_rep__username=sales_rep,customer=customer)
            qs_due_bills_customer=qs_due_bills_customer.filter(customer=customer)
        
        

        for customer in qs_due_bills_customer:
            # for data in customer_data: 
            customer_name = customer.customer.customer_name
            sales_rep = customer.customer.sales_rep if customer.customer.sales_rep else "-----"
            order_id = customer.order.id
            total_amount = customer.bill_amount
            total_paid = customer.paid_amount
            total_due = customer.due_amount
            writer.writerow([customer_name, sales_rep, order_id, total_amount, total_paid, total_due]) 
        return response
    
    
# class ReportByDueTablePrintAjaxView(LoginRequiredMixin, ListView):
#     template_name = "reports/by_due_table_print.html"
#     model = Customer

#     def get_queryset(self):
#         # sales_rep = self.request.GET.get("sales_rep")
#         customer = Customer.objects.all()
#         order = Order.objects.all()
#         for c in customer:
#             for o in order:
#                 if c.id == o.customer.id:
#                     if o.get_due_amount>=0:
#                         qs = Customer.objects.filter(id=c.id)
#                         return qs
                    

#     # def get_context_data(self, **kwargs):
#     #     context = super().get_context_data(**kwargs)
        
#     #     return context




#views for Commision Report

class ReportByCommisionListView(AccountantLoginRequiredMixin, ListView):
    template_name="reports/by_commision_list.html"
    model = SalesRepCommissionCodeReport

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_obj = self.request.user.company
        
        if company_obj is not None:
            context["sales_rep"] = CompanyUsers.objects.filter(company__company_name=company_obj, user__role=User.SALES_REPRESENTATIVE)
        else:
            context["sales_rep"] = CompanyUsers.objects.filter(user__role=User.SALES_REPRESENTATIVE)
        return context


class ReportByCommisionDataTableAjaxPagination(DataTableMixin, View):
    model = SalesRepCommissionCodeReport

    def get_queryset(self):

        company_obj = self.request.user.company
        
        qs = SalesRepCommissionCodeReport.objects.filter(product_commission_code__gt=0, created_by__role=User.SALES_REPRESENTATIVE)

        if company_obj is not None:
            qs = SalesRepCommissionCodeReport.objects.filter( order_product__order__company__id=self.request.user.get_company_id,product_commission_code__gt=0, created_by__role=User.SALES_REPRESENTATIVE)
        
            
       
        sales_rep = self.request.GET.get("sales_rep")
        start_date = self.request.GET.get("from_date")
        end_date = self.request.GET.get("to_date")

        if sales_rep:
            if end_date:
                return qs.filter(created_by__username=sales_rep, created_at__range=[start_date, end_date])
            return qs.filter(created_by__username=sales_rep)
        
        if end_date:
            if sales_rep:
                return qs.filter(created_at__range=[start_date, end_date], created_by__username=sales_rep)
            return qs.filter(created_at__range=[start_date, end_date])
       

        return qs.order_by("-id")
    
    def filter_queryset(self, qs):
        # sourcery skip: assign-if-exp, reintroduce-else
        if self.search:
            return qs.filter(
                Q(customer__customer_name__icontains=self.search) 
            )
        return qs
    
    def get_order_details(self, obj):
        t = get_template("reports/report_order_details.html")
        return t.render(
            {"order_id": obj.order_product.order.id }
        )
    
    def get_customer_details(self, obj):
        t = get_template("reports/report_customer_details.html")
        return t.render(
            {"customer_id": obj.order_product.order.customer}
        )
    
    
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'created_by': o.created_by.full_name ,
                'order_id': self.get_order_details(o),
                'customer_name': self.get_customer_details(o),
                'product_name': o.order_product.product.name,
                'unit_sold': o.unit_sold,
                'unit_type': o.unit_type,
                'cost_price': o.product_cost_price,
                'sold_price': o.product_sold_price,
                'product_commission_code': o.product_commission_code,
                'total_sales_rep_commision': o.total_sales_rep_commision,
                'product_label': o.product_label or "Not Selected ",
            }
            for o in qs
        ]

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)
    

class ReportByCommisionCsvAjaxPagination(LoginRequiredMixin, View):
    
    def get(self, request):
        
        response = HttpResponse(content_type='text/csv')  
        response['Content-Disposition'] = 'attachment; filename="Report by Commission file.csv"'

        company_obj = self.request.user.company

        qs_due_bills_commision_tax = SalesRepCommissionCodeReport.objects.filter(product_commission_code__gt=0, created_by__role=User.SALES_REPRESENTATIVE).distinct()
        if company_obj is not None:
            qs_due_bills_commision_tax = SalesRepCommissionCodeReport.objects.filter( order_product__order__company__id=self.request.user.get_company_id,product_commission_code__gt=0, created_by__role=User.SALES_REPRESENTATIVE)
        
            
        writer = csv.writer(response)  
        writer.writerow(['Sales Rep', 'Order Id', 'Customer',  'Product Name', 'Quantity', 'Unit Type', 'Product Cost Price', 'Product Sold Price', 'Product label', 'Product Commission (%)', 'Sales Rep Commission']) 
        writer.writerow(['', '', '', '', '', '', '']) 

        sales_rep_data = self.request.GET.get("sales_rep")
        start_date = self.request.GET.get("from_date")
        end_date = self.request.GET.get("to_date")

        if sales_rep_data:
            if end_date:
                qs_due_bills_commision_tax= qs_due_bills_commision_tax.filter(created_by__username=sales_rep_data, created_at__range=[start_date, end_date])
            qs_due_bills_commision_tax= qs_due_bills_commision_tax.filter(created_by__username=sales_rep_data)
        
        if end_date:
            if sales_rep_data:
                qs_due_bills_commision_tax= qs_due_bills_commision_tax.filter(created_at__range=[start_date, end_date], created_by__username=sales_rep_data)
            qs_due_bills_commision_tax= qs_due_bills_commision_tax.filter(created_at__range=[start_date, end_date])


        for commisssion in qs_due_bills_commision_tax:
            # for data in customer_data: 
            sales_rep = commisssion.created_by.full_name
            order_id = commisssion.order_product.order.id
            customer = commisssion.order_product.order.customer.customer_name
            product_name = commisssion.order_product.product.name
            quantity = commisssion.unit_sold
            unit_type = commisssion.unit_type
            product_cost_price = commisssion.product_cost_price
            product_sold_price = commisssion.product_sold_price
            product_label = commisssion.product_label
            product_commssion = commisssion.product_commission_code
            total_sales_rep_commision = commisssion.total_sales_rep_commision
            writer.writerow([sales_rep, order_id, customer, product_name, quantity, unit_type, product_cost_price, product_sold_price, product_label, product_commssion, total_sales_rep_commision]) 
        return response 

#views for ML Report

class ReportByMlListView(AccountantLoginRequiredMixin, ListView):
    template_name="reports/by_ml_list.html"
    model = SalesRepCommissionCodeReport

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_obj = self.request.user.get_company_id  
        
        if company_obj is not None:
            context["product"] = SalesRepCommissionCodeReport.objects.filter(is_apply_ml=True,product__company=company_obj).values("product__id","product__name").distinct()
        else:
            context["product"] = SalesRepCommissionCodeReport.objects.filter(is_apply_ml=True).values("product__id","product__name").distinct()

        sales_rep = SalesRepCommissionCodeReport.objects.filter(order_product__order__status=Order.SHIPPED, is_apply_ml=True).aggregate(product_total_ml_quantity=Sum("product_total_ml_quantity"),ml_tax=Sum("ml_tax"))
        # total_ml_quantity = sales_rep['product_total_ml_quantity']
        # total_ml_tax = sales_rep['ml_tax']
        context['total_ml_quantity'] = sales_rep['product_total_ml_quantity']
        context['total_ml_tax'] = sales_rep['ml_tax']
        
        return context



class ReportByMlDataTableAjaxPagination(DataTableMixin, View):
    model = SalesRepCommissionCodeReport

    def get_queryset(self):
        qs = SalesRepCommissionCodeReport.objects.filter(order_product__order__status=Order.SHIPPED, is_apply_ml=True).order_by("-id")
        if self.request.user.role in ["company admin", "sales representative", "accountant"]:
            qs = qs.filter(order_product__order__company__id=self.request.user.get_company_id).order_by("-id")
        
        product = self.request.GET.get("product")
        start_date = self.request.GET.get("from_date")
        end_date = self.request.GET.get("to_date")

        if product:
            if end_date:
                return qs.filter(product=product, order_product__order__order_date__range =[start_date, end_date]).order_by("-id")
            return qs.filter(product=product).order_by("-id")
        
        elif end_date:
            if product:
                return qs.filter(order_product__order__order_date__range =[start_date, end_date], product=product).order_by("-id")
            return qs.filter(order_product__order__order_date__range =[start_date, end_date]).order_by("-id")

        return qs


    def filter_queryset(self, qs):
        if self.search:
            return qs.filter(
                Q(product__name__icontains=self.search) 
            ) 
        return qs
    
    
    def prepare_results(self, qs):
        return [
            {
                'id': o.id,
                'product_name': o.order_product.product.name,
                'order_id': o.order_product.order.id,
                'total_sold_piece': o.total_sold_piece,
                'unit_type': o.unit_type,
                'unit_sold': o.unit_sold,
                'ml_tax': o.ml_tax ,
                'product_ml_quantity': o.product_ml_quantity,
                'total_product_ml_quantity_sold': o.product_total_ml_quantity,
            }
            for o in qs
        ]


    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        # product_id = self.request.GET.get("product")
        # print("➡ product_issdadasdadsadadsadasdsadasdasdasdasdasdadasdasdd :", product_id)
        # from_date = parse_date(self.request.GET.get("from_date"))
        # to_date = parse_date(self.request.GET.get("to_date"))

        # sales_rep = SalesRepCommissionCodeReport.objects.filter(order_product__order__status=Order.SHIPPED, is_apply_ml=True).aggregate(product_total_ml_quantity=Sum("product_total_ml_quantity"),ml_tax=Sum("ml_tax"))
        # # total_ml_quantity = sales_rep['product_total_ml_quantity']
        # # total_ml_tax = sales_rep['ml_tax']

        # if product_id and not to_date:
        #     sales_rep = SalesRepCommissionCodeReport.objects.filter(product__id=product_id,order_product__order__status=Order.SHIPPED, is_apply_ml=True).aggregate(product_total_ml_quantity=Sum("product_total_ml_quantity"),ml_tax=Sum("ml_tax"))
        #     print("➡ sales_rep :", sales_rep)
        # if to_date and not product_id:
        #     sales_rep = SalesRepCommissionCodeReport.objects.filter(order_product__order__status=Order.SHIPPED, is_apply_ml=True, order_product__order__order_date__range = [from_date, to_date]).aggregate(product_total_ml_quantity=Sum("product_total_ml_quantity"),ml_tax=Sum("ml_tax"))
        #     print("➡ sales_rep :", sales_rep)
        # if to_date and product_id:
        #     sales_rep = SalesRepCommissionCodeReport.objects.filter(product__id=product_id,order_product__order__status=Order.SHIPPED, is_apply_ml=True, order_product__order__order_date__range = [from_date, to_date]).aggregate(product_total_ml_quantity=Sum("product_total_ml_quantity"),ml_tax=Sum("ml_tax"))
        #     print("➡ sales_rep :", sales_rep)

        # context_data['total_ml_quantity'] = sales_rep['product_total_ml_quantity']
        # print(">>>>>>>>>", sales_rep['product_total_ml_quantity'])
        # context_data['total_ml_tax'] = sales_rep['ml_tax']
        
        return JsonResponse(context_data)
    
class ReportByMlTotalCalculationAjax(View):     
    def get(self,request,*args, **kwargs):
        product_id = self.request.GET.get("product_id")
        from_date = parse_date(self.request.GET.get("from_date"))
        to_date = parse_date(self.request.GET.get("to_date"))
        if product_id and to_date is None:
            sales_rep = SalesRepCommissionCodeReport.objects.filter(product__id=product_id,order_product__order__status=Order.SHIPPED, is_apply_ml=True).aggregate(product_total_ml_quantity=Sum("product_total_ml_quantity"),ml_tax=Sum("ml_tax"))
        elif to_date and product_id == "":
            sales_rep = SalesRepCommissionCodeReport.objects.filter(order_product__order__status=Order.SHIPPED, is_apply_ml=True, order_product__order__order_date__range = [from_date, to_date]).aggregate(product_total_ml_quantity=Sum("product_total_ml_quantity"),ml_tax=Sum("ml_tax"))
        elif to_date and product_id is not None:
            sales_rep = SalesRepCommissionCodeReport.objects.filter(product__id=product_id,order_product__order__status=Order.SHIPPED, is_apply_ml=True, order_product__order__order_date__range = [from_date, to_date]).aggregate(product_total_ml_quantity=Sum("product_total_ml_quantity"),ml_tax=Sum("ml_tax"))

        data = {
            'total_ml_quantity': sales_rep['product_total_ml_quantity'],
            'total_ml_tax': sales_rep['ml_tax'],
        }
        return JsonResponse(data, safe=False)
    

class ReportByMlTaxTableCsvAjaxView(LoginRequiredMixin, View):
    
    def get(self, request):
        response = HttpResponse(content_type='text/csv')  
        response['Content-Disposition'] = 'attachment; filename="Report by ml tax file.csv"'
        qs_due_bills_ml_tax = SalesRepCommissionCodeReport.objects.filter(order_product__order__status=Order.SHIPPED, 
        order_product__product__is_apply_ml_quantity=True).distinct()

        if self.request.user.role in ["company admin", "sales representative", "accountant"]:
            qs_due_bills_ml_tax = SalesRepCommissionCodeReport.objects.filter(order_product__order__company__id=self.request.user.get_company_id,order_product__order__status=Order.SHIPPED, 
        order_product__product__is_apply_ml_quantity=True).distinct()
        writer = csv.writer(response)  
        writer.writerow(['Product Name', 'Ml Quantity/Piece', 'Product Type',  'Sold Unit', 'Total Piece Sold', 'Total Ml Quantity Sold', 'Ml Tax']) 
        writer.writerow(['', '', '', '', '', '', '']) 

        product = self.request.GET.get("product")
        start_date = self.request.GET.get("from_date")
        end_date = self.request.GET.get("to_date")

        if product:
            if end_date:
                qs_due_bills_ml_tax=qs_due_bills_ml_tax.filter(product=product, created_at__range=[start_date, end_date])
            qs_due_bills_ml_tax=qs_due_bills_ml_tax.filter(product=product)
        
        if end_date:
            if product:
               qs_due_bills_ml_tax=qs_due_bills_ml_tax.filter(created_at__range=[start_date, end_date], product=product)
            qs_due_bills_ml_tax=qs_due_bills_ml_tax.filter(created_at__range=[start_date, end_date])



        for ml in qs_due_bills_ml_tax:
            # for data in customer_data: 
            product_name = ml.order_product.product.name
            total_sold_piece = ml.total_sold_piece
            unit_type = ml.unit_type
            unit_sold = ml.unit_sold
            ml_tax = ml.ml_tax
            product_ml_quantity = ml.product_ml_quantity
            total_product_ml_quantity_sold = ml.product_total_ml_quantity
            writer.writerow([product_name, product_ml_quantity, unit_type, unit_sold, total_sold_piece, total_product_ml_quantity_sold, ml_tax]) 
        return response  

class LoadCustomer(LoginRequiredMixin, ListView):
    def get(self, request):
        data = {
            'customer_list' : list(Customer.objects.filter(sales_rep__username=request.GET.get('sales_rep'),status = Customer.ACTIVE).values('id', 'customer_name'))
        }
        return JsonResponse(data, safe=False)
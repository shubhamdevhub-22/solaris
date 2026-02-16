from django.urls import path
from app_modules.reports import views

app_name = "reports"

urlpatterns = [
    # path("due-payment-list/", views.ReportByDuePaymentListView.as_view(), name="by_due_payment_list"),
    # path("due-payment-list-ajax/", views.ReportByDuePaymentDataTableAjaxPagination.as_view(), name="report_due_list_ajax"),
    # path("due-payment-table-print-ajax/", views.ReportByDueTablePrintAjaxView.as_view(), name="by_due_table_print_ajax"),
    
    path("zone-wise-collection-report/", views.ZoneWiseCollectionReport.as_view(), name="zone_wise_collection_report"),
    path("zone-wise-collection-report-ajax/", views.ZoneWiseCollectionReportAjax.as_view(), name="zone_wise_collection_report_ajax"),
    path("export/<str:type>/collection/", views.ExportCollectionReport.as_view(), name="export_collection_report"),

    path("daily-bill-report/", views.DailyBillReport.as_view(), name="daily_bill_report"),
    path("daily-bill-report-ajax/", views.DailyBillReportAjax.as_view(), name="daily_bill_report_ajax"),
    path("export/daily-bill-report/", views.ExportDailyBillReport.as_view(), name="export_daily_bill_report"),

    path("bill-summary-report/", views.BillSummaryReport.as_view(), name="bill_summary_report"),
    path("bill-summary-report-ajax/", views.BillSummaryReportAjax.as_view(), name="bill_summary_report_ajax"),
    path("export/bill-summary-report/", views.ExportBillSummaryReport.as_view(), name="export_bill_summary_report"),

    path("ledger-report/", views.LedgerReport.as_view(), name="ledger_report"),
    path("ledger-report-ajax/", views.LedgerReportAjax.as_view(), name="ledger_report_ajax"),
    path("export/ledger-report/", views.ExportLedgerReport.as_view(), name="export_ledger_report"),

    path("by-commision-list/", views.ReportByCommisionListView.as_view(), name="by_commision_list"),
    path("report-commision-list-ajax/",views.ReportByCommisionDataTableAjaxPagination.as_view(),name="report_commision_list_ajax"),
    path("report-comision-list-ajax/",views.ReportByCommisionCsvAjaxPagination.as_view(),name="by_commission_table_csv_ajax"),

    path("by-ml-list/", views.ReportByMlListView.as_view(), name="by_ml_list"),
    path("report-ml-list-ajax/",views.ReportByMlDataTableAjaxPagination.as_view(),name="report_ml_list_ajax"),
    path("by-ml-table-csv-ajax/", views.ReportByMlTaxTableCsvAjaxView.as_view(), name="by_ml_table_csv_ajax"),

    path("report-ml-list-total-calculation-ajax/",views.ReportByMlTotalCalculationAjax.as_view(),name="report_ml_list_ajax_total_calculation"),

    path("by-due-payment-list/", views.ReportByDuePaymentListView.as_view(),name="by_due_payment_list"),
    path("due-payment-list-ajax/", views.ReportByDuePaymentDataTableAjaxPagination.as_view(), name="report_due_list_ajax"),
    path("due-payment-table-csv-ajax/", views.ReportByDueTableCsvAjaxView.as_view(), name="by_due_table_csv_ajax"),

    path("load-customer/",views.LoadCustomer.as_view(),name="load_customer"),
]

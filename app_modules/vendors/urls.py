from django.urls import path
from app_modules.vendors.views import VendorCreateView, VendorDataTablesAjaxPagination, VendorDeleteAjaxView, VendorListView, VendorUpdateView,VendorDetailsView,VendorReceviedListView,VendorReceivedBillDataTablesAjaxPagination,VendorDocumentsListView,VendorDocumentDataTablesAjaxPagination,VendorDocumentCreateView,VendorDocumentUpdateView,VendorDocumentDeleteAjaxView,VendorPaymentCreateView,LoadVendorAjax,VendorBillListView,VendorPaymentListView,VendorPaymentDataTablesAjaxPagination,VendorDetailsPaymentListView,VendorDetailsPaymentDataTablesAjaxPagination, VendorPaymentHistoryDetailsView, VendorPaymentAjaxView
app_name = "vendors"

urlpatterns = [
    # url for user
    path("", VendorListView.as_view(), name="vendor_list"),
    path("create/", VendorCreateView.as_view(), name="vendor_create"),
    path("<int:pk>/update/", VendorUpdateView.as_view(), name="vendor_update"),
    path("vendor-delete-ajax/", VendorDeleteAjaxView.as_view(), name="vendor_delete"),
    path("vendor-list-ajax/", VendorDataTablesAjaxPagination.as_view(), name="vendor_list_ajax"),
    path("<int:pk>/details/", VendorDetailsView.as_view(), name="vendor_details"),

    path("<int:pk>/vendor-received-bills/", VendorReceviedListView.as_view(), name="received_bills"),
    path("<int:pk>/vendor-upload-documents/", VendorDocumentsListView.as_view(), name="upload_documents"),

    path("<int:pk>/vendor-payment-history/", VendorDetailsPaymentListView.as_view(), name="payment_history"),
    path("vendor-payment-history-list-ajax/", VendorDetailsPaymentDataTablesAjaxPagination.as_view(), name="vendor_payment_history_list_ajax"),


    path("vendors-payment-history/", VendorPaymentListView.as_view(), name="payment_history_vendors"),
    path("vendors-payment-history-list-ajax/", VendorPaymentDataTablesAjaxPagination.as_view(), name="vendors_payment_history_list_ajax"),
    path("<int:pk>/payment-details/", VendorPaymentHistoryDetailsView.as_view(), name="payment_history_detail"),
    path('<int:pk>/vendor-payment-list-ajax/', VendorPaymentAjaxView.as_view(), name='payment_model_ajax'),
    
    
    path("vendor-recevied-bill-list-ajax/", VendorReceivedBillDataTablesAjaxPagination.as_view(), name="vendor_recevied_bill_list_ajax"),

    

    
    path("vendor-document-list-ajax/", VendorDocumentDataTablesAjaxPagination.as_view(), name="vendor_document_list_ajax"),
    path("<int:vendor_pk>/vendor-document-create/", VendorDocumentCreateView.as_view(), name="vendor_document_create"),
    path("<int:vendor_pk>/<int:pk>/vendor-document-update/", VendorDocumentUpdateView.as_view(), name="vendor_document_update"),
    path("vendor-document-delete-ajax/", VendorDocumentDeleteAjaxView.as_view(), name="vendor_document_delete"),

    path("vendor-payment-create/", VendorPaymentCreateView.as_view(), name="vendor_payment_create"),
    path("vendor-payment-create/load-vendor-ajax", LoadVendorAjax.as_view(), name="load_vendor_ajax"),
    path("vendor-payment-create/load-vendor-table-list-ajax", VendorBillListView.as_view(), name="load_vendor_table_list_ajax"),
    path("vendor-payment-create/load-vendor-table-list-ajax", VendorBillListView.as_view(), name="vendor_po_detailview"),
    

    

    

    
    
    
]
    
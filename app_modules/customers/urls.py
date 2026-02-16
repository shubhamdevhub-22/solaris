from django.urls import path
from app_modules.customers import views

app_name = "customer"

urlpatterns = [
    # '''url for Customer model'''
    path("", views.CustomerListView.as_view(), name="customer_list"),
    path("create/", views.CustomerCreateView.as_view(), name="customer_create"),
    path('customer-list-ajax/', views.CustomerDataTablesAjaxPagination.as_view(), name='customer_list_ajax'),
    path("<int:pk>/update/", views.CustomerUpdateView.as_view(), name="customer_update"),
    path("delete/", views.CustomerDeleteAjaxView.as_view(), name="customer_delete"),
    path("create/load-sales-rep-ajax/", views.LoadSalesRep.as_view(), name="load_sales_rep"),

    path("get-discounts/", views.CustomerDiscountAjaxView.as_view(), name="get_customer_discount_table"),

    path("discounts/", views.DiscountListView.as_view(), name="discount_list"),
    path("discount-list-ajax/", views.DiscountListAjaxView.as_view(), name="discount_list_ajax"),
    path("discount/create/", views.DiscountCreateView.as_view(), name="discount_create"),
    path("discount/<int:pk>/update/", views.DiscountUpdateView.as_view(), name="discount_update"),
    path("discount/delete/", views.DiscountDeleteView.as_view(), name="discount_delete"),

    path("discount/search/", views.DiscountSearchAjaxView.as_view(), name="discount_search"),
    path("customer/search/", views.CustomerSearchAjaxView.as_view(), name="customer_search"),

    path("replacements/", views.ReplacementListView.as_view(), name="replacement_list"),
    path("replacement-list-ajax/", views.ReplacementListAjaxView.as_view(), name="replacement_list_ajax"),
    path("replacements/create/", views.ReplacementCreateView.as_view(), name="replacement_create"),
    path("replacements/<int:pk>/update/", views.ReplacementUpdateView.as_view(), name="replacement_update"),
    path("replacements/delete/", views.ReplacementDeleteView.as_view(), name="replacement_delete"),

    #'''url for customer details'''
    path("<int:pk>/details/", views.CustomerDetailsView.as_view(), name="customer_details"),
    path("customer-lock/", views.CustomerBillingLockAjaxView.as_view(), name="customer_billing_lock"),

    path("<int:pk>/customer-address-info/", views.CustomerAddressListView.as_view(), name="customer_addressinfo"),
    
    path("customer-addressinfo-billing-list-ajax/", views.CustomerBillingAddressDataTablesAjaxPagination.as_view(), name="customer_addressinfo_billing_list_ajax"),
    path("<int:pk>/customer-billing-addressinfo/create/", views.CustomerBillingAddressInfoCreateView.as_view(), name="customer_billing_addressinfo_create"),
    path("<int:customer_id>/customer-billing-addressinfo/<int:pk>/update/", views.CustomerBillingAddressInfoUpdateView.as_view(), name="customer_billing_addressinfo_update"),
    path("customer-billing-addressinfo/delete/", views.CustomerBillingAddressInfoDeleteAjaxView.as_view(), name="customer_billing_addressinfo_delete"),

    path("customer-addressinfo-shipping-list-ajax/", views.CustomerShippingAddressDataTablesAjaxPagination.as_view(), name="customer_addressinfo_shipping_list_ajax"),
    path("<int:pk>/customer-shipping-addressinfo/create/", views.CustomerShippingAddressInfoCreateView.as_view(), name="customer_shipping_addressinfo_create"),
    path("<int:customer_id>/customer-shipping-addressinfo/<int:pk>/update/", views.CustomerShippingAddressInfoUpdateView.as_view(), name="customer_shipping_addressinfo_update"),
    path("customer-shipping-addressinfo/delete/", views.CustomerShippingAddressInfoDeleteAjaxView.as_view(), name="customer_shipping_addressinfo_delete"),

    path("<int:pk>/customer-document-info/create/", views.UploadDocumentsCreateView.as_view(), name="upload_document"),
    path("<int:customer_pk>/customer-document-info/<int:pk>/update/", views.UploadDocumentsUpdateView.as_view(), name="customer_document_update"),
    path("<int:pk>/customer-documents-info/", views.CustomerDocumentsListView.as_view(), name="customer_documents"),
    path("customer-document-list-ajax/", views.CustomerDocumentsDataTablesAjaxPagination.as_view(), name="customer_documents_list_ajax"),
    path("customer-document/delete/", views.CustomerDocumentDeleteAjaxView.as_view(), name="customer_document_delete"),

    path("<int:pk>/contact-add/create/", views.CustomerContactCreateView.as_view(), name="contact_add"),
    path("<int:pk>/customer-contact-ajax/", views.CustomerContactListView.as_view(), name="customer_contact_ajax"),
    path("customer-contact-list-ajax/", views.CustomerContactDataTableAjaxPagination.as_view(), name="customer_contact_list_ajax"),
    path("<int:customer_pk>/customer-contact-info/<int:pk>/update/", views.CustomerContactUpdateView.as_view(), name="customer_contact_update"),
    path("customer-contact/delete/", views.CustomerContactDeleteAjaxView.as_view(), name="customer_contact_delete"),

    path("<int:pk>/customer-creditmemo-ajax/", views.CustomerCreditMemoListView.as_view(), name="customer_creditmemo"),
    path("customer-credit-memo-list-ajax/", views.CustomerCreditMemoDataTableAjaxPagination.as_view(), name="customer_creditmemo_list_ajax"),

    path("<int:pk>/customer-order-ajax", views.CustomerOrderListView.as_view() , name="customer_order"),
    path("customer-order-list-ajax", views.CustomerOrderDataTableAjaxPagination.as_view() , name="customer_order_list_ajax"),

    path("<int:pk>/customer-replacement-ajax", views.CustomerReplacementListView.as_view() , name="customer_replacement"),
    path("customer-replacement-list-ajax", views.CustomerReplacementDataTableAjaxPagination.as_view() , name="customer_replacement_list_ajax"),
    path("customer-ledger-list-ajax", views.LedgerDataTableAjaxPagination.as_view() , name="customer_ledger_list_ajax"),

    path("<int:pk>/customer-ledger-ajax", views.CustomerLedgerListView.as_view() , name="customer_ledger_list"),
    path("<int:pk>/customer-payment-history-ajax", views.CustomerPaymentHistoryListView.as_view() , name="customer_payment_history"),
    path("customer-payment-history-list-ajax", views.CustomerPaymentHistoryDataTableAjaxPagination.as_view() , name="customer_payment_history_list_ajax"),
    path("<int:pk>/payment-details/", views.PaymentHistoryDetailsView.as_view(), name="payment_history_detail"),
    

    # '''url for Payment model'''
    path("payment/", views.PaymentListView.as_view(), name="payment_list"),
    path("payment/create/", views.PaymentCreateView.as_view(), name="payment_create"),
    path('payment-list-ajax/', views.PaymentDataTablesAjaxPagination.as_view(), name='payment_list_ajax'),
    path("payment/<int:pk>/update/", views.PaymentUpdateView.as_view(), name="payment_update"),
    path("payment/delete/", views.PaymentDeleteAjaxView.as_view(), name="payment_delete"),
    path("load-customer-for-payment-ajax", views.LoadCustomerForPaymentAjax.as_view(), name="load_customer_for_payment_ajax"),
    path("customer-bill-list-ajax", views.CustomerBillListView.as_view(), name="customer_bill_list_ajax"),
    path('<int:pk>/payment-list-ajax/', views.PaymentAjaxView.as_view(), name='payment_model_ajax'),

    # '''url for Sales Route model'''
    path("sales-route/", views.SalesRouteListView.as_view(), name="sales_route_list"),
    path("sales-route/create/", views.SalesRouteCreateView.as_view(), name="sales_route_create"),
    path('sales-route-list-ajax/', views.SalesRouteDataTablesAjaxPagination.as_view(), name='sales_route_list_ajax'),
    path("sales-route/<int:pk>/update/", views.SalesRouteUpdateView.as_view(), name="sales_route_update"),
    path("sales-route/delete/", views.SalesRouteDeleteAjaxView.as_view(), name="sales_route_delete"),
    path("load-customer-salesrep-ajax", views.LoadCustomerSalesrepAjax.as_view(), name="load_customer_sales_rep"),

    # '''url for Price Level model'''
    # path("price-level/", views.PricelevelListView.as_view(), name="price_level_list"),
    # path("price-level/create/", views.PricelevelCreateView.as_view(), name="price_level_create"),
    # path('price-level-list-ajax/', views.PricelevelDataTablesAjaxPagination.as_view(), name='price_level_list_ajax'),
    # path("price-level/<int:pk>/update/", views.PricelevelUpdateView.as_view(), name="price_level_update"),
    # path("price-level/delete/", views.PricelevelDeleteAjaxView.as_view(), name="price_level_delete"),

    #'''url for Product Price level'''
    path('price-level-product-ajax/', views.PricelevelProductDataTablesAjaxPagination.as_view(), name='price_level_product_list'),
    path('price-level-product-update-ajax/', views.PricelevelProductUpdateDataTablesAjaxPagination.as_view(), name='price_level_product_update'),
    path('<int:pk>/customer-log-list-ajax/', views.CustomerLogAjaxView.as_view(), name='customer_log_ajax'),
    path('customer-log-list-ajax-datatable/', views.CustomerLogDatatableAjaxView.as_view(), name='customer_log_ajax_datatable'),


    # """" url for import csv

    path("customer-create-from-csv/", views.CustomerCreateFromCSVFormView.as_view(), name="customer_create_from_csv"),
    path("zone-create-from-csv/", views.ZoneCreateFromCSVFormView.as_view(), name="zone_create_from_csv"),
    #''' url for Zone '''
    path('zone-list/', views.ZoneListView.as_view(), name="zone_list"),
    path('zone-list-ajax/', views.ZoneDataTablesAjaxPagination.as_view(), name='zone_list_ajax'),
    path('zone-create/', views.ZoneCreateView.as_view(), name="zone_create"),
    path('zone-update/<int:pk>/', views.ZoneUpdateView.as_view(), name="zone_update"),
    path('zone-delete/', views.ZoneDeleteAjaxView.as_view(), name="zone_delete"),

    # For delete all Customer And Zone:
    path('customer-delete-all/', views.AllCustomerDeleteView.as_view(), name="customer_delete_all"),
    path('zone-delete-all/', views.AllZoneDeleteView.as_view(), name="zone_delete_all"),

    
]
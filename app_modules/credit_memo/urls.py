from django.urls import path

from app_modules.credit_memo.views import AddProductInCreditMemoListAjaxView, AjaxGetUpdateProductDetailsCreditMemo, CreditMemoCreateView, CreditMemoDataTablesAjaxPagination, CreditMemoDetailView, CreditMemoListView, CreditMemoLogAjaxView, CreditMemoLogDatatableAjaxView, CreditMemoUpdateView, GetCustomersAndProductsByCompanyAjaxView, GetProductDetailsAjaxView

app_name = "credit_memo"

urlpatterns = [
    # path("", CreditMemoListView.as_view(), name="credit_memo_list"),
    # path("<int:pk>/update", CreditMemoUpdateView.as_view(), name="credit_memo_update"),
    # path("<int:pk>/details", CreditMemoDetailView.as_view(), name="credit_memo_detail"),
    # path("credit-memo-list-ajax/", CreditMemoDataTablesAjaxPagination.as_view(), name="credit_memo_list_ajax"),
    # path("create/",CreditMemoCreateView.as_view(),name="credit_memo_create"),
    path("get-customers-and-products-by-company/",GetCustomersAndProductsByCompanyAjaxView.as_view(),name="get_customers_and_products_by_company"),
    path("ajax-get-product-details/",GetProductDetailsAjaxView.as_view(),name="get_product_details_ajax"),
    path("add-product-in-purchase-list-ajax/",AddProductInCreditMemoListAjaxView.as_view(),name="add_product_in_credit_memo_list"),
    path("ajax-get-update-product-details-credit-memo-update/",AjaxGetUpdateProductDetailsCreditMemo.as_view(),name="ajax_get_update_product_details_credit_memo"),
    path('<int:pk>/credit-memo-log-list-ajax/', CreditMemoLogAjaxView.as_view(), name='credit_memo_log_ajax'),
    path('credit-memo-log-list-ajax-datatable/', CreditMemoLogDatatableAjaxView.as_view(), name='credit_memo_log_ajax_datatable'),
    # path("ajax-get-vendors-by-company/",GetVendorsAndProductsByCompanyAjax.as_view(),name="ajax_get_vendors_by_company"),
    # path("ajax-get-product-details/",AjaxGetProductDetails.as_view(),name="ajax_get_product_details"),
    # path("ajax-add-product-in-purchase-list/",AddProductInPurchaseList.as_view(),name="add_product_in_purchase_list"),
    # path("",PurchaseOrderListView.as_view(), name="purchase_order_list"),
    # path("purchase_order/data-table-ajax",PurchaseOrderListAjax.as_view(), name="purchase_order_list_ajax"),
    # path("<int:pk>/update",PurchaseOrderUpdateView.as_view(),name="purchase_order_update"),
    # path("ajax-get-update-product-details/",AjaxGetUpdateProductDetails.as_view(),name="ajax_get_update_product_details"),
]
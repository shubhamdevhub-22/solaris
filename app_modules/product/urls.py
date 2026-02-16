from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from app_modules.product.views import (
    AddStockFromCSVFormView,
    BrandListView,
    BrandCreateView,
    BrandUpdateView,
    BrandDataTablesAjaxPagination,
    BrandDeleteAjaxView,

#     CategoryListView,
#     CategoryCreateView,
#     CategoryUpdateView,
#     CategoryDataTablesAjaxPagination,
#     CategoryDeleteAjaxView,
    ProductCreateFromCSVFormView,

#     SubCategoryListView,
#     SubCategoryCreateView,
#     SubCategoryUpdateView,
#     SubCategoryDataTablesAjaxPagination,
#     SubCategoryDeleteAjaxView,

    ProductListView,
    ProductCreateView,
    ProductUpdateView,
    ProductDataTablesAjaxPagination,
    ProductDeleteAjaxView,
    VehicleCreateAjaxView,

    ProductPriceListView,
    ProductPriceDataTablesAjaxPagination,
    ProductPriceUpdateAjaxView,

    ManageProductStock,
    LoadWarehouse,
    LoadProduct,
    TransferStockAdd,
    LoadAvailableStock,
    WarehouseProuctstockUpdateView,
    UpdateStock,
    ProdcutStockHistoryListView,
    ProdcutStockHistoryDataTablesAjaxPagination,
    StockUpdateAjaxView,
    StockFormAjaxView,
    TransferStockView,
    
    ProductDetailView,
    BarcodeGenerateView,
    ProdcutBarcodeDataTablesAjaxPagination,
    DeleteBarcodeAjaxView,
    preview_csv,
    
    SearchAjaxView,

    ProductSearchAjaxView,
    ProductPriceAjaxView,
)


app_name = "product"

urlpatterns = [

     path("brands/", BrandListView.as_view(), name="list_brand"),
     path("brands/add/", BrandCreateView.as_view(), name="add_brand"),
     path("brands/<str:pk>/update/",
          BrandUpdateView.as_view(), name="update_brand"),
     path('brands/ajax/',
          BrandDataTablesAjaxPagination.as_view(), name='brands-list-ajax'),
     path("brand-delete-ajax/", BrandDeleteAjaxView.as_view(), name="delete_brand"),



     path("", ProductListView.as_view(), name="list_product"),
     path("add/", ProductCreateView.as_view(), name="add_product"),
     path("<str:pk>/update/",
          ProductUpdateView.as_view(), name="update_product"),
     path("vehicle/add/", VehicleCreateAjaxView.as_view(), name="add_vehicle"),
      
     path("ajax/",
          ProductDataTablesAjaxPagination.as_view(), name='product-list-ajax'),

     path("price/", ProductPriceListView.as_view(),
          name="list_product_price"),
     path('price/ajax/',
          ProductPriceDataTablesAjaxPagination.as_view(), name='product-price-list-ajax'),
     path("price/<int:pk>/update/",
          ProductPriceUpdateAjaxView.as_view(), name="update_product_price"),
     path("product-delete-ajax/", ProductDeleteAjaxView.as_view(), name="delete_product"),
         
     path("product-create-from-csv/", ProductCreateFromCSVFormView.as_view(), name="product_create_from_csv"),
     path("add-stock-from-csv/", AddStockFromCSVFormView.as_view(), name="add_stock_from_csv"),
     path("manage-stocks/", ManageProductStock.as_view(), name="manage_stocks"),
     path('manage-stocks/load_warehouse/',LoadWarehouse.as_view(),
         name='load_warehouse'),
     
     path('transfer-stocks/load_product/',LoadProduct.as_view(),
         name='load_product'),
     path("load-available-stock", LoadAvailableStock.as_view(), name="load_available_stock"),
     path("transfer-stock-add/", TransferStockAdd.as_view(), name="transfer_stock_add"),

     path('manage-stocks/get_form/',WarehouseProuctstockUpdateView.as_view(),
         name='get_form'),
     path('manage-stocks/update_stock/',UpdateStock.as_view(),
         name='update_stock'),

     path("list-product-history/",
          ProdcutStockHistoryListView.as_view(), name="list_product_history"),
     path("list-product-history/ajax/",
          ProdcutStockHistoryDataTablesAjaxPagination.as_view(), name='stock_history'),

     path("stock/<int:pk>/update/", StockUpdateAjaxView.as_view(), name="stock_update"),
     path("stock/form/", StockFormAjaxView.as_view(), name="stock_form_url"),
     

     path("transfer-stocks/", TransferStockView.as_view(), name="transfer_stocks"),

     path('<int:pk>/details/', ProductDetailView.as_view(), name="product_detail"),
     path('generate-barcode/barcode/', BarcodeGenerateView.as_view(), name="generate_barcode"),
     path("product-barcode-list/ajax/",ProdcutBarcodeDataTablesAjaxPagination.as_view(), name="product_barcode_list"),
     path('delete-barcode-ajax/',DeleteBarcodeAjaxView.as_view(), name='delete_barcode'),

     path("search/", SearchAjaxView.as_view(), name="search_url"),

     path('csv-list-preview/', preview_csv, name='csv_list_preview'),

     path("product/search/", ProductSearchAjaxView.as_view(), name="product_search"),
     path("product/price/", ProductPriceAjaxView.as_view(), name="get_product_price"),
     
     # path("discount/list", DiscountListView.as_view(), name="discount_list"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

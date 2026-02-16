"""unity_wholesale URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from app_modules.users.views import HomeView, DasboardTemplateView , CustomPasswordChangeView

from allauth.account import views as allauth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("dashboard/",DasboardTemplateView.as_view(), name="dashboard"),
    path("company/", include('app_modules.company.urls'), name="company"),
    path("product/",include("app_modules.product.urls")),
    path("users/", include('app_modules.users.urls')),
    path("vendors/", include('app_modules.vendors.urls')),
    path("order/", include('app_modules.order.urls')),
    path('accounts/password/change/',CustomPasswordChangeView.as_view(),name='account_change_password'),
    # path("accounts/password/set/", allauth_views.password_set, name="account_set_password"),
    # path("accounts/logout/", allauth_views.logout, name="account_logout"),
    # path("accounts/signup/", allauth_views.signup, name="account_signup"),
    # path("accounts/password/reset/", allauth_views.password_reset, name="account_reset_password"),
    path("accounts/", include("allauth.urls")),
    path("", HomeView.as_view(), name="home_view"),
    path("customers/", include('app_modules.customers.urls'), name="customers"),
    path("purchase-order/",include('app_modules.purchase_order.urls')),
    path("credit-memo/",include('app_modules.credit_memo.urls')),
    path("reports/",include('app_modules.reports.urls')),
    path("expanse-management/",include('app_modules.expanse_management.urls')),
    

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

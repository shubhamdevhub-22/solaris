from django.contrib import admin
from app_modules.credit_memo.models import CreditMemo,CreditMemoProduct,CreditMemoLog
# Register your models here.
admin.site.register(CreditMemo)
admin.site.register(CreditMemoProduct)
admin.site.register(CreditMemoLog)

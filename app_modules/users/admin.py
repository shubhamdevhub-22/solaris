from django.contrib import admin
from app_modules.users.models import User, CustomErrorLogs
# Register your models here.

admin.site.register(User)
admin.site.register(CustomErrorLogs)
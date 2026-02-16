from django.contrib import admin
from .models import ExpanseCategory, ExpanseBudget, ExpanseManagement

@admin.register(ExpanseCategory)
class ExpanseCategoryAdmin(admin.ModelAdmin):
    list_display = ('category', 'company')
    search_fields = ('category', 'company__name')
    list_filter = ('company',)
    ordering = ('category',)

@admin.register(ExpanseBudget)
class ExpanseBudgetAdmin(admin.ModelAdmin):
    list_display = ('category', 'budget_amount', 'date')
    search_fields = ('category__category', 'budget_amount')
    list_filter = ('date', 'category')
    ordering = ('-date',)

@admin.register(ExpanseManagement)
class ExpanseManagementAdmin(admin.ModelAdmin):
    list_display = ('expanse_budget', 'expanse', 'date', 'note')
    search_fields = ('expanse_budget__category__category', 'expanse', 'note')
    list_filter = ('date', 'expanse_budget__category')
    ordering = ('-date',)
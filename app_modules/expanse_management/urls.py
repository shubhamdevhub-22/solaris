from django.urls import path
from app_modules.expanse_management.views import (
   BudgetListView,
   ExpanseCreateView,
   ExapnseDeleteView,
   ExpanseDetailView,
   GetMonthlyTotalsBudget,
   GetBudget,
   SaveBudgetView,
   BudgetListAjaxView,
   GetCategoriesView,
   ExpanseListAjaxView,
   ExpanseDetailAllView
)

app_name = "expanse_management"

urlpatterns = [
    path("", BudgetListView.as_view(), name="budget_list"),
    path("budget-ajax", BudgetListAjaxView.as_view(), name="budget_list_ajax"),
    path("create/", ExpanseCreateView.as_view(), name="expanse_create"),
    path('get-categories/', GetCategoriesView.as_view(), name='get_categories'),
    path("delete/", ExapnseDeleteView.as_view(), name="expanse_delete"),
    path("detail/<int:pk>", ExpanseDetailView.as_view(), name="expanse_detail"),
    path("detail/all/<str:month>", ExpanseDetailAllView.as_view(), name="expanse_detail_all"),
    path('get_monthly_totals/', GetMonthlyTotalsBudget.as_view(), name='get_monthly_totals'),
    path('get_month-budget/', GetBudget.as_view(), name='get_month_budget'),
    path('save-budget/', SaveBudgetView.as_view(), name='save_budget'),
    path("expanse-ajax", ExpanseListAjaxView.as_view(), name="expanse_list_ajax"),

]
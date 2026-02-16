from datetime import datetime, timedelta
import json
from django.shortcuts import get_object_or_404, render
from django.views.generic import CreateView, UpdateView, ListView, DeleteView, TemplateView, View, DetailView
from app_modules.base.mixins import CompanyAdminLoginRequiredMixin
# from app_modules.expanse_management.forms import ExpanseManagementForm
from app_modules.company.models import Company, CompanyUsers
from app_modules.expanse_management.forms import ExpanseManagementForm
from app_modules.expanse_management.models import ExpanseBudget, ExpanseCategory, ExpanseManagement
from django_datatables_too.mixins import DataTableMixin
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.http import HttpResponse, JsonResponse,HttpResponseRedirect
from django.template.loader import get_template
from django.contrib import messages
from django.db.models import Sum
from django.utils.dateparse import parse_date

User = get_user_model()
def handler404(request, args, *argv):
    return render(request, "404.html", status=404)
def handler403(request, args, *argv):
    return render(request, "403.html", status=403)
# Create your views here.


class BudgetListView(ListView):
    template_name = "expanse_management/budget_list.html"
    model = ExpanseManagement
    context_object_name = "expanse"

    def get_queryset(self):
        user_company = CompanyUsers.objects.get(user=self.request.user).company
        print('user_company: ', user_company.id)
        return ExpanseManagement.objects.filter(expanse_budget__category__company=user_company)


class GetMonthlyTotalsBudget(View):
    def get(self, request):
        if request.method == 'GET' and 'month' in request.GET:
            selected_month = request.GET['month']
            print('selected_month: ', selected_month)
            year, month = map(int, selected_month.split('-'))
            
            user_company = CompanyUsers.objects.get(user=request.user).company
            print('user_company: ', user_company)

            # Calculate total budget
            budget_totals = ExpanseBudget.objects.filter(
                date__year=year, 
                date__month=month, 
                category__company=user_company
            ).aggregate(total_budget=Sum('budget_amount'))
            print('budget_totals: ', budget_totals)

            # Calculate total expense
            expanse_totals = ExpanseManagement.objects.filter(
                date__year=year, 
                date__month=month, 
                expanse_budget__category__company=user_company
            ).aggregate(total_expanse=Sum('expanse'))
            print('expanse_totals: ', expanse_totals)

            # Check if there are any budgets for the selected month
            has_budget = ExpanseBudget.objects.filter(
                date__year=year, 
                date__month=month, 
                category__company=user_company
            ).exists()

            data = {
                'total_budget': budget_totals['total_budget'] or 0,
                'total_expanse': expanse_totals['total_expanse'] or 0,
                'has_budget': has_budget
            }
            print('data: ', data)
            return JsonResponse(data)
        
class GetBudget(View):
    def get(self, request, *args, **kwargs):
        month = self.request.GET.get('month')
        if not month:
            return JsonResponse({'categories': [], 'budgets': {}, 'updatebutton': 'false'})
        
        try:
            start_date = datetime.strptime(month, '%Y-%m').date().replace(day=1)
            end_date = (start_date.replace(month=start_date.month % 12 + 1, day=1) - timedelta(days=1))
            
            user_company = CompanyUsers.objects.get(user=self.request.user).company
            categories = ExpanseCategory.objects.filter(company=user_company)
            budgets = {}

            # Check if there is any budget for the selected month
            has_budget = ExpanseBudget.objects.filter(date__range=[start_date, end_date], category__company=user_company).exists()
            
            for category in categories:
                budget = ExpanseBudget.objects.filter(category=category, date__range=[start_date, end_date]).first()
                if budget:
                    budgets[category.category] = budget.budget_amount
                else:
                    budgets[category.category] = 0.00

            response_data = {
                'categories': [cat.category for cat in categories],
                'budgets': budgets,
                'has_budget': 'true' if has_budget else 'false'
            }

            return JsonResponse(response_data)
        
        except ValueError:
            return JsonResponse({'categories': [], 'budgets': {}, 'has_budget': 'false'})

class SaveBudgetView(View):
    def post(self, request, *args, **kwargs):
        month = request.POST.get('month')
        print('month: ', month)
        has_budget = request.POST.get('has_budget')
        print('has_budget: ', has_budget)
        budgets = json.loads(request.POST.get('budgets'))
        print('budgets: ', budgets)

        try:
            start_date = datetime.strptime(month, '%Y-%m').date().replace(day=1)
        except ValueError:
            return JsonResponse({'error': 'Invalid month format. Use YYYY-MM.'}, status=400)

        end_date = (start_date.replace(month=start_date.month % 12 + 1, day=1) - timedelta(days=1))
        
        user_company = CompanyUsers.objects.get(user=self.request.user).company

        for category_name, amount in budgets.items():
            # Get or create the category
            category = ExpanseCategory.objects.get(
                category=category_name, 
                company=user_company
            )
            print('category: ', category)

            if category is None:
                return JsonResponse({'error': f'Category {category_name} does not exist.'}, status=201)

            # Check if a budget entry exists for the category and date
            if has_budget == "true":
                budget = ExpanseBudget.objects.filter(
                    category=category,
                    date=start_date
                ).first()
                if budget:
                    # Update existing budget
                    budget.budget_amount = amount
                    budget.save()
                else:
                    # If no budget exists, create a new one
                    ExpanseBudget.objects.create(
                        category=category,
                        date=start_date,
                        budget_amount=amount
                    )
            else:
                # Create new budget entry
                ExpanseBudget.objects.create(
                    category=category,
                    date=start_date,
                    budget_amount=amount
                )

        return JsonResponse({'message': 'Budget updated successfully'})
class BudgetListAjaxView(DataTableMixin, View):
    model = ExpanseBudget

    def get_queryset(self):
        current_month = self.request.GET.get("current_month")
        user_company = CompanyUsers.objects.get(user=self.request.user).company

        if current_month:
            try:
                start_date = datetime.strptime(current_month, '%Y-%m').date().replace(day=1)
                end_date = (start_date.replace(month=start_date.month % 12 + 1, day=1) - timedelta(days=1))
                qs = ExpanseBudget.objects.filter(date__range=[start_date, end_date], category__company=user_company)
                if qs.exists():
                    return qs
                else:
                    return ExpanseBudget.objects.none()
            except ValueError:
                return ExpanseBudget.objects.none()
        else:
            return ExpanseBudget.objects.filter(category__company=user_company).order_by("-id")

    def _get_actions(self, obj):
        t = get_template("action_button/budget_action_button.html")
        return t.render({"budget": obj, "request": self.request})

    def filter_queryset(self, qs):
        if self.search:
            return qs.filter(
                Q(category__category__icontains=self.search) |
                Q(budget_amount__icontains=self.search) |
                Q(date__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs, current_month=None):
        results = []

        total_budget_amount = 0
        total_expanse_amount = 0

        if not qs.exists() and current_month:
            user_company = CompanyUsers.objects.get(user=self.request.user).company
            categories = ExpanseCategory.objects.filter(company=user_company)
            for category in categories:
                results.append({
                    'category': category.category,
                    'budget_amount': 0.00,
                    'actual_amount': 0.00,
                    'actions': '',
                })
        else:
            for o in qs:
                total_expanse = ExpanseManagement.objects.filter(
                    expanse_budget=o
                ).aggregate(total_expense=Sum('expanse'))['total_expense'] or 0.00

                b_amount = float(o.budget_amount)
                ex_amount = float(total_expanse)

                total_budget_amount += b_amount
                total_expanse_amount += ex_amount
                results.append({
                    'category': o.category.category,
                    'budget_amount': o.budget_amount,
                    'actual_amount': f"<span class=\"primary\"> {ex_amount} </span>" if ex_amount < b_amount else f"<span class=\"danger\"> {ex_amount} </span>",
                    'actions': self._get_actions(o),
                })
            
        
        results.append({
            'category': f"<span style=\"font-weight:700\"> Total: </span>",
            'budget_amount': total_budget_amount,
            'actual_amount': f"<span class=\"primary\"> {total_expanse_amount} </span>" if total_expanse_amount < total_budget_amount else f"<span class=\"danger\"> {total_expanse_amount} </span>",
            'actions': f"""<td>
                <a href="{reverse('expanse_management:expanse_detail_all', kwargs={"month": current_month})}" title="Edit" class="update-expanse"><i class="ft-eye font-medium-3 mr-2 text-primary"></i></a>
            </td>""",
        })

        return results

    def get(self, request, *args, **kwargs):
        current_month = self.request.GET.get("current_month")
        qs = self.get_queryset()
        context_data = self.get_context_data(request, qs, current_month)
        return JsonResponse(context_data)

    def get_context_data(self, request, qs=None, current_month=None):
        if qs is None:
            qs = self.get_queryset()
        filtered_qs = self.filter_queryset(qs)
        results = self.prepare_results(filtered_qs, current_month)
        return {
            "data": results,
            "recordsTotal": filtered_qs.count(),
            "recordsFiltered": filtered_qs.count(),
        }


from datetime import date as dt_date, timedelta 
class ExpanseCreateView(CompanyAdminLoginRequiredMixin, CreateView):
    template_name = "expanse_management/expanse_create_update_form.html"
    model = ExpanseManagement
    form_class = ExpanseManagementForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form), status=201)  # Status 201 for invalid form

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance_date = instance.date
        print('date: ', instance_date)

        # Extract year and month from the `date` attribute
        year = instance_date.year
        print('year: ', year)
        month = instance_date.month
        print('month: ', month)
        
        # Define the start and end dates for the month
        start_date = dt_date(year, month, 1)
        end_date = (start_date.replace(month=(month % 12) + 1, day=1) - timedelta(days=1))

        # Extract category from the form data
        category_id = self.request.POST.get('category')
        if not category_id:
            return JsonResponse({'error': 'Category is required.'}, status=201)

        try:
            category_id = int(category_id)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid category ID.'}, status=201)

        user_company = CompanyUsers.objects.get(user=self.request.user).company

        # Check if there are any budget entries for the selected month and year
        budget_exists = ExpanseBudget.objects.filter(date__year=year, date__month=month, category__company=user_company).exists()

        if not budget_exists:
            # Create budget entries for all categories if none exist for the selected month and year
            categories = ExpanseCategory.objects.filter(company=user_company)
            for category in categories:
                ExpanseBudget.objects.create(
                    category=category,
                    date=start_date,
                    budget_amount=0.00
                )

        # Get the category object for the form submission
        category = get_object_or_404(ExpanseCategory, pk=category_id, company=user_company)

        # Get or create the budget for the selected category and date
        expanse_budget, created = ExpanseBudget.objects.get_or_create(
            category=category,
            date=start_date,
            defaults={'budget_amount': 0.00}
        )

        # Assign the budget to the instance and save
        instance.expanse_budget = expanse_budget
        instance.save()

        response = HttpResponse(status=200)
        response["HX-Trigger"] = json.dumps(
            {
                "customerExpanseCreate": {
                    "message": "Expanse Added.",
                    "level": "success",
                }
            }
        )
        return response
    

class GetCategoriesView(View):
    def get(self, request):
        categories = ExpanseCategory.objects.values('id', 'category')
        category_dict = {cat['id']: cat['category'] for cat in categories}
        return JsonResponse({'categories': category_dict})

class ExapnseDeleteView(CompanyAdminLoginRequiredMixin, View):
    def post(self, request):
        company_id = self.request.POST.get("id")
        # print('company_id: ', company_id)
        # ExpanseManagement.objects.filter(id = company_id).delete()
        return JsonResponse({"message": "Company deleted successfully."})
    
class ExpanseDetailView(CompanyAdminLoginRequiredMixin, DetailView):
    model = ExpanseBudget
    template_name = "expanse_management/expanse_detail.html"
    context_object_name = "expanse"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expanse_budget = self.get_object()
        # category = expanse_budget.category
        # month = expanse_budget.date.strftime('%Y-%m')  # Extract month in 'YYYY-MM' format

        # # Fetch all expenses for the same category and month
        # expenses = ExpanseManagement.objects.filter(
        #     expanse_budget__category=category,
        #     date__year=expanse_budget.date.year,
        #     date__month=expanse_budget.date.month
        # ).order_by('date')

        # context['expenses'] = expenses
        context["expanse_budget"]=expanse_budget.pk
        return context
    
class ExpanseDetailAllView(CompanyAdminLoginRequiredMixin, ListView):
    model = ExpanseBudget
    template_name = "expanse_management/expanse_detail.html"
    context_object_name = "expanse"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # category = expanse_budget.category
        # month = expanse_budget.date.strftime('%Y-%m')  # Extract month in 'YYYY-MM' format

        # # Fetch all expenses for the same category and month
        # expenses = ExpanseManagement.objects.filter(
        #     expanse_budget__category=category,
        #     date__year=expanse_budget.date.year,
        #     date__month=expanse_budget.date.month
        # ).order_by('date')

        # context['expenses'] = expenses
        print(self.kwargs.get("month"))
        print("============ month", self.kwargs.get("month"))
        context["month"] = self.kwargs.get("month")
        context["expanse_budget"]= "all"
        return context

class ExpanseListAjaxView(DataTableMixin, View):
    model = ExpanseManagement

    def get_queryset(self):
        obj_pk = self.request.GET.get("obj_pk")
        month = self.request.GET.get("month")
        print(self.request.user)

        filter = {}

        if month:
            c_year = month.split("-")[0]
            c_month = month.split("-")[1]
            filter = {
                "date__year":c_year,
                "date__month":c_month,
                "expanse_budget__category__company__id": self.request.user.get_company_id
            }
        if obj_pk != "all":
            expanse_budget = ExpanseBudget.objects.get(id=obj_pk)
            filter = {
                "date__year":expanse_budget.date.year,
                "date__month":expanse_budget.date.month,
                "expanse_budget__category": expanse_budget.category,
                "expanse_budget__category__company__id": self.request.user.get_company_id
            }

        # Fetch all expenses for the same category and month
        qs = ExpanseManagement.objects.filter(**filter).order_by('date')

        return qs
          
    def filter_queryset(self, qs):
        if self.search:
            return qs.filter(
                Q(expanse_budget__category__category__icontains=self.search) |
                Q(expanse__icontains=self.search) |
                Q(date__icontains=self.search)|
                Q(note__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs, current_month=None):
        results = []

        for o in qs:

            formatted_date = o.date.strftime('%m-%d-%Y %H:%M')
            print('formatted_date: ', formatted_date,"stored Date" ,o.date)
            results.append({
                'date': formatted_date,
                'category': o.expanse_budget.category.category,
                'expanse': o.expanse,
                'note': o.note,
            })
        return results

    def get(self, request, *args, **kwargs):
        obj_pk = self.request.GET.get("obj_pk")
        qs = self.get_queryset()
        context_data = self.get_context_data(request, qs, obj_pk)
        return JsonResponse(context_data)

    def get_context_data(self, request, qs=None, obj_pk=None):
        if qs is None:
            qs = self.get_queryset()
        filtered_qs = self.filter_queryset(qs)
        results = self.prepare_results(filtered_qs, obj_pk)
        return {
            "data": results,
            "recordsTotal": filtered_qs.count(),
            "recordsFiltered": filtered_qs.count(),
        }




import datetime
from django.db import models
from django.utils.translation import gettext_lazy as _
from app_modules.base.models import BaseModel
from app_modules.company.models import Company

# Create your models here.

class ExpanseCategory(BaseModel):
    category = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="company_category", null=True, blank=True)

    def __str__(self):
        return self.category
    
class ExpanseBudget(BaseModel):
    category = models.ForeignKey(ExpanseCategory,on_delete=models.CASCADE,null=True,related_name="expanse_budget_category")
    budget_amount = models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    date = models.DateTimeField()
    
    def __str__(self):
        return self.category.category
    

class ExpanseManagement(BaseModel):
    expanse_budget = models.ForeignKey(ExpanseBudget,on_delete=models.CASCADE,null=True,related_name="budget_amount_expanse")
    expanse = models.DecimalField(max_digits=10, decimal_places=2 ,default=0.00)
    date = models.DateTimeField()
    note = models.TextField()

    def __str__(self):
        return self.expanse_budget
    

from django.db import models
from app_modules.base.models import BaseModel
from django.utils.translation import gettext_lazy as _
from app_modules.customers.models import Customer
from app_modules.company.models import Company
from app_modules.product.models import Product
from django.contrib.auth import get_user_model
User = get_user_model()


# Create your models here.
class CreditMemo(BaseModel):
    APP_CREDIT = "app credit"
    WALK_IN_CREDIT = "walk in credit"
    WEB_CREDIT = "web credit"

    CREDIT_TYPES = (
        (APP_CREDIT, "App Credit"),
        (WALK_IN_CREDIT, "Walk-in Credit"),
        (WEB_CREDIT, "Web Credit"),
    )

    NEW = "new"
    APPROVED = "approved"
    CANCELLED = "cancelled"
    DECLINE = "decline"

    STATUS_CHOICES = (
        (NEW, "New"),
        (APPROVED, "Approved"),
        (CANCELLED, "Cancelled"),
        (DECLINE, "Decline"),
    )

    customer = models.ForeignKey(Customer, verbose_name=_("Customer"), on_delete=models.CASCADE)
    company = models.ForeignKey(Company, verbose_name=_("Company"), on_delete=models.CASCADE, null=True, blank=True, related_name="company_credit_memos")
    date = models.DateField()
    credit_type = models.CharField(_("Credit Type"), max_length=20, choices=CREDIT_TYPES, default=WEB_CREDIT)
    status = models.CharField(_("Status"), max_length=10, choices=STATUS_CHOICES, default=NEW)
    remark = models.TextField(_("Remark"), null=True, blank=True)
    item_total = models.FloatField(_("Item Total"), default=0)
    grand_total = models.FloatField(_("Grand Total"), default=0)
    adjustment = models.FloatField(_("Adjustment"), default=0)
    discount = models.FloatField(_("Discount"), default=0)
    added_by = models.ForeignKey(User, verbose_name=_("Added By"), on_delete=models.CASCADE, null=True, blank=True)

    @property
    def item_count(self):
        return self.credit_memo_products.all().count()

    @property
    def discount_amount(self):
        return round((self.item_total - self.grand_total + self.adjustment), 2)


class CreditMemoProduct(BaseModel):
    credit_memo = models.ForeignKey(CreditMemo, verbose_name=_("Credit Memo"), on_delete=models.CASCADE, related_name="credit_memo_products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, related_name="product_credit_memo")
    unit_type = models.CharField(max_length=50, verbose_name=_('Unit Type'))
    return_quantity = models.PositiveIntegerField(verbose_name=_('Quantity'), default=0)
    fresh_return_quantity = models.PositiveIntegerField(verbose_name=_('Fresh Quantity'), default=0)
    damage_return_quantity = models.PositiveIntegerField(verbose_name=_('Damage Quantity'), default=0)
    total_pieces = models.PositiveIntegerField(verbose_name=_('Total Pieces'), default=0)
    total_price = models.PositiveIntegerField(verbose_name=_('Total Price'), default=0)
    unit_price = models.PositiveIntegerField(verbose_name=_('Unit Price'), default=0)

    @property
    def get_unit_type_pieces(self):
        current_product = Product.objects.get(id=self.product.id)
        if(self.unit_type == 'Piece'):
            return 1
        elif(self.unit_type == 'Box'):
            return current_product.box_piece
        elif(self.unit_type == 'Case'):
            return current_product.case_piece
    
    @property
    def get_total_pieces(self):
        return self.return_quantity * self.get_unit_type_pieces


class CreditMemoLog(BaseModel):
    credit_memo = models.ForeignKey(CreditMemo, verbose_name=_("Credit Memo"), on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, verbose_name=_("Credit Memo"), on_delete=models.CASCADE, null=True, blank=True)
    remark = models.TextField(_("Remark"))
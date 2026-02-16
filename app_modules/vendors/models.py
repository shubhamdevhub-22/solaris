from django.db import models
from app_modules.base.models import BaseModel
from django.utils.translation import gettext_lazy as _
from app_modules.customers.validators import validate_file_extension
from django.core.validators import MinValueValidator



from app_modules.company.models import Company

# Create your models here.
class Vendor(BaseModel):
    ACTIVE = "active"
    INACTIVE = "inactive"

    VENDOR_STATUS = (
        (ACTIVE, "Active"),
        (INACTIVE, "Inactive"),
    )
    address_line_1 = models.CharField(max_length=100, null=True, blank=True)
    address_line_2 = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    zip_code = models.IntegerField(null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    office_number_1 = models.CharField(max_length=50, null=True, blank=True)
    office_number_2 = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, null=True, blank=True)
    website = models.URLField(max_length=200, null=True, blank=True)
    status = models.CharField(_("Status"), max_length=10, choices=VENDOR_STATUS, default=ACTIVE)
    company = models.ForeignKey(Company, verbose_name=_("Company"), on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name+' '+self.last_name}"
    

class VendorDocument(BaseModel):
    vendor = models.ForeignKey(Vendor, verbose_name=_("Vendor"), on_delete=models.CASCADE , related_name="vendor")
    document_name= models.CharField(_("Document Name"), max_length=50)
    document = models.FileField(_("Document"), upload_to='vendor-documents',validators=[validate_file_extension])

    def __str__(self):
        return self.document_name
    
class VendorPayment(BaseModel):

    ELECTRONIC_TRANSFER = 'electronic transfer'
    CASH = 'cash'
    CHEQUE = 'cheque'
    CREDIT_CARD='credit card'
    MONEY_ORDER='money order'

    PAYMENT_MODE_CHOICES=(
        (ELECTRONIC_TRANSFER, 'Electronic Transfer'),
        (CASH,'Cash'),
        (CHEQUE,'Cheque'),
        (CREDIT_CARD,'Credit Card'),
        (MONEY_ORDER, 'Money Order'),
    )

    vendor = models.ForeignKey(Vendor, verbose_name=_("Vendor"), on_delete=models.CASCADE , related_name="vendor_payment")
    payment_mode=models.CharField(_("Payment Mode"),choices=PAYMENT_MODE_CHOICES, max_length=50, default=CASH )
    payment_date=models.DateField(_("Payment Date"), auto_now=False, auto_now_add=False)
    reference_number=models.CharField(_("Reference Number"), max_length=50, null=True,blank=True)
    remark = models.CharField(_("Remark"), max_length=100, null=True, blank=True)
    payment_amount = models.FloatField(_("Payment Amount"), default=0.00,validators=[MinValueValidator(0.0)])
    
    @property
    def get_no_of_bills(self):
        return self.vendor_payment.all().count()
    
    @property
    def get_amount(self):
        payment_history_amount = VendorPaymentBill.objects.filter(vendor_payment__id=self.id).values_list('amount', flat=True)
        # print("➡ payment_history_amount :", payment_history_amount)
        # history_amount = payment_history_amount.amount
        # print("➡ history_amount :", history_amount)
        return payment_history_amount if payment_history_amount else 0
    
    @property
    def get_purchase_order_detail(self):
        from app_modules.purchase_order.models import PurchaseOrder
        vendor_bills = self.vendor_payment.all().values_list('vendor_bill', flat=True) 
        vendor_bill=VendorBill.objects.filter(id__in=vendor_bills).values_list('purchase_order__id', flat=True)
        return PurchaseOrder.objects.filter(id__in=vendor_bill) #if self.customer_payment else ""
    
    def __str__(self):
        return self.vendor.first_name
    
    

class VendorBill(BaseModel):
    from app_modules.purchase_order.models import PurchaseOrder

    COMPLETE = "complete"
    INCOMPLETE = "incomplete"

    VENDOR_BILL_STATUS = (
        (COMPLETE, "Complete"),
        (INCOMPLETE, "Incomplete"),
    )

    purchase_order=models.ForeignKey(PurchaseOrder, verbose_name=_("Purchase Order"), on_delete=models.CASCADE,related_name="purchase_order")
    vendor = models.ForeignKey(Vendor, verbose_name=_("Vendor"), on_delete=models.CASCADE , related_name="vendor_bill")
    status= models.CharField(_("Status"), choices=VENDOR_BILL_STATUS, max_length=50, default=INCOMPLETE)
    bill_amount= models.FloatField(_("Bill Amount"),default=0.00)
    paid_amount= models.FloatField(_("Paid Amount"),default=0.0)
    due_amount= models.FloatField(_("Due Amount"),default=0.00)

    def __str__(self):
        return self.vendor.first_name

class VendorPaymentBill(BaseModel):
    vendor_payment = models.ForeignKey(VendorPayment, verbose_name=_("Vendor Payment"), on_delete=models.CASCADE,related_name='vendor_payment')
    vendor_bill = models.ForeignKey(VendorBill, verbose_name=_("Vendor Bill"), on_delete=models.CASCADE,related_name='vendor_bill')
    amount= models.FloatField(_("Amount"))

    def __str__(self):
        return self.vendor_payment.vendor.first_name
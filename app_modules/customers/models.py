from django.db import models
from app_modules.base.models import BaseModel
from django.utils.translation import gettext_lazy as _
from app_modules.users.models import User
from app_modules.company.models import Company
import datetime
from app_modules.customers.validators import validate_file_extension
from app_modules.product.models import Product, Brand
from app_modules.vendors.models import Vendor

# Create your models here.
class Zone(BaseModel):
    zone_code = models.CharField(_("Zone Code"), max_length=50)
    zone_description = models.TextField(_("Zone Description"), null= True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="company_zone", null=True, blank=True)

    def __str__(self):
        return self.zone_code

class PriceLevel(BaseModel):
    ACTIVE = "active"
    INACTIVE = "inactive"

    DISTRIBUTOR = "distributor"
    RETAIL = "retail"
    WHOLESALE = "wholesale"

    STATUS_CHOICES = (
        (ACTIVE,'Active'),
        (INACTIVE,'Inactive')
    )

    TYPE_CHOICES = (
        (DISTRIBUTOR,'Distributor'),
        (RETAIL,'Retail'),
        (WHOLESALE,'Wholesale')
    )


    customer_type = models.CharField(_('Customer Type'), choices=TYPE_CHOICES, max_length=20)
    price_level = models.CharField(_('Price Level Name'), max_length=30)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="company_pricelevel", null=True, blank=True)
    status = models.CharField(_('Status'), choices=STATUS_CHOICES, max_length=20, default=ACTIVE)

    def __str__(self):
        return self.price_level

class Customer(BaseModel):
    ACTIVE = "active"
    INACTIVE = "inactive"

    DISTRIBUTOR = "distributor"
    RETAIL = "retail"
    WHOLESALE = "wholesale"

    CASE = "case"
    CHECK = "check"
    NET_10 = "net 10"
    NET_15 = "net 15"
    NET_30 = "net 30"


    STATUS_CHOICES = (
        (ACTIVE,'Active'),
        (INACTIVE,'Inactive')
    )

    TYPE_CHOICES = (
        (DISTRIBUTOR,'Distributor'),
        (RETAIL,'Retail'),
        (WHOLESALE,'Wholesale')
    )

    TERM_CHOICES = (
        (CASE,'Case'),
        (CHECK,'Check'),
        (NET_10,'Net 10'),
        (NET_15, 'Net 15'),
        (NET_30, 'Net 30')
    )

    customer_name = models.CharField(_('Shop Name'), max_length=255)
    customer_type = models.CharField(_('Customer Type'), choices=TYPE_CHOICES, max_length=255, default=RETAIL)
    status = models.CharField(_('Status'), choices=STATUS_CHOICES, max_length=255, default=ACTIVE)
    sales_rep = models.ForeignKey(User , on_delete= models.CASCADE, null=True, blank=True)
    tax_id = models.CharField(_('Tax Id'), max_length=255, null=True, blank=True)
    terms = models.CharField(_('Terms'), choices=TERM_CHOICES, max_length=255,null=True, blank=True)
    dba_name = models.CharField(_('DBA Name'), max_length=255, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="company", null=True, blank=True)
    price_level = models.ForeignKey(PriceLevel, on_delete=models.CASCADE, related_name="price_level_customer", null=True, blank=True)
    store_open_time = models.TimeField(_('Store Open Time'), auto_now=False, auto_now_add=False,null=True, blank=True)
    store_close_time = models.TimeField(_('Store Close Time'), auto_now=False, auto_now_add=False,null=True, blank=True)
    total_credit_amount = models.FloatField(_("Total Credit Amount"), default=0)
    #for Solaris Project field
    zone = models.ForeignKey(Zone, verbose_name=_("Zone"), on_delete=models.CASCADE,null=True, blank=True)
    area = models.CharField(_("Area"), max_length=255,null=True, blank=True)
    transport = models.CharField(_("Transport"), max_length=255,null=True, blank=True)
    cst =models.CharField(_("CST Number"),max_length=255 , null=True, blank=True )
    gst =models.CharField(_("GST Number"), max_length=255 , null=True, blank=True)
    phone_1 = models.CharField(_("Phone 1"), max_length=255,null=True, blank= True)
    phone_2 = models.CharField(_("Phone 2"), max_length=255,null=True, blank= True)
    mobile = models.CharField(_("Mobile Number"), max_length=255,null=True, blank= True)
    past_due_amount = models.FloatField(_("Past Due Amount"), default=0)
    credit_amount = models.FloatField(_("Credit Amount"), default=0)
    fax = models.CharField(_("Fax Number"), max_length=255, null=True, blank=True)
    remark = models.CharField(_('Remark'), max_length=255, null=True, blank=True)
    email = models.CharField(_('Email'),max_length=255,null=True, blank=True)
    code = models.CharField(_("Customer Code"), max_length=255,null=True, blank=True, unique=True)
    is_locked = models.BooleanField(_("Lock Status"), default=False)
    contact_name = models.CharField(_("Contact Name"), max_length=255,null=True, blank=True,)
    
    def __str__(self):
        return self.customer_name
        
    @property
    def get_due_order(self):
        customer_order = self.order_customers.all()
        
        order_count = customer_order.count()

        total_balance_amount = 0
        total_paid_amount = 0
        for customer in customer_order:
            total_balance_amount += customer.grand_total
            total_paid_amount += customer.get_paid_amount
            
        total_due_amount = total_balance_amount-total_paid_amount

        return order_count, total_balance_amount,total_paid_amount, total_due_amount
    
    

class CustomerDocuments(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="customer_documents")
    document_name = models.CharField(_("Document Name"), max_length=30, null=True, blank=True)
    document = models.FileField(upload_to='customer documents', validators=[validate_file_extension])

    def __str__(self):
        return self.document_name

 # for shipping address
class CustomerShippingAddress(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="customer_shipping_address")
    shipping_address_line_1 = models.CharField(_('Address line 1'), max_length=255)
    shipping_address_line_2 = models.CharField(_('Address line 2'), max_length=255, null=True, blank=True)
    
    shipping_suite_apartment = models.CharField(_('Address line 3'), max_length=255, null=True, blank=True)
    shipping_city = models.CharField(_('City'), max_length=255)
    shipping_state = models.CharField(_('State'), max_length=255, default="", null=True, blank=True)
    shipping_country = models.CharField(_('Country'), max_length=255, default="INDIA")
    shipping_zip_code = models.IntegerField(_('Zip Code'), null=True, blank=True)
    shipping_latitude = models.FloatField(_('Latitude'), null=True, blank=True)
    shipping_longitude = models.FloatField(_('Longitude'), null=True, blank=True)
    is_default = models.BooleanField(_('is Default'), default=False)

    #FOR SOLARIS
    shipping_address_line_3 = models.CharField(_('Address line 3'), max_length=2550, null=True, blank=True)
    

    def __str__(self):
        return self.shipping_address_line_1

 # for billing address    
class CustomerBillingAddress(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="customer_billing_address")
    billing_address_line_1 = models.CharField(_('Address line 1'), max_length=255)
    billing_address_line_2 = models.CharField(_('Address line 2'), max_length=255, null=True, blank=True)
    billing_suite_apartment = models.CharField(_('Address line 3'), max_length=255, null=True, blank=True)
    billing_city = models.CharField(_('City'), max_length=255)
    billing_state = models.CharField(_('State'), max_length=255, default="", null=True, blank=True)
    billing_country = models.CharField(_('Country'), max_length=255, default="INDIA")
    billing_zip_code = models.IntegerField(_('Zip Code'),null=True, blank=True)
    billing_latitude = models.FloatField(_('Latitude'), null=True, blank=True)
    billing_longitude = models.FloatField(_('Longitude'), null=True, blank=True)
    is_default = models.BooleanField(_('is Default'), default=False)

    # FOR SOLARIS
    billing_address_line_3 = models.CharField(_('Address line 3'), max_length=100, null=True, blank=True)


    def __str__(self):
        return self.billing_address_line_1
    
class MultipleContact(BaseModel):
    
    STORE = "store"
    MANAGER = "manager"
    EMPLOYEE = "employee"

    PERSON_TYPE_CHOICES = (
        (STORE,'Store'),
        (MANAGER,'Manager'),
        (EMPLOYEE,'Employee')
    )

    customer_obj = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="customer")
    type = models.CharField(_('Type'), max_length=255, choices=PERSON_TYPE_CHOICES,null=True, blank=True)
    contact_person = models.CharField(_('Contact Person'), max_length=255,null=True, blank=True)
    email = models.CharField(_('Email'),max_length=255,null=True, blank=True)
    mobile_no = models.CharField(_('Mobile No'), max_length=50, null=True, blank=True)
    is_default = models.BooleanField(_('is Default'), default=False)


    def __str__(self):
        return self.contact_person
    

class Payment(BaseModel):
    CHECK = "check"
    CASH = "cash"
    UPI = "upi/neft/rtgs"

    PAYMENT_MODE_CHOICE = (
        (CHECK,'Cheque'),
        (CASH,'Cash'),
        (UPI,'UPI/NEFT/RTGS'),
    )

    customer_name = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="payment_customer")
    receive_date = models.DateField(_('Receive Date'),default=datetime.date.today)
    entry_date = models.DateField(_('Entry Date'),default=datetime.date.today)
    receive_amount = models.FloatField(_('Receive Amount'), default=0.0)
    payment_mode = models.CharField(_('Payment Mode'), choices=PAYMENT_MODE_CHOICE , max_length=30, default=CASH)
    check_no = models.IntegerField(_('Check No'),  null=True, blank=True)
    reference_id = models.CharField(_('Reference Id'), max_length=50, null=True, blank=True)
    remark = models.CharField(_('Remark'), max_length=20, null=True, blank=True)
    
    def __str__(self):
        return self.customer_name.customer_name
    
    @property
    def get_status(self):
        customer_payment = CustomerPaymentBill.objects.filter(customer_payment__id=self.id).first()
        if customer_payment and customer_payment.customer_bill:
            return customer_payment.customer_bill.status
        return ""
    
    @property
    def get_amount(self):
        payment_history_amount = CustomerPaymentBill.objects.filter(customer_payment__id=self.id).values_list('amount', flat=True)
        return payment_history_amount if payment_history_amount else 0
    
    @property
    def get_order_count(self):
        return self.customer_payment.all().count() if self.customer_payment else 0
    
    @property
    def get_order_details(self):
        from app_modules.order.models import Order, OrderBill
        customer_bills = self.customer_payment.all().values_list('customer_bill', flat=True) 
        customer_bill=OrderBill.objects.filter(id__in=customer_bills).values_list('order__id', flat=True)
        return Order.objects.filter(id__in=customer_bill) #if self.customer_payment else ""
        
        

class CustomerBill(BaseModel):

    COMPLETE = "complete"
    INCOMPLETE = "incomplete"

    CUSTOMER_BILL_STATUS = (
        (COMPLETE, "Complete"),
        (INCOMPLETE, "Incomplete"),
    )

    from app_modules.order.models import Order
    
    order=models.ForeignKey(Order, verbose_name=_("Order"), on_delete=models.CASCADE,related_name="order")
    customer = models.ForeignKey(Customer, verbose_name=_("Customer"), on_delete=models.CASCADE , related_name="customer_bill")
    status= models.CharField(_("Status"), choices=CUSTOMER_BILL_STATUS, max_length=50, default=INCOMPLETE)
    bill_amount= models.FloatField(_("Bill Amount"), default=0.00)
    paid_amount= models.FloatField(_("Paid Amount"), default=0.0)
    due_amount= models.FloatField(_("Due Amount"), default=0.00)

    def __str__(self):
        return self.customer.customer_name

class CustomerPaymentBill(BaseModel):
    from app_modules.order.models import Order, OrderBill
    customer_payment = models.ForeignKey(Payment, verbose_name=_("Customer Payment"), on_delete=models.CASCADE,related_name='customer_payment')
    customer_bill = models.ForeignKey(OrderBill, verbose_name=_("Order Bill"), on_delete=models.CASCADE,related_name='customer_bill', null=True, blank=True)
    amount = models.DecimalField(_("Amount"), decimal_places=2, max_digits=20)

    def __str__(self):
        return self.customer_bill.customer.customer_name
    

class SalesRoute(BaseModel):
    ACTIVE = "active"
    INACTIVE = "inactive"

    STATUS_CHOICES = (
        (ACTIVE,'Active'),
        (INACTIVE,'Inactive')
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="salesroute_company", null=True, blank=True)
    route_name = models.CharField(_('Route Name'), max_length=50)
    sales_rep = models.ForeignKey(User , on_delete= models.CASCADE, null=True, blank=True, related_name="user")
    status = models.CharField(_('Status'), choices=STATUS_CHOICES, max_length=20, default=ACTIVE)
    customer = models.ManyToManyField(Customer, null=True, blank=True, related_name="salesroute_customer")

    def __str__(self):
        return self.route_name
    
    
    
class PriceLevelProduct(BaseModel):

    BOX = "box"
    CASE = "case"
    PIECE = "piece"

    UNIT_TYPES_CHOICES = (
        (BOX, 'Box'),
        (CASE, 'Case'),
        (PIECE, 'Piece'),
    )

    price_level = models.ForeignKey(PriceLevel, on_delete=models.CASCADE, related_name="pricelevel")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product")
    unit_type = models.CharField(_('Unit Type'), choices=UNIT_TYPES_CHOICES, max_length=7, default=PIECE)
    custom_price = models.FloatField(_('Custom Price'))

    def __str__(self):
        return self.product.name
    

class CustomerLog(BaseModel):
    customer = models.ForeignKey(Customer, verbose_name=_("Customer"), on_delete=models.CASCADE, null=True, blank=True)
    action_by = models.ForeignKey(User, verbose_name=_("Action By"), on_delete=models.CASCADE, null=True, blank=True)
    remark = models.TextField(_("Remark"))
    order = models.ForeignKey("order.Order", verbose_name=_("Order"), on_delete=models.CASCADE)
    
    def __str__(self):
        return self.customer.customer_name
    

class Discount(BaseModel):
    PRIMARY = "primary"
    SECONDARY = "secondary"

    TYPE_CHOICES = (
        ("PRIMARY", PRIMARY),
        ("SECONDARY", SECONDARY),
    )
    category = models.CharField(_("Category Name"), max_length=50)
    discount = models.FloatField(_("Discount (%)"), null=True, blank=True)
    brand = models.ForeignKey(Brand, verbose_name=_("Brand"), on_delete=models.CASCADE, related_name="brand_discounts", null=True, blank=True)
    company = models.ForeignKey(Company, verbose_name=_("Company"), on_delete=models.CASCADE, related_name="brand_discounts", null=True, blank=True)
    type = models.CharField(_("Type"), max_length=50, choices=TYPE_CHOICES, null=True, blank=True)

    def __str__(self):
        return self.category+" ("+str(self.discount)+" %)"


class MultipleVendorDiscount(BaseModel):
    primary_discount = models.ForeignKey(Discount, on_delete=models.CASCADE, related_name="customer_primary_discounts", null=True, blank=True)
    primary_percent = models.FloatField(_("Primary Discount (%)"), null=True, blank=True, default=0)
    additional_discount = models.ForeignKey(Discount, on_delete=models.CASCADE, null=True, blank=True, related_name="customer_secondary_discounts")
    additional_percent = models.FloatField(_("Additional Discount (%)"), null=True, blank=True, default=0)
    brand = models.ForeignKey(Brand, verbose_name=_("Brand"), on_delete=models.CASCADE, related_name="customer_discounts", null=True, blank=True)
    customer = models.ForeignKey(Customer, verbose_name=_("Customer"), on_delete=models.CASCADE, related_name="customer_discounts", null=True, blank=True)
    is_primary_brand_discount = models.BooleanField(("Is Primary Brand Discount"), default=False)
    is_secondary_brand_discount = models.BooleanField(("Is Secondary Brand Discount"), default=False)

    def __str__(self):
        return self.discount.category


class Replacement(BaseModel):
    from app_modules.order.models import Order

    CREDIT = "credit"
    MONEY = "money"
    SETTLEMENT = "settlement"

    STATUS_CHOICES = (
        # (MONEY, "Money"),
        (CREDIT, "Credit"),
        (SETTLEMENT, "Settlement")
    )

    replace_id = models.CharField("Replace ID", max_length=50, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name="replacement_customers")
    created_by = models.ForeignKey(User, verbose_name=_("Created BY"), on_delete=models.CASCADE, related_name="replacement_created_user", null=True, blank=True)
    return_type = models.CharField(max_length=25, verbose_name=_("Return Type"), choices=STATUS_CHOICES)
    order = models.ForeignKey(Order, verbose_name="Order", on_delete=models.SET_NULL, null=True, blank=True, related_name="replacement_orders")
    settlement_pending = models.BooleanField(_("Settlement Pending"), default=False)
    settlement_completed = models.BooleanField(_("Settlement Completed"), default=False)

    @property
    def get_replacement_total(self):
        replacement_products = ReplacementProduct.objects.filter(replacement_order = self)
        
        order_total = 0
        for replacement_product in replacement_products:
            order_total = order_total + (replacement_product.replace_quantity * replacement_product.order_product.unit_price)
        
        return "%.2f" % round(float(order_total), 2)

    def __str__(self):
        return self.customer.customer_name


class ReplacementProduct(BaseModel):
    from app_modules.order.models import OrderedProduct

    replacement_order = models.ForeignKey(Replacement,on_delete=models.SET_NULL,null=True,related_name="replacement_order_products")
    order_product = models.ForeignKey(OrderedProduct, related_name="replacement_order_products", on_delete=models.CASCADE, null=True, blank=True)
    replace_quantity = models.PositiveIntegerField(_('Replace Quantity'))
    
    @property
    def get_replace_item_total(self):
        # unit_type_pieces = self.order_product.get_unit_type_pieces
        item_total = float(self.replace_quantity) * self.order_product.unit_price
        return "%.2f" % round(float(item_total), 2)
    
    @property
    def get_available_replace_quantity(self):
        return self.order_product.get_available_replacement_stock + self.replace_quantity

    def __str__(self):
        return self.order_product.product.name

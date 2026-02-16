import datetime
from django.db import models
from app_modules.base.models import BaseModel
from app_modules.product.models import Product, WarehouseProductStock, WarehouseProductStockHistory
from app_modules.company.models import Company,Warehouse
from app_modules.customers.models import Customer
from django.utils.translation import gettext_lazy as _
import datetime
from app_modules.users.models import User,Driver
from django.db.models import Sum, F

class Order(BaseModel):

    DRAFT = "draft"
    SAVED = "saved"
    NEW = "new"
    PACKED = "packed"
    PACKING = "packing"
    READY_TO_SHIP = "ready to ship"
    DISPATCH = "dispatch"
    SHIPPED = "shipped"
    UNDELIVERED = "undelivered"
    CANCEL = "cancel"
    CLOSE = "close"
    GENERATE = "generate bill"
    READY_FOR_DISPATCH = "ready for dispatch"
    COMPLETED = "completed"


    CHECK = "check"
    CASH = "cash"
    UPI = "upi/neft/rtgs"
    CREDIT = "credit"

    PAYMENT_METHOD_CHOICE = (
        (CASH, 'Cash'),
        (CREDIT, 'Credit'),
    )

    STATUS_CHOICES = (
        (DRAFT, "Draft"),
        # (SAVED, "Saved"),
        # (GENERATE, "Generate Bill"),
        (DISPATCH, "Dispatch"),
        (NEW, "New"),
        # (PACKED, "Packed"),
        # (READY_TO_SHIP, "Ready to Ship"),
        # (SHIPPED, "Shipped"),
        # (UNDELIVERED, "Undelivered"),
        (CANCEL, "Cancel"),
        # (READY_FOR_DISPATCH, "Ready For Dispatch"),
        (COMPLETED, "Completed"),
        # (CLOSE, "Close"),
    )

    from app_modules.customers.models import Customer
    order_id = models.CharField("Order ID", max_length=50, null=True, blank=True)

    created_by = models.ForeignKey(User, verbose_name=_("Created BY"), on_delete=models.CASCADE, related_name="order_created_user", null=True, blank=True)
    customer = models.ForeignKey(Customer,on_delete=models.SET_NULL,null=True,related_name="order_customers")
    item_total = models.FloatField(_("Gross Bill Total"),null=True, blank=True)
    
    shipping_charges = models.FloatField(_("Shipping Charges"), null=True, blank=True)
    packing_charges = models.FloatField(_("Packing Charges"), null=True, blank=True)
    adjustments = models.FloatField(_("Adjustments"), null=True, blank=True, default=0)
    use_credits = models.FloatField(_("Use Credits"), null=True, blank=True, default=0)
    grand_total = models.FloatField(_("Grand Total"), null=True, blank=True, default=0)
    paid_amount = models.FloatField(_("Paid Amount"), null=True, blank=True, default=0)
    balance_amount = models.FloatField(_("Balance Amount"), null=True, blank=True, default=0)
    payment_method = models.CharField(_('Payment Method'), choices=PAYMENT_METHOD_CHOICE , max_length=30, null=True, blank=True)
    company = models.ForeignKey(Company,on_delete=models.SET_NULL,null=True,related_name="company_orders")
    warehouse = models.ForeignKey(Warehouse,on_delete=models.SET_NULL,null=True,related_name="warehouse_orders")
    status = models.CharField(max_length=25, verbose_name=_("Status"), choices=STATUS_CHOICES, default=NEW)
    internal_remarks = models.CharField(verbose_name=_("Internal Remark"), max_length=100, null=True, blank=True)
    order_date = models.DateField(verbose_name=_("Order Date"),default=datetime.date.today)
    reference_number = models.PositiveBigIntegerField(_('Reference Number'), null=True, blank=True)

    is_bill_generated = models.BooleanField(_("Is Bill Generated"), default=False)
    
    # shipping address
    shipping_address_line_1 = models.CharField(_("Address Line 1 "), null=True, blank=True, max_length=255)
    shipping_address_line_2 = models.CharField(_("Address Line 2 "), null=True, blank=True, max_length=255)
    shipping_city = models.CharField(_('City'), max_length=30, null=True, blank=True)
    shipping_state = models.CharField(_('State'), max_length=30, null=True, blank=True)
    shipping_country = models.CharField(_('Country'), max_length=30, null=True, blank=True)
    shipping_zip_code = models.IntegerField(_('Zip Code'), null=True, blank=True)

    # billing address
    billing_address_line_1 = models.CharField(_('Address line 1'), max_length=255, null=True, blank=True)
    billing_address_line_2 = models.CharField(_('Address line 2'), max_length=255, null=True, blank=True)
    billing_city = models.CharField(_('City'), max_length=30, null=True, blank=True)
    billing_state = models.CharField(_('State'), max_length=30, null=True, blank=True)
    billing_country = models.CharField(_('Country'), max_length=30, null=True, blank=True)
    billing_zip_code = models.IntegerField(_('Zip Code'), null=True, blank=True)
    product_reference = models.JSONField(null=True,blank=True)

    inform_admin_for_settlement = models.BooleanField(_("Inform Admin For Settlement"), default=False)
    
    def __str__(self):
        if self.order_id:
            return self.order_id
        else:
            return str("------")

    @property
    def get_item_count(self):
       return self.orders.count()
    
    @property
    def get_paid_amount(self):
       customer_bill = OrderBill.objects.filter(order__id=self.id).first()

    #    paid_amount = CustomerBill.objects.filter(order__id=self.id).aggregate(total_paid_amount=Sum("paid_amount"))
    #    paid = paid_amount['total_paid_amount']

       return customer_bill.paid_amount if customer_bill else self.paid_amount
    
    @property
    def get_total_amount(self):
       customer_bill = OrderBill.objects.filter(order__id=self.id).first()
       return customer_bill.bill_amount if customer_bill else 0
    
    @property
    def get_due_amount(self):
        customer_bill = OrderBill.objects.filter(order__id=self.id).first()
        return customer_bill.due_amount if customer_bill else self.grand_total - self.paid_amount
    
    @property
    def get_order_due_amount(self):
        return self.grand_total-self.paid_amount
    
    # @property

    
    
        
    

class OrderedProduct(BaseModel):
    MRP = "mrp"
    WHOLESALE = "wholesale"
    RETAIL = "retail"

    PRICE_TYPES = (
        (MRP, "MRP"),
        (WHOLESALE, "Wholesale"),
        (RETAIL, "Retail"),
    )

    from app_modules.product.models import Product

    order = models.ForeignKey(Order,on_delete=models.SET_NULL,null=True,related_name="orders")
    product = models.ForeignKey(Product,on_delete=models.SET_NULL,null=True,related_name="products")
    unit_type = models.CharField(_('Unit Type'), max_length=50, default="piece")
    quantity = models.PositiveIntegerField(_('Quantity'))
    price_type = models.CharField(_("Price Type"), choices=PRICE_TYPES, max_length=50, null=True, blank=True, default=MRP)
    unit_price = models.DecimalField(_("Unit Price"), decimal_places=2, max_digits=20)
    product_discount1 = models.FloatField(_("Product Discount 1"),null=True, blank=True,default=0)
    product_discount2 = models.FloatField(_("Product Discount 2"), null=True, blank=True,default=0)
    packed_quantity = models.PositiveIntegerField(_('Packed Quantity'),default=0)
    unpacked_quantity = models.PositiveIntegerField(_('Unpacked Quantity'),default=0)
    special_rate = models.FloatField(_("Special Rate"),null=True, blank=True, default=0)
    special_discount = models.FloatField(_("Special Discount"),null=True, blank=True, default=0)
    free_quantity = models.PositiveIntegerField(_("Free Quantity"),null=True, blank=True, default=0)

    def __str__(self):
        return self.order.customer.customer_name 

    def get_unit_type_pieces(self):
        current_product = self.Product.objects.get(id=self.product.id)
        if(self.unit_type == 'box'):
            return f'{current_product.box_piece}'
        elif(self.unit_type == 'case'):
            return f'{current_product.case_piece}'
        else:
            return f'1'
    
    @property
    def get_total_quantity(self):
        return self.quantity + self.free_quantity
    
    @property
    def get_ready_for_dispatch_stock(self):
        warehouse_stock = WarehouseProductStock.objects.filter(warehouse__name = "WAREHOUSE 1", product = self.product)
        if warehouse_stock:
            total_stock = warehouse_stock.aggregate(total_stock = Sum("stock"))["total_stock"]
            return min(total_stock, self.quantity)
        return 0
    
    @property
    def get_pending_stock(self):
        return max(self.quantity - int(self.get_ready_for_dispatch_stock), 0)

    @property
    def get_product_total_stock(self):
        product_stock = WarehouseProductStock.objects.filter(product = self.product)
        if product_stock:
            total_quantity = product_stock.aggregate(total_quantity = Sum("stock"))["total_quantity"]
        else:
            total_quantity = 0
        return min(total_quantity, self.quantity)

    @property
    def get_available_replacement_stock(self):
        from app_modules.customers.models import ReplacementProduct

        replacements = ReplacementProduct.objects.filter(order_product = self)
        if replacements:
            return self.quantity - replacements.aggregate(total_replace_quantity = Sum("replace_quantity"))["total_replace_quantity"]
        return self.quantity

    @property
    def get_unit_type_pieces(self):
        current_product = self.Product.objects.get(id=self.product.id)
        if(self.unit_type == 'Box'):
            return current_product.box_piece
        elif(self.unit_type == 'Case'):
            return current_product.case_piece
        else:
            return 1
        
    @property
    def get_total_pieces(self):
        unit_type_pieces = self.get_unit_type_pieces
        return self.quantity * unit_type_pieces
    
    @property
    def get_item_total(self):
        unit_type_pieces = self.get_unit_type_pieces
        item_total = self.quantity * unit_type_pieces * self.unit_price
        return "%.2f" % round(float(item_total), 2)
    
    @property
    def get_net_price(self):
        item_total = float(self.get_item_total)
        # if self.product_discount1:
        #     item_total = item_total - (item_total*self.product_discount1)/100
        # if self.product_discount2:
        #     item_total = item_total - (item_total*self.product_discount2)/100
        return "%.2f" % round(item_total, 2)
    
    @property
    def get_available_stock(self):
        warehouse_product_stock = WarehouseProductStock.objects.filter(product=self.product)
        available_stock = 0
        for obj in warehouse_product_stock:
            available_stock += (obj.stock)/self.get_unit_type_pieces + self.quantity
            if self.order.status == Order.DRAFT:
                available_stock = (obj.stock)/self.get_unit_type_pieces 
        return int(available_stock)



class Car(BaseModel):

    ACTIVE = 'active'
    INACTIVE ='inactive'

    STATUS_CHOICES = (
        (ACTIVE, "Active"),
        (INACTIVE, "Inactive")
    )
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="driver")
    car_nickname = models.CharField(_("Car Nick Name"), max_length=30)
    year = models.IntegerField(_("Year"))
    model = models.CharField(_("Model"), max_length=20)
    licence_plate = models.CharField(_("Licence Plate"), max_length=20)
    start_mileage = models.CharField(_("Start Mileage"), max_length=50)
    description = models.TextField(_("Description"), null=True, blank=True)
    make = models.CharField(_("Make"), max_length=30)
    vin_number = models.IntegerField(_("VIN Number"))
    inspect_exp_date = models.DateField(_("Inspect. Exp Date"),default=datetime.date.today)
    status = models.CharField(_("Status"), choices=STATUS_CHOICES, max_length=10, default=ACTIVE)
    company = models.ForeignKey(Company, verbose_name=_("Company"), on_delete=models.CASCADE , related_name="car_company")

    def __str__(self):
        return self.car_nickname
    

class OrderLog(BaseModel):
    order = models.ForeignKey(Order, verbose_name=_("Order"), on_delete=models.CASCADE, related_name="order_logs", null=True, blank=True)
    action_by = models.ForeignKey(User, verbose_name=_("Action By"), on_delete=models.SET_NULL, null=True, blank=True)
    remark = models.TextField(_("Remark"))   

    def __str__(self):
        return self.action_by.full_name 
    

# class DriverAssignedOrders(BaseModel):
#     driver = models.ForeignKey(Driver, verbose_name=_("Assign Driver"), on_delete=models.CASCADE, related_name='driver_assign_orders')
#     order = models.ForeignKey(Order, verbose_name=_("Assign Order"), on_delete=models.CASCADE, related_name='assign_order')
#     date = models.DateField(_("Deliver Date"))

#     def __str__(self):
#         return str(self.date)
    
class AssignDriverRoutes(BaseModel):
    COMPLETED = "completed"
    PENDING = "pending"
    CANCEL = "cancel"
    ROUTE_STATUS=(
        (COMPLETED, 'Completed'),
        (PENDING, 'Pending'),
        (CANCEL, 'Cancel'),
    )

    name =  models.CharField(_("Route Name"), max_length=50)
    driver = models.ForeignKey(Driver, verbose_name=_("Driver"), on_delete=models.CASCADE, related_name='driver_assign_routes')
    date = models.DateField(_("Deliver Date"))
    start_location = models.ForeignKey(Warehouse, verbose_name=_("Start Location"), on_delete=models.CASCADE)
    status = models.CharField(_("Status"), choices=ROUTE_STATUS, max_length=50,default=PENDING)
    synchronized_route = models.BooleanField(default=False)
    def __str__(self):
        return self.name
    
    @property   
    def get_order_count(self):
        return self.assigned_driver_routes.all().count()
  

class AssignOrderRoutes(BaseModel):
    driver_route = models.ForeignKey(AssignDriverRoutes, verbose_name=_("Assigned Driver Routes"), on_delete=models.CASCADE, related_name='assigned_driver_routes')
    order = models.ForeignKey(Order, verbose_name=_("Assigned Order"), on_delete=models.CASCADE, related_name='assined_orders')
    stop = models.IntegerField(_("stop"),null=True,blank=True)
    remark = models.CharField(_("Remark"), max_length=120, null=True, blank=True)

    def __str__(self):
        return f'{int(self.order.id)}'


class OrderBill(BaseModel):

    COMPLETE = "complete"
    INCOMPLETE = "incomplete"

    BILL_STATUS = (
        (COMPLETE, "Complete"),
        (INCOMPLETE, "Incomplete"),
    )

    from app_modules.order.models import Order
    
    is_local_bill = models.BooleanField(_("Is Local Bill"), default=True)

    slip_no = models.IntegerField(_("Slip No"), null=True, blank=True)
    bill_id = models.CharField(_("Bill No"), null=True, blank=True, max_length=20)
    bill_date = models.DateField(_("Bill Date"), null=True, blank=True)
    order=models.ForeignKey(Order, verbose_name=_("Order"), on_delete=models.CASCADE,related_name="order_bill")
    customer = models.ForeignKey(Customer, verbose_name=_("Customer"), on_delete=models.CASCADE , related_name="order_bill")
    status= models.CharField(_("Status"), choices=BILL_STATUS, max_length=50, default=INCOMPLETE)
    due_date = models.DateField(_("Due Date"), null=True, blank=True)
    bill_amount= models.DecimalField(_("Bill Amount"), decimal_places=2, max_digits=20, default=0.00)
    paid_amount= models.DecimalField(_("Paid Amount"), decimal_places=2, max_digits=20, default=0.00)
    due_amount= models.DecimalField(_("Due Amount"), decimal_places=2, max_digits=20, default=0.00)

    gr_number = models.CharField(max_length=100, null=True, blank=True)
    gr_date = models.DateField(_("G.R. Date"), null=True, blank=True)
    transporter = models.CharField(max_length=100, null=True, blank=True)
    case_number = models.IntegerField(_("Case No"), null=True, blank=True)
    packed_by = models.CharField(max_length=100, null=True, blank=True)
    checked_by = models.CharField(max_length=100, null=True, blank=True)
    written_by = models.CharField(max_length=100, null=True, blank=True)

    bill_pdf = models.FileField(upload_to='sales-bills/%Y/%m/%d/', null=True, blank=True)

    @property
    def get_due_days(self):
        try:
            days = self.due_date - self.bill_date
        except:
            return 0
        return days.days
    
    @property
    def get_pending_amount(self):
        remaining_amount = float(self.bill_amount) - self.customer.credit_amount
        return max(remaining_amount, 0)

    def __str__(self):
        return self.customer.customer_name

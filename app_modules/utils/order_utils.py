from app_modules.product.models import Product, WarehouseProductStock,WarehouseProductStockHistory
from app_modules.customers.models import Customer, PriceLevel, PriceLevelProduct, ReplacementProduct, MultipleVendorDiscount, Brand
from app_modules.order.models import Order, OrderedProduct
from app_modules.order.models import Warehouse
from django.db.models import Sum


def get_customer_price_level(customer_id,product_id,unit_type):
    # print('=================')
    # print("➡ unit_type :", unit_type)
    # print("➡ customer_id :", customer_id)

    context = {}
    available_stock = 0
    customer = Customer.objects.get(id = customer_id)
    # print("➡ customer :", customer)
    product = Product.objects.get(id = product_id)
    # warehouse = Warehouse.objects.get(id = warehouse_id)
    

    available_stock = 0
    warehouse_product_stock = WarehouseProductStock.objects.filter(product=product).aggregate(total_sum=Sum("stock"))
    # print("➡ warehouse_product_stock :", warehouse_product_stock)
    # print('=================')
    
    if unit_type == 'Piece':
        price_level_product_type = PriceLevelProduct.PIECE
        available_stock = warehouse_product_stock['total_sum']
    elif unit_type == 'Box':
        price_level_product_type = PriceLevelProduct.BOX
        if product.box:
            available_stock = warehouse_product_stock['total_sum'] / product.box_piece
    elif unit_type == 'Case':
        price_level_product_type = PriceLevelProduct.CASE
        if product.case:
            available_stock = warehouse_product_stock['total_sum'] / product.case_piece
    
    if customer.price_level:
        obj_price_level = PriceLevel.objects.filter(id = customer.price_level.id,status=PriceLevel.ACTIVE).first()
        # #print("➡ obj_price_level :", obj_price_level)
        obj_price_level_products = PriceLevelProduct.objects.filter(price_level = obj_price_level,product = product, unit_type=price_level_product_type).first()
        if not obj_price_level_products:
            if customer.customer_type == Customer.DISTRIBUTOR:
                base_price = product.mrp

            elif customer.customer_type ==  Customer.RETAIL:
                base_price = product.retail_rate

            elif customer.customer_type == Customer.WHOLESALE:
                base_price = product.wholesale_rate

        # #print("➡ obj_price_level_products :", obj_price_level_products.custom_price)
        else:
            # base_price = obj_price_level_products.custom_price
            if obj_price_level_products.custom_price <= 0:
                base_price = product.wholesale_rate
            else:
                base_price = obj_price_level_products.custom_price
                
                if price_level_product_type == PriceLevelProduct.BOX:
                    base_price = base_price / product.box_piece

                elif price_level_product_type == PriceLevelProduct.CASE:
                    base_price = base_price / product.case_piece


    elif customer.customer_type == Customer.DISTRIBUTOR:
        base_price = product.mrp

    elif customer.customer_type ==  Customer.RETAIL:
        base_price = product.retail_rate

    elif customer.customer_type == Customer.WHOLESALE:
        base_price = product.wholesale_rate

    context['available_stock'] = int(available_stock) if available_stock else 0
    context['base_price'] = base_price
    return context

def manage_stock(product,product_id,refrance,product_total_pieces):
    warehouse_stock__list = WarehouseProductStock.objects.filter(product=product, warehouse__name="WAREHOUSE 1", stock__gt =0).order_by("id")
        
    for warehouse_stock_obj in warehouse_stock__list:
        data = {}
        stock_obj = WarehouseProductStock.objects.get(id=warehouse_stock_obj.id)
        intial_stock = stock_obj.stock
        
        # Calculate how much product can be taken from this warehouse
        product_taken = min(product_total_pieces, stock_obj.stock)
        current_stock = stock_obj.stock - product_taken
        if refrance:
            for i in refrance:
                if i["product_id"] == product_id and i['warehouse']==stock_obj.warehouse_id:
                    i["beforestock"]=stock_obj.stock
                    i["taken_stock"]=product_taken
                    i["after_stock"]=current_stock
                    i["product_id"]=product_id
        else:
            data['warehouse']=stock_obj.warehouse_id
            data["beforestock"]=stock_obj.stock
            data["taken_stock"]=product_taken
            data["after_stock"]=current_stock
            data["product_id"]=product_id
            refrance.append(data)
        
        
        # print("➡ Product taken from this warehouse:", product_taken)
        # print("➡ Current stock in this warehouse:", current_stock)
        
        # Update the stock object
        stock_obj.stock = current_stock

        # ready_for_dispatch = min(product_total_pieces, stock_obj.ready_for_dispatch)
        # ready_for_dispatch = stock_obj.ready_for_dispatch - ready_for_dispatch
        # stock_obj.ready_for_dispatch = ready_for_dispatch

        stock_history_obj=WarehouseProductStockHistory.objects.filter(product=product,warehouse=stock_obj.warehouse).last()
        # print("➡ stock_history_obj :", stock_history_obj)
        # print("➡ stock_history_obj :", stock_history_obj.id)
        stock_new_history_obj=WarehouseProductStockHistory.objects.create(product=product,warehouse=stock_obj.warehouse,remark= "New Order")
        # print("➡ stock_new_history_obj :", stock_new_history_obj)
    
    
        if not stock_history_obj:
            # print("there is no history")
            stock_new_history_obj.before_stock=0
            stock_new_history_obj.stock=current_stock
        else:
            # print('there is history')
            # print(stock_history_obj.stock)
            stock_new_history_obj.before_stock=intial_stock
            stock_new_history_obj.stock=current_stock
        stock_new_history_obj.affected_stock=product_taken
        stock_new_history_obj.save()
        stock_obj.save()
        
        # Update the remaining product_total_pieces
        product_total_pieces -= product_taken
        
        # If all products are taken, break out of the loop
        if product_total_pieces == 0:
            # print("➡ product_total_pieces :", product_total_pieces)
            break
        # print("➡ order_reference :", refrance)


def add_product_list_in_order(self, order, product_id, submit_type, refrance):
    
    product=Product.objects.get(id=product_id)
    # print("➡ product :", product)
    
    quantity = self.request.POST.get(f"product_{product_id}__quantity", 0)
    free_quantity = self.request.POST.get(f"product_{product_id}__free_quantity", 0)
    special_rate = self.request.POST.get(f"product_{product_id}__special_rate", 0)
    special_discount = self.request.POST.get(f"product_{product_id}__special_discount", 0)
    unit_price = self.request.POST.get(f"product_{product_id}__unitprice", 0)
    price_type = self.request.POST.get(f"product_{product_id}__price_type")
    discount1 = self.request.POST.get(f"product_{product_id}__discount1", 0)
    discount2 = self.request.POST.get(f"product_{product_id}__discount2", 0)
    
    new_order_product=OrderedProduct(order = order, product = product, quantity = quantity, special_discount=special_discount, special_rate=special_rate, unit_price = unit_price, price_type = price_type, free_quantity=free_quantity, unpacked_quantity=quantity, product_discount1=discount1, product_discount2=discount2)
    new_order_product.save()

    # if submit_type == "new":
    #     manage_stock(product=product,product_id=product_id,refrance=refrance,product_total_pieces=int(self.request.POST.get(f"product_{product_id}__totalpieces")))

            


def set_order_product_labels(order_product_label):
    exchange = False
    textable = False
    free = False
    if order_product_label == "exchange":
        exchange = True
    elif order_product_label == 'textable':
        textable = True
    elif order_product_label == 'free':
        free = True
    return exchange,textable,free
    

def update_product_list_in_order(self,order,product_ids,before_save,submit_type):
    # for product_id in product_ids:
        # print("➡ product_id :", product_id)
        # product=Product.objects.get(id=product_id)
        # order_reference = order.product_reference
        # print("➡ order_reference :", order.id)
        # print("➡ order_reference :", order_reference)
            
        # new_quentity = self.request.POST.get(f"product_{product_id}__quantity")
        # print("➡ new_quentity :", new_quentity)
        
        # for ordered_product in OrderedProduct.objects.filter(order=order,product_id=product_id):
        #     # print("➡ ordered_product :", ordered_product)
        #     old_quantity = ordered_product.quantity
        #     # print("➡ old_quantity :", old_quantity)
            
        #     if int(new_quentity)>int(old_quantity):
        #         # print("quantity badha diya")
        #         difference = int(new_quentity) - int(old_quantity)
        #         # print("➡ difference :", difference)
        #         ordered_product = OrderedProduct.objects.filter(order=order,product_id=product_id).last()
        #         ordered_product.quantity = new_quentity
        #         ordered_product.save()
        #         # print("➡ order_reference :", order_reference)
        #         manage_stock(product=product,product_id=product_id,refrance=order_reference,product_total_pieces=difference)
        #         order.save()
                
                
        #     elif int(new_quentity)<int(old_quantity):
        #         difference = int(old_quantity) - int(new_quentity)
        #         # print("➡ difference :", difference)
        #         for i in order_reference[::-1]:
        #             print("➡ i :", i)
        #             if i["product_id"] == product_id:
        #                 # print("-------------------------")
        #                 # print("----warehouse",i["warehouse"])
        #                 # print("----product_id",i["product_id"])
        #                 # print("----after_stock",i["after_stock"])
        #                 # print("----beforestock",i["beforestock"])
        #                 # print("----taken_stock",i["taken_stock"])
        #                 # print("-------------------------")
        #                 stock_obj = WarehouseProductStock.objects.get(product_id=i["product_id"],warehouse_id=i["warehouse"])
        #                 # stock_obj.stock = 
        #                 returned_stock = min(difference,i["beforestock"])
        #                 # print("➡ returned_stock :", returned_stock)
        #                 current_stock = stock_obj.stock + returned_stock
        #                 # print("➡ current_stock :", current_stock)
        #                 stock_obj.stock = current_stock
        #                 # print("➡ stock_obj :", stock_obj)
        #                 stock_history_obj=WarehouseProductStockHistory.objects.filter(product=product,warehouse=stock_obj.warehouse).last()
        #                 stock_new_history_obj=WarehouseProductStockHistory.objects.create(product=product,warehouse=stock_obj.warehouse,remark= "canceled stock")
        #                 stock_new_history_obj.before_stock=stock_history_obj.stock
        #                 stock_new_history_obj.stock=current_stock
        #                 stock_new_history_obj.save()
        #                 stock_obj.save()
                        
        #                 if difference <= i["after_stock"]:
        #                     order_reference.remove(i)
        #                     break
        #                 else:
        #                     i["after_stock"] =current_stock
        #                     i["beforestock"] =stock_obj.stock
        #                     i["taken_stock"] = i["taken_stock"] - returned_stock
        #                     order.save()
               
                
        #     else:
        #         pass

    for product_id in product_ids:
        ordered_product_obj = OrderedProduct.objects.filter(order = order,product_id=product_id).last()
        if not ordered_product_obj:
            ordered_product_obj = OrderedProduct(order = order, product_id=product_id)
            # ordered_product_obj.product_order_label = self.request.POST.get(f"product_{product_id}__orderlabel")
        
        ordered_product_obj.quantity = self.request.POST.get(f"product_{product_id}__quantity")
        ordered_product_obj.free_quantity = self.request.POST.get(f"product_{product_id}__free_quantity")
        ordered_product_obj.special_rate = self.request.POST.get(f"product_{product_id}__special_rate")
        ordered_product_obj.special_discount = self.request.POST.get(f"product_{product_id}__special_discount")
        ordered_product_obj.unpacked_quantity = self.request.POST.get(f"product_{product_id}__quantity")
        ordered_product_obj.unit_price = self.request.POST.get(f"product_{product_id}__unitprice")
        ordered_product_obj.price_type = self.request.POST.get(f"product_{product_id}__price_type")
        ordered_product_obj.product_discount1 = self.request.POST.get(f"product_{product_id}__discount1", 0)
        ordered_product_obj.product_discount2 = self.request.POST.get(f"product_{product_id}__discount2", 0)
        ordered_product_obj.save()

    OrderedProduct.objects.filter(order=order).exclude(product__id__in = product_ids).delete()

    # if submit_type == "draft-to-new" or order.status == Order.DRAFT:
    #     for to_deletes_product in to_delete_products:
    #         to_deletes_product.delete()

    # else:
    #     if order.status != Order.DRAFT:
    #         for to_deletes_product in to_delete_products:

    #             warehouse_product = WarehouseProductStock.objects.filter(warehouse=before_save.warehouse, product=to_deletes_product.product).first()
    #             if warehouse_product:
    #                 warehouse_product.stock += to_deletes_product.get_total_pieces
    #                 warehouse_product.save()

    #                 stock_history_obj=WarehouseProductStockHistory.objects.filter(product=to_deletes_product.product,warehouse=before_save.warehouse).last()
    #                 stock_new_history_obj=WarehouseProductStockHistory.objects.create(product=to_deletes_product.product,warehouse=before_save.warehouse)

    #                 stock_new_history_obj.before_stock=stock_history_obj.stock
    #                 stock_new_history_obj.stock=int(stock_history_obj.stock) + int(to_deletes_product.get_total_pieces)
                    
    #                 stock_new_history_obj.affected_stock=to_deletes_product.get_total_pieces
    #                 stock_new_history_obj.save()

    #             to_deletes_product.delete()


    # for product_id in product_ids:
    #     product=Product.objects.get(id=product_id)
    #     product_order_label = self.request.POST.get(f"product_{product_id}__orderlabel")
    #     # #print("➡ product_order_label :", product_order_label)

    #     exchange,textable,free_item = set_order_product_labels(product_order_label)
    #     unit_type = self.request.POST.get(f"product_{product_id}__unit_type")
    #     quantity = self.request.POST.get(f"product_{product_id}__quantity")
    #     unit_price = self.request.POST.get(f"product_{product_id}__unitprice")
    #     product_discount1 = self.request.POST.get(f"product_{product.id}__product_discount1")
    #     product_discount2 = self.request.POST.get(f"product_{product_id}__product_discount2")
    #     product_total_pieces = int(self.request.POST.get(f"product_{product_id}__totalpieces"))

    #     # #print("➡ order :", order)
    #     # #print("➡ product :", product)
    #     # #print("➡ unit_type :", unit_type)
    #     # #print("➡ quantity :", quantity)
    #     # #print("➡ exchange :", exchange)
    #     # #print("➡ textable :", textable)
    #     # #print("➡ free_item :", free_item)
    #     # #print("➡ unit_price :", unit_price)
    #     # #print("➡ product_discount :", product_discount)
        
    #     new_order_product=OrderedProduct(order = order, product = product, unit_type = unit_type, quantity = quantity,unit_price = unit_price , product_discount1 = product_discount1,product_discount2=product_discount2,unpacked_quantity=quantity)
        
    #     new_order_product.save()

    #     if order.status != Order.DRAFT:
    #         # update warehouse product stock history
    #         warehouse_product = WarehouseProductStock.objects.filter(warehouse=order.warehouse,product = product).first()
    #         current_stock = warehouse_product.stock - product_total_pieces
    #         warehouse_product.stock = current_stock
    #         warehouse_product.save()

    #         stock_history_obj=WarehouseProductStockHistory.objects.filter(product=product,warehouse=order.warehouse).last()
    #         stock_new_history_obj=WarehouseProductStockHistory.objects.create(product=product,warehouse=order.warehouse)
    #         if not stock_history_obj:
    #             stock_new_history_obj.before_stock=0
    #             stock_new_history_obj.stock=product_total_pieces
    #         else:
    #             stock_new_history_obj.before_stock=stock_history_obj.stock
    #             stock_new_history_obj.stock=int(stock_history_obj.stock)- int(product_total_pieces)
    #         stock_new_history_obj.affected_stock=product_total_pieces
    #         stock_new_history_obj.save()


def add_stock_when_order_cancel(order_id):
    order = Order.objects.get(id=order_id)
    to_delete_products = OrderedProduct.objects.filter(order=order)
    for to_deletes_product in to_delete_products:

        warehouse_product = WarehouseProductStock.objects.filter(warehouse=order.warehouse, product=to_deletes_product.product).first()
        if warehouse_product:
            warehouse_product.stock += to_deletes_product.get_total_pieces
            warehouse_product.save()

            stock_history_obj=WarehouseProductStockHistory.objects.filter(product=to_deletes_product.product,warehouse=order.warehouse).last()
            stock_new_history_obj=WarehouseProductStockHistory.objects.create(product=to_deletes_product.product,warehouse=order.warehouse)

            stock_new_history_obj.before_stock=stock_history_obj.stock
            stock_new_history_obj.stock=int(stock_history_obj.stock) + int(to_deletes_product.get_total_pieces)
            
            stock_new_history_obj.affected_stock=to_deletes_product.get_total_pieces
            stock_new_history_obj.save()


def add_product_list_in_replacement(self, replacement, product_id):
    order_product = OrderedProduct.objects.filter(id = product_id).last()
    
    replace_quantity = int(self.request.POST.get(f"product_{product_id}_replace_quantity"))
    
    if replace_quantity > 0:
        replace_product = ReplacementProduct(replacement_order=replacement, order_product=order_product, replace_quantity=replace_quantity)
        replace_product.save()


def update_product_list_in_replacement(self, replacement, product_list):

    for order_product_id in product_list:
        replace_quantity = int(self.request.POST.get(f"product_{order_product_id}_replace_quantity"))

        replace_product_obj = ReplacementProduct.objects.filter(replacement_order=replacement, order_product__id=order_product_id).last()

        if replace_product_obj:
            if replace_quantity > 0:
                replace_product_obj.replace_quantity = replace_quantity
                replace_product_obj.save()
            else:
                replace_product_obj.delete()
        else:
            if replace_quantity > 0:
                replace_product_obj = ReplacementProduct(replacement_order=replacement, order_product_id=order_product_id)
                replace_product_obj.replace_quantity = replace_quantity
                replace_product_obj.save()
    
    replace_products = ReplacementProduct.objects.filter(replacement_order = replacement).exclude(order_product__id__in = product_list)
    if replace_products.exists():
        replace_products.delete()


def add_customer_discounts(form, instance):
    brand_list = list(Brand.objects.filter(company = instance.company).values_list("id", flat=True))

    for brand in brand_list:
        primary_discount = form.data.get(f"discount-{brand}-primary_discount")
        primary_percent = float(form.data.get(f"percent-{brand}-primary_discount", 0))

        secondary_discount = form.data.get(f"discount-{brand}-secondary_discount")
        secondary_percent = float(form.data.get(f"percent-{brand}-secondary_discount", 0))

        if primary_discount == "0" or secondary_discount == "0":
            if primary_discount == "0" and secondary_discount == "0":
                customer_discount = MultipleVendorDiscount(customer = instance, brand_id = brand, is_primary_brand_discount = True, is_secondary_brand_discount = True)
            elif primary_discount == "0":
                customer_discount = MultipleVendorDiscount(customer = instance, brand_id = brand, is_primary_brand_discount = True)
            else:
                customer_discount = MultipleVendorDiscount(customer = instance, brand_id = brand, is_secondary_brand_discount = True)
        else:
            customer_discount = MultipleVendorDiscount(customer = instance, brand_id = brand, primary_discount_id = primary_discount, additional_discount_id = secondary_discount)
        customer_discount.primary_percent = primary_percent
        customer_discount.additional_percent = secondary_percent
        customer_discount.save()
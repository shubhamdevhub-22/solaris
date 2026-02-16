import contextlib
from django.db.models.signals import  post_save
from django.dispatch import receiver
from app_modules.order.models import OrderedProduct, Order
from app_modules.reports.models import SalesRepCommissionCodeReport
from django.http import JsonResponse


@receiver(post_save, sender=OrderedProduct)
def save_sales_rep_commision_model(sender, created, instance, **kwargs):
    
    try:   
            order_product = instance

            # if order_product.product.commission_code > 0 or order_product.product.is_apply_ml_quantity:
            #     total_sales_rep_commision = 0
            #     total_sold_piece=0
            #     if not order_product.exchange and not order_product.free_item:
            #         # print("➡ order_product.unit_type :", order_product.unit_type)
            #         if order_product.unit_type.lower() == "piece":
            #             # print("➡ order_product.unit_type after:", order_product.unit_type)
            #             # print("➡ order_product.product_commission_code after:", order_product.product.commission_code)
        
            #             total_sales_rep_commision = float(order_product.quantity) * float(order_product.product.commission_code)

            #             total_sold_piece = float(order_product.quantity)
            #         elif order_product.unit_type.lower() == "box":
            #             # print("➡ order_product.unit_type after:", order_product.unit_type)
            #             # print("➡ order_product.product_commission_code after:", order_product.product.commission_code)


            #             total_sales_rep_commision = (float(order_product.quantity) *float(order_product.product.box_piece)) * float(order_product.product.commission_code) 
            #             total_sold_piece=float(order_product.quantity) *float(order_product.product.box_piece)
            #         elif order_product.unit_type.lower() == "case":
            #             # print("➡ order_product.unit_type after:", order_product.unit_type)
            #             # print("➡ order_product.product_commission_code after:", order_product.product.commission_code)


            #             total_sales_rep_commision = (float(order_product.quantity) *float(order_product.product.case_piece)) * float(order_product.product.commission_code)
            #             total_sold_piece=float(order_product.quantity) *float(order_product.product.case_piece)
            # # product_lable logic
            
            #     if order_product.exchange:
            #         product_label = SalesRepCommissionCodeReport.EXCHANGE
            #     elif order_product.textable:
            #         product_label = SalesRepCommissionCodeReport.TEXTABLE
            #     elif order_product.free_item:
            #         product_label = SalesRepCommissionCodeReport.FREE_ITEM
            #     else:
            #         product_label=""

            #     # product_ml_tax logic
            #     report_ml_tax = 0
            #     is_apply_ml = False
            #     product_total_ml_quantity=0
            #     if order_product.product.is_apply_ml_quantity and not order_product.exchange and not order_product.free_item:
            #         # print("slkdjaklsdjadjadaskdjjasdjlkasjdklajdlkasjdlkjlkjdljdlkajajskldjklasjdklsjdkldkl")

            #         is_apply_ml=True
            #         if order_product.unit_type.lower() == "piece":
            #             # print("➡ order_product.unit_type :", order_product.unit_type)

            #             report_ml_tax = float(order_product.product.ml_quantity) * float(order_product.quantity) * 0.10
            #             # print("➡ report_ml_tax :", report_ml_tax)

            #             product_total_ml_quantity=float(order_product.product.ml_quantity) * float(order_product.quantity)
            #             # print("➡ product_total_ml_quantity :", product_total_ml_quantity)
                    
            #         elif order_product.unit_type.lower() == "box":
            #             # print("➡ order_product.unit_type :", order_product.unit_type)

            #             # print("➡ order_product.unit_type after:", order_product.unit_type)
            #             # print("➡ order_product.product_commission_code after:", order_product.product.commission_code)
            #             report_ml_tax = (float(order_product.quantity) *float(order_product.product.box_piece)) * float(order_product.quantity) * 0.10
            #             product_total_ml_quantity=float(order_product.product.ml_quantity) * (float(order_product.quantity) * float(order_product.product.box_piece))


            #         elif order_product.unit_type.lower() == "case":
            #             # print("➡ order_product.unit_type :", order_product.unit_type)

            #             # print("➡ order_product.unit_type after:", order_product.unit_type)
            #             # print("➡ order_product.product_commission_code after:", order_product.product.commission_code)
            #             report_ml_tax = (float(order_product.quantity) *float(order_product.product.case_piece)) * float(order_product.quantity) * 0.10
            #             product_total_ml_quantity=float(order_product.product.ml_quantity) * (float(order_product.quantity) * float(order_product.product.case_piece))



 
            #     SalesRepCommissionCodeReport.objects.get_or_create(order_product = order_product,
            #                                                                         product = order_product.product,
            #                                                                         customer = order_product.order.customer,
            #                                                                         created_by = order_product.order.created_by,
            #                                                                         # product_commission_code = order_product.product.commission_code,

            #                                                                         total_sales_rep_commision=total_sales_rep_commision,

            #                                                                         unit_sold = order_product.quantity,
            #                                                                         unit_type = order_product.unit_type,
                                                                                    
            #                                                                         product_label = product_label,

            #                                                                         product_ml_quantity = order_product.product.ml_quantity,

            #                                                                         ml_tax = report_ml_tax,

            #                                                                         is_apply_ml=is_apply_ml,

            #                                                                         total_sold_piece=total_sold_piece,

            #                                                                         product_total_ml_quantity=product_total_ml_quantity,

            #                                                                         product_cost_price = order_product.product.cost_price,
            #                                                                         product_wholesale_min_price = order_product.product.wholesale_min_price,
            #                                                                         product_wholesale_base_price = order_product.product.wholesale_base_price,
            #                                                                         product_retail_min_price = order_product.product.retail_min_price,
            #                                                                         product_retail_base_price = order_product.product.retail_base_price,
            #                                                                         product_sold_price = order_product.unit_price,
            #                                                                         )
            #     # commision_code_report.save()

    except Exception as e:
        print("********************",e)
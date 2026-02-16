from django import template
import phonenumbers

register = template.Library()


@register.simple_tag
def product_item_total (quantity,total_piece,unit_price):
    item_total = float(quantity) * float(total_piece) * float(unit_price)
    return "{:.2f}".format(round(item_total, 2))

@register.simple_tag
def product_net_price(quantity,total_piece,unit_price,discount=0,additional_discount=0):
    item_total = float(quantity) * float(total_piece) * float(unit_price)
    discount_total = item_total - ((item_total*float(discount))/100)
    
    additional_discount_total = discount_total - ((discount_total*float(additional_discount))/100)
    return "{:.2f}".format(round(additional_discount_total, 2))

@register.simple_tag
def calc_total_pieces(quantity,unit_type_pieces):
    return int(quantity)*int(unit_type_pieces)

@register.simple_tag
def calc_total_ml_quantity(ml_qunatity,quantity_ml_qunatity):
    return int(quantity_ml_qunatity)*int(ml_qunatity)


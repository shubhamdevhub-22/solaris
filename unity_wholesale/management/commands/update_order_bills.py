from django.core.management import BaseCommand
from app_modules.order.models import OrderBill, Order, OrderedProduct
from num2words import num2words
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from io import BytesIO
from xhtml2pdf import pisa


class Command(BaseCommand):
    help = "Update generate bill order."

    def handle(self, *args, **options):
        self.update_orders()
    
    def render_to_pdf(self, template_src, context_dict):
        html_string = render_to_string(template_src, context_dict)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html_string.encode("UTF-8")), result)
        if not pdf.err:
            return result.getvalue()
        return None

    def update_orders(self):
        order_bills = OrderBill.objects.all()
        for order_bill in order_bills:
            if not order_bill.bill_id:
                order_bill.bill_id = "{}{:05d}".format("BILL#", order_bill.id)
            if not order_bill.bill_date:
                order_bill.bill_date = order_bill.created_at.date()
            order_bill.save()
                
            order = Order.objects.filter(id = order_bill.order.id).last()
            context = {}
            context["order_products"] = OrderedProduct.objects.filter(order=order)
            context["order"] = order
            context["amount_in_words"] = num2words(order.grand_total, lang='en_IN').title()
            context["order_bill"] = order_bill

            pdf = self.render_to_pdf('order/bills/print_order_bill.html', context)
            pdf_name = "order-%s.pdf" % str(order.order_id)

            if pdf:
                if order_bill.bill_pdf:
                    order_bill.bill_pdf.delete()
                order_bill.bill_pdf.save(pdf_name, ContentFile(pdf))
                order_bill.save()
    
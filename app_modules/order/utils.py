from django.conf import settings
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from app_modules.order.models import Order, OrderedProduct

from django.http import HttpResponse
from django.template.loader import get_template
from django.template.loader import render_to_string
from datetime import datetime

from xhtml2pdf import pisa
import googlemaps
import os

def generate_order_pdf(context):

    customer_name = context["customer_name"]
    customer_area = context["customer_area"]
    transport_name = context["transport"]
    date = datetime.today().strftime("%d-%m-%Y")
    # grand_total = context["grand_total"]

    order_products = OrderedProduct.objects.filter(order__id = context["order_id"])
    order = Order.objects.filter(id = context["order_id"]).last()

    items = [["Item", "Vehicle", "Qty"]]
    
    for order_product in order_products:

        quantity = "<table width='100%'><tr>"
        if order_product.product.unit:
            quantity += f"<td style='text-align:left;'> {order_product.product.unit}</td>"
        else:
            quantity += "<td></td>"

        quantity += "<td style='width:20%;'></td>"

        quantity += f"<td style='text-align:right;'>&nbsp;{order_product.quantity}</td></tr></table>"

        if order_product.free_quantity > 0:
            quantity += f" + {str(order_product.free_quantity)}"

        if order_product.special_rate > 0:
            quantity += f"<br/> (Rs. {str(order_product.special_rate)})"
        elif order_product.special_discount > 0:
            quantity += f"<br/> ({str(order_product.special_discount)} %)"
        
        if order_product.product.vehicle:
            vehicle_name = order_product.product.vehicle.name
        else:
            vehicle_name = "-"
        
        product_name = order_product.product.name

        if order_product.product.brand and order_product.product.brand.name.lower() not in ["solaris", "sap", "belrise"]:
            product_name += "<br/>"+order_product.product.brand.name+" &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; "+order_product.product.code

        product_column = [product_name, vehicle_name, quantity]
        items.append(product_column)

    for i in range(10):
        items.append([".","",""])
    
    # items.append(["", "Grand Total: ", str(grand_total)])

    # PDF dimensions
    pdf_width = 10 * cm  # 10 cm width
    # pdf_height = 20 * cm

    content_height = 0
    content_height += 2 * cm  # Height for date, customer name, city, transport name
    content_height += 0.2 * cm  # Additional space for separator
    content_height += len(items) * cm  # Height for each row in the table
    # content_height += 5 * cm  # Additional padding at the bottom

    if order.internal_remarks:
        content_height += 0.2 * cm  # Additional space for internal_remarks

    A4 = (210*mm, 297*mm)

    # Create a buffer for the PDF content
    buffer = BytesIO()

    # Create PDF
    doc = SimpleDocTemplate(buffer, pagesize=(pdf_width, content_height), topMargin=10, leftMargin=2*cm, rightMargin=2*cm)

    styles = getSampleStyleSheet()
    heading_style = styles['Heading6']

    FONT_SIZE = 8
    LEADING = 10

    directory_path = settings.APPS_DIR
    bold = os.path.join(directory_path, 'static', 'font-agane', 'Agane-65-Bold.ttf')
    extra_bold = os.path.join(directory_path, 'static', 'font-agane', 'Agane-75-Extra-Bold.ttf')
    pdfmetrics.registerFont(TTFont('FontAgane-Bold', bold))
    pdfmetrics.registerFont(TTFont('FontAgane-Extra-Bold', extra_bold))

    pdfmetrics.registerFontFamily(
        'FontAgane',
        normal='FontAgane-Bold',
        bold='FontAgane-Extra-Bold',
    )

    # Styles
    paragraph_style = ParagraphStyle(name='Normal', fontName='FontAgane-Extra-Bold', fontSize=9, alignment=1)
    right_aligned_style = ParagraphStyle(name='RightAlign', fontName='FontAgane-Bold', parent=heading_style, alignment=2, rightIndent=-60)
    product_style = ParagraphStyle(name='Normal', fontName='FontAgane-Bold', fontSize=FONT_SIZE, alignment=0, leading=LEADING, leftIndent=0)
    product_last_column_style = ParagraphStyle(name='Normal', fontName='FontAgane-Bold', fontSize=FONT_SIZE, alignment=0, leftIndent=5, leading=LEADING)
    
    # Content elements
    elements = []

    # Date, Customer Name, Customer area, Transport Name
    elements.append(Paragraph(date, right_aligned_style))
    elements.append(Paragraph(f"{customer_name}\n-\n{customer_area}", paragraph_style))
    elements.append(Paragraph(transport_name, paragraph_style))

    elements.append(Spacer(1, 0.5 * cm))

    # Table data
    table_data = []
    for i, row in enumerate(items):
        if i == 0:
            table_data.append([Paragraph(cell, ParagraphStyle(name='Header', parent=product_style, fontName='FontAgane-Bold', alignment=1, fontSize=8, rightIndent=10)) for cell in row])
        elif i == 1:
            table_row_data = []
            for j, cell in enumerate(row):
                if j == 2:
                    table_row_data.append(Paragraph(cell, ParagraphStyle(name='Normal', fontSize=FONT_SIZE, alignment=0, fontName='FontAgane-Bold', leading=LEADING, leftIndent=5)))
                else:
                    table_row_data.append(Paragraph(cell, ParagraphStyle(name='Normal', fontSize=FONT_SIZE, alignment=0, fontName='FontAgane-Bold', leading=LEADING, leftIndent=0)))

            table_data.append(table_row_data)
        else:
            table_row_data = []
            for j, cell in enumerate(row):
                if j == 2:
                    table_row_data.append(Paragraph(cell, product_last_column_style))
                else:
                    table_row_data.append(Paragraph(cell, product_style))

            table_data.append(table_row_data)

    # Table style
    # table_style = TableStyle([
    #     ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    #     ('BACKGROUND', (0, 0), (-1, 0), (0.9, 0.9, 0.9)),  # Gray background for header row
    #     ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold font for header row
    #     # ('LINEABOVE', (0, -1), (-1, -1), 1, (0, 0, 0)),  # Add top border to the last row
    # ])

    table_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # Left align all cells
        ('BACKGROUND', (0, 0), (-1, 0), (0.9, 0.9, 0.9)),  # Gray background for header row
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold font for header row
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Center align header row (optional)
        # ('LINEABOVE', (0, -1), (-1, -1), 1, (0, 0, 0)),  # Add top border to the last row
        ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Left padding for all cells
    ])

    # Create Table object
    table = Table(table_data, colWidths=[6.0 * cm, 1.8 * cm, 2 * cm], vAlign="TOP")
    table.setStyle(table_style)

    # Add table to elements list
    elements.append(table)

    if order.internal_remarks:
        elements.append(Spacer(1, 1 * cm))
        footer_style = ParagraphStyle(name='Normal', fontSize=9, alignment=1, fontName='Helvetica', leftIndent=0)
        elements.append(Paragraph("<b>"+order.internal_remarks+"</b>", footer_style))

    # Build PDF
    doc.build(elements)

    response = HttpResponse(content_type='application/pdf')
    pdf_name = "order-%s.pdf" % str(order.order_id)
    response['Content-Disposition'] = 'inline; filename=%s' % pdf_name

    # Get the PDF content from the buffer
    response.write(buffer.getvalue())
    buffer.close()

    return response


def generate_order_bill(template, context):
    template = get_template(template)
    html  = template.render(context)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if pdf.err:
        return HttpResponse("Invalid PDF", status_code=400, content_type='text/plain')
    # file = pdf.getFile()

    return HttpResponse(result.getvalue(), content_type='application/pdf')


def render_to_pdf(template_src, context_dict):
    html_string = render_to_string(template_src, context_dict)
    # save to html file
    html_file = open("test.html", "w")
    html_file.write(html_string)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_string.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None

# def get_best_route(waypoints, origin):
#     print('origin: ', origin)
#     print('waypoints: ', waypoints)
    
#     try:
#         # Create the Google Maps client
#         gmaps = googlemaps.Client(key=settings.GOOGLE_MAP_API_KEY)
#         print('gmaps client created: ', gmaps)
        
#         # Fetch the directions
#         result = gmaps.directions(
#             origin,
#             origin,
#             waypoints=waypoints,
#             mode="driving",
#             optimize_waypoints=True
#         )
#         # print('result: ', result)
        
#         if not result:
#             raise ValueError("No route found")
        
#         # Extract information from the result, such as the best route and duration
#         best_route = result[0]["legs"][0]["steps"]
#         total_duration = result[0]["legs"][0]["duration"]["text"]
        
#         return {
#             "best_route": best_route,
#             "total_duration": total_duration
#         }
#     except Exception as e:
#         print(f"Error fetching best route: {e}")
#         raise


def get_best_route(waypoints, origin):
    print('waypoints: ', waypoints)
    '''map api for find best route'''
    gmaps = googlemaps.Client(key=settings.GOOGLE_MAP_API_KEY)
    result = gmaps.directions(
        origin,
        origin,
        waypoints=waypoints,
        mode="driving",
        optimize_waypoints=True
    )
    # Extract information from the result, such as the best route and duration
    best_route = result[0]["legs"][0]["steps"]
    total_duration = result[0]["legs"][0]["duration"]["text"]
    # print("Best Route:", best_route)
    # for step in best_route:
    #     print(step["html_instructions"])
    # print(f"Total Duration: {total_duration}")
    return result

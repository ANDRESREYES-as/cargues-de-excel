import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.platypus.frames import Frame
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from .size_utils import sort_sizes

def generate_pdf(production_sheet, context):
    # Crear un buffer para el PDF
    buffer = io.BytesIO()
    
    # Configurar el documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=80,  # Aumentar el margen superior para el encabezado
        bottomMargin=30
    )
    
    def header_footer(canvas, doc):
        canvas.saveState()
        width, height = landscape(letter)
        
        # Título principal y manifiesto
        canvas.setFont('Helvetica-Bold', 20)
        title = f'Planilla de Producción - {production_sheet.manifest_number}'
        title_width = canvas.stringWidth(title, 'Helvetica-Bold', 20)
        canvas.drawString((width - title_width) / 2, height - 40, title)
        
        # Información secundaria
        canvas.setFont('Helvetica', 12)
        info = f'Fecha: {production_sheet.packing_date.strftime("%d/%m/%Y")} - Origen: {production_sheet.get_origin_display()}'
        info_width = canvas.stringWidth(info, 'Helvetica', 12)
        canvas.drawString((width - info_width) / 2, height - 55, info)
        
        # Línea separadora
        canvas.line(30, height - 65, width - 30, height - 65)
        
        canvas.restoreState()
    
    # Contenedor para los elementos del PDF
    elements = []
    
    # Preparar datos para la tabla
    headers = ['OP', 'REF'] + [str(size) for size in context['sizes']] + ['TOTAL']
    table_data = [headers]
    
    for row in context['table_data']:
        row_data = [row['op'], row['ref']]
        for size in context['sizes']:
            row_data.append(str(row.get(size, '-')))
        row_data.append(str(row['total']))
        table_data.append(row_data)
    
    # Agregar fila de totales
    totals_row = ['TOTAL GENERAL', '']
    for size in context['sizes']:
        totals_row.append(str(context['size_totals'].get(size, 0)))
    totals_row.append(str(context['grand_total']))
    table_data.append(totals_row)
    
    # Crear tabla
    table = Table(table_data)
    
    # Estilo de la tabla
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.grey),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    table.setStyle(style)
    
    elements.append(table)
    
    # Generar PDF con encabezado en cada página
    doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
    
    # Obtener el valor del buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Crear la respuesta HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="planilla_produccion_{production_sheet.manifest_number}.pdf"'
    response.write(pdf)
    
    return response
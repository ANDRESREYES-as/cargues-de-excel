from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
import openpyxl
from .models import ResultadoCalculo
from datetime import datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import inch

def historico_calculos(request):
    """
    Vista para mostrar el histórico de cálculos y permitir su exportación a Excel o PDF
    """
    context = {
        'referencia': request.GET.get('referencia', '').strip(),
        'fecha_inicio': request.GET.get('fecha_inicio'),
        'fecha_fin': request.GET.get('fecha_fin'),
    }
    
    try:
        # Iniciar queryset
        resultados = ResultadoCalculo.objects.all().order_by('-fecha_calculo')
        
        # Aplicar filtros
        if context['referencia']:
            resultados = resultados.filter(referencia__icontains=context['referencia'])
        
        # Validar y convertir fechas
        if context['fecha_inicio']:
            try:
                datetime.strptime(context['fecha_inicio'], '%Y-%m-%d')
                resultados = resultados.filter(fecha_calculo__date__gte=context['fecha_inicio'])
            except ValueError:
                messages.error(request, 'Formato de fecha inicial inválido. Use YYYY-MM-DD')
        
        if context['fecha_fin']:
            try:
                datetime.strptime(context['fecha_fin'], '%Y-%m-%d')
                resultados = resultados.filter(fecha_calculo__date__lte=context['fecha_fin'])
            except ValueError:
                messages.error(request, 'Formato de fecha final inválido. Use YYYY-MM-DD')
        
        # Si se solicita exportar a PDF
        if request.GET.get('export') == 'pdf':
            buffer = BytesIO()
            
            try:
                doc = SimpleDocTemplate(buffer, pagesize=letter)
                elements = []
                
                # Preparar datos para la tabla
                data = [['Referencia', 'Talla', 'Ventas Pendientes', 'Inventario',
                         'Producción', 'Total Disponible', 'Balance', 'Fecha Cálculo']]
                
                for resultado in resultados:
                    data.append([
                        str(resultado.referencia),
                        str(resultado.talla),
                        str(resultado.ventas),
                        str(resultado.inventario),
                        str(resultado.produccion),
                        str(resultado.total_disponible),
                        str(resultado.balance),
                        resultado.fecha_calculo.strftime('%Y-%m-%d %H:%M')
                    ])
                
                # Crear tabla
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                elements.append(table)
                doc.build(elements)
                
                buffer.seek(0)
                response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename=resultados_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
                return response
                
            finally:
                buffer.close()
        
        # Si se solicita exportar a Excel
        if request.GET.get('export') == 'excel':
            excel_file = BytesIO()
            
            try:
                # Crear libro de Excel
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "Resultados"
                
                # Encabezados
                headers = [
                    'Referencia', 'Talla', 'Ventas Pendientes', 'Inventario',
                    'Producción', 'Total Disponible', 'Balance', 'Fecha Cálculo'
                ]
                ws.append(headers)
                
                # Datos
                for resultado in resultados:
                    try:
                        ws.append([
                            str(resultado.referencia),
                            str(resultado.talla),
                            float(resultado.ventas),
                            float(resultado.inventario),
                            float(resultado.produccion),
                            float(resultado.total_disponible),
                            float(resultado.balance),
                            resultado.fecha_calculo.strftime('%Y-%m-%d %H:%M')
                        ])
                    except (ValueError, AttributeError) as e:
                        print(f"Error al procesar resultado {resultado.id}: {str(e)}")
                        continue
                
                # Ajustar anchos de columna
                for idx, col in enumerate(ws.columns, 1):
                    max_length = 0
                    column = openpyxl.utils.get_column_letter(idx)
                    for cell in col:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = (max_length + 2)
                    ws.column_dimensions[column].width = adjusted_width
                
                # Guardar en el buffer
                wb.save(excel_file)
                excel_file.seek(0)
                
                # Preparar respuesta
                response = HttpResponse(
                    excel_file.getvalue(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename=resultados_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
                
                return response
            
            finally:
                if 'wb' in locals() and wb:
                    wb.close()
                excel_file.close()
        
        # Paginación para vista normal
        paginator = Paginator(resultados, 50)
        page = request.GET.get('page')
        context['resultados'] = paginator.get_page(page)
        
        return render(request, 'excel_calculator/historico.html', context)
    
    except Exception as e:
        print(f"Error general: {str(e)}")
        messages.error(request, f'Error en el procesamiento: {str(e)}')
        return render(request, 'excel_calculator/historico.html', context)
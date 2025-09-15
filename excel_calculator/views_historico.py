from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator
import openpyxl
from .models import ResultadoCalculo
from datetime import datetime

def historico_calculos(request):
    """
    Vista para mostrar el histórico de cálculos y permitir su exportación a Excel
    """
    # Obtener parámetros de filtrado
    referencia = request.GET.get('referencia', '').strip()
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Iniciar queryset
    resultados = ResultadoCalculo.objects.all().order_by('-fecha_calculo')
    
    # Aplicar filtros
    if referencia:
        resultados = resultados.filter(referencia__icontains=referencia)
    if fecha_inicio:
        resultados = resultados.filter(fecha_calculo__date__gte=fecha_inicio)
    if fecha_fin:
        resultados = resultados.filter(fecha_calculo__date__lte=fecha_fin)
    
    # Paginación
    paginator = Paginator(resultados, 50)  # 50 resultados por página
    page = request.GET.get('page')
    resultados_page = paginator.get_page(page)
    
    # Si se solicita exportar a Excel
    if request.GET.get('export') == 'excel':
        # Crear un nuevo libro de Excel
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
            ws.append([
                resultado.referencia,
                resultado.talla,
                resultado.ventas,
                resultado.inventario,
                resultado.produccion,
                resultado.total_disponible,
                resultado.balance,
                resultado.fecha_calculo.strftime('%Y-%m-%d %H:%M')
            ])
        
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
        
        # Crear la respuesta HTTP con el archivo Excel
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=resultados_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        
        wb.save(response)
        return response
    
    return render(request, 'excel_calculator/historico.html', {
        'resultados': resultados_page,
        'referencia': referencia,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    })
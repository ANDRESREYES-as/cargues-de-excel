from django.views.decorators.http import require_GET
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.db.models import Q
import datetime
from .models import RegistroExcel
import traceback
import xlsxwriter
from io import BytesIO

def form_exportar_manifiestos(request):
    """
    Muestra el formulario para exportar manifiestos a Excel.
    """
    context = {
        'error_message': request.GET.get('error')
    }
    return render(request, 'excel_processor/exportar_manifiestos.html', context)

def build_filename(manifest_start, manifest_end=None):
    """
    Construye el nombre del archivo basado en el manifiesto o rango de manifiestos.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if manifest_end:
        return f'manifiesto_{manifest_start}_a_{manifest_end}_{timestamp}.xlsx'
    return f'manifiesto_{manifest_start}_{timestamp}.xlsx'

def write_manifest_data(worksheet, manifest_records, formats):
    """
    Escribe los datos de un manifiesto en el worksheet.
    """
    # Escribir encabezados
    headers = [
        'Manifiesto', 'Archivo', 'Orden', 'Producción', 
        'Cant. Original', 'Saldo Entregar', 'Cant. Producida', 
        'Fecha Registro'
    ]
    
    # Configurar ancho de columnas
    column_widths = [12, 30, 15, 15, 15, 15, 15, 20]
    for i, width in enumerate(column_widths):
        worksheet.set_column(i, i, width)
    
    # Escribir encabezados
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, formats['header'])
    
    # Establecer altura de la fila de encabezados
    worksheet.set_row(0, 30)
    
    # Escribir datos
    for row_idx, record in enumerate(manifest_records, start=1):
        row_data = [
            record.proceso.consecutivo if record.proceso else '',
            str(record.proceso.archivo) if record.proceso else '',
            record.orden or '',
            record.produccion or '',
            record.cant_orig or '',
            record.saldo_entregar or '',
            record.cant_produc or '',
            record.fecha_registro.strftime('%Y-%m-%d %H:%M') if record.fecha_registro else ''
        ]
        
        for col, value in enumerate(row_data):
            if col == 7:  # Fecha
                if value:
                    worksheet.write(row_idx, col, value, formats['date'])
                else:
                    worksheet.write(row_idx, col, '')
            else:
                worksheet.write(row_idx, col, value)

def format_excel_date(date_str):
    """
    Convierte una fecha en string a objeto datetime.
    """
    try:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        return None

def build_filename(params):
    """
    Construye el nombre del archivo basado en los parámetros de filtro.
    """
    parts = ['informe_historico']
    
    if params.get('manifest'):
        parts.append(f"Manifiesto_{params['manifest']}")
    if params.get('op'):
        parts.append(f"OP_{params['op']}")
    if params.get('date_from'):
        date = format_excel_date(params['date_from'])
        if date:
            parts.append(f"desde_{date.strftime('%Y%m%d')}")
    if params.get('date_to'):
        date = format_excel_date(params['date_to'])
        if date:
            parts.append(f"hasta_{date.strftime('%Y%m%d')}")
    if params.get('origin'):
        parts.append(f"origen_{params['origin']}")
    
    parts.append(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    return '_'.join(parts) + '.xlsx'

@require_GET
def exportar_excel_historico(request):
    """
    Exporta un Excel con datos de un manifiesto específico o un rango de manifiestos.
    
    Parámetros GET:
    - manifest_start: Número de manifiesto inicial (requerido)
    - manifest_end: Número de manifiesto final (opcional)
    """
    try:
        # Validar manifiesto inicial
        manifest_start = request.GET.get('manifest_start')
        if not manifest_start:
            return JsonResponse({
                'error': 'El parámetro manifest_start es requerido'
            }, status=400)
            
        try:
            manifest_start = int(manifest_start)
        except ValueError:
            return JsonResponse({
                'error': 'El número de manifiesto debe ser un número entero'
            }, status=400)
            
        # Validar manifiesto final si existe
        manifest_end = request.GET.get('manifest_end')
        if manifest_end:
            try:
                manifest_end = int(manifest_end)
                if manifest_end < manifest_start:
                    return JsonResponse({
                        'error': 'El manifiesto final debe ser mayor que el inicial'
                    }, status=400)
            except ValueError:
                return JsonResponse({
                    'error': 'El número de manifiesto final debe ser un número entero'
                }, status=400)
        
        # Construir query
        query = Q(proceso__consecutivo=manifest_start)
        if manifest_end:
            query = Q(proceso__consecutivo__gte=manifest_start) & \
                   Q(proceso__consecutivo__lte=manifest_end)
        
        # Obtener registros ordenados por consecutivo y fecha
        records = RegistroExcel.objects.select_related('proceso')\
            .filter(query)\
            .order_by('proceso__consecutivo', '-fecha_registro')
            
        if not records.exists():
            return JsonResponse({
                'error': 'No se encontraron registros para el/los manifiesto(s) especificado(s)'
            }, status=404)

        # Crear archivo Excel en memoria
        with BytesIO() as output:
            workbook = xlsxwriter.Workbook(output, {'in_memory': True, 'constant_memory': True})
            worksheet = workbook.add_worksheet('Manifiestos')
            
            # Crear formatos
            formats = {
                'header': workbook.add_format({
                    'bold': True,
                    'font_color': 'white',
                    'bg_color': '#366092',
                    'align': 'center',
                    'valign': 'vcenter',
                    'text_wrap': True,
                    'border': 1
                }),
                'date': workbook.add_format({
                    'num_format': 'yyyy-mm-dd hh:mm',
                    'align': 'center'
                })
            }
            
            # Escribir datos
            write_manifest_data(worksheet, records, formats)
            
            # Cerrar workbook y obtener contenido
            workbook.close()
            excel_content = output.getvalue()
            
        # Crear respuesta HTTP
        response = HttpResponse(
            excel_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Establecer nombre del archivo
        filename = build_filename(manifest_start, manifest_end)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        print(f"Error al exportar Excel: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'error': 'Error al generar el archivo Excel. Por favor contacte al administrador.'
        }, status=500)
        
        # Establecer el nombre del archivo
        filename = build_filename(request.GET)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response

    except Exception as e:
        print(f"Error al exportar Excel: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'error': 'Error al generar el archivo Excel. Por favor contacte al administrador.'
        }, status=500)
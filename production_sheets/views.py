import pandas as pd
import io
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count, Sum, Q, Min, Max
from django.utils import timezone
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from .models import ProductionSheet, ProductionDetail
from .forms import ProductionSheetForm
from .pdf_generator import generate_pdf
from .excel_export import export_to_excel
from .size_utils import sort_sizes

def process_production_sheet(request):
    if request.method == 'POST':
        form = ProductionSheetForm(request.POST, request.FILES)
        if form.is_valid():
            production_sheet = form.save(commit=False)
            
            # Leer el archivo Excel
            try:
                df = pd.read_excel(request.FILES['excel_file'])
                
                # Verificar las columnas requeridas
                required_columns = ['Consecutivo', 'Referencia', 'OP', 'Fecha Empaque', 'Manifiesto']
                if not all(col in df.columns for col in required_columns):
                    messages.error(request, 'El archivo Excel no tiene el formato correcto. Debe incluir las columnas: ' + ', '.join(required_columns))
                    return render(request, 'production_sheets/upload.html', {'form': form})
                
                # Obtener el número de manifiesto
                manifest_number = str(df['Manifiesto'].iloc[0])
                
                # Verificar si el manifiesto ya existe y está procesado
                existing_sheet = ProductionSheet.objects.filter(manifest_number=manifest_number).first()
                if existing_sheet:
                    if existing_sheet.processed:
                        messages.error(request, f'El manifiesto {manifest_number} ya ha sido procesado anteriormente.')
                        return render(request, 'production_sheets/upload.html', {'form': form})
                    else:
                        # Si existe pero no está procesado, lo eliminamos para procesarlo de nuevo
                        existing_sheet.delete()
                
                # Asignar el número de manifiesto
                production_sheet.manifest_number = manifest_number
                production_sheet.packing_date = pd.to_datetime(df['Fecha Empaque'].iloc[0]).date()
                production_sheet.save()
                
                # Procesar cada fila
                for _, row in df.iterrows():
                    referencia = str(row['Referencia'])
                    # Extraer la talla (últimos 3 dígitos) y la referencia
                    size = referencia[-3:]
                    ref = referencia[:-3]
                    op = str(row['OP'])
                    
                    # Obtener cantidad producida (si existe)
                    quantity = int(row.get('Cant. Produc', 1))
                    
                    # Actualizar o crear el detalle de producción
                    detail, created = ProductionDetail.objects.get_or_create(
                        production_sheet=production_sheet,
                        op=op,
                        ref=ref,
                        size=size,
                        defaults={'quantity': quantity}
                    )
                    if not created:
                        detail.quantity += quantity
                        detail.save()
                
                # Intentar marcar como procesada
                success, message = production_sheet.mark_as_processed()
                if success:
                    messages.success(request, f'Planilla de producción para el manifiesto {production_sheet.manifest_number} procesada correctamente.')
                else:
                    messages.error(request, message)
                    return render(request, 'production_sheets/upload.html', {'form': form})
                return redirect('production_sheets:production_sheet_detail', pk=production_sheet.pk)
                
            except Exception as e:
                messages.error(request, f'Error al procesar el archivo: {str(e)}')
                return render(request, 'production_sheets/upload.html', {'form': form})
    else:
        form = ProductionSheetForm()
    
    return render(request, 'production_sheets/upload.html', {'form': form})

def production_sheets_historic(request):
    # Obtener parámetros de filtro
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    origin = request.GET.get('origin')
    manifest = request.GET.get('manifest')
    op_search = request.GET.get('op')
    
    # Construir query base
    sheets = ProductionSheet.objects.all()
    
    # Aplicar filtros básicos
    if date_from:
        sheets = sheets.filter(packing_date__gte=datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        sheets = sheets.filter(packing_date__lte=datetime.strptime(date_to, '%Y-%m-%d'))
    if origin:
        sheets = sheets.filter(origin=origin)
    if manifest:
        sheets = sheets.filter(manifest_number__icontains=manifest)
        
        # Si hay búsqueda por OP, preparar datos específicos
    op_summary = None
    if op_search:
        # Obtener todos los detalles que coinciden con la OP y agruparlos
        op_details = ProductionDetail.objects.filter(
            production_sheet__in=sheets,
            op__icontains=op_search
        )
        
        # Obtener totales por talla
        op_details_summary = op_details.values('op', 'ref', 'size').annotate(
            total_quantity=Sum('quantity'),
            sheet_count=Count('production_sheet', distinct=True),
            first_date=Min('production_sheet__packing_date'),
            last_date=Max('production_sheet__packing_date')
        ).order_by('op', 'ref', 'size')        # Organizar los datos por OP y REF
        op_summary = {}
        for detail in op_details_summary:
            key = (detail['op'], detail['ref'])
            if key not in op_summary:
                op_summary[key] = {
                    'op': detail['op'],
                    'ref': detail['ref'],
                    'sizes': {},
                    'total': 0,
                    'sheet_count': detail['sheet_count'],
                    'first_date': detail['first_date'],
                    'last_date': detail['last_date']
                }
            op_summary[key]['sizes'][detail['size']] = detail['total_quantity']
            op_summary[key]['total'] += detail['total_quantity']

        # Calcular totales generales
        total_general = op_details.aggregate(
            total_unidades=Sum('quantity'),
            total_planillas=Count('production_sheet', distinct=True)
        )
        
        # Convertir a lista y ordenar por OP
        op_summary = list(op_summary.values())
        
    # Agregar totales
    sheets = sheets.annotate(
        total_refs=Count('productiondetail__ref', distinct=True),
        total_units=Sum('productiondetail__quantity')
    ).order_by('-upload_date')
    
    # Exportar a Excel si se solicita
    if request.GET.get('export') == 'excel':
        return export_to_excel(sheets)
    
    # Preparar contexto
    context = {
        'sheets': sheets,
        'date_from': date_from,
        'date_to': date_to,
        'origin': origin,
        'manifest': manifest,
        'op_summary': op_summary,
        'total_general': total_general if op_search else None
    }
    return render(request, 'production_sheets/historic.html', context)

def production_sheet_detail(request, pk):
    production_sheet = ProductionSheet.objects.get(pk=pk)
    # Obtener todos los detalles agrupados por OP y REF
    details = ProductionDetail.objects.filter(production_sheet=production_sheet)
    
    # Obtener todas las tallas únicas y ordenarlas según el orden predefinido
    sizes = sort_sizes(details.values_list('size', flat=True).distinct())
    
    # Crear una estructura de datos para la tabla
    table_data = {}
    size_totals = {}
    grand_total = 0
    
    for detail in details:
        key = (detail.op, detail.ref)
        if key not in table_data:
            table_data[key] = {'op': detail.op, 'ref': detail.ref, 'total': 0}
        table_data[key][detail.size] = detail.quantity
        table_data[key]['total'] = table_data[key].get('total', 0) + detail.quantity
        
        # Actualizar totales por talla
        size_totals[detail.size] = size_totals.get(detail.size, 0) + detail.quantity
        grand_total += detail.quantity
    
    context = {
        'production_sheet': production_sheet,
        'table_data': list(table_data.values()),
        'sizes': sizes,
        'size_totals': size_totals,
        'grand_total': grand_total
    }
    
    # Si se solicita PDF, generar el PDF
    if request.GET.get('format') == 'pdf':
        return generate_pdf(production_sheet, context)
        
    return render(request, 'production_sheets/detail.html', context)

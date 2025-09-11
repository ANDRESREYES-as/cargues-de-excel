"""
Vistas para el procesamiento por lotes de PDFs
"""
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from django.conf import settings
from django.db import models
from pathlib import Path
import os
import datetime
import traceback

from .models import PDFProcessHistory
from .pdf_utils import PDFBatchProcessor

@csrf_exempt
def pdf_batch_process(request):
    """Vista para procesar PDFs por lotes y mostrar todos los PDFs"""
    
    # Manejar la subida y procesamiento de PDFs
    if request.method == 'POST' and not request.POST.get('action'):
        uploaded_files = request.FILES.getlist('pdf_files[]')
        print(f"Archivos recibidos: {len(uploaded_files)}")  # Log
        
        if uploaded_files:
            processor = PDFBatchProcessor()
            try:
                # Crear directorio temporal para los archivos subidos
                temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads')
                os.makedirs(temp_dir, exist_ok=True)
                
                # Guardar archivos subidos
                saved_files = []
                for uploaded_file in uploaded_files:
                    try:
                        if not uploaded_file.name.lower().endswith('.pdf'):
                            print(f"Archivo ignorado (no es PDF): {uploaded_file.name}")
                            continue
                            
                        # Generar un nombre único para evitar colisiones
                        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                        safe_name = ''.join(c for c in uploaded_file.name if c.isalnum() or c in '._-')
                        unique_name = f"{timestamp}_{safe_name}"
                        file_path = os.path.join(temp_dir, unique_name)
                        
                        print(f"Guardando archivo: {file_path}")
                        
                        # Guardar el archivo en chunks para manejar archivos grandes
                        with open(file_path, 'wb+') as destination:
                            for chunk in uploaded_file.chunks():
                                destination.write(chunk)
                                
                        # Verificar que el archivo se guardó correctamente
                        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                            saved_files.append(file_path)
                            print(f"Archivo guardado exitosamente: {file_path}")
                        else:
                            print(f"Error: El archivo {file_path} no se guardó correctamente")
                            
                    except Exception as e:
                        print(f"Error al guardar archivo {uploaded_file.name}: {str(e)}")
                        print(traceback.format_exc())
                
                if saved_files:
                    output_path = os.path.join(settings.MEDIA_ROOT, 'combined_pdfs', 
                                             f'combined_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    print(f"Ruta de salida: {output_path}")
                    
                    result = processor.combine_pdfs(saved_files, output_path)
                    print(f"Resultado de combinación: {result}")
                    
                    # Limpiar archivos temporales
                    for file_path in saved_files:
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            print(f"Error al eliminar archivo temporal {file_path}: {e}")
                            
                    if result:
                        return JsonResponse({
                            'success': True,
                            'message': f'PDFs procesados exitosamente. Archivo generado: {os.path.basename(result)}'
                        })
                    else:
                        return JsonResponse({
                            'success': False,
                            'error': 'Error al procesar los PDFs'
                        })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'No se recibieron archivos PDF válidos'
                    })
                    
            except Exception as e:
                print(f"Error al procesar PDFs: {str(e)}")
                print(traceback.format_exc())
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
            finally:
                processor.cleanup()
                
    # Manejar la solicitud de apertura de PDF
    elif request.method == 'POST' and request.POST.get('action') == 'open_pdf':
        pdf_path = request.POST.get('pdf_path')
        if pdf_path:
            try:
                # Convertir la ruta del archivo a una URL relativa
                if os.path.exists(pdf_path):
                    relative_path = os.path.relpath(pdf_path, settings.MEDIA_ROOT)
                    pdf_url = settings.MEDIA_URL + relative_path.replace('\\', '/')
                    return JsonResponse({'success': True, 'url': pdf_url})
                else:
                    return JsonResponse({'success': False, 'error': 'Archivo no encontrado'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        return JsonResponse({'success': False, 'error': 'Ruta de PDF no proporcionada'})
    
    # Obtener solo los PDFs combinados finales (no los individuales)
    pdfs_generados = PDFProcessHistory.objects.filter(
        is_batch=True,
        filepath=models.F('output_path')  # Solo los PDFs que son el resultado de la combinación
    ).order_by('-process_date')

    # Obtener historial de PDFs procesados con paginación
    history = PDFProcessHistory.objects.all().order_by('-process_date')
    
    # Filtrar por nombre de archivo si se especifica
    filename_filter = request.GET.get('filename')
    if filename_filter:
        history = history.filter(filename__icontains=filename_filter)
    
    # Paginación
    paginator = Paginator(history, 50)  # 50 items por página
    page = request.GET.get('page')
    history_page = paginator.get_page(page)

    return render(request, 'excel_processor/pdf_batch.html', {
        'history': history_page,
        'pdfs_generados': pdfs_generados
    })

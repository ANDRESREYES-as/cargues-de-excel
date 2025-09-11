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

def handle_uploaded_files(files):
    """
    Maneja los archivos subidos y los guarda en el directorio temporal.
    Retorna una lista de las rutas de los archivos guardados.
    """
    saved_files = []
    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads')
    os.makedirs(temp_dir, exist_ok=True)
    
    for uploaded_file in files:
        try:
            if not uploaded_file.name.lower().endswith('.pdf'):
                print(f"Archivo ignorado (no es PDF): {uploaded_file.name}")
                continue
                
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            safe_name = ''.join(c for c in uploaded_file.name if c.isalnum() or c in '._-')
            unique_name = f"{timestamp}_{safe_name}"
            file_path = os.path.join(temp_dir, unique_name)
            
            print(f"Guardando archivo: {file_path}")
            
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
                    
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                saved_files.append(file_path)
                print(f"Archivo guardado exitosamente: {file_path}")
            else:
                print(f"Error: El archivo {file_path} no se guardó correctamente")
                
        except Exception as e:
            print(f"Error al guardar archivo {uploaded_file.name}: {str(e)}")
            print(traceback.format_exc())
            
    return saved_files

@csrf_exempt
def pdf_batch_process(request):
    """Vista para procesar PDFs por lotes y mostrar todos los PDFs"""
    
    if request.method == 'POST':
        try:
            # Manejar la solicitud de apertura de PDF
            if request.POST.get('action') == 'open_pdf':
                pdf_path = request.POST.get('pdf_path')
                if not pdf_path or not os.path.exists(pdf_path):
                    return JsonResponse({
                        'success': False,
                        'error': 'Archivo PDF no encontrado'
                    })
                
                relative_path = os.path.relpath(pdf_path, settings.MEDIA_ROOT)
                pdf_url = settings.MEDIA_URL + relative_path.replace('\\', '/')
                return JsonResponse({'success': True, 'url': pdf_url})
            
            # Procesar la carga de archivos PDF
            print("Procesando carga de archivos PDF")
            uploaded_files = request.FILES.getlist('pdf_files[]')
            print(f"Archivos recibidos: {len(uploaded_files)}")
            
            if not uploaded_files:
                return JsonResponse({
                    'success': False,
                    'error': 'No se recibieron archivos PDF'
                })
            
            # Procesar los archivos subidos
            saved_files = handle_uploaded_files(uploaded_files)
            
            if not saved_files:
                return JsonResponse({
                    'success': False,
                    'error': 'No se pudo guardar ningún archivo PDF'
                })
            
            # Procesar los PDFs
            processor = PDFBatchProcessor()
            try:
                output_path = os.path.join(settings.MEDIA_ROOT, 'combined_pdfs', 
                             f'combined_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                result = processor.combine_pdfs(saved_files, output_path)
                
                # Limpiar archivos temporales
                for file_path in saved_files:
                    try:
                        if os.path.exists(file_path):
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
            finally:
                processor.cleanup()
                
        except Exception as e:
            print(f"Error durante el procesamiento: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'error': f'Error durante el procesamiento: {str(e)}'
            })
    
    # Manejar solicitud GET
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
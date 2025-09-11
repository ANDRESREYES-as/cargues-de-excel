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
    
    # Limpiar archivos temporales antiguos
    try:
        for old_file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, old_file)
            if os.path.isfile(file_path):
                file_age = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_age.total_seconds() > 3600:  # Más de 1 hora
                    try:
                        os.remove(file_path)
                        print(f"Archivo temporal antiguo eliminado: {file_path}")
                    except:
                        pass
    except Exception as e:
        print(f"Error al limpiar archivos temporales: {e}")
    
    for uploaded_file in files:
        try:
            if not uploaded_file.name.lower().endswith('.pdf'):
                print(f"Archivo ignorado (no es PDF): {uploaded_file.name}")
                continue
            
            # Validar tamaño del archivo
            if uploaded_file.size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
                print(f"Archivo demasiado grande ignorado: {uploaded_file.name}")
                continue
                
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            safe_name = ''.join(c for c in uploaded_file.name if c.isalnum() or c in '._-')
            unique_name = f"{timestamp}_{safe_name}"
            file_path = os.path.join(temp_dir, unique_name)
            
            print(f"Guardando archivo: {file_path}")
            
            # Guardar directamente en la ubicación final
            try:
                with open(file_path, 'wb') as dest_file:
                    for chunk in uploaded_file.chunks(chunk_size=1024*1024):  # 1MB chunks
                        dest_file.write(chunk)
                    dest_file.flush()
                    os.fsync(dest_file.fileno())  # Asegurar que los datos se escriban en disco
                    
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    saved_files.append(file_path)
                    print(f"Archivo guardado exitosamente: {file_path}")
            except Exception as e:
                print(f"Error al guardar archivo {uploaded_file.name}: {str(e)}")
                print(traceback.format_exc())
                # Si hay error, intentar limpiar el archivo parcial
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except:
                    pass
            
                continue
                
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
            
            # Validar archivos antes de procesarlos
            total_size = sum(f.size for f in uploaded_files)
            if total_size > settings.DATA_UPLOAD_MAX_MEMORY_SIZE:
                return JsonResponse({
                    'success': False,
                    'error': f'El tamaño total de los archivos ({total_size / (1024*1024):.1f}MB) excede el límite permitido ({settings.DATA_UPLOAD_MAX_MEMORY_SIZE / (1024*1024):.1f}MB)'
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
                # Crear directorios si no existen
                output_dir = os.path.join(settings.MEDIA_ROOT, 'combined_pdfs')
                os.makedirs(output_dir, exist_ok=True)
                os.makedirs(os.path.join(settings.MEDIA_ROOT, 'temp_uploads'), exist_ok=True)
                
                # Generar nombre único para el archivo combinado
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(output_dir, f'combined_{timestamp}.pdf')
                
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
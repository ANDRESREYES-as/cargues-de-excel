"""
Utilidades para el procesamiento por lotes de archivos PDF.
"""
from pathlib import Path
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import tempfile
import os
from django.conf import settings


class PDFBatchProcessor:
    """
    Clase para procesar PDFs por lotes.
    """
    
    def __init__(self):
        """Inicializa el procesador."""
        self.temp_dir = Path(tempfile.gettempdir())
        self.blank_page_path = self.temp_dir / "blank_page.pdf"
        self._create_blank_page()

    def _create_blank_page(self):
        """Crea una página en blanco para usar cuando sea necesario."""
        with open(self.blank_page_path, 'wb') as blank_file:
            writer = PdfWriter()
            writer.add_blank_page(width=595, height=842)  # Tamaño A4
            writer.write(blank_file)

    def combine_pdfs(self, pdf_files, output_path=None):
        """
        Combina PDFs y agrega páginas en blanco donde sea necesario.
        
        Args:
            pdf_files: Lista de rutas a PDFs para combinar.
            output_path: Ruta opcional para el PDF combinado.
            
        Returns:
            Path al PDF combinado o None si hay error.
        """
        from .models import PDFProcessHistory
        import datetime
        
        if not pdf_files:
            print("No se proporcionaron archivos PDF")
            return None
            
        # Convertir output_path a string si es un objeto Path
        if isinstance(output_path, Path):
            output_path = str(output_path)
            
        if not output_path:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(settings.MEDIA_ROOT, 'combined_pdfs')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f'combined_{timestamp}.pdf')
        
        # Lista para almacenar la información de los PDFs procesados
        processed_files_info = []
        total_pages = 0
        merger = PdfMerger()
        
        try:
            print("Iniciando procesamiento de PDFs...")
            # Primero verificamos que todos los archivos sean válidos
            for pdf_file in pdf_files:
                pdf_path = str(pdf_file) if isinstance(pdf_file, Path) else pdf_file
                print(f"Procesando archivo: {pdf_path}")
                
                try:
                    with open(pdf_path, 'rb') as file:
                        pdf = PdfReader(file)
                        num_pages = len(pdf.pages)
                        if num_pages > 0:
                            processed_files_info.append({
                                'path': pdf_path,
                                'pages': num_pages,
                                'filename': os.path.basename(pdf_path)
                            })
                            print(f"PDF válido encontrado: {pdf_path} con {num_pages} páginas")
                        else:
                            print(f"PDF sin páginas encontrado: {pdf_path}")
                except Exception as e:
                    print(f"Error al verificar PDF {pdf_path}: {str(e)}")
                    continue

            if not processed_files_info:
                print("No se encontraron PDFs válidos para procesar")
                return None

            print("Combinando PDFs...")
            # Ahora combinamos los PDFs válidos
            for file_info in processed_files_info:
                with open(file_info['path'], 'rb') as file:
                    merger.append(file)
                    total_pages += file_info['pages']
                    
                    # Agregar página en blanco si es necesario
                    if file_info['pages'] % 2 != 0:
                        with open(str(self.blank_page_path), 'rb') as blank:
                            merger.append(blank)
                        total_pages += 1

            # Guardar el PDF combinado
            print(f"Guardando PDF combinado en: {output_path}")
            merger.write(output_path)
            
            # Registrar el PDF combinado en la base de datos
            combined_pdf = PDFProcessHistory.objects.create(
                filename=os.path.basename(output_path),
                filepath=output_path,
                pages=total_pages,
                output_path=output_path,
                is_batch=True
            )
            
            # Registrar los archivos individuales
            for file_info in processed_files_info:
                PDFProcessHistory.objects.create(
                    filename=file_info['filename'],
                    filepath=file_info['path'],
                    pages=file_info['pages'],
                    output_path=output_path,
                    is_batch=True
                )
            
            print(f"Proceso completado. Se generó el archivo: {output_path}")
            return output_path
                
        except Exception as e:
            print(f"Error al combinar PDFs: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None
            
        finally:
            merger.close()

    def cleanup(self):
        """Limpia archivos temporales."""
        if self.blank_page_path.exists():
            self.blank_page_path.unlink()

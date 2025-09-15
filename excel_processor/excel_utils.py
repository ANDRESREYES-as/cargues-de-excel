import openpyxl
from io import BytesIO
import contextlib
import tempfile
import os

class ExcelContextManager:
    def __init__(self):
        self.workbook = None
        self.output = None
        self.temp_files = []

    def __enter__(self):
        self.output = BytesIO()
        self.workbook = openpyxl.Workbook()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.workbook:
                self.workbook.close()
            if self.output:
                self.output.close()
            # Limpiar archivos temporales
            for temp_file in self.temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except (OSError, PermissionError):
                    pass
        except Exception:
            pass  # Asegurar que no se propaguen errores durante la limpieza

    def save(self):
        """
        Guarda el workbook en el BytesIO y retorna el contenido.
        """
        if not self.workbook or not self.output:
            raise ValueError("Workbook no inicializado")
        
        try:
            # Crear un archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                self.temp_files.append(tmp.name)
                self.workbook.save(tmp.name)
                
            # Leer el archivo temporal en el BytesIO
            with open(self.temp_files[-1], 'rb') as f:
                content = f.read()
                
            return content
            
        except Exception as e:
            raise Exception(f"Error al guardar Excel: {str(e)}")

def create_excel_response(content, filename):
    """
    Crea una respuesta HTTP con el contenido Excel.
    """
    from django.http import HttpResponse
    
    response = HttpResponse(
        content,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
from django.db import models
from pathlib import Path

class ExcelProcess(models.Model):
    archivo = models.FileField(upload_to='excels/')
    consecutivo = models.IntegerField()
    fecha_carga = models.DateTimeField(auto_now_add=True)

class PDFProcessHistory(models.Model):
    filename = models.CharField(max_length=255)
    filepath = models.CharField(max_length=500)
    output_path = models.CharField(max_length=500, null=True, blank=True)
    process_date = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(null=True, blank=True)
    is_batch = models.BooleanField(default=False)  # True si es un PDF combinado
    pages = models.IntegerField(default=0)  # Número de páginas en el PDF

    def __str__(self):
        return f"{self.filename} - {self.process_date.strftime('%Y-%m-%d %H:%M')}"

    def get_file_url(self):
        return str(Path(self.filepath).as_posix())

class RegistroExcel(models.Model):
    proceso = models.ForeignKey(ExcelProcess, on_delete=models.CASCADE, related_name='registros')
    orden = models.CharField(max_length=100, blank=True, null=True)
    produccion = models.CharField(max_length=100, blank=True, null=True)
    cant_orig = models.FloatField(blank=True, null=True)
    saldo_entregar = models.FloatField(blank=True, null=True)
    cant_produc = models.FloatField(blank=True, null=True)
    iny = models.CharField(max_length=20, blank=True, null=True)
    otros = models.CharField(max_length=100, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

from django.db import models

class ExcelProcess(models.Model):
    archivo = models.FileField(upload_to='excels/')
    consecutivo = models.IntegerField()
    fecha_carga = models.DateTimeField(auto_now_add=True)

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

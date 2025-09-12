from django.db import models
from django.core.validators import FileExtensionValidator

class ProductionSheet(models.Model):
    ORIGIN_CHOICES = [
        ('BANDA_1_2', 'Banda 1 y 2'),
        ('BANDA_4', 'Banda 4'),
    ]

    excel_file = models.FileField(
        upload_to='production_sheets/',
        validators=[FileExtensionValidator(allowed_extensions=['xlsx'])]
    )
    origin = models.CharField(max_length=10, choices=ORIGIN_CHOICES)
    manifest_number = models.CharField(max_length=100)
    packing_date = models.DateField()
    upload_date = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    class Meta:
        constraints = []

    def __str__(self):
        return f"Planilla de Producción - Manifiesto {self.manifest_number}"
        
    def mark_as_processed(self):
        """
        Marca la planilla como procesada y verifica si es seguro hacerlo.
        Retorna (bool, str) donde bool indica si fue exitoso y str contiene un mensaje.
        """
        if self.processed:
            return False, "La planilla ya está marcada como procesada."
            
        # Verificar si existe otro manifiesto procesado con el mismo número
        if ProductionSheet.objects.filter(
            manifest_number=self.manifest_number,
            processed=True
        ).exclude(id=self.id).exists():
            return False, f"Ya existe una planilla procesada con el manifiesto {self.manifest_number}"
            
        self.processed = True
        self.save()
        return True, "Planilla marcada como procesada correctamente."

class ProductionDetail(models.Model):
    production_sheet = models.ForeignKey(ProductionSheet, on_delete=models.CASCADE)
    op = models.CharField(max_length=100)
    ref = models.CharField(max_length=100)
    size = models.CharField(max_length=3)
    quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = ['production_sheet', 'op', 'ref', 'size']

    def __str__(self):
        return f"{self.op} - {self.ref} - Talla {self.size}"

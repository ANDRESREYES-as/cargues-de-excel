from django.db import models

class ArchivoCalculo(models.Model):
    """
    Modelo para almacenar los archivos Excel cargados y su tipo
    """
    TIPO_ARCHIVO_CHOICES = [
        ('INV', 'Inventario'),
        ('VEN', 'Ventas'),
        ('PRO', 'Producción'),
    ]

    archivo = models.FileField(upload_to='calculos/')
    tipo_archivo = models.CharField(max_length=3, choices=TIPO_ARCHIVO_CHOICES)
    fecha_carga = models.DateTimeField(auto_now_add=True)
    procesado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_tipo_archivo_display()} - {self.fecha_carga.strftime('%Y-%m-%d %H:%M')}"

class ResultadoCalculo(models.Model):
    """
    Modelo para almacenar los resultados del cálculo
    """
    referencia = models.CharField(max_length=97, help_text='Referencia del producto sin la talla', default='')
    talla = models.CharField(max_length=3, help_text='Talla del producto', default='')
    ventas = models.DecimalField(max_digits=15, decimal_places=2, default=0, 
                               help_text='Cantidad pendiente de ventas')
    inventario = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                   help_text='Saldo actual en inventario')
    produccion = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                   help_text='Saldo por entregar de producción')
    total_disponible = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                         help_text='Suma de inventario y producción')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                help_text='Ventas - Total Disponible')
    fecha_calculo = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.referencia}-{self.talla} - Balance: {self.balance} ({self.fecha_calculo.strftime('%Y-%m-%d %H:%M')})"

    class Meta:
        ordering = ['referencia', 'talla', '-fecha_calculo']

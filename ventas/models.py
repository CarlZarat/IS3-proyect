from django.db import models
from facturacion.models import Factura

class Venta(models.Model):
    CONTADO = 'CO'
    CREDITO = 'CR'
    MODALIDAD_CHOICES = [
        (CONTADO, 'Contado'),
        (CREDITO, 'Crédito'),
    ]
    factura = models.OneToOneField(Factura, on_delete=models.CASCADE)
    modalidad = models.CharField(max_length=2, choices=MODALIDAD_CHOICES)
    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Venta {self.factura.numero} - {self.get_modalidad_display()}"

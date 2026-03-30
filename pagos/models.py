from django.db import models
from cuentas_cobrar.models import Cuota

class Pago(models.Model):
    cuota = models.ForeignKey(Cuota, on_delete=models.CASCADE, related_name='pagos')
    fecha_pago = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Pago de {self.monto} el {self.fecha_pago}"

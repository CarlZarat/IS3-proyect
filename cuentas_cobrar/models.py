from django.db import models
from ventas.models import Venta
from facturacion.models import Factura
from clientes.models import Cliente
from django.utils import timezone

class Credito(models.Model):
    MODALIDAD_MENSUAL = 'mensual'
    MODALIDAD_PERSONALIZADA = 'personalizada'
    MODALIDAD_CHOICES = [
        (MODALIDAD_MENSUAL, 'Mensual'),
        (MODALIDAD_PERSONALIZADA, 'Personalizada'),
    ]
    venta = models.OneToOneField('ventas.Venta', on_delete=models.CASCADE, related_name='credito')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad_cuotas = models.PositiveIntegerField()
    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES)
    fecha_inicio = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Crédito de {self.cliente.nombre} - {self.monto} Gs. ({self.cantidad_cuotas} cuotas)"

class Cuota(models.Model):
    credito = models.ForeignKey(Credito, on_delete=models.CASCADE, related_name='cuotas', default=None)
    numero = models.PositiveIntegerField()  # Ej: 1, 2, 3...
    importe = models.DecimalField(max_digits=12, decimal_places=2)
    vence = models.DateField()
    cobrado = models.BooleanField(default=False)

    def __str__(self):
        return f"Cuota {self.numero} de {self.credito}"

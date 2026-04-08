from django.db import models
from cxc.models import Venta
from clientes.models import Cliente

# ⚠️ NOTA: Este módulo mantiene referencia a clientes.Cliente por compatibilidad con datos existentes
# Los nuevos desarrollos deben usar cxc.Cliente + cxc.Venta en su lugar

class Credito(models.Model):
    MODALIDAD_MENSUAL = 'mensual'
    MODALIDAD_PERSONALIZADA = 'personalizada'
    MODALIDAD_CHOICES = [
        (MODALIDAD_MENSUAL, 'Mensual'),
        (MODALIDAD_PERSONALIZADA, 'Personalizada'),
    ]
    venta = models.OneToOneField(Venta, on_delete=models.CASCADE, related_name='credito_compat')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad_cuotas = models.PositiveIntegerField()
    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES)
    fecha_inicio = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'cuentas_cobrar_credito'

    def __str__(self):
        return f"Crédito de {self.cliente.nombre} - {self.monto} Gs. ({self.cantidad_cuotas} cuotas)"

class Cuota(models.Model):
    credito = models.ForeignKey(Credito, on_delete=models.CASCADE, related_name='cuotas', default=None)
    numero = models.PositiveIntegerField()  # Ej: 1, 2, 3...
    importe = models.DecimalField(max_digits=12, decimal_places=2)
    vence = models.DateField()
    cobrado = models.BooleanField(default=False)

    class Meta:
        db_table = 'cuentas_cobrar_cuota'

    def __str__(self):
        return f"Cuota {self.numero} de {self.credito}"

from django.db import models
from clientes.models import Cliente

class Factura(models.Model):
    class Moneda(models.TextChoices):
        DOLAR = 'USD', 'Dólar'
        GUARANI = 'PYG', 'Guaraní'
        PESO_ARGENTINO = 'ARS', 'Peso argentino'
        REAL_BRASILENO = 'BRL', 'Real brasileño'

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    numero = models.CharField(max_length=20)
    fecha = models.DateField()
    moneda = models.CharField(max_length=3, choices=Moneda.choices, default=Moneda.GUARANI)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'facturacion_factura'

    def __str__(self):
        return f"{self.numero} - {self.cliente.nombre}"
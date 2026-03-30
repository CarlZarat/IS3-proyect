from django.db import models
from clientes.models import Cliente
# Create your models here.

class Factura(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    numero = models.CharField(max_length=20)
    fecha = models.DateField()
    moneda = models.CharField(max_length=20, default='Guaraní')
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.numero} - {self.cliente.nombre}"
    
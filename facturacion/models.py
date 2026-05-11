from django.db import models
from clientes.models import Cliente

class Factura(models.Model):
    class Moneda(models.TextChoices):
        DOLAR = 'USD', 'Dólar'
        GUARANI = 'PYG', 'Guaraní'
        PESO_ARGENTINO = 'ARS', 'Peso argentino'
        REAL_BRASILENO = 'BRL', 'Real brasileño'

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    numero = models.CharField(max_length=20, editable=False, unique=True)
    fecha = models.DateField()
    moneda = models.CharField(max_length=3, choices=Moneda.choices, default=Moneda.GUARANI)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'facturacion_factura'

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generar_numero_factura()
        super().save(*args, **kwargs)

    @staticmethod
    def _generar_numero_factura():
        """Genera el siguiente número de factura de forma secuencial."""
        ultima_factura = Factura.objects.order_by('-id').first()
        if ultima_factura and ultima_factura.numero:
            try:
                numero_actual = int(ultima_factura.numero)
                return str(numero_actual + 1)
            except ValueError:
                pass
        return '001'

    def __str__(self):
        return f"{self.numero} - {self.cliente.nombre}"
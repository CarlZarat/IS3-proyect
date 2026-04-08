from django.db import models

# ⚠️ DEPRECATED: Usar cxc.Cliente en su lugar
# Este modelo se mantiene solo por compatibilidad retroactiva.
# Todos los nuevos desarrollos deben usar cxc.Cliente

class Cliente(models.Model):
    nombre = models.CharField(max_length=255)
    ruc = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    class Meta:
        db_table = 'clientes_cliente'

    def __str__(self):
        return self.nombre

    
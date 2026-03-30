from django.contrib import admin
from .models import Factura

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente', 'fecha', 'moneda', 'total')
    search_fields = ('numero', 'cliente__nombre')
    list_filter = ('moneda', 'fecha')
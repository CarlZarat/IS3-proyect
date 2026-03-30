from django.contrib import admin
from .models import Venta

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('factura', 'modalidad', 'observacion')
    search_fields = ('factura__numero',)
    list_filter = ('modalidad',)
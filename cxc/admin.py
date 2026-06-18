from django.contrib import admin
from .models import (
    Moneda, Cliente, Deposito, TipoDocumento, Timbrado, Plazo, PlazoDetalle,
    Empresa, Producto, ProductoDetalle, Venta, VentaDetalle,
    CuentaCobrar, Cobro
)

# Configuración inline para detalles anidados
class VentaDetalleInline(admin.TabularInline):
    model = VentaDetalle
    extra = 1
    fields = ['producto_detalle', 'precio', 'cantidad', 'impuesto10', 'total']

class VentaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nrofactura', 'cliente', 'fechafactura', 'totalfactura', 'plazo']
    list_filter = ['fechafactura', 'moneda', 'plazo']
    search_fields = ['nrofactura', 'cliente__nombre']
    readonly_fields = ['id']
    inlines = [VentaDetalleInline]

class ProductoDetalleInline(admin.TabularInline):
    model = ProductoDetalle
    extra = 1
    fields = ['codbarra', 'colorid', 'tamanoid', 'disenoid', 'uxb']

class ProductoAdmin(admin.ModelAdmin):
    list_display = ['id', 'producto', 'iva', 'precio_venta', 'servicio']
    list_filter = ['servicio', 'iva']
    search_fields = ['producto']
    inlines = [ProductoDetalleInline]

class PlazoDetalleInline(admin.TabularInline):
    model = PlazoDetalle
    extra = 1
    fields = ['cuota', 'dias']

class PlazoAdmin(admin.ModelAdmin):
    list_display = ['id', 'plazo', 'tipo_documento', 'cuotas', 'irregular']
    list_filter = ['irregular', 'tipo_documento']
    search_fields = ['plazo']
    inlines = [PlazoDetalleInline]

class TimbradoAdmin(admin.ModelAdmin):
    list_display = ['id', 'numero', 'serie', 'nro_inicio', 'nro_fin', 'fecha_vencimiento', 'estado']
    list_filter = ['estado', 'fecha_vencimiento']
    search_fields = ['numero', 'serie']

class CuentaCobrarAdmin(admin.ModelAdmin):
    list_display = ['id', 'venta', 'cuota', 'importe', 'vence', 'cobrado']
    list_filter = ['vence', 'cobrado']
    search_fields = ['venta__nrofactura']

# Registrar todos los modelos
admin.site.register(Moneda)
admin.site.register(Cliente)
admin.site.register(Deposito)
admin.site.register(TipoDocumento)
admin.site.register(Plazo, PlazoAdmin)
admin.site.register(Timbrado, TimbradoAdmin)
admin.site.register(Empresa)
admin.site.register(Producto, ProductoAdmin)
admin.site.register(Venta, VentaAdmin)
admin.site.register(CuentaCobrar, CuentaCobrarAdmin)
admin.site.register(Cobro)

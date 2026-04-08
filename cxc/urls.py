from django.urls import path

from . import views

urlpatterns = [
    # URLs existentes de cuentas por cobrar
    path('cuentas/', views.lista_cuentas, name='cxc_lista_cuentas'),
    path('dashboard/', views.dashboard_cxc, name='cxc_dashboard'),
    path('cuentas/<int:venta_id>/', views.detalle_cuenta, name='cxc_detalle_cuenta'),
    path('cuentas/<int:venta_id>/cuota/<int:cuota_id>/cobro/', views.registrar_cobro, name='cxc_registrar_cobro'),
    
    # URLs nuevas para gestión de ventas con detalles
    path('ventas/', views.lista_ventas, name='cxc_lista_ventas'),
    path('ventas/nueva/', views.crear_venta, name='cxc_crear_venta'),
    path('ventas/<int:venta_id>/', views.detalle_venta, name='cxc_detalle_venta'),
    path('ventas/<int:venta_id>/editar/', views.editar_venta, name='cxc_editar_venta'),
    path('ventas/<int:venta_id>/eliminar/', views.eliminar_venta, name='cxc_eliminar_venta'),
    path('api/ventas/<int:venta_id>/total/', views.api_total_venta, name='cxc_api_total_venta'),
]

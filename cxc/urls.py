from django.urls import path

from . import views

urlpatterns = [
    path('cuentas/', views.lista_cuentas, name='cxc_lista_cuentas'),
    path('dashboard/', views.dashboard_cxc, name='cxc_dashboard'),
    path('cuentas/<int:venta_id>/', views.detalle_cuenta, name='cxc_detalle_cuenta'),
    path('cuentas/<int:venta_id>/cuota/<int:cuota_id>/cobro/', views.registrar_cobro, name='cxc_registrar_cobro'),
]

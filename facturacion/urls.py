from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_facturas, name='lista_facturas'),
    path('nuevo/', views.crear_factura, name='crear_factura'),
    path('factura/<int:factura_id>/', views.detalle_cuenta, name='detalle_cuenta'),
]
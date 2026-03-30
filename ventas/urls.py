from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_ventas, name='lista_ventas'),
    path('nuevo/', views.crear_venta, name='crear_venta'),
    path('<int:venta_id>/editar/', views.editar_venta, name='editar_venta'),
]
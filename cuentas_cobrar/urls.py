from django.urls import path
from . import views

urlpatterns = [
    path('registrar/', views.registrar_credito, name='registrar_credito'),
    path('lista/', views.lista_creditos, name='lista_creditos'),
    path('cuotas/<int:credito_id>/', views.detalle_cuotas, name='detalle_cuotas'),
] 
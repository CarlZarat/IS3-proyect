from django.shortcuts import get_object_or_404, render, redirect
from cxc.models import Venta
from django import forms
from django.contrib import messages
from django.db.models import Q


class VentaForm(forms.ModelForm):
    """Formulario simplificado - usar cxc.forms.VentaForm para lo completo"""
    class Meta:
        model = Venta
        fields = ['cliente', 'serie', 'nrofactura', 'fechafactura', 'plazo']

def lista_ventas(request):
    """Listar ventas - REDIRIGIR a cxc/ventas/"""
    messages.info(request, 'Las ventas ahora se manejan en CXC. Redirigiendo...')
    return redirect('cxc_lista_ventas')

def crear_venta(request):
    """Crear venta - REDIRIGIR a cxc/ventas/nueva/"""
    messages.info(request, 'Las ventas ahora se manejan en CXC. Redirigiendo...')
    return redirect('cxc_crear_venta')

def editar_venta(request, venta_id):
    """Editar venta - REDIRIGIR a cxc/ventas/<id>/editar/"""
    messages.info(request, 'Las ventas ahora se manejan en CXC. Redirigiendo...')
    return redirect('cxc_editar_venta', venta_id=venta_id)
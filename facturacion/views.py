from django.shortcuts import render, redirect, get_object_or_404
from .models import Factura
from clientes.models import Cliente
from django import forms

class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = ['cliente', 'numero', 'fecha', 'moneda', 'total']

def lista_facturas(request):
    facturas = Factura.objects.select_related('cliente').all()
    return render(request, 'facturacion/lista.html', {'facturas': facturas})

def crear_factura(request):
    if request.method == 'POST':
        form = FacturaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_facturas')
    else:
        form = FacturaForm()
    return render(request, 'facturacion/form.html', {'form': form})

def detalle_cuenta(request, factura_id):
    factura = get_object_or_404(Factura, id=factura_id)
    return render(request, 'facturacion/detalle_cuenta.html', {'factura': factura})
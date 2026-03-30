from django.shortcuts import get_object_or_404, render, redirect
from .models import Venta
from facturacion.models import Factura
from django import forms
from django.contrib import messages
from django.db.models import Q


class FacturaChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.numero} - {obj.cliente.nombre} ({obj.fecha})"

class VentaForm(forms.ModelForm):
    factura = FacturaChoiceField(
        queryset=Factura.objects.none(),
        empty_label='Seleccionar factura...'
    )

    class Meta:
        model = Venta
        fields = ['factura', 'modalidad', 'observacion']

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        qs = Factura.objects.filter(venta__isnull=True)
        if instance and instance.factura_id:
            qs = Factura.objects.filter(Q(venta__isnull=True) | Q(pk=instance.factura_id))
        self.fields['factura'].queryset = qs.select_related('cliente')

def lista_ventas(request):
    ventas = Venta.objects.select_related('factura__cliente').all()
    return render(request, 'ventas/lista.html', {'ventas': ventas})

def crear_venta(request):
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venta registrada correctamente.')
            return redirect('lista_ventas')
    else:
        form = VentaForm()
        if not form.fields['factura'].queryset.exists():
            messages.warning(
                request,
                'No hay facturas disponibles para vender. Debes crear una factura nueva o usar una no asociada a venta.',
            )
    return render(request, 'ventas/form.html', {
        'form': form,
        'is_edit': False,
    })


def editar_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    if request.method == 'POST':
        form = VentaForm(request.POST, instance=venta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venta actualizada correctamente.')
            return redirect('lista_ventas')
    else:
        form = VentaForm(instance=venta)

    return render(request, 'ventas/form.html', {
        'form': form,
        'is_edit': True,
        'venta': venta,
    })
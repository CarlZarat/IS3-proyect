from django.shortcuts import render, redirect, get_object_or_404
from .models import Factura
from clientes.models import Cliente
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

class FacturaForm(forms.ModelForm):
    cliente = forms.CharField(
        label='Cliente',
        widget=forms.TextInput(attrs={
            'list': 'clientes-list',
            'placeholder': 'Escribe nombre o RUC',
        }),
        help_text='Busca y selecciona un cliente por nombre o RUC.',
    )

    class Meta:
        model = Factura
        fields = ['cliente', 'numero', 'fecha', 'moneda', 'total']
        labels = {
            'numero': 'Número de factura',
            'fecha': 'Fecha de factura',
        }
        help_texts = {
            'numero': 'Ingresa el número o comprobante de la factura emitida.',
            'fecha': 'Selecciona la fecha de emisión de la factura.',
        }
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_cliente(self):
        value = self.cleaned_data['cliente'].strip()
        if not value:
            raise ValidationError('Selecciona un cliente.')

        if ' - ' in value:
            nombre, ruc = [part.strip() for part in value.split(' - ', 1)]
            cliente = Cliente.objects.filter(nombre__iexact=nombre, ruc__iexact=ruc).first()
            if cliente is not None:
                return cliente

        cliente = (
            Cliente.objects.filter(Q(nombre__iexact=value) | Q(ruc__iexact=value)).first()
            or Cliente.objects.filter(Q(nombre__icontains=value) | Q(ruc__icontains=value)).first()
        )

        if cliente is None:
            raise ValidationError('No se encontró un cliente con ese nombre o RUC.')

        return cliente

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
    clientes = Cliente.objects.order_by('nombre', 'ruc')
    return render(request, 'facturacion/form.html', {'form': form, 'clientes': clientes})

def detalle_cuenta(request, factura_id):
    factura = get_object_or_404(Factura, id=factura_id)
    return render(request, 'facturacion/detalle_cuenta.html', {'factura': factura})
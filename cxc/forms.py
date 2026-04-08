from django import forms
from django.forms import inlineformset_factory
from .models import Venta, VentaDetalle, Cliente, Producto, ProductoDetalle, Deposito, Moneda, Plazo

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = [
            'cliente', 'serie', 'nrofactura', 'fechafactura', 'fechaproce',
            'timbrado', 'timbrado_vence', 'deposito', 'moneda', 'tipo_documento', 'plazo',
            'totalexentas', 'totalimponible', 'totalbase', 'totalfactura'
        ]
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'serie': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '10'}),
            'nrofactura': forms.NumberInput(attrs={'class': 'form-control'}),
            'fechafactura': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fechaproce': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'timbrado': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '20'}),
            'timbrado_vence': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'deposito': forms.Select(attrs={'class': 'form-control'}),
            'moneda': forms.Select(attrs={'class': 'form-control'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'plazo': forms.Select(attrs={'class': 'form-control'}),
            'totalexentas': forms.NumberInput(attrs={'class': 'form-control'}),
            'totalimponible': forms.NumberInput(attrs={'class': 'form-control'}),
            'totalbase': forms.NumberInput(attrs={'class': 'form-control'}),
            'totalfactura': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class VentaDetalleForm(forms.ModelForm):
    class Meta:
        model = VentaDetalle
        fields = ['producto_detalle', 'precio', 'cantidad', 'iva', 'impuesto5', 'impuesto10', 'total']
        widgets = {
            'producto_detalle': forms.Select(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'iva': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'impuesto5': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'impuesto10': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

# Formset para manejar múltiples detalles de venta
VentaDetalleFormSet = inlineformset_factory(
    Venta,
    VentaDetalle,
    form=VentaDetalleForm,
    extra=3,
    can_delete=True
)

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['producto', 'iva', 'servicio']
        widgets = {
            'producto': forms.TextInput(attrs={'class': 'form-control'}),
            'iva': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'servicio': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ProductoDetalleForm(forms.ModelForm):
    class Meta:
        model = ProductoDetalle
        fields = ['codbarra', 'colorid', 'tamanoid', 'disenoid', 'uxb']
        widgets = {
            'codbarra': forms.TextInput(attrs={'class': 'form-control'}),
            'colorid': forms.NumberInput(attrs={'class': 'form-control'}),
            'tamanoid': forms.NumberInput(attrs={'class': 'form-control'}),
            'disenoid': forms.NumberInput(attrs={'class': 'form-control'}),
            'uxb': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

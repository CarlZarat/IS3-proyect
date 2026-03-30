from django import forms
from .models import Credito
from ventas.models import Venta

class CreditoForm(forms.ModelForm):
    venta = forms.ModelChoiceField(
        queryset=Venta.objects.none(),
        label='Venta a Crédito',
        empty_label='Seleccionar venta de crédito...'
    )
    dias_vencimiento = forms.CharField(
        required=False,
        label='Días de vencimiento para cada cuota (separados por coma)',
        help_text='Ejemplo: 30,45,60'
    )

    class Meta:
        model = Credito
        fields = ['venta', 'cliente', 'monto', 'cantidad_cuotas', 'modalidad', 'fecha_inicio'] 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['venta'].queryset = Venta.objects.filter(
            modalidad=Venta.CREDITO,
            credito__isnull=True,
        ).select_related('factura')
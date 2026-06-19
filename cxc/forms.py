from decimal import Decimal, ROUND_HALF_UP

from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from .models import Cliente, Moneda, Plazo, Producto, ProductoDetalle, Timbrado, TipoDocumento, Venta, VentaDetalle


class ClienteChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        nombre = f'{obj.nombre} {obj.apellido}'.strip()
        return nombre or obj.documento


class PlazoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.plazo


class ProductoDetalleChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        precio = getattr(obj.producto, 'precio_venta', None)
        if precio is not None:
            return f'{obj.producto.producto} - {obj.codbarra} - {precio}'
        return f'{obj.producto.producto} - {obj.codbarra}'


class VentaForm(forms.ModelForm):
    timbrado_registro = forms.ModelChoiceField(
        queryset=Timbrado.objects.none(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Timbrado',
    )
    cliente = ClienteChoiceField(
        queryset=Cliente.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select searchable-select'}),
        label='Cliente',
    )
    plazo = PlazoChoiceField(
        queryset=Plazo.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Plazo',
    )
    tipo_vencimiento = forms.ChoiceField(
        choices=(('regular', 'Regular'), ('irregular', 'Irregular')),
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Tipo de vencimiento',
    )
    cantidad_cuotas = forms.IntegerField(
        required=False,
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        label='Cantidad de cuotas',
    )
    dias_entre_cuotas = forms.IntegerField(
        required=False,
        min_value=1,
        initial=30,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        label='Días entre cuotas',
    )
    dias_irregulares = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '30,45,60'}),
        label='Días por cuota',
        help_text='Separados por coma.',
    )

    class Meta:
        model = Venta
        fields = [
            'cliente', 'serie', 'nrofactura', 'fechafactura',
            'timbrado', 'timbrado_vence', 'moneda', 'tipo_documento', 'plazo',
            'totalexentas', 'totalimponible', 'totalfactura',
        ]
        widgets = {
            'serie': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'nrofactura': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'fechafactura': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'timbrado': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'timbrado_vence': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'readonly': 'readonly'}),
            'moneda': forms.Select(attrs={'class': 'form-select'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'totalexentas': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'totalimponible': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'totalfactura': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        sale_defaults = kwargs.pop('sale_defaults', {})
        super().__init__(*args, **kwargs)

        self.fields['cliente'].queryset = Cliente.objects.filter(activo=True).order_by('nombre', 'apellido')
        self.fields['plazo'].queryset = Plazo.objects.select_related('tipo_documento').order_by('plazo')
        self.fields['timbrado_registro'].queryset = Timbrado.objects.filter(estado=Timbrado.ESTADO_VIGENTE).order_by('fecha_vencimiento', 'serie')

        moneda_qs = Moneda.objects.filter(activo=True).order_by('-decimales', 'abreviatura')
        if moneda_qs.exists():
            self.fields['moneda'].queryset = moneda_qs
            self.fields['moneda'].initial = moneda_qs.filter(abreviatura__iexact='PYG').first() or moneda_qs.first()
        else:
            self.fields['moneda'].queryset = Moneda.objects.all()

        self.fields['tipo_documento'].queryset = TipoDocumento.objects.filter(activo=True).order_by('tipo')
        self.fields['tipo_documento'].initial = (
            self.fields['tipo_documento'].queryset.filter(abreviatura__iexact='FAC').first()
            or self.fields['tipo_documento'].queryset.first()
        )

        active_timbrados = self.fields['timbrado_registro'].queryset
        selected_timbrado = sale_defaults.get('timbrado_registro') or active_timbrados.first()
        if selected_timbrado:
            self.fields['timbrado_registro'].initial = selected_timbrado

        if self.instance and self.instance.pk:
            self.fields['timbrado_registro'].initial = self.instance.timbrado_registro
            self.fields['serie'].initial = self.instance.serie
            self.fields['nrofactura'].initial = self.instance.nrofactura
            self.fields['timbrado'].initial = self.instance.timbrado
            self.fields['timbrado_vence'].initial = self.instance.timbrado_vence
        else:
            self.fields['fechafactura'].initial = sale_defaults.get('fechafactura')
            self.fields['serie'].initial = sale_defaults.get('serie', selected_timbrado.serie if selected_timbrado else '001-001')
            self.fields['nrofactura'].initial = sale_defaults.get('nrofactura', 1)
            self.fields['timbrado'].initial = sale_defaults.get('timbrado', selected_timbrado.numero if selected_timbrado else '12345678')
            self.fields['timbrado_vence'].initial = sale_defaults.get('timbrado_vence', selected_timbrado.fecha_vencimiento if selected_timbrado else None)

        self.fields['serie'].disabled = True
        self.fields['nrofactura'].disabled = True
        self.fields['timbrado'].disabled = True
        self.fields['timbrado_vence'].disabled = True
        self.fields['timbrado_registro'].disabled = False

        for field_name in ['totalexentas', 'totalimponible', 'totalfactura']:
            self.fields[field_name].required = False

        for field_name in ['cliente', 'plazo', 'moneda', 'tipo_documento']:
            self.fields[field_name].widget.attrs.setdefault('data-searchable', 'true')

    def clean(self):
        cleaned_data = super().clean()
        plazo = cleaned_data.get('plazo')
        timbrado_registro = cleaned_data.get('timbrado_registro')
        cantidad_cuotas = cleaned_data.get('cantidad_cuotas')
        tipo_vencimiento = cleaned_data.get('tipo_vencimiento')
        dias_entre_cuotas = cleaned_data.get('dias_entre_cuotas')
        dias_irregulares = (cleaned_data.get('dias_irregulares') or '').strip()

        if not timbrado_registro:
            self.add_error('timbrado_registro', 'Selecciona un timbrado vigente.')

        if timbrado_registro and cleaned_data.get('nrofactura'):
            nro_factura = cleaned_data['nrofactura']
            if nro_factura < timbrado_registro.nro_inicio or nro_factura > timbrado_registro.nro_fin:
                self.add_error('nrofactura', f'El número de factura debe estar entre {timbrado_registro.nro_inicio} y {timbrado_registro.nro_fin}.')

        if not plazo:
            return cleaned_data

        if plazo.plazo.upper() == 'CO':
            return cleaned_data

        tipo_esperado = 'irregular' if plazo.irregular else 'regular'
        if tipo_vencimiento and tipo_vencimiento != tipo_esperado:
            self.add_error('tipo_vencimiento', 'El tipo de vencimiento no coincide con el plazo seleccionado.')
        cleaned_data['tipo_vencimiento'] = tipo_esperado
        tipo_vencimiento = tipo_esperado

        if not cantidad_cuotas:
            cantidad_cuotas = plazo.cuotas or 1
            cleaned_data['cantidad_cuotas'] = cantidad_cuotas

        if tipo_vencimiento == 'regular':
            if not dias_entre_cuotas:
                self.add_error('dias_entre_cuotas', 'Los días entre cuotas son obligatorios para vencimiento regular.')
        elif tipo_vencimiento == 'irregular':
            if not dias_irregulares:
                self.add_error('dias_irregulares', 'Debes indicar los días de cada cuota.')
            else:
                dias = [d.strip() for d in dias_irregulares.split(',') if d.strip()]
                if cantidad_cuotas and len(dias) != cantidad_cuotas:
                    self.add_error('dias_irregulares', 'La cantidad de días debe coincidir con la cantidad de cuotas.')

        return cleaned_data


class VentaDetalleForm(forms.ModelForm):
    producto_detalle = ProductoDetalleChoiceField(
        queryset=ProductoDetalle.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select searchable-product'}),
        label='Producto',
    )

    class Meta:
        model = VentaDetalle
        fields = ['producto_detalle', 'precio', 'cantidad', 'impuesto10', 'total']
        widgets = {
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': 'readonly'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '1'}),
            'impuesto10': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': 'readonly'}),
            'total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto_detalle'].queryset = ProductoDetalle.objects.select_related('producto').order_by('producto__producto', 'codbarra')
        self.fields['cantidad'].initial = 1

    def clean(self):
        cleaned_data = super().clean()
        producto_detalle = cleaned_data.get('producto_detalle')
        if producto_detalle:
            producto = producto_detalle.producto
            cleaned_data['precio'] = cleaned_data.get('precio') or producto.precio_venta
            cantidad = cleaned_data.get('cantidad') or 1
            subtotal = cleaned_data['precio'] * cantidad
            iva = Decimal(str(producto.iva or 0))
            if iva == Decimal('10'):
                cleaned_data['impuesto10'] = (subtotal * Decimal('0.10')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            elif iva == Decimal('5'):
                cleaned_data['impuesto10'] = Decimal('0')
            else:
                cleaned_data['impuesto10'] = Decimal('0')
            cleaned_data['total'] = subtotal
        if not cleaned_data.get('cantidad'):
            cleaned_data['cantidad'] = 1
        return cleaned_data


class BaseVentaDetalleFormSet(forms.BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            return
        producto_ids = []
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                prod = form.cleaned_data.get('producto_detalle')
                if prod:
                    if prod.pk in producto_ids:
                        raise ValidationError(
                            f'El producto "{prod}" está repetido. Cada producto solo puede aparecer una vez por venta.'
                        )
                    producto_ids.append(prod.pk)


VentaDetalleFormSet = inlineformset_factory(
    Venta,
    VentaDetalle,
    form=VentaDetalleForm,
    formset=BaseVentaDetalleFormSet,
    extra=1,
    min_num=0,
    validate_min=False,
    can_delete=True,
)


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['producto', 'iva', 'precio_venta', 'servicio']
        widgets = {
            'producto': forms.TextInput(attrs={'class': 'form-control'}),
            'iva': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
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

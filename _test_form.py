import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'gqc_system.settings'
os.chdir(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from cxc.forms import VentaForm, VentaDetalleFormSet
from cxc.models import *
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

# Build POST data as the real form would receive it
post = {
    'csrfmiddlewaretoken': 'test',
    'cliente': '4',
    'fechafactura': '2026-06-19',
    'timbrado_registro': '1',
    'moneda': '3',
    'tipo_documento': '3',
    'plazo': '7',
    'tipo_vencimiento': 'regular',
    'cantidad_cuotas': '1',
    'dias_entre_cuotas': '30',
    'detalles-TOTAL_FORMS': '1',
    'detalles-INITIAL_FORMS': '0',
    'detalles-MIN_NUM_FORMS': '0',
    'detalles-MAX_NUM_FORMS': '1000',
    'detalles-0-producto_detalle': 'P10-001',
    'detalles-0-precio': '5000000',
    'detalles-0-cantidad': '1',
    'detalles-0-impuesto10': '500000',
    'detalles-0-total': '5000000',
}

form = VentaForm(post)
formset = VentaDetalleFormSet(post)

print('Form valid:', form.is_valid())
if not form.is_valid():
    print('Form errors:', form.errors)
    print('Form cleaned:', form.cleaned_data if hasattr(form, 'cleaned_data') else 'N/A')

print('Formset valid:', formset.is_valid())
if not formset.is_valid():
    print('Formset errors:', formset.errors)
    print('Formset non form errors:', formset.non_form_errors())
    for f in formset.forms:
        print('  Form errors:', f.errors)
        print('  Form cleaned:', f.cleaned_data if hasattr(f, 'cleaned_data') else 'N/A')

if form.is_valid() and formset.is_valid():
    from cxc.views import _first_deposito, _next_nrofactura, _calcular_detalle, _generar_cuentas_cobrar
    
    from django.db import transaction
    try:
        with transaction.atomic():
            venta = form.save(commit=False)
            venta.fechaproce = timezone.now()
            venta.deposito = _first_deposito()
            timbrado_registro = form.cleaned_data.get('timbrado_registro')
            venta.timbrado_registro = timbrado_registro
            venta.serie = timbrado_registro.serie
            venta.nrofactura = _next_nrofactura(timbrado_registro)
            venta.timbrado = timbrado_registro.numero
            venta.timbrado_vence = timbrado_registro.fecha_vencimiento
            
            detalles = []
            total_exentas = 0
            total_imponible = 0
            total_factura = 0
            
            for detalle_form in formset.forms:
                if not hasattr(detalle_form, 'cleaned_data'):
                    continue
                if detalle_form.cleaned_data.get('DELETE'):
                    continue
                if not detalle_form.cleaned_data or not detalle_form.cleaned_data.get('producto_detalle'):
                    continue
                detalle, exentas, imponible, factura = _calcular_detalle(detalle_form)
                detalles.append(detalle)
                total_exentas += exentas
                total_imponible += imponible
                total_factura += factura
            
            venta.totalexentas = total_exentas
            venta.totalimponible = total_imponible
            venta.totalbase = total_imponible
            venta.totalfactura = total_factura
            
            print('venta.deposito:', venta.deposito)
            print('venta.cliente:', venta.cliente_id)
            print('venta.moneda:', venta.moneda_id)
            print('venta.tipo_documento:', venta.tipo_documento_id)
            print('venta.plazo:', venta.plazo_id)
            print('venta.timbrado_registro:', venta.timbrado_registro_id)
            
            venta.save()
            print('Venta saved, id=', venta.id)
            
            for detalle in detalles:
                detalle.venta = venta
                print('Saving detalle with producto_detalle:', detalle.producto_detalle_id)
                detalle.save()
            
            _generar_cuentas_cobrar(venta, total_factura, form.cleaned_data)
            print('Cuentas cobrar created')
            
            raise Exception('ROLLBACK_OK')
    except Exception as e:
        if str(e) == 'ROLLBACK_OK':
            print('ALL OK - rolled back')
        else:
            print(f'ERROR: {type(e).__name__}: {e}')
            import traceback
            traceback.print_exc()

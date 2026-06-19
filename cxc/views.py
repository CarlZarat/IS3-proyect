from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Case, CharField, Count, F, Max, Min, Q, Sum, Value, When
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.utils import timezone

from .models import Cobro, CuentaCobrar, Deposito, Plazo, ProductoDetalle, Timbrado, Venta, VentaDetalle
from .forms import VentaForm, VentaDetalleFormSet


def _default_sale_values():
	hoy = timezone.localdate()
	timbrado_registro = Timbrado.objects.filter(estado=Timbrado.ESTADO_VIGENTE).order_by('fecha_vencimiento', 'serie').first()
	serie = timbrado_registro.serie if timbrado_registro else '001-001'
	timbrado = timbrado_registro.numero if timbrado_registro else '12345678'
	timbrado_vence = timbrado_registro.fecha_vencimiento if timbrado_registro else hoy + timedelta(days=365)
	return {
		'fechafactura': hoy,
		'serie': serie,
		'nrofactura': _next_nrofactura(timbrado_registro),
		'timbrado': timbrado,
		'timbrado_vence': timbrado_vence,
		'timbrado_registro': timbrado_registro,
	}


def _plazo_catalog():
	return [
		{
			'id': plazo.id,
			'label': plazo.plazo,
			'irregular': plazo.irregular,
			'cuotas': plazo.cuotas,
		}
		for plazo in Plazo.objects.order_by('plazo')
	]


def _timbrado_catalog():
	return [
		{
			'id': timbrado.id,
			'label': f'{timbrado.numero} - {timbrado.serie}',
			'numero': timbrado.numero,
			'serie': timbrado.serie,
			'fecha_vencimiento': timbrado.fecha_vencimiento.isoformat(),
		}
		for timbrado in Timbrado.objects.filter(estado=Timbrado.ESTADO_VIGENTE).order_by('fecha_vencimiento', 'serie')
	]


def _product_catalog():
	return [
		{
			'id': detalle.pk,
			'label': f'{detalle.producto.producto} - {detalle.codbarra}',
			'iva': float(detalle.producto.iva),
			'precio': float(detalle.producto.precio_venta),
		}
		for detalle in ProductoDetalle.objects.select_related('producto').order_by('producto__producto', 'codbarra')
	]


def _next_nrofactura(timbrado_registro_or_serie):
	if hasattr(timbrado_registro_or_serie, 'nro_inicio'):
		timbrado_registro = timbrado_registro_or_serie
		ultimo_moderno = Venta.objects.filter(timbrado_registro=timbrado_registro).aggregate(maximo=Max('nrofactura'))['maximo']
		ultimo_legacy = Venta.objects.filter(serie=timbrado_registro.serie, timbrado=timbrado_registro.numero).aggregate(maximo=Max('nrofactura'))['maximo']
		ultimo = max([valor for valor in [ultimo_moderno, ultimo_legacy] if valor is not None], default=0)
		return max(ultimo + 1, timbrado_registro.nro_inicio)
	ultimo = Venta.objects.filter(serie=timbrado_registro_or_serie).aggregate(maximo=Max('nrofactura'))['maximo']
	return (ultimo or 0) + 1


def _first_deposito():
	return Deposito.objects.order_by('id').first()


def _calcular_detalle(form):
	detalle = form.save(commit=False)
	precio = Decimal(str(form.cleaned_data['precio'] or 0))
	cantidad = Decimal(str(form.cleaned_data['cantidad'] or 0))
	iva = Decimal(str(detalle.producto_detalle.producto.iva or 0))
	total = (precio * cantidad).quantize(Decimal('0.00001'), rounding=ROUND_HALF_UP)

	if iva == Decimal('5'):
		impuesto5 = (total * Decimal('0.05')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
		impuesto10 = Decimal('0')
		total_exentas = 0
		total_imponible = int(total)
	elif iva == Decimal('10'):
		impuesto5 = Decimal('0')
		impuesto10 = (total * Decimal('0.10')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
		total_exentas = 0
		total_imponible = int(total)
	else:
		impuesto5 = Decimal('0')
		impuesto10 = Decimal('0')
		total_exentas = int(total)
		total_imponible = 0

	detalle.iva = iva
	detalle.precio = precio
	detalle.cantidad = cantidad
	detalle.impuesto5 = impuesto5
	detalle.impuesto10 = impuesto10
	detalle.total = total
	return detalle, total_exentas, total_imponible, int(total.to_integral_value(rounding=ROUND_HALF_UP))


def _generar_cuentas_cobrar(venta, total_factura, cleaned_data):
	if venta.plazo.plazo.upper() == 'CO':
		CuentaCobrar.objects.create(
			tabla='VENTAS',
			venta=venta,
			cuota=1,
			importe=total_factura,
			cobrado=total_factura,
			vence=venta.fechafactura,
		)
		return

	cantidad_cuotas = int(cleaned_data['cantidad_cuotas'])
	tipo_vencimiento = cleaned_data['tipo_vencimiento']
	base, resto = divmod(total_factura, cantidad_cuotas)

	if tipo_vencimiento == 'irregular':
		dias_lista = [int(d.strip()) for d in (cleaned_data.get('dias_irregulares') or '').split(',') if d.strip()]
		for indice, dias in enumerate(dias_lista):
			importe = base + (1 if indice < resto else 0)
			CuentaCobrar.objects.create(
				tabla='VENTAS',
				venta=venta,
				cuota=indice + 1,
				importe=importe,
				cobrado=0,
				vence=venta.fechafactura + timedelta(days=dias),
			)
		return

	dias_entre_cuotas = int(cleaned_data['dias_entre_cuotas'])
	for indice in range(cantidad_cuotas):
		importe = base + (1 if indice < resto else 0)
		CuentaCobrar.objects.create(
			tabla='VENTAS',
			venta=venta,
			cuota=indice + 1,
			importe=importe,
			cobrado=0,
			vence=venta.fechafactura + timedelta(days=dias_entre_cuotas * (indice + 1)),
		)


def _resumen_cuentas_queryset(cliente_q='', factura_q=''):
	cuentas = CuentaCobrar.objects.select_related('venta__cliente', 'venta__plazo')

	if cliente_q:
		cuentas = cuentas.filter(
			Q(venta__cliente__nombre__icontains=cliente_q)
			| Q(venta__cliente__apellido__icontains=cliente_q)
		)
	if factura_q:
		factura_filter = Q(venta__serie__icontains=factura_q)
		if factura_q.isdigit():
			factura_filter |= Q(venta__nrofactura=int(factura_q))
		cuentas = cuentas.filter(factura_filter)

	hoy = date.today()
	return (
		cuentas.values(
			'venta_id',
			'venta__cliente__nombre',
			'venta__cliente__apellido',
			'venta__serie',
			'venta__nrofactura',
			'venta__fechafactura',
			'venta__plazo__plazo',
		)
		.annotate(
			total=Sum('importe'),
			cobrado_total=Sum('cobrado'),
			cuota_count=Count('id'),
			min_vence=Min('vence'),
		)
		.annotate(saldo=F('total') - F('cobrado_total'))
		.annotate(
			estado=Case(
				When(saldo__lte=0, then=Value('cobrada')),
				When(saldo__gt=0, min_vence__lt=hoy, then=Value('vencida')),
				When(saldo__gt=0, cobrado_total__gt=0, then=Value('parcial')),
				default=Value('pendiente'),
				output_field=CharField(),
			)
		)
		.order_by('-venta__fechafactura', '-venta__nrofactura')
	)


def lista_cuentas(request):
	cliente_q = request.GET.get('cliente', '').strip()
	factura_q = request.GET.get('factura', '').strip()
	estado_q = request.GET.get('estado', '').strip().lower()

	resumen = _resumen_cuentas_queryset(cliente_q=cliente_q, factura_q=factura_q)

	if estado_q in {'pendiente', 'parcial', 'cobrada', 'vencida'}:
		resumen = resumen.filter(estado=estado_q)

	paginator = Paginator(resumen, 10)
	page_obj = paginator.get_page(request.GET.get('page'))

	context = {
		'page_obj': page_obj,
		'filtros': {
			'cliente': cliente_q,
			'factura': factura_q,
			'estado': estado_q,
		},
	}
	return render(request, 'cxc/lista_cuentas.html', context)


def dashboard_cxc(request):
	rows = list(_resumen_cuentas_queryset())

	totales_estado = {
		'pendiente': 0,
		'parcial': 0,
		'cobrada': 0,
		'vencida': 0,
	}
	monto_total = 0
	monto_vencido = 0
	monto_saldo_total = 0

	for row in rows:
		estado = row['estado']
		totales_estado[estado] = totales_estado.get(estado, 0) + 1
		monto_total += row['total'] or 0
		monto_saldo_total += row['saldo'] or 0
		if estado == 'vencida':
			monto_vencido += row['saldo'] or 0

	context = {
		'totales_estado': totales_estado,
		'monto_total': monto_total,
		'monto_vencido': monto_vencido,
		'monto_saldo_total': monto_saldo_total,
		'total_cuentas': len(rows),
	}
	return render(request, 'cxc/dashboard.html', context)


def detalle_cuenta(request, venta_id):
	venta = get_object_or_404(
		Venta.objects.select_related('cliente', 'moneda', 'plazo'),
		id=venta_id,
	)
	cuotas = CuentaCobrar.objects.filter(venta_id=venta_id).order_by('cuota')
	total = sum(c.importe for c in cuotas)
	cobrado_total = sum(c.cobrado for c in cuotas)
	saldo_total = total - cobrado_total

	for cuota in cuotas:
		saldo = cuota.importe - cuota.cobrado
		if saldo <= 0:
			cuota.estado = 'cobrada'
		elif cuota.vence < date.today():
			cuota.estado = 'vencida'
		elif cuota.cobrado > 0:
			cuota.estado = 'parcial'
		else:
			cuota.estado = 'pendiente'
		cuota.saldo = saldo

	context = {
		'venta': venta,
		'cuotas': cuotas,
		'total': total,
		'cobrado_total': cobrado_total,
		'saldo_total': saldo_total,
	}
	return render(request, 'cxc/detalle_cuenta.html', context)


def registrar_cobro(request, venta_id, cuota_id):
	if request.method != 'POST':
		return redirect('cxc_detalle_cuenta', venta_id=venta_id)

	cuota = get_object_or_404(CuentaCobrar, id=cuota_id, venta_id=venta_id)
	monto_raw = (request.POST.get('monto') or '').strip()
	referencia = (request.POST.get('referencia') or '').strip()

	if not monto_raw.isdigit():
		messages.error(request, 'El monto debe ser un numero entero sin decimales.')
		return redirect('cxc_detalle_cuenta', venta_id=venta_id)

	monto = int(monto_raw)
	if monto <= 0:
		messages.error(request, 'El monto debe ser mayor a 0.')
		return redirect('cxc_detalle_cuenta', venta_id=venta_id)

	saldo = cuota.importe - cuota.cobrado
	if monto > saldo:
		messages.error(request, f'El monto excede el saldo disponible de la cuota ({saldo}).')
		return redirect('cxc_detalle_cuenta', venta_id=venta_id)

	Cobro.objects.create(
		cuenta=cuota,
		fecha_pago=date.today(),
		monto=monto,
		referencia=referencia,
	)
	cuota.cobrado = cuota.cobrado + monto
	cuota.save(update_fields=['cobrado'])
	messages.success(request, 'Cobro registrado correctamente.')
	return redirect('cxc_detalle_cuenta', venta_id=venta_id)


# ==============================================================================
# NUEVAS VISTAS PARA VENTAS CON DETALLES
# ==============================================================================

def crear_venta(request):
	"""Crear una venta con múltiples detalles de items"""
	sale_defaults = _default_sale_values()
	if request.method == 'POST':
		form = VentaForm(request.POST, sale_defaults=sale_defaults)
		formset = VentaDetalleFormSet(request.POST)
		
		if form.is_valid() and formset.is_valid():
			venta_creada = None
			with transaction.atomic():
				venta = form.save(commit=False)
				venta.fechaproce = timezone.now()
				venta.deposito = _first_deposito()
				if not venta.deposito:
					form.add_error(None, 'No hay depósitos disponibles para asignar a la venta.')
				elif not form.cleaned_data.get('timbrado_registro'):
					form.add_error('timbrado_registro', 'Debes seleccionar un timbrado vigente.')
				else:
					timbrado_registro = form.cleaned_data['timbrado_registro']
					venta.timbrado_registro = timbrado_registro
					venta.serie = timbrado_registro.serie
					venta.nrofactura = _next_nrofactura(timbrado_registro)
					if venta.nrofactura > timbrado_registro.nro_fin:
						form.add_error('nrofactura', f'El timbrado {timbrado_registro.numero} no tiene más números disponibles.')
					else:
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

						if not detalles:
							form.add_error(None, 'Debes agregar al menos un item a la venta.')
						else:
							venta.totalexentas = total_exentas
							venta.totalimponible = total_imponible
							venta.totalbase = total_imponible
							venta.totalfactura = total_factura
							venta.save()
							for detalle in detalles:
								detalle.venta = venta
								detalle.save()
							_generar_cuentas_cobrar(venta, total_factura, form.cleaned_data)
							venta_creada = venta

			if venta_creada:
				messages.success(request, f'Venta {venta_creada.nrofactura} creada exitosamente con {venta_creada.detalles.count()} items.')
				return redirect('cxc_detalle_venta', venta_id=venta_creada.id)
	else:
		form = VentaForm(sale_defaults=sale_defaults)
		formset = VentaDetalleFormSet()
	
	context = {
		'form': form,
		'formset': formset,
		'titulo': 'Crear Nueva Venta',
		'sale_defaults': sale_defaults,
		'plazo_catalog': _plazo_catalog(),
		'product_catalog': _product_catalog(),
		'timbrado_catalog': _timbrado_catalog(),
	}
	return render(request, 'cxc/venta_form.html', context)


def editar_venta(request, venta_id):
	"""Editar una venta existente y sus detalles"""
	venta = get_object_or_404(Venta, id=venta_id)
	
	if request.method == 'POST':
		form = VentaForm(request.POST, instance=venta)
		formset = VentaDetalleFormSet(request.POST, instance=venta)
		
		if form.is_valid() and formset.is_valid():
			with transaction.atomic():
				venta = form.save(commit=False)
				venta.save()
				formset.save()
				messages.success(request, f'Venta {venta.nrofactura} actualizada exitosamente.')
				return redirect('cxc_detalle_venta', venta_id=venta.id)
	else:
		form = VentaForm(instance=venta)
		formset = VentaDetalleFormSet(instance=venta)
	
	context = {
		'form': form,
		'formset': formset,
		'venta': venta,
		'titulo': f'Editar Venta {venta.nrofactura}',
		'plazo_catalog': _plazo_catalog(),
		'product_catalog': _product_catalog(),
		'timbrado_catalog': _timbrado_catalog(),
	}
	return render(request, 'cxc/venta_form.html', context)


def detalle_venta(request, venta_id):
	"""Ver detalles completos de una venta"""
	venta = get_object_or_404(
		Venta.objects.select_related('cliente', 'moneda', 'plazo', 'deposito'),
		id=venta_id
	)
	detalles = venta.detalles.select_related('producto_detalle__producto')
	
	context = {
		'venta': venta,
		'detalles': detalles,
		'total_items': detalles.count(),
	}
	return render(request, 'cxc/detalle_venta_completo.html', context)


def lista_ventas(request):
	"""Listar todas las ventas"""
	cliente_q = request.GET.get('cliente', '').strip()
	fecha_desde = request.GET.get('fecha_desde', '').strip()
	fecha_hasta = request.GET.get('fecha_hasta', '').strip()
	
	ventas = Venta.objects.select_related('cliente', 'moneda').all()
	
	if cliente_q:
		ventas = ventas.filter(
			Q(cliente__nombre__icontains=cliente_q)
			| Q(cliente__apellido__icontains=cliente_q)
		)
	
	if fecha_desde:
		ventas = ventas.filter(fechafactura__gte=fecha_desde)
	
	if fecha_hasta:
		ventas = ventas.filter(fechafactura__lte=fecha_hasta)
	
	ventas = ventas.order_by('-fechafactura', '-nrofactura')
	
	paginator = Paginator(ventas, 20)
	page_obj = paginator.get_page(request.GET.get('page'))
	
	context = {
		'page_obj': page_obj,
		'filtros': {
			'cliente': cliente_q,
			'fecha_desde': fecha_desde,
			'fecha_hasta': fecha_hasta,
		},
	}
	return render(request, 'cxc/lista_ventas.html', context)


def eliminar_venta(request, venta_id):
	"""Eliminar una venta y todos sus detalles"""
	venta = get_object_or_404(Venta, id=venta_id)
	nrofactura = venta.nrofactura
	
	if request.method == 'POST':
		venta.delete()
		messages.success(request, f'Venta {nrofactura} eliminada correctamente.')
		return redirect('cxc_lista_ventas')
	
	context = {'venta': venta}
	return render(request, 'cxc/confirmar_eliminar_venta.html', context)


def api_total_venta(request, venta_id):
	"""API para calcular totales en tiempo real (AJAX)"""
	venta = get_object_or_404(Venta, id=venta_id)
	detalles = venta.detalles.all()
	
	total_cantidad = sum(d.cantidad for d in detalles)
	total_base = sum(d.total for d in detalles)
	total_impuestos = sum(d.impuesto5 + d.impuesto10 for d in detalles)
	total_general = total_base + total_impuestos
	
	return JsonResponse({
		'cantidad_items': detalles.count(),
		'total_cantidad': float(total_cantidad),
		'total_base': float(total_base),
		'total_impuestos': float(total_impuestos),
		'total_general': float(total_general),
	})

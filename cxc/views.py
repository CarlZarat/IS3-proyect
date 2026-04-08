from datetime import date

from django.core.paginator import Paginator
from django.db.models import Case, CharField, Count, F, Min, Q, Sum, Value, When
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse

from .models import Cobro, CuentaCobrar, Venta, VentaDetalle
from .forms import VentaForm, VentaDetalleFormSet


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
	if request.method == 'POST':
		form = VentaForm(request.POST)
		formset = VentaDetalleFormSet(request.POST)
		
		if form.is_valid() and formset.is_valid():
			venta = form.save()
			formset.instance = venta
			formset.save()
			messages.success(request, f'Venta {venta.nrofactura} creada exitosamente con {venta.detalles.count()} items.')
			return redirect('cxc_detalle_venta', venta_id=venta.id)
	else:
		form = VentaForm()
		formset = VentaDetalleFormSet()
	
	context = {
		'form': form,
		'formset': formset,
		'titulo': 'Crear Nueva Venta',
	}
	return render(request, 'cxc/venta_form.html', context)


def editar_venta(request, venta_id):
	"""Editar una venta existente y sus detalles"""
	venta = get_object_or_404(Venta, id=venta_id)
	
	if request.method == 'POST':
		form = VentaForm(request.POST, instance=venta)
		formset = VentaDetalleFormSet(request.POST, instance=venta)
		
		if form.is_valid() and formset.is_valid():
			venta = form.save()
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

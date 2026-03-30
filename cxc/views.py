from datetime import date

from django.core.paginator import Paginator
from django.db.models import Case, CharField, Count, F, Min, Q, Sum, Value, When
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .models import Cobro, CuentaCobrar, Venta


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

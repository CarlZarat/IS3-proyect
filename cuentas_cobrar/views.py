from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CreditoForm
from .models import Credito, Cuota
from datetime import timedelta
from django.db.models import Count, Q

# Create your views here.

def registrar_credito(request):
    if request.method == 'POST':
        form = CreditoForm(request.POST)
        if form.is_valid():
            credito = form.save()
            monto_cuota = credito.monto / credito.cantidad_cuotas
            fecha_vencimiento = credito.fecha_inicio
            dias_vencimiento = form.cleaned_data.get('dias_vencimiento')
            if credito.modalidad == Credito.MODALIDAD_PERSONALIZADA and dias_vencimiento:
                dias = [int(d.strip()) for d in dias_vencimiento.split(',') if d.strip()]
                if len(dias) != credito.cantidad_cuotas:
                    messages.error(request, 'La cantidad de días debe coincidir con la cantidad de cuotas.')
                    credito.delete()
                    return render(request, 'cuentas_cobrar/registrar_credito.html', {'form': form})
                for i, dias_cuota in enumerate(dias):
                    fecha_vencimiento = credito.fecha_inicio + timedelta(days=dias_cuota)
                    Cuota.objects.create(
                        credito=credito,
                        numero=i + 1,
                        importe=monto_cuota,
                        vence=fecha_vencimiento
                    )
            else:
                for i in range(credito.cantidad_cuotas):
                    fecha_vencimiento = credito.fecha_inicio + timedelta(days=30 * (i + 1))
                    Cuota.objects.create(
                        credito=credito,
                        numero=i + 1,
                        importe=monto_cuota,
                        vence=fecha_vencimiento
                    )
            messages.success(request, 'Crédito registrado y cuotas generadas correctamente.')
            return redirect('lista_creditos')
    else:
        form = CreditoForm()
        if not form.fields['venta'].queryset.exists():
            messages.warning(
                request,
                'No hay ventas en modalidad Crédito disponibles. Primero registra una venta CR en el módulo Ventas.',
            )
    return render(request, 'cuentas_cobrar/registrar_credito.html', {'form': form})

def lista_creditos(request):
    creditos = (
        Credito.objects.select_related('cliente', 'venta__factura')
        .annotate(
            total_cuotas=Count('cuotas'),
            cuotas_cobradas=Count('cuotas', filter=Q(cuotas__cobrado=True)),
        )
        .order_by('-id')
    )
    return render(request, 'cuentas_cobrar/lista_creditos.html', {'creditos': creditos})

def detalle_cuotas(request, credito_id):
    credito = Credito.objects.get(id=credito_id)
    cuotas = credito.cuotas.all().order_by('numero')
    return render(request, 'cuentas_cobrar/detalle_cuotas.html', {
        'credito': credito,
        'cuotas': cuotas
    })

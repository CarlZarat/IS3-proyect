from datetime import date

from django.core.management.base import BaseCommand

from cxc.models import CuentaCobrar


class Command(BaseCommand):
    help = 'Ejecuta checks de integridad funcional para CXC.'

    def handle(self, *args, **options):
        errores = []

        for cuota in CuentaCobrar.objects.select_related('venta').all():
            if cuota.cobrado > cuota.importe:
                errores.append(
                    f"Sobrecobro detectado en venta {cuota.venta_id} cuota {cuota.cuota}: "
                    f"cobrado {cuota.cobrado} > importe {cuota.importe}"
                )
            if cuota.importe < 0 or cuota.cobrado < 0:
                errores.append(
                    f"Monto negativo detectado en venta {cuota.venta_id} cuota {cuota.cuota}."
                )

        ventas = {}
        for cuota in CuentaCobrar.objects.values('venta_id', 'importe', 'cobrado'):
            bucket = ventas.setdefault(cuota['venta_id'], {'importe': 0, 'cobrado': 0})
            bucket['importe'] += cuota['importe']
            bucket['cobrado'] += cuota['cobrado']

        for venta_id, data in ventas.items():
            if data['cobrado'] > data['importe']:
                errores.append(
                    f"Saldo inconsistente en venta {venta_id}: cobrado agregado {data['cobrado']} > total {data['importe']}"
                )

        hoy = date.today()
        vencidas = CuentaCobrar.objects.filter(vence__lt=hoy, cobrado__lt=1)
        pendientes = CuentaCobrar.objects.filter(vence__gte=hoy, cobrado=0)

        self.stdout.write(self.style.SUCCESS(f"Cuotas vencidas pendientes: {vencidas.count()}"))
        self.stdout.write(self.style.SUCCESS(f"Cuotas pendientes no vencidas: {pendientes.count()}"))

        if errores:
            self.stdout.write(self.style.ERROR('FALLA: Se encontraron inconsistencias.'))
            for err in errores:
                self.stdout.write(self.style.ERROR(f"- {err}"))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS('OK: Integridad CXC validada.'))

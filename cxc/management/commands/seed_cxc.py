from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from cxc.models import Cliente, CuentaCobrar, Deposito, Moneda, Plazo, TipoDocumento, Venta


class Command(BaseCommand):
    help = 'Carga semillas minimas para CXC (CO y CR regular/irregular).'

    def handle(self, *args, **options):
        CuentaCobrar.objects.all().delete()
        Venta.objects.all().delete()
        Plazo.objects.all().delete()
        TipoDocumento.objects.all().delete()
        Cliente.objects.all().delete()
        Deposito.objects.all().delete()
        Moneda.objects.all().delete()

        moneda = Moneda.objects.create(moneda='Guarani', abreviatura='Gs', decimales=0, activo=True)
        deposito = Deposito.objects.create(deposito='Casa Central', direccion='Asuncion', telefono='0000')
        tipo = TipoDocumento.objects.create(tipo='Factura', abreviatura='FAC', tipoid=1, activo=True)

        plazo_co = Plazo.objects.create(plazo='CO', tipo_documento=tipo, cuotas=1, irregular=False)
        plazo_cr_regular = Plazo.objects.create(plazo='CR-30-60-90 dias', tipo_documento=tipo, cuotas=3, irregular=False)
        plazo_cr_irregular = Plazo.objects.create(plazo='CR-30-45-60 dias', tipo_documento=tipo, cuotas=3, irregular=True)

        c1 = Cliente.objects.create(nombre='Cliente Ejemplo', apellido='S.A.', documento='80011111-1', activo=True)
        c2 = Cliente.objects.create(nombre='Gregorio', apellido='Quintana Gonzalez', documento='80022222-2', activo=True)

        hoy = date.today()

        v1 = Venta.objects.create(
            fechaproce=timezone.now(),
            fechafactura=hoy - timedelta(days=5),
            cliente=c1,
            serie='001-001',
            nrofactura=44686,
            timbrado='12345678',
            totalfactura=120000,
            deposito=deposito,
            moneda=moneda,
            tipo_documento=tipo,
            plazo=plazo_co,
        )
        CuentaCobrar.objects.create(tabla='VENTAS', venta=v1, cuota=1, importe=120000, cobrado=120000, vence=hoy - timedelta(days=5))

        v2 = Venta.objects.create(
            fechaproce=timezone.now(),
            fechafactura=hoy,
            cliente=c1,
            serie='001-001',
            nrofactura=44685,
            timbrado='12345678',
            totalfactura=600000,
            deposito=deposito,
            moneda=moneda,
            tipo_documento=tipo,
            plazo=plazo_cr_regular,
        )
        CuentaCobrar.objects.create(tabla='VENTAS', venta=v2, cuota=1, importe=200000, cobrado=0, vence=hoy + timedelta(days=30))
        CuentaCobrar.objects.create(tabla='VENTAS', venta=v2, cuota=2, importe=200000, cobrado=0, vence=hoy + timedelta(days=60))
        CuentaCobrar.objects.create(tabla='VENTAS', venta=v2, cuota=3, importe=200000, cobrado=0, vence=hoy + timedelta(days=90))

        v3 = Venta.objects.create(
            fechaproce=timezone.now(),
            fechafactura=hoy - timedelta(days=10),
            cliente=c2,
            serie='001-001',
            nrofactura=44687,
            timbrado='12345678',
            totalfactura=584226,
            deposito=deposito,
            moneda=moneda,
            tipo_documento=tipo,
            plazo=plazo_cr_irregular,
        )
        CuentaCobrar.objects.create(tabla='VENTAS', venta=v3, cuota=1, importe=194742, cobrado=100000, vence=hoy + timedelta(days=20))
        CuentaCobrar.objects.create(tabla='VENTAS', venta=v3, cuota=2, importe=194742, cobrado=0, vence=hoy + timedelta(days=45))
        CuentaCobrar.objects.create(tabla='VENTAS', venta=v3, cuota=3, importe=194742, cobrado=0, vence=hoy + timedelta(days=60))

        v4 = Venta.objects.create(
            fechaproce=timezone.now(),
            fechafactura=hoy - timedelta(days=40),
            cliente=c2,
            serie='001-001',
            nrofactura=44688,
            timbrado='12345678',
            totalfactura=300000,
            deposito=deposito,
            moneda=moneda,
            tipo_documento=tipo,
            plazo=plazo_cr_regular,
        )
        CuentaCobrar.objects.create(tabla='VENTAS', venta=v4, cuota=1, importe=150000, cobrado=0, vence=hoy - timedelta(days=10))
        CuentaCobrar.objects.create(tabla='VENTAS', venta=v4, cuota=2, importe=150000, cobrado=0, vence=hoy + timedelta(days=20))

        self.stdout.write(self.style.SUCCESS('Semillas CXC cargadas correctamente.'))

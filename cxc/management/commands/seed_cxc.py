from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from cxc.models import Cliente, CuentaCobrar, Deposito, Moneda, Plazo, Producto, ProductoDetalle, Timbrado, TipoDocumento, Venta


class Command(BaseCommand):
    help = 'Carga semillas minimas para CXC (CO y CR regular/irregular).'

    def handle(self, *args, **options):
        CuentaCobrar.objects.all().delete()
        Venta.objects.all().delete()
        Plazo.objects.all().delete()
        Timbrado.objects.all().delete()
        TipoDocumento.objects.all().delete()
        ProductoDetalle.objects.all().delete()
        Producto.objects.all().delete()
        Deposito.objects.all().delete()
        Moneda.objects.all().delete()

        hoy = date.today()
        moneda = Moneda.objects.create(moneda='Guarani', abreviatura='Gs', decimales=0, activo=True)
        deposito = Deposito.objects.create(deposito='Casa Central', direccion='Asuncion', telefono='0000')
        tipo = TipoDocumento.objects.create(tipo='Factura', abreviatura='FAC', tipoid=1, activo=True)
        timbrado = Timbrado.objects.create(
            numero='12345678',
            serie='001-001',
            nro_inicio=44685,
            nro_fin=44699,
            fecha_vencimiento=hoy + timedelta(days=365),
            estado=Timbrado.ESTADO_VIGENTE,
        )

        plazo_co = Plazo.objects.create(plazo='CO', tipo_documento=tipo, cuotas=1, irregular=False)
        plazo_cr_regular = Plazo.objects.create(plazo='CR-30-60-90 dias', tipo_documento=tipo, cuotas=3, irregular=False)
        plazo_cr_irregular = Plazo.objects.create(plazo='CR-30-45-60 dias', tipo_documento=tipo, cuotas=3, irregular=True)

        producto_10 = Producto.objects.create(producto='Producto A', iva=10, precio_venta=5000000, servicio=False)
        producto_5 = Producto.objects.create(producto='Producto B', iva=5, precio_venta=2500000, servicio=False)
        producto_exento = Producto.objects.create(producto='Producto C', iva=0, precio_venta=1000000, servicio=False)

        ProductoDetalle.objects.create(codbarra='P10-001', producto=producto_10, colorid=None, tamanoid=None, disenoid=None, uxb=None)
        ProductoDetalle.objects.create(codbarra='P05-001', producto=producto_5, colorid=None, tamanoid=None, disenoid=None, uxb=None)
        ProductoDetalle.objects.create(codbarra='PEX-001', producto=producto_exento, colorid=None, tamanoid=None, disenoid=None, uxb=None)

        c1, _ = Cliente.objects.get_or_create(
            documento='80011111-1',
            defaults={'nombre': 'Cliente Ejemplo', 'apellido': 'S.A.', 'activo': True},
        )
        c2, _ = Cliente.objects.get_or_create(
            documento='80022222-2',
            defaults={'nombre': 'Gregorio', 'apellido': 'Quintana Gonzalez', 'activo': True},
        )

        v1 = Venta.objects.create(
            fechaproce=timezone.now(),
            fechafactura=hoy - timedelta(days=5),
            cliente=c1,
            timbrado_registro=timbrado,
            serie='001-001',
            nrofactura=44686,
            timbrado=timbrado.numero,
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
            timbrado_registro=timbrado,
            serie='001-001',
            nrofactura=44685,
            timbrado=timbrado.numero,
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
            timbrado_registro=timbrado,
            serie='001-001',
            nrofactura=44687,
            timbrado=timbrado.numero,
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
            timbrado_registro=timbrado,
            serie='001-001',
            nrofactura=44688,
            timbrado=timbrado.numero,
            totalfactura=300000,
            deposito=deposito,
            moneda=moneda,
            tipo_documento=tipo,
            plazo=plazo_cr_regular,
        )
        CuentaCobrar.objects.create(tabla='VENTAS', venta=v4, cuota=1, importe=150000, cobrado=0, vence=hoy - timedelta(days=10))
        CuentaCobrar.objects.create(tabla='VENTAS', venta=v4, cuota=2, importe=150000, cobrado=0, vence=hoy + timedelta(days=20))

        self.stdout.write(self.style.SUCCESS('Semillas CXC cargadas correctamente.'))

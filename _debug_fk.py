import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'gqc_system.settings'
os.chdir(os.path.dirname(os.path.abspath(__file__)))
django.setup()
from cxc.models import *
from django.db import connection
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

# Check FK
cursor = connection.cursor()
cursor.execute("PRAGMA foreign_key_list(VENTAS)")
print('VENTAS FK:')
for row in cursor.fetchall():
    print(' ', row)

cursor.execute("PRAGMA foreign_key_list(VENTA_DETALLES)")
print('VENTA_DETALLES FK:')
for row in cursor.fetchall():
    print(' ', row)

cursor.execute("PRAGMA foreign_key_list(CUENTAS_COBRAR)")
print('CUENTAS_COBRAR FK:')
for row in cursor.fetchall():
    print(' ', row)

# Check Venta model's FK fields
from django.db import models as dm
for f in Venta._meta.get_fields():
    if isinstance(f, dm.ForeignKey):
        print(f"Venta FK: {f.name} -> {f.remote_field.model.__name__} (db_column={f.column})")

for f in VentaDetalle._meta.get_fields():
    if isinstance(f, dm.ForeignKey):
        print(f"VentaDetalle FK: {f.name} -> {f.remote_field.model.__name__} (db_column={f.column})")

# Test creating a venta directly
cliente = Cliente.objects.get(id=4)
timbrado = Timbrado.objects.get(id=1)
moneda = Moneda.objects.get(id=3)
tipodoc = TipoDocumento.objects.get(id=3)
plazo = Plazo.objects.get(id=7)
deposito = Deposito.objects.get(id=3)
productodet = ProductoDetalle.objects.get(codbarra='P10-001')

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

try:
    with transaction.atomic():
        ultimo = Venta.objects.filter(timbrado_registro=timbrado).aggregate(maximo=Max('nrofactura'))['maximo'] or 0
        nro = max(ultimo + 1, timbrado.nro_inicio)
        v = Venta(
            fechaproce=timezone.now(),
            fechafactura=date.today(),
            cliente=cliente,
            timbrado_registro=timbrado,
            serie=timbrado.serie,
            nrofactura=nro,
            timbrado=timbrado.numero,
            timbrado_vence=timbrado.fecha_vencimiento,
            totalexentas=0,
            totalimponible=5000000,
            totalbase=5000000,
            totalfactura=5000000,
            deposito=deposito,
            moneda=moneda,
            tipo_documento=tipodoc,
            plazo=plazo,
        )
        v.save()
        print(f'Venta saved with id={v.id}')
        
        # Now create detail
        d = VentaDetalle(
            venta=v,
            producto_detalle=productodet,
            precio=Decimal('5000000'),
            cantidad=Decimal('1'),
            iva=Decimal('10'),
            impuesto5=Decimal('0'),
            impuesto10=Decimal('500000'),
            total=Decimal('5000000'),
        )
        d.save()
        print('Detalle saved')
        
        # Create cuenta
        cc = CuentaCobrar(
            tabla='VENTAS',
            venta=v,
            cuota=1,
            importe=5000000,
            cobrado=5000000,
            vence=date.today(),
        )
        cc.save()
        print('CuentaCobrar saved')
        
        raise Exception('ROLLBACK')
except Exception as e:
    if str(e) == 'ROLLBACK':
        print('All saves OK (rolled back)')
    else:
        print(f'ERROR: {e}')

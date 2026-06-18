import os
import sys
import pathlib
import django

# Asegurar que la raíz del proyecto esté en sys.path (permite importar gqc_system)
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gqc_system.settings')
django.setup()

from cxc.models import Cliente as CxcCliente
from clientes.models import Cliente as ClientesCliente

print('cxc.Cliente count:', CxcCliente.objects.count())
print('clientes.Cliente count:', ClientesCliente.objects.count())

print('\nAlgunos clientes desde cxc.Cliente:')
for c in CxcCliente.objects.all()[:5]:
    print('-', str(c))

print('\nAlgunos clientes desde clientes.Cliente:')
for c in ClientesCliente.objects.all()[:5]:
    print('-', str(c))

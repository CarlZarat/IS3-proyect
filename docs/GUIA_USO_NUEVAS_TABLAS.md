# Guía: Uso de las Nuevas Tablas en el Sistema

## 📋 Introducción

Las nuevas tablas implementadas permiten un desglose completo de las ventas y mejor gestión del catálogo de productos.

---

## 🎯 Flujo Principal Actualizado

### FLUJO ANTERIOR (INCOMPLETO):
```
VENTA (cxc)
  ├─ Cliente
  ├─ Moneda
  ├─ Deposito
  └─ Plazo
     └─ Totales (pero SIN detalles de items)
```

### NUEVO FLUJO (COMPLETO):
```
EMPRESA
  └─ MONEDA

PRODUCTO
  └─ PRODUCTO_DETALLE (variantes por código de barras)
     └─ Color, Tamaño, Diseño

CLIENTE
  └─ VENTA
     ├─ Cliente FK
     ├─ Moneda FK
     ├─ Deposito FK
     ├─ Plazo FK
     ├─ Totales resumidos
     └─ VENTA_DETALLES ✨ (NUEVO)
        └─ Para cada item:
           ├─ ProductoDetalle FK
           ├─ Precio unitario
           ├─ Cantidad
           ├─ IVA
           ├─ Impuestos (5%, 10%)
           └─ Total del item

PLAZO
  └─ PLAZO_DETALLE (vencimiento por cuota)
     ├─ Número de cuota
     └─ Días de vencimiento

VENTA → CUENTA_COBRAR (créditos)
  └─ COBRO
```

---

## 💾 Ejemplos de Uso en Código

### 1. Crear una Venta Completa

```python
from cxc.models import Venta, VentaDetalle, Cliente, ProductoDetalle, Deposito, Moneda, Plazo

# Obtener o crear datos previos
cliente = Cliente.objects.get(id=1)
deposito = Deposito.objects.get(id=1)
moneda = Moneda.objects.get(abreviatura='Gs.')
plazo = Plazo.objects.get(plazo='30 días')

# Crear la venta principal
venta = Venta.objects.create(
    fechaproce=timezone.now(),
    fechafactura=timezone.now().date(),
    cliente=cliente,
    serie='001',
    nrofactura=2024001,
    timbrado='98765432',
    totalexentas=0,
    totalimponible=100000,
    totalbase=100000,
    totalfactura=110000,  # Con impuestos
    deposito=deposito,
    moneda=moneda,
    plazo=plazo
)

# Crear detalles de la venta
# Item 1
pd1 = ProductoDetalle.objects.get(codbarra='001-BLUE-M')
VentaDetalle.objects.create(
    venta=venta,
    producto_detalle=pd1,
    precio=50000,  # Precio unitario
    cantidad=1,
    iva=10,
    impuesto5=0,
    impuesto10=10000,
    total=60000
)

# Item 2
pd2 = ProductoDetalle.objects.get(codbarra='002-RED-L')
VentaDetalle.objects.create(
    venta=venta,
    producto_detalle=pd2,
    precio=50000,
    cantidad=1,
    iva=10,
    impuesto5=0,
    impuesto10=10000,
    total=60000
)

print(f"Venta {venta} creada con {venta.detalles.count()} items")
```

### 2. Obtener Detalles de una Venta

```python
# Obtener venta
venta = Venta.objects.get(id=1)

# Ver todos los detalles
for detalle in venta.detalles.all():
    print(f"Producto: {detalle.producto_detalle.producto.producto}")
    print(f"Código: {detalle.producto_detalle.codbarra}")
    print(f"Cantidad: {detalle.cantidad}")
    print(f"Precio unitario: {detalle.precio}")
    print(f"Total: {detalle.total}")
    print("---")

# Calcular totales
total_items = venta.detalles.count()
total_cantidad = sum(d.cantidad for d in venta.detalles.all())
total_venta = sum(d.total for d in venta.detalles.all())

print(f"\nTotal items: {total_items}")
print(f"Cantidad total: {total_cantidad}")
print(f"Total venta: {total_venta}")
```

### 3. Crear Productos y Variantes

```python
from cxc.models import Producto, ProductoDetalle

# Crear un producto base
producto = Producto.objects.create(
    producto='Remera básica',
    iva=10,
    servicio=False
)

# Crear variantes (por código de barras)
ProductoDetalle.objects.create(
    codbarra='001-BLUE-S',
    producto=producto,
    colorid=1,  # Blue
    tamanoid=1, # Small
    uxb=12      # 12 piezas por bulto
)

ProductoDetalle.objects.create(
    codbarra='001-BLUE-M',
    producto=producto,
    colorid=1,  # Blue
    tamanoid=2, # Medium
    uxb=12
)

ProductoDetalle.objects.create(
    codbarra='001-RED-S',
    producto=producto,
    colorid=2,  # Red
    tamanoid=1, # Small
    uxb=12
)

print(f"Producto '{producto}' creado con {producto.detalles.count()} variantes")
```

### 4. Obtener Reporte de Venta por Cliente

```python
from cxc.models import Venta
from django.db.models import Sum, Count

cliente = Cliente.objects.get(id=1)

# Ventas del cliente
ventas = Venta.objects.filter(cliente=cliente)

for venta in ventas:
    detalles = venta.detalles.all()
    print(f"\n=== Venta {venta.nrofactura} ===")
    print(f"Fecha: {venta.fechafactura}")
    print(f"Total: {venta.totalfactura}")
    print(f"Cantidad de items: {detalles.count()}")
    
    for det in detalles:
        print(f"  - {det.producto_detalle.producto.producto} ({det.producto_detalle.codbarra})")
        print(f"    Qty: {det.cantidad} x {det.precio} = {det.total}")
```

### 5. Definir Vencimientos en Plazos

```python
from cxc.models import Plazo, PlazoDetalle

# Crear un plazo de 90 días en 3 cuotas
plazo = Plazo.objects.create(
    plazo='90 días (3 cuotas)',
    tipo_documento=tipo_doc,
    cuotas=3,
    irregular=False
)

# Definir vencimiento para cada cuota
PlazoDetalle.objects.create(
    plazo=plazo,
    cuota=1,
    dias=30   # Primera cuota a 30 días
)

PlazoDetalle.objects.create(
    plazo=plazo,
    cuota=2,
    dias=60   # Segunda cuota a 60 días
)

PlazoDetalle.objects.create(
    plazo=plazo,
    cuota=3,
    dias=90   # Tercera cuota a 90 días
)

print(f"Plazo '{plazo}' creado con detalles de vencimiento")
```

---

## 📊 Consultas Útiles

### Consulta 1: Total vendido por producto

```python
from django.db.models import Sum, F

ventas_por_producto = VentaDetalle.objects.values(
    'producto_detalle__producto__producto'
).annotate(
    total_cantidad=Sum('cantidad'),
    total_venta=Sum('total')
).order_by('-total_venta')

for item in ventas_por_producto:
    print(f"{item['producto_detalle__producto__producto']}")
    print(f"  Cantidad: {item['total_cantidad']}")
    print(f"  Total: {item['total_venta']}")
```

### Consulta 2: Productos más vendidos en mes

```python
from django.db.models import Sum, Q
from datetime import date, timedelta

hace_30_dias = date.today() - timedelta(days=30)

top_productos = VentaDetalle.objects.filter(
    venta__fechafactura__gte=hace_30_dias
).values('producto_detalle__producto__producto').annotate(
    total_vendido=Sum('cantidad')
).order_by('-total_vendido')[:10]

for item in top_productos:
    print(f"{item['producto_detalle__producto__producto']}: {item['total_vendido']} unidades")
```

### Consulta 3: Ingresos por cliente en fecha

```python
from django.db.models import Sum

cliente = Cliente.objects.get(id=1)
fecha_inicio = date(2024, 1, 1)
fecha_fin = date(2024, 12, 31)

ingresos = Venta.objects.filter(
    cliente=cliente,
    fechafactura__range=[fecha_inicio, fecha_fin]
).aggregate(
    total=Sum('totalfactura'),
    cantidad_ventas=Count('id')
)

print(f"Cliente: {cliente.nombre}")
print(f"Período: {fecha_inicio} a {fecha_fin}")
print(f"Total ingresos: {ingresos['total']}")
print(f"Cantidad de ventas: {ingresos['cantidad_ventas']}")
```

---

## 🔄 ForeignKey Reference Visualization

```
Cliente
  │
  └─ Venta (One-to-Many)
      │
      ├─ VentaDetalle (One-to-Many) ✨ NUEVO
      │   │
      │   └─ ProductoDetalle (FK)
      │       │
      │       └─ Producto (FK)
      │
      ├─ CuentaCobrar (One-to-Many) 
      │   │
      │   └─ Cobro (One-to-Many)
      │
      └─ Related to:
          ├─ Moneda
          ├─ Deposito
          └─ Plazo
              └─ PlazoDetalle (One-to-Many) ✨ NUEVO
```

---

## ⚙️ Vista/Formulario Recomendado (Ejemplo)

```python
# views.py
from django.shortcuts import render, redirect
from django.forms import inlineformset_factory
from .models import Venta, VentaDetalle
from .forms import VentaForm, VentaDetalleForm

# Crear un formset para VentaDetalle
VentaDetalleFormSet = inlineformset_factory(
    Venta,
    VentaDetalle,
    form=VentaDetalleForm,
    extra=3,  # 3 items por defecto
    can_delete=True
)

def crear_venta(request):
    if request.method == 'POST':
        form = VentaForm(request.POST)
        formset = VentaDetalleFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            venta = form.save()
            formset.instance = venta
            formset.save()
            
            return redirect('venta_detalle', pk=venta.id)
    else:
        form = VentaForm()
        formset = VentaDetalleFormSet()
    
    context = {
        'form': form,
        'formset': formset,
    }
    return render(request, 'venta_form.html', context)
```

```html
<!-- templates/venta_form.html -->
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    
    <h2>Detalles de la venta</h2>
    {{ formset.management_form }}
    
    {% for form in formset.forms %}
        <div class="item">
            {{ form.producto_detalle }}
            {{ form.cantidad }}
            {{ form.precio }}
            {{ form.total }}
            {{ form.DELETE }}
        </div>
    {% endfor %}
    
    <button type="submit">Guardar Venta</button>
</form>
```

---

## ✅ Checklist para Implementación

- [ ] Crear vistas para VENTA_DETALLE
- [ ] Crear formularios para VENTA_DETALLE
- [ ] Crear vistas para PRODUCTO
- [ ] Crear vistas para PRODUCTO_DETALLE
- [ ] Actualizar formularios de Venta para usar VentaDetalle
- [ ] Crear reportes con desglose por producto
- [ ] Crear reportes por cliente
- [ ] Actualizar Admin de Django
- [ ] Testing de flujo completo
- [ ] Migración de datos históricos (si aplica)

---

## 🔗 Documentación Relacionada

- [ESTRUCTURA_BASE_DATOS.md](ESTRUCTURA_BASE_DATOS.md) - DER completo
- [IMPLEMENTACION_TABLAS_NUEVAS.md](IMPLEMENTACION_TABLAS_NUEVAS.md) - Detalles técnicos de migraciones
- [ANALISIS_TABLAS_FALTANTES.md](ANALISIS_TABLAS_FALTANTES.md) - Comparación antes/después

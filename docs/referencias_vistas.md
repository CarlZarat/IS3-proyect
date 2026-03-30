# Referencias de vistas (capturas)

Estado: linea base validada para guiar rediseño de UI/UX y flujo de cuentas a cobrar.

## Vista A: Cuentas a cobrar (lista)
Objetivo:
- Buscar y filtrar cuentas por cobrar.
- Ver estado y saldo.
- Ejecutar acciones por fila.

Elementos observados:
- Tabs superiores:
  - Cuentas a cobrar
  - Detalle factura + cuotas
  - Facturacion - Seleccionar plazo
  - Dashboard
- Filtros:
  - Cliente (texto)
  - Factura (texto)
  - Estado (select)
  - Botones Buscar y Limpiar
- Tabla principal:
  - Columnas: Cliente, Factura, Fecha, Plazo, Total, Saldo, Estado, Acciones
  - Acciones por fila: Ver detalle, Registrar cobro
- Paginacion:
  - Primero, Anterior, Pagina x de y, Siguiente, Ultimo

Reglas validadas para MVP:
- Estado derivado por saldo:
  - Cobrada si saldo = 0
  - Pendiente si saldo > 0 y no vencida
  - Vencida si existe saldo > 0 y fecha de vencimiento superada
- Disponibilidad de acciones:
  - Registrar cobro visible solo si hay saldo pendiente

## Vista B: Detalle factura + cuotas
Objetivo:
- Mostrar cabecera de la cuenta (cliente/factura/fecha/moneda/plazo).
- Listar cuotas y estado de cobro.
- Disparar registro de cobro.

Elementos observados:
- Cabecera:
  - Cliente
  - Factura
  - Fecha
  - Moneda
  - Cuotas (ejemplo de plan: CR-30-45-60 dias)
- Tabla de cuotas:
  - Columnas: Cuota, Importe, Vence, Cobrado
  - Filas tipo: 1/3, 2/3, 3/3
- Acciones:
  - Registrar cobro
  - Volver al listado

Reglas validadas para MVP:
- Orden de cuotas por numero ascendente.
- Campo cobrado por cuota en monto acumulado (inicia en 0).
- Validar que el saldo total sea consistente con suma de cuotas pendientes.
- Criterio de vencida por fecha (si hoy > fecha de vencimiento y saldo > 0).

## Reglas de modalidad (requerimiento formal)
- CO (Contado):
  - Cuenta unica.
  - Cancelada en la misma fecha de la factura.
- CR (Credito):
  - Permite multiples cuotas.
  - Dos formas de vencimiento:
    - Regular: mensual desde la fecha de la factura (ejemplo: CR-30-60-90).
    - Irregular: dias personalizados por cuota (ejemplo: CR-30-45-60).

## Decisiones cerradas
- Reinicio de BD para rediseño: SI.
- Estado intermedio Parcial: SI (a nivel cuenta y cuota).
- Criterio de vencida: por fecha y saldo.
- Dashboard: incluir totales por estado, vencidos y monto total (segun capturas).
- Auditoria de operaciones: SI.

## Nota sobre activos visuales
Las capturas estan tomadas como referencia funcional en este documento.
Si quieres conservarlas como archivos del repositorio, podemos agregarlas luego en una carpeta docs/mockups/ (por ejemplo: cuentas-lista.png y detalle-cuotas.png).

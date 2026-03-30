# Plan Fase 4 - Vertical 1 (Lista de cuentas y filtros)

Alcance: primer vertical implementable sobre el esquema ER aprobado, enfocado en consulta y estado de cuentas por cobrar.

## Objetivo del vertical
- Entregar pantalla Lista de cuentas a cobrar con filtros y acciones basicas.
- Garantizar consistencia de estados y montos para consulta operativa.

## Entradas aprobadas
- Diagrama ER oficial (tablas y relaciones definidas en Fase 3).
- Redondeo entero sin decimales.
- Estado vencida por fecha y saldo.

## Entidades que intervienen en Vertical 1
- CLIENTES
- VENTAS
- PLAZOS
- CUENTAS_COBRAR

## Campos minimos a exponer en la vista
- Cliente
- Factura (serie + nrofactura)
- Fecha
- Plazo
- Total
- Saldo
- Estado
- Acciones: Ver detalle, Registrar cobro

## Filtros funcionales
- Cliente (texto)
- Factura (texto)
- Estado (pendiente, parcial, cobrada, vencida)
- Paginacion de resultados

## Reglas operativas del vertical
- Estado cobrada: saldo = 0.
- Estado vencida: saldo > 0 y fecha de vencimiento menor a hoy.
- Estado parcial: saldo > 0 y cobrado acumulado > 0.
- Estado pendiente: saldo > 0 y cobrado acumulado = 0 y no vencida.

## Orden de implementacion recomendado
1. Esquema
- Confirmar tablas y claves foraneas necesarias para consulta.

2. Capa de datos
- Definir consulta principal para listado (join CLIENTES, VENTAS, PLAZOS, CUENTAS_COBRAR).
- Definir orden por fecha descendente y paginacion.

3. Capa de aplicacion
- Endpoint/listado con filtros.
- Mapeo de estado calculado o persistido segun decision tecnica.

4. Capa de interfaz
- Tabla y barra de filtros conforme mockup aprobado.
- Acciones visibles segun estado/saldo.

5. Pruebas
- Caso CO cobrada.
- Caso CR pendiente.
- Caso CR parcial.
- Caso vencida por fecha.

## Datos semilla minimos para este vertical
- 2 clientes.
- 2 ventas CO.
- 2 ventas CR (1 regular, 1 irregular).
- Cuentas en estados distintos para validar filtros.

## Definition of Done del Vertical 1
- El listado filtra por cliente, factura y estado.
- La paginacion funciona.
- Los estados mostrados son consistentes con reglas de negocio.
- Los montos se muestran sin decimales.
- Las acciones por fila respetan el estado/saldo.

## Riesgos y mitigacion
- Riesgo: estado inconsistente por fuente de datos mixta.
- Mitigacion: una sola fuente de verdad para estado (persistido o calculado), no ambas.

- Riesgo: consulta lenta por joins.
- Mitigacion: indices en clienteid, nrofactura, estado, fecha, vence.

## Checklist de salida
- [x] Consulta principal validada.
- [x] Filtros y paginacion validados.
- [x] Estados validados con casos de prueba.
- [x] Formato de montos sin decimales validado.
- [x] Acciones por fila validadas.

## Estado actualizado
- Vertical 1: CERRADO.
- Vertical 2 (detalle): CERRADO.
- Vertical 3 (registrar cobro): CERRADO.
- Vertical 4 (dashboard): EN PROGRESO.

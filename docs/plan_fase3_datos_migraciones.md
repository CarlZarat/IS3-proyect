# Plan Fase 3 - Datos, migraciones y rollback (Opcion 1)

Alcance: ejecutar una transicion segura desde el dominio actual hacia el nuevo dominio, con reinicio de base de datos y controles de regresion.

## Objetivo de Fase 3
- Preparar el esquema objetivo para implementacion por verticales.
- Definir orden de migraciones con rollback controlado.
- Establecer estrategia de pruebas de integridad de datos.
- Dejar especificado el paquete de triggers a implementar en fase tecnica.

## Decisiones de entrada (ya confirmadas)
- Reinicio de BD para rediseño: SI.
- Redondeo monetario: sin decimales, entero redondeado, sin punto flotante.
- Estado vencida: por fecha y saldo pendiente.
- Auditoria minima: SI.
- Dashboard MVP: total por estado, total vencido, monto total.
- Esquema objetivo: el diagrama ER aprobado por cliente pasa a ser la fuente oficial para tablas y relaciones.

## Esquema objetivo aprobado (segun diagrama)
Tablas aprobadas:
- EMPRESAS
- MONEDAS
- CLIENTES
- DEPOSITOS
- TIPOS_DOCUMENTO
- PLAZOS
- PLAZO_DETALLES
- PRODUCTOS
- PRODUCTO_DETALLE
- VENTAS
- VENTA_DETALLES
- CUENTAS_COBRAR

Relaciones clave aprobadas:
- EMPRESAS.monedaid -> MONEDAS.id
- VENTAS.clienteid -> CLIENTES.id
- VENTAS.depositoid -> DEPOSITOS.id
- VENTAS.monedaid -> MONEDAS.id
- VENTAS.tipodocid -> TIPOS_DOCUMENTO.id
- VENTAS.plazoid -> PLAZOS.id
- VENTA_DETALLES.ventaid -> VENTAS.id
- VENTA_DETALLES.codbarra -> PRODUCTO_DETALLE.codbarra
- PRODUCTO_DETALLE.productoid -> PRODUCTOS.id
- PLAZO_DETALLES.plazoid -> PLAZOS.id
- CUENTAS_COBRAR.tablaid -> VENTAS.id (tabla origen parametrizable via campo tabla)

Nota de alcance:
- El modelo CuentaPorCobrar/Cuota/Cobro se implementa sobre estas tablas aprobadas, sin contradecir el diagrama.
- Los nombres finales de modelos Django pueden usar convencion Pythonica, conservando mapeo explicito a tablas legacy del diagrama.

## Estrategia de transicion de datos
- Tipo de transicion: reset controlado (sin migrar historico viejo).
- Entorno objetivo inicial: desarrollo y prueba.
- Politica de semillas:
  - Cargar datos de prueba minimos para validar casos CO y CR.
  - Incluir un caso CR regular y un caso CR irregular.

## Orden de migraciones recomendado
1. Migracion 00_base
- Crear tablas base comunes y catalogos necesarios.
- Crear columnas de auditoria estandar.

2. Migracion 01_nucleo_comercial
- MONEDAS, EMPRESAS
- CLIENTES, DEPOSITOS
- TIPOS_DOCUMENTO

3. Migracion 02_cuentas
- PLAZOS, PLAZO_DETALLES
- VENTAS
- CUENTAS_COBRAR

4. Migracion 03_cobros
- PRODUCTOS, PRODUCTO_DETALLE
- VENTA_DETALLES
- indices de consulta operativa (cliente, factura, estado, vence)

5. Migracion 04_integridad
- constraints de negocio
- checks de dominio de estados/modalidad

6. Migracion 05_triggers
- trigger de cobro
- trigger de generacion de cuotas
- trigger de detalle de talonarios

7. Migracion 06_semillas_prueba
- datos iniciales controlados para smoke test

## Reglas de rollback por etapa
- Si falla 00 o 01:
  - revertir inmediatamente a estado vacio.
- Si falla 02 o 03:
  - rollback a ultima migracion estable y revalidar constraints.
- Si falla 04:
  - desactivar constraint agregado y rehacer en rama de correccion.
- Si falla 05:
  - mantener esquema sin triggers, corregir logica y reintentar.
- Si falla 06:
  - limpiar semillas y cargar paquete corregido.

## Catalogo de triggers (diseno funcional)
1. Trigger de cobro
- Evento: insercion de cobro.
- Objetivo:
  - actualizar cuota (cobrado, saldo, estado).
  - actualizar cuenta_cobrar (saldo agregado, estado).
- Validaciones:
  - no sobrecobro.
  - consistencia de saldo.
  - vencida por fecha y saldo.

2. Trigger de generacion de cuotas
- Evento: insercion/confirmacion de documento en modalidad CR.
- Objetivo:
  - generar registros en CUENTAS_COBRAR segun plan regular o irregular.
  - asignar importes enteros redondeados.
  - ajustar diferencia de redondeo en la ultima cuota.
- Validaciones:
  - cantidad de cuotas consistente con plan.
  - suma de cuotas igual al total del documento.

3. Trigger de detalle de talonarios
- Evento: alta de cabecera de talonario/documento.
- Objetivo:
  - generar detalle asociado segun regla de negocio definida.
  - garantizar correlatividad y consistencia de cabecera-detalle.
- Validaciones:
  - no duplicidad de rangos.
  - alineacion de cantidad/rango con la cabecera.

4. Trigger de detalle de venta (alineado al diagrama)
- Evento: insercion de VENTA_DETALLES.
- Objetivo:
  - recalcular totales de VENTAS (exentas, IVA, total final).
  - validar integridad con PRODUCTO_DETALLE/PRODUCTOS.
- Validaciones:
  - no permitir detalle con codbarra inexistente.
  - mantener coherencia de impuestos y total.

## Matriz de riesgos de Fase 3
- Riesgo: inconsistencia por redondeo en cuotas.
- Mitigacion: ajustar residuo en la ultima cuota y validar suma exacta.

- Riesgo: estados incorrectos despues de cobros parciales.
- Mitigacion: recalculo transaccional cuota-cuenta en trigger de cobro.

- Riesgo: bloqueo operativo por trigger defectuoso.
- Mitigacion: despliegue progresivo de triggers y plan de rollback por migracion.

- Riesgo: desalineacion entre cabecera y detalle de talonarios.
- Mitigacion: trigger dedicado + constraint de integridad referencial.

## Criterios de aceptacion de Fase 3
- Existe plan de migraciones versionado y secuencial.
- Existe plan de rollback por cada bloque de migracion.
- Existe especificacion de triggers (cobro, cuotas, talonario).
- Existen semillas de prueba para CO y CR regular/irregular.
- Se valida redondeo entero sin decimales en todos los montos operativos.

## Lista de verificacion de salida
- [x] Orden de migraciones aprobado.
- [x] Politica de rollback aprobada.
- [x] Catalogo de triggers aprobado.
- [x] Conjunto minimo de semillas definido.
- [x] Casos de prueba de integridad definidos.

## Paso siguiente sugerido
- Iniciar Fase 4, Vertical 1 (lista de cuentas y filtros), implementando primero esquema y consultas sin activar aun todos los triggers.

## Estado actualizado
- Fase 3: CERRADA para ambiente de desarrollo (sin triggers SQL activos aun).

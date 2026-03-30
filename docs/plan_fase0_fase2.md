# Plan operativo - Fase 0 y Fase 2

Alcance: estrategia de transformacion manteniendo base Django, sin implementar codigo todavia.

## Fase 0 - Alineacion y linea base

### Objetivo
Congelar alcance, riesgos y criterios de exito para no romper el sistema durante la migracion.

### Entregables
- Alcance firmado: que se conserva vs que se reemplaza.
- Inventario funcional actual por modulo.
- Riesgos y mitigaciones.
- Criterios de aceptacion por fase.

### Propuesta base (prellenada)
Meta propuesta:
- Rehacer el sistema como plataforma Django reutilizable para cuentas por cobrar, desacoplando totalmente el dominio actual y dejando una arquitectura limpia por verticales (lista, detalle, cobro, dashboard).

Conservar:
- Base tecnica Django del proyecto (settings, entorno, estructura general, admin, auth y plantillas base).

Reemplazar:
- Modelos de negocio actuales, rutas de negocio, vistas de negocio, formularios de negocio y templates de negocio.

Procesos que no deben migrarse tal cual:
- Reglas acopladas del flujo viejo cliente-factura-venta-credito-cuota.
- Formularios incrustados en views sin capa de dominio clara.

MVP sugerido:
- Lista de cuentas, detalle de factura + cuotas, registro de cobro, dashboard basico.

Politica de datos confirmada:
- Reinicio controlado de BD para entorno de rediseno (sin arrastrar historico viejo).

Definition of Done por fase (obligatoria):
- Servidor levanta.
- Migraciones limpias.
- Flujo vertical definido para la fase funciona de punta a punta.

### Checklist de ejecucion
- [x] Definir meta del producto nuevo en 1 parrafo.
- [x] Confirmar que se conserva base tecnica Django (proyecto, settings, entorno, admin).
- [x] Confirmar que se reemplaza dominio actual (modelos, vistas, rutas, templates, reglas).
- [x] Listar procesos actuales que NO deben migrarse.
- [x] Definir prioridad de modulos futuros (MVP primero).
- [x] Definir politica de datos: se descarta y se reinicia BD.
- [x] Definir criterios minimos de salida por fase:
  - [x] Arranca servidor
  - [x] No errores de migracion
  - [x] Flujo vertical en prueba manual

### Riesgos y controles (fase 0)
- Riesgo: sobrecargar alcance al inicio.
  - Control: MVP por verticales y backlog acotado.
- Riesgo: romper relaciones entre apps existentes.
  - Control: no eliminar legado hasta tener reemplazo validado.
- Riesgo: ambiguedad funcional en cobros/plazos.
  - Control: cerrar reglas en Fase 2 antes de implementar.

### Resultado esperado para cerrar Fase 0
- Documento de alcance aprobado.
- Backlog inicial priorizado.
- Reglas de avance (Definition of Done por fase).

### Estado de cierre Fase 0
- Fase 0: CERRADA.
- Comentario: alcance y politica de datos ya definidos con reinicio de BD.

---

## Fase 2 - Diseno de dominio y contrato funcional

### Objetivo
Definir el nuevo modelo de negocio y los contratos funcionales de UI/API antes de codificar.

### Inputs usados
- Referencias de interfaz: [docs/referencias_vistas.md](docs/referencias_vistas.md)
- Estructura actual del proyecto.

### Entregables
- Modelo conceptual del dominio (entidades y relaciones).
- Definicion de estados y transiciones.
- Catalogo de reglas de negocio validado.
- Mapa de pantallas y rutas objetivo.
- Casos de prueba funcionales (Given/When/Then) para futuras fases.

### Propuesta de diseno MVP (prellenada)
Entidades MVP:
- CuentaPorCobrar
- Cuota
- Cobro
- Cliente
- DocumentoComercial

Estados propuestos:
- CuentaPorCobrar: pendiente, parcial, cobrada, vencida
- Cuota: pendiente, parcial, cobrada, vencida

Reglas propuestas:
- Una cuenta se compone de una o mas cuotas.
- El saldo de cuenta se recalcula con la suma de cuotas pendientes.
- No se permite cobrar por encima del saldo de cuota.
- Registrar cobro actualiza cuota y luego estado agregado de la cuenta.
- Plazos admiten modalidad predefinida (ejemplo CR-30-45-60) o personalizada.

Reglas de modalidad confirmadas (requerimiento formal):
- Contado (CO): cuenta unica y cancelada en la misma fecha de la factura.
- Credito (CR): multiples cuotas con vencimiento:
  - Regular: mensual desde la fecha de factura (ejemplo CR-30-60-90).
  - Irregular: dias personalizados por cuota (ejemplo CR-30-45-60).

Contrato de UI basado en capturas:
- Lista de cuentas: filtros por cliente, factura y estado; tabla con acciones ver detalle y registrar cobro.
- Detalle: cabecera de documento + grilla de cuotas ordenadas por numero.
- Cobro: accion principal desde lista y detalle.
- Dashboard: totales por estado, total vencido y monto total.

Contrato de datos minimo:
- Campos de auditoria en entidades transaccionales (fecha_creacion, fecha_actualizacion, usuario_creacion).
- Indices en cliente, documento y estado para filtros rapidos.

Decision de auditoria confirmada:
- SI, incluir auditoria minima en cuentas, cuotas y cobros.

Pendientes de definicion funcional (solo de precision):
- Criterio de presentacion para estado Parcial en UI (colores/texto).

Definiciones ya cerradas:
- Regla de vencida: por fecha y saldo pendiente.
- Estados para MVP: pendiente, parcial, cobrada, vencida.
- Redondeo monetario: sin decimales (numero entero redondeado, sin punto flotante).

### Matriz de definicion (completar)
1. Entidades principales:
- [x] CuentaPorCobrar
- [x] Cuota
- [x] Cobro
- [x] Cliente (nuevo o adaptado)
- [x] Documento comercial (Factura u otro)

2. Estados y transiciones:
- [x] Cuenta: Pendiente -> Parcial -> Cobrada
- [x] Cuota: Pendiente -> Parcial -> Cobrada -> Vencida (si aplica)
- [x] Reglas de recalculo de saldo

3. Reglas de negocio clave:
- [x] Como se genera el plan de cuotas
- [x] Si hay plazos predefinidos (CR-30-45-60) y reglas de validacion
- [x] Si hay cobro parcial por cuota
- [x] Reglas de redondeo/moneda
- [x] Reglas de bloqueo (no cobrar mas que saldo)

4. Contrato de vistas (UI):
- [x] Lista de cuentas (filtros, paginacion, acciones)
- [x] Detalle de factura + cuotas
- [x] Registrar cobro
- [x] Dashboard (metricas minimas)

5. Contrato de datos:
- [x] Campos obligatorios por entidad
- [x] Indices y busquedas esperadas
- [x] Auditoria minima (fecha_creacion, fecha_actualizacion, usuario)

### Diseno de tablas para el ejercicio (sin codigo aun)
Tablas nucleares propuestas y justificacion:
- cliente:
  - id, nombre, documento, telefono, email, activo, timestamps.
  - Justificacion: identificacion y contacto para filtros y gestion.
- documento_comercial:
  - id, tipo_documento (compra/venta), numero, fecha, moneda, total, cliente_id.
  - Justificacion: cabecera del proceso administrativo y origen de cuenta.
- cuenta_cobrar:
  - id, documento_id, modalidad (CO/CR), plan_cuotas, total, saldo, estado, fecha_estado.
  - Justificacion: consolidado financiero y estado operativo.
- cuota:
  - id, cuenta_id, nro_cuota, importe, cobrado, saldo, fecha_vencimiento, estado.
  - Justificacion: gestion granular de vencimientos y cobros.
- cobro:
  - id, cuota_id, fecha_cobro, monto, medio_pago, referencia, usuario_id.
  - Justificacion: historial transaccional y auditoria.
- auditoria_evento (opcional para trazabilidad extendida):
  - id, entidad, entidad_id, accion, payload, usuario_id, fecha.
  - Justificacion: soporte de auditoria y diagnostico.

### Triggers a ensayar (alcance de fase de diseno)
Procesos elegidos para trigger:
- Registro de cobro en cuota.
- Generacion automatica de cuotas.
- Generacion de detalle de talonarios.

Comportamiento esperado de los triggers (a implementar luego):
- Al insertar cobro:
  - actualizar cuota.cobrado y cuota.saldo.
  - recalcular estado de cuota (cobrada/parcial/pendiente/vencida por fecha).
  - recalcular saldo y estado de cuenta_cobrar asociada.
  - bloquear montos que excedan saldo vigente.
- Al insertar documento en modalidad CR:
  - generar cuotas segun plan regular o irregular.
  - asignar fechas de vencimiento y montos enteros redondeados.
  - recalcular diferencia residual de redondeo en la ultima cuota.
- Al generar documento/talonario:
  - crear detalle de talonario asociado (rangos/lineas segun regla de negocio).
  - mantener consistencia entre cabecera de talonario y detalle generado.

Validaciones de negocio cubiertas por trigger:
- Integridad monetaria (no sobrecobro).
- Consistencia entre cuota y cuenta agregada.
- Estado vencida por fecha cuando existe saldo.
- Integridad de cuotas generadas contra el total del documento.
- Integridad de detalle de talonarios contra su cabecera.

### Criterios de salida Fase 2
- [x] No hay reglas ambiguas pendientes para MVP.
- [x] Se puede implementar por verticales sin redefinir modelos base.
- [x] Cada pantalla tiene objetivo, datos y acciones definidos.

### Estado de cierre Fase 2
- Fase 2: CERRADA.

---

## Orden recomendado para pasar a implementacion (cuando lo decidamos)
1. Vertical 1: Lista de cuentas + filtros + estado.
2. Vertical 2: Detalle de cuenta + cuotas.
3. Vertical 3: Registrar cobro y recalculo de saldo.
4. Vertical 4: Dashboard basico.

## Politica de trabajo segura
- Cambios pequenos y reversibles.
- Prueba manual al cierre de cada vertical.
- No borrar legado hasta validar reemplazo equivalente.

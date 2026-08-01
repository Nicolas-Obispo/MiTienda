# Observabilidad y Operacion del Sistema

Estado del documento: Documento Tecnico-Operativo Oficial.
Version: 1.0.
Categoria: Documento tecnico-operativo transversal.
Nivel de autoridad: Alto para observabilidad, diagnostico, operacion,
health, metricas, alertas, logging seguro y runbooks.
Documento dueno: `docs/17_OBSERVABILITY_AND_OPERATIONS.md`.
Responsable funcional: Operacion del Sistema.
Documentos relacionados: `00_GOVERNANCE.md`, `01_ENGINEERING.md`,
`04_CURRENT_STAGE.md`, `05_SEARCH_ROADMAP.md`, `07_DECISIONS.md`,
`08_ENGINEERING_PRINCIPLES.md`, `15_LEGAL_AND_OPERATIONAL.md`,
`16_DATA_INTEGRITY_AND_RECOVERY.md`.
Cuando debe consultarse: antes de disenar o implementar logging, manejo de
errores, request context, correlation ID, health checks, metricas, alertas,
runbooks, diagnostico productivo, validacion de configuracion o cambios en
uploads/storage con impacto operativo.

## 1. Objetivo

Este documento gobierna la arquitectura operativa de FeedGo.

Define contratos, politicas y limites para observar, diagnosticar y operar el
sistema sin acoplarlo prematuramente a proveedores concretos.

No implementa logging productivo, middleware, endpoints, tablas, metricas,
alertas, proveedores externos ni almacenamiento persistente de eventos.

## 2. Estado oficial de ETAPA 93.1

ETAPA 93 esta cerrada.

ETAPA 92 esta cerrada y deja como base reutilizable:

- scripts operativos seguros;
- checker read-only profundo de schema;
- arquitectura extensible de backup, restore y storage;
- backup oficial validado;
- restore real temporal validado;
- evidencia operativa fuera del repositorio.

Pendientes heredados que pertenecen a ETAPA 93:

- logs;
- monitoreo;
- diagnostico;
- configuracion productiva;
- operacion minima;
- ownership y ciclo de vida de uploads;
- preparacion de automatizacion operativa inicial.

## 3. Principio rector

Toda capacidad operativa permanente debe definirse mediante contratos estables
antes de acoplarse a una implementacion o proveedor concreto.

Este principio aplica cuando la capacidad sea transversal, evolutiva o tenga
mas de una implementacion razonablemente posible.

No debe producir:

- interfaces vacias;
- providers especulativos;
- capas duplicadas;
- abstracciones sin consumidor real;
- almacenamiento persistente sin necesidad aprobada.

DEC-043 gobierna esta regla para infraestructura. DEC-045 la extiende a la
operacion del sistema.

## 4. Contratos operativos aprobados

### 4.1 `OperationEvent`

Responsabilidad:

Representar un hecho operativo relevante que puede alimentar logs, metricas,
alertas o auditoria cuando corresponda.

Campos minimos:

- `event_id`;
- `occurred_at`;
- `severity`;
- `category`;
- `component`;
- `operation`;
- `result`;
- `message`;
- `context`.

Datos opcionales:

- `duration_ms`;
- `request_context`;
- `actor_context`;
- `resource_context`;
- `safe_error`;
- `metadata` sanitizada.

Datos prohibidos:

- secretos;
- tokens;
- contrasenas;
- cookies;
- cuerpos completos de requests o responses;
- payloads completos;
- datos personales sin necesidad operativa;
- stack traces enviados al frontend.

Consumidores:

- logs estructurados;
- metricas operativas;
- alertas;
- auditoria de seguridad, solo si corresponde.

Ciclo de vida:

Se crea durante una operacion o proceso. Puede enviarse a uno o mas sinks. No
se persiste en base de datos salvo decision futura aprobada.

### 4.2 `OperationContext`

Responsabilidad:

Describir donde ocurre el evento.

Campos minimos:

- `component`;
- `module`;
- `operation`;
- `environment`.

Datos opcionales:

- `process_name`;
- `script_name`;
- `dependency_name`.

No debe contener secretos ni rutas sensibles completas.

### 4.3 `RequestContext`

Responsabilidad:

Correlacionar eventos originados por una misma solicitud HTTP.

Campos minimos:

- `request_id`;
- `method`;
- `route_pattern`;
- `status_code`;
- `duration_ms`.

Datos opcionales:

- `client_ip_hash` si existe justificacion;
- `user_agent_family` sanitizado;
- `correlation_id` recibido y validado.

No debe registrar URL con query completa si contiene busquedas, tokens o datos
personales.

### 4.4 `ActorContext`

Responsabilidad:

Representar el actor minimo relacionado con un evento.

Campos permitidos:

- `user_id` cuando sea necesario;
- tipo de actor: anonimo, autenticado, sistema o script.

Datos prohibidos:

- email;
- nombre;
- token;
- sesion;
- IP completa salvo necesidad documentada.

### 4.5 `ResourceContext`

Responsabilidad:

Identificar el recurso minimo afectado sin exponer contenido.

Campos permitidos:

- `resource_type`;
- `resource_id`;
- `owner_scope` cuando corresponda.

No debe incluir textos, imagenes, detalles privados ni contenido generado por el
usuario.

### 4.6 `StructuredLogSink`

Responsabilidad:

Convertir `OperationEvent` en log estructurado seguro.

No debe calcular metricas parseando texto de logs.

### 4.7 `MetricSink`

Responsabilidad:

Recibir eventos o mediciones y producir senales cuantitativas.

No depende de parsear logs. No define almacenamiento ni exportador en 93.1.

### 4.8 `AlertSink`

Responsabilidad:

Evaluar condiciones operativas y preparar alertas desacopladas del proveedor.

No envia email, Slack, WhatsApp, push ni integraciones externas en 93.1.

### 4.9 `HealthCheck`

Responsabilidad:

Ejecutar una verificacion read-only de un componente.

Debe ser acotado, rapido, no destructivo y sin secretos.

### 4.10 `HealthCheckResult`

Responsabilidad:

Informar el resultado de una verificacion.

Campos minimos:

- `name`;
- `status`;
- `checked_at`;
- `duration_ms`;
- `summary`.

Datos opcionales:

- `safe_details`;
- `degraded_reason`;
- `dependency`.

No debe exponer credenciales, rutas sensibles ni errores internos completos.

### 4.11 `HealthRegistry`

Responsabilidad:

Registrar checks disponibles y ejecutar grupos de checks por tipo: liveness,
readiness o startup.

No debe ser una lista informal de funciones sueltas.

## 5. Contratos descartados en 93.1

No se aprueban todavia:

- `AuditSink` general persistente;
- `EmailAlertProvider`;
- `SlackAlertProvider`;
- `SentryProvider`;
- `PrometheusExporter`;
- `OpenTelemetryProvider`;
- `CloudStorageProvider`;
- tablas de eventos operativos;
- cola de eventos operativos.

Podran evaluarse solo con evidencia y etapa aprobada.

## 6. Modelo de evento operativo

Un evento operativo representa algo relevante para operar el sistema.

Debe poder responder, cuando corresponda:

- que ocurrio;
- cuando ocurrio;
- donde ocurrio;
- que componente intervino;
- que operacion se ejecutaba;
- cual fue el resultado;
- cuanto duro;
- que request o proceso lo origino;
- que actor minimo estuvo involucrado;
- que recurso minimo estuvo afectado;
- que error seguro puede asociarse;
- que identificador permite correlacionarlo.

No todo evento debe contener todos los contextos.

Un evento operativo no es:

- evento de negocio;
- analytics de producto;
- evidencia legal;
- decision de moderacion;
- backup fisico;
- registro de auditoria persistente por defecto.

## 7. Categorias y niveles

Categorias minimas:

- `lifecycle`;
- `request`;
- `authentication`;
- `authorization`;
- `database`;
- `storage`;
- `upload`;
- `search`;
- `indexing`;
- `backup`;
- `restore`;
- `dependency`;
- `configuration`;
- `background_process`;
- `security`;
- `error`.

Niveles:

- `debug`: diagnostico local o temporal, nunca por defecto en produccion.
- `info`: operacion normal relevante.
- `warning`: degradacion o condicion recuperable.
- `error`: fallo de operacion que requiere investigacion.
- `critical`: perdida de capacidad critica, riesgo de datos o incidente.

Usos prohibidos:

- usar `critical` para errores esperables de usuario;
- usar `debug` para datos sensibles;
- registrar errores de validacion de usuario como incidentes;
- duplicar un mismo hecho en multiples categorias sin necesidad.

## 8. Politica de minimizacion

Prohibido registrar, salvo excepcion aprobada y sanitizada:

- contrasenas;
- tokens;
- JWT completos;
- cookies;
- secretos;
- claves;
- credenciales;
- archivos `.env`;
- request bodies completos;
- response bodies completos;
- datos bancarios;
- documentos personales;
- direcciones privadas innecesarias;
- contenido privado de usuarios;
- stack traces enviados al frontend.

Tratamiento por dato:

| Dato | Regla |
| --- | --- |
| `user_id` | Permitido solo cuando aporte diagnostico, seguridad u ownership. |
| `comercio_id` | Permitido para diagnostico de recurso, sin datos del comercio. |
| `publicacion_id` | Permitido para diagnostico de recurso, sin contenido. |
| `reserva_id` | Permitido solo cuando exista dominio de reservas y necesidad operativa. |
| IP | Evitar IP completa. Preferir hash o truncamiento si se justifica. |
| User-agent | Registrar familia o clase sanitizada, no cadena completa por defecto. |
| Email | No registrar salvo excepcion legal/soporte aprobada. |
| Query de busqueda | Evitar texto completo; usar longitud, hash o categoria si alcanza. |
| Nombre de archivo | Preferir ID interno o extension; evitar nombres originales. |
| Rutas del sistema | No registrar rutas absolutas sensibles. |
| Excepciones | Registrar clase segura y mensaje sanitizado. |
| Payloads | No registrar payload completo; registrar campos permitidos y tamanos. |

## 9. Separacion de dominios observables

Logs operativos:

- describen hechos tecnicos;
- permiten diagnostico;
- no son fuente de metricas por parseo de texto.

Metricas operativas:

- cuantifican volumen, duracion, errores y estado;
- no contienen datos personales innecesarios.

Auditoria de seguridad:

- registra hechos sensibles cuando existe necesidad de trazabilidad;
- requiere retencion, acceso y finalidad propia.

Analytics de producto:

- mide comportamiento de uso o descubrimiento;
- no sustituye observabilidad ni auditoria.

Eventos de negocio:

- pertenecen al dominio funcional;
- no deben mezclarse con logs por conveniencia.

Evidencia de backup y restore:

- pertenece a `16_DATA_INTEGRITY_AND_RECOVERY`;
- puede producir senales operativas sobre vigencia, resultado y duracion.

Un mismo hecho puede generar log, metrica y alerta, pero cada salida conserva su
responsabilidad.

## 10. Matriz de configuracion productiva

| Variable / capacidad | Proposito | Sensibilidad | Obligatoriedad | Validacion | Ausencia | Default | Exposicion permitida |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Entorno de ejecucion | Diferenciar local, test, staging, produccion | baja | obligatoria antes de produccion | valor permitido | impedir produccion ambigua | no | nombre del entorno |
| `DATABASE_URL` | Conexion principal DB | alta | obligatoria | esquema, host, base | impedir arranque | no | motor y host sin credenciales |
| `SECRET_KEY` | Firma JWT | critica | obligatoria | longitud/fortaleza | impedir arranque | no | nunca |
| `ALGORITHM` | Algoritmo JWT | media | obligatoria | lista permitida | impedir arranque | no | valor seguro |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiracion JWT | media | obligatoria | entero positivo razonable | impedir arranque | no | rango, no secreto |
| Upload path | Directorio de archivos | media | obligatoria para media | existencia/escritura | degradar media o impedir segun modo | no | estado, no ruta sensible |
| Upload max size | Limite operativo | baja | obligatoria | entero positivo | impedir upload | si | valor publico |
| Embeddings provider | IA/embeddings | media | obligatoria para busqueda inteligente | provider permitido | degradar a modo disponible | si | provider, no credenciales |
| CORS origins | Origenes frontend | media | obligatoria en produccion | lista explicita | impedir arranque productivo | no | cantidad, no secretos |
| `FEEDGO_MYSQL_DEFAULTS_FILE` | Credenciales backup/restore | critica | obligatoria para backups/restores | existe y legible | degradar backup/restore | no | existencia, no ruta completa sensible |
| `FEEDGO_BACKUP_DIR` | Destino backups | media | obligatoria para backups | fuera del repo/escribible | degradar backup | si local dev | estado, no contenido |
| `FEEDGO_RESTORE_EVIDENCE_DIR` | Evidencia restore | media | obligatoria para restore | fuera del repo/escribible | degradar restore | si local dev | estado |
| Debug flag | Diagnostico local | media | prohibido en produccion | false en produccion | impedir produccion | no | booleano seguro |

## 11. Modelo de salud

Estados:

- `healthy`: componente funciona dentro de parametros esperados.
- `degraded`: componente responde pero con capacidad reducida.
- `unhealthy`: componente no puede cumplir su funcion minima.
- `unknown`: no pudo verificarse sin riesgo, costo o permisos.

Tipos:

- `liveness`: confirma que el proceso responde.
- `readiness`: confirma que el proceso puede recibir trafico util.
- `startup`: confirma que dependencias y configuracion inicial permiten arrancar.

Checks conceptuales:

| Componente | Liveness | Readiness | Startup | Regla |
| --- | --- | --- | --- | --- |
| API | proceso responde | router y config cargados | app inicia | sin detalles internos |
| Database connectivity | no aplica | consulta read-only minima | conexion configurable | sin credenciales |
| Database schema | no aplica | checker read-only resumido | metadata cargada | no ejecutar `create_all` |
| Storage/uploads | no aplica | path existe y es escribible si media activa | directorio configurado | no crear archivos permanentes |
| Embeddings | no aplica | provider disponible o degradado | config valida | no cargar modelos costosos en cada check |
| Cache | solo si existe capacidad real | segun provider futuro | segun provider futuro | no inventar cache |
| Backup evidence | no aplica | ultimo backup valido dentro de umbral | config disponible | usar manifiestos, no ejecutar backup |
| Restore evidence | no aplica | ultima prueba valida dentro de umbral | config disponible | usar evidencia, no ejecutar restore |
| Background jobs | solo si existen procesos reales | ultimo resultado conocido | registro de proceso | no inventar scheduler |

No debe existir un unico `/health` generico que oculte estas diferencias.

## 12. Metricas minimas

Contadores:

- requests por metodo/ruta normalizada/status;
- errores 4xx;
- errores 5xx;
- fallos de autenticacion;
- fallos de autorizacion;
- uploads aceptados y rechazados;
- busquedas;
- busquedas sin resultados;
- errores de embeddings;
- backups ejecutados;
- restores probados;
- procesos operativos fallidos.

Duraciones:

- latencia de request;
- duracion de queries o bloques DB relevantes;
- duracion de upload;
- duracion de busqueda;
- duracion de backup;
- duracion de restore;
- duracion de procesos operativos.

Gauges / estados:

- estado de readiness;
- antiguedad de ultimo backup valido;
- antiguedad de ultima evidencia de restore;
- espacio disponible de storage si se implementa verificacion segura;
- cantidad de errores recientes por categoria.

Eventos excepcionales:

- backup fallido;
- restore fallido;
- schema divergente;
- storage no escribible;
- configuracion critica invalida;
- tasa elevada de 5xx;
- fallos repetidos de autenticacion/autorizacion.

No se define almacenamiento ni exportacion en 93.1.

## 13. Alertas

Contrato minimo:

- `alert_id`;
- `condition`;
- `severity`;
- `window`;
- `deduplication_key`;
- `cooldown`;
- `status`;
- `context`;
- `future_destination`.

Severidades:

- informativa;
- advertencia;
- critica.

Casos minimos que justifican alerta futura:

- API no esta ready;
- DB no responde;
- schema divergente;
- backup valido vencido;
- restore evidence vencida;
- errores 5xx por encima de umbral;
- storage/uploads no escribible;
- configuracion critica invalida;
- proceso operativo recurrentemente fallido.

No se implementa proveedor externo en 93.1.

## 14. Auditoria de uploads y storage

Estado actual auditado:

- `backend/main.py` monta `/uploads` como archivos estaticos desde filesystem
  local.
- `backend/app/modules/media/routes/media_routers.py` requiere JWT para
  `POST /media/upload`.
- El upload valida MIME permitido y tamano maximo.
- El archivo se guarda con nombre UUID y se devuelve una ruta publica
  `/uploads/<archivo>`.
- No existe asociacion persistente del archivo con usuario, comercio,
  publicacion, historia u otro recurso.
- No existe cuota.
- No existe limpieza de archivos huerfanos.
- No existe verificacion operativa formal del storage.
- Existe inconsistencia documental en el mensaje de tamano: la constante permite
  50 MB y el mensaje indica 5 MB.

Destino arquitectonico:

- uploads/storage queda como deuda operativa posterior al cierre de ETAPA 93,
  gobernada por este documento cuando vuelva a trabajarse;
- antes de crear tablas o columnas debe aplicarse la auditoria obligatoria del
  modelo de datos;
- si una tabla existente es el dueno natural de la asociacion, debe preferirse
  extender esa relacion;
- una entidad nueva solo se justifica si su responsabilidad unica es gobernar
  archivos, asociaciones, lifecycle y limpieza;
- no debe implementarse cloud storage ni proveedor externo sin etapa futura.

La resolucion futura debera reutilizar logging, errores, Request Context,
health, metricas y alertas ya implementados, sin crear tablas ni modelos antes
de aplicar el gobierno del modelo de datos.

## 15. Division definitiva de ETAPA 93

Division aprobada como plan de trabajo:

1. `93.1 - Arquitectura Operativa`.
2. `93.2 - Logging Enterprise y Error Handling`.
3. `93.3 - Contexto Operativo y Correlacion`.
4. `93.4 - Health, Readiness y Estado del Sistema`.
5. `93.5 - Metricas y Senales Operativas`.
6. `93.6 - Alertas mediante Contratos`.
7. `93.7 - Runbooks, Validacion y Cierre`.

Uploads, media, storage, ownership, cuotas, archivos huerfanos y ciclo de vida
no tienen sprint exclusivo inicial. Deben auditarse y asignarse al sprint que
corresponda segun evidencia, sin crear tablas ni modelos antes de aplicar el
gobierno del modelo de datos.

## 16. Criterios de cierre de 93.1

93.1 queda cerrada documentalmente cuando:

- existe arquitectura coherente y minima;
- cada contrato tiene responsabilidad clara;
- los datos prohibidos estan definidos;
- logs, metricas, alertas, health, auditoria y analytics estan separados;
- configuracion critica tiene reglas explicitas;
- uploads tiene destino arquitectonico definido;
- la division restante de ETAPA 93 esta justificada;
- la documentacion oficial queda consistente;
- no se introducen endpoints, middleware, tablas, migraciones, proveedores
  externos ni infraestructura productiva prematura.

## 17. Sprint 93.2 - Logging Enterprise y Error Handling

Estado:

Cerrado tecnicamente.

Implementacion aprobada:

- logger central reutilizable basado en `logging` estandar;
- namespace operativo `feedgo`;
- politica de niveles `DEBUG`, `INFO`, `WARNING`, `ERROR` y `CRITICAL`;
- handlers centrales de `HTTPException`, `RequestValidationError` y errores no
  controlados;
- sanitizacion de detalles sensibles antes de responder al frontend;
- respuesta generica para excepciones no controladas;
- respuesta generica para errores de validacion;
- cliente HTTP frontend sin propagacion de cuerpos crudos de error del backend.

Limites:

- no se implementa middleware;
- no se implementa correlation ID;
- no se crea RequestContext runtime;
- no se crean endpoints;
- no se crean tablas ni migraciones;
- no se integran proveedores externos;
- los scripts CLI conservan `print` operativo hasta una decision futura
  especifica.

Criterio de seguridad:

Los errores no deben exponer al frontend:

- `SECRET_KEY`;
- JWT;
- tokens;
- passwords;
- `.env`;
- stack traces;
- payloads completos;
- datos personales innecesarios.

El logging de errores no controlados registra clase segura del error y contexto
tecnico minimo. No registra traceback ni mensaje original cuando puede contener
datos sensibles.

## 18. Sprint 93.3 - Contexto Operativo y Correlacion

Estado:

Cerrado tecnicamente.

Implementacion aprobada:

- middleware unico de Request Context;
- `request_id` unico generado por backend para cada request;
- `correlation_id` reutilizado desde `X-Correlation-ID` cuando el valor es
  seguro;
- `correlation_id` generado por backend cuando el cliente no lo envia o envia
  un valor invalido;
- propagacion durante la request mediante contexto operativo local;
- headers de respuesta `X-Request-ID` y `X-Correlation-ID`;
- integracion con logger central;
- integracion con handlers de errores HTTP, validacion y errores no
  controlados.

Reglas:

- el `request_id` identifica una request concreta;
- el `correlation_id` permite agrupar una operacion o flujo distribuido futuro;
- valores entrantes de `X-Correlation-ID` deben validarse y normalizarse;
- no se deben aceptar tokens, secretos ni texto libre arbitrario como
  correlation ID;
- los IDs no reemplazan autenticacion, autorizacion ni auditoria de seguridad.

Limites:

- no se implementan health checks;
- no se implementan metricas;
- no se implementan alertas;
- no se implementa OpenTelemetry;
- no se crean endpoints;
- no se crean tablas ni migraciones.

## 19. Sprint 93.4 - Health, Readiness y Estado del Sistema

Estado:

Cerrado tecnicamente.

Implementacion aprobada:

- endpoints separados `GET /health/live` y `GET /health/ready`;
- `HealthRegistry` para registrar y ejecutar checks por tipo;
- `HealthCheckResult` con componente, estado, duracion y mensaje seguro;
- liveness acotado a disponibilidad del proceso API;
- readiness con checks read-only para:
  - API;
  - conexion a base de datos;
  - compatibilidad de schema mediante el checker read-only existente;
  - uploads/storage local;
  - configuracion de embeddings;
  - evidencia de backup;
  - evidencia de restore;
- integracion con logger central;
- integracion con Request Context y headers `X-Request-ID` y
  `X-Correlation-ID`.

Estados:

- `healthy`: el componente esta disponible.
- `degraded`: el componente existe pero la capacidad es parcial o la evidencia
  operativa no esta disponible.
- `unhealthy`: el componente impide readiness.
- `unknown`: reservado para verificaciones que no puedan ejecutarse de forma
  segura.

Reglas:

- los checks son read-only;
- no ejecutan backups ni restores;
- no ejecutan `create_all`, `drop_all`, `ALTER`, migraciones ni escrituras de
  datos;
- no exponen secretos, rutas internas, SQL, stack traces ni configuracion
  sensible;
- readiness devuelve `503` cuando algun componente es `unhealthy`;
- readiness puede devolver `200` con estado `degraded` cuando la aplicacion
  puede responder pero existe una capacidad operativa reducida.

Limites:

- no se implementan metricas;
- no se implementan alertas;
- no se integra Prometheus, Grafana, Sentry ni OpenTelemetry;
- no se crean tablas ni migraciones;
- no se resuelve ownership ni lifecycle persistente de uploads.

## 20. Sprint 93.5 - Metricas y Senales Operativas

Estado:

Cerrado tecnicamente.

Implementacion aprobada:

- contratos minimos para metricas de tipo `counter`, `duration` y `gauge`;
- `MetricSample` como unidad minima de senal operativa;
- `MetricsRecorder` como orquestador local de emision;
- `LocalMetricsSink` como sink inicial en memoria, sin almacenamiento
  persistente ni exportador externo;
- catalogo inicial de nombres estables de metricas;
- middleware operativo para request count, latencia y respuestas `4xx`/`5xx`;
- senales de errores no controlados;
- senales de fallos de autenticacion y autorizacion;
- senales de readiness y duracion de checks;
- senales de backup y restore desde sus servicios operativos;
- senales de uploads aceptados y rechazados;
- senal de busquedas sin resultados desde el punto natural de busqueda de
  comercios activos.

Catalogo inicial:

- `http.request.count`;
- `http.request.duration_ms`;
- `http.response.4xx.count`;
- `http.response.5xx.count`;
- `http.unhandled_error.count`;
- `auth.failure.count`;
- `authorization.failure.count`;
- `health.readiness.status`;
- `health.check.duration_ms`;
- `backup.run.count`;
- `backup.run.duration_ms`;
- `restore.run.count`;
- `restore.run.duration_ms`;
- `upload.accepted.count`;
- `upload.rejected.count`;
- `upload.duration_ms`;
- `search.no_results.count`.

Reglas:

- las metricas no se calculan parseando texto de logs;
- las metricas no exponen secretos, tokens, payloads completos ni datos
  personales;
- las metricas pueden incluir identificadores operativos de request y
  correlacion cuando existan;
- las etiquetas deben ser acotadas, tecnicas y sanitizadas;
- cada modulo emite las senales que conoce de forma natural;
- readiness, backup, restore, uploads y busqueda conservan su responsabilidad
  funcional y solo emiten senales operativas.

Limites:

- no se implementan alertas;
- no se crean endpoints de metricas;
- no se integra Prometheus, Grafana, Sentry ni OpenTelemetry;
- no se crean tablas ni migraciones;
- no se convierte analytics de producto en metrica operativa;
- no se resuelve ownership ni lifecycle persistente de uploads.

## 21. Sprint 93.6 - Alertas mediante Contratos

Estado:

Cerrado tecnicamente.

Implementacion aprobada:

- contratos minimos `AlertRule`, `AlertEvent`, `AlertSeverity` y `AlertSink`;
- `AlertEngine` como evaluador interno de reglas;
- `LocalAlertSink` como sink inicial en memoria para desarrollo y tests;
- registro de listener sobre metricas operativas para evaluar reglas sin
  parsear logs;
- deduplicacion por regla y contexto seguro;
- cooldown por clave de deduplicacion;
- estado de alerta `active` o `suppressed`;
- contexto tecnico minimo y sanitizado;
- catalogo inicial de reglas operativas.

Catalogo inicial:

- `readiness_unhealthy`: alerta critica cuando readiness informa estado
  `unhealthy`;
- `http_5xx_repeated`: alerta critica por errores `5xx` repetidos dentro de
  una ventana operativa;
- `backup_failed`: alerta critica cuando un backup finaliza con error;
- `backup_evidence_not_healthy`: alerta de advertencia cuando la evidencia de
  backup no esta disponible o no es valida;
- `restore_failed`: alerta critica cuando un restore finaliza con error;
- `uploads_rejected_repeated`: alerta de advertencia por rechazos repetidos de
  uploads dentro de una ventana operativa.

Reglas:

- las alertas se derivan de metricas, health o procesos operativos existentes;
- las alertas no se calculan parseando logs;
- una alerta aislada solo se permite cuando el hecho tiene impacto operativo
  directo, como backup o restore fallido;
- los errores `5xx` y rechazos de upload requieren repeticion dentro de una
  ventana;
- las alertas no exponen secretos, tokens, payloads completos ni datos
  personales;
- el sink local no constituye notificacion externa ni monitoreo productivo
  completo.

Limites:

- no se integra email, Slack, Discord, Telegram, Sentry ni servicios cloud;
- no se crean dashboards;
- no se crean endpoints de alertas;
- no se crean tablas ni migraciones;
- no se implementa persistencia historica de alertas;
- no se implementan politicas de guardia, escalamiento ni resolucion manual;
- no se resuelve ownership ni lifecycle persistente de uploads.

## 22. Sprint 93.7 - Runbooks, Validacion y Cierre

Estado:

Cerrado.

Resultado:

- Se audita integralmente lo implementado desde 93.1 hasta 93.6.
- Se confirma coherencia entre logging, handlers de errores, Request Context,
  health, metricas y alertas.
- Se documentan runbooks operativos iniciales para incidentes minimos.
- Se confirma que no se crearon tablas, migraciones, dashboards ni proveedores
  externos.
- Se confirma que las senales operativas no dependen de parsear logs.
- Se mantiene la separacion entre observabilidad, auditoria, analytics,
  evidencia de backup/restore y alertas.

## 23. Runbooks iniciales

Los runbooks son guias breves de respuesta operativa.

No reemplazan monitoreo productivo, guardias, proveedores externos ni procesos
formales de incidentes.

### 23.1 API no disponible

Senales:

- `GET /health/live` no responde o devuelve error.
- Errores de conexion desde frontend o cliente HTTP.
- Logs de arranque ausentes o proceso detenido.

Acciones:

1. Confirmar que el proceso backend este iniciado.
2. Revisar logs del proceso buscando `startup_catalogos_error` o errores
   criticos.
3. Verificar configuracion minima de entorno sin imprimir secretos.
4. Reiniciar el proceso solo si el diagnostico confirma falla de runtime.
5. Si liveness se recupera, ejecutar readiness antes de permitir trafico util.

No hacer:

- ejecutar `reset_db.py`;
- ejecutar `create_tables.py` como respuesta automatica;
- exponer trazas internas al frontend.

### 23.2 Readiness `unhealthy`

Senales:

- `GET /health/ready` devuelve `503`.
- Metrica `health.readiness.status` igual a `0`.
- Alerta `readiness_unhealthy` activa.

Acciones:

1. Identificar el componente informado como `unhealthy`.
2. Revisar logs correlacionados mediante `X-Request-ID` o
   `X-Correlation-ID`.
3. Si el componente es base de datos, verificar conectividad read-only.
4. Si el componente es schema, ejecutar el checker read-only.
5. Si el componente es uploads/storage, verificar existencia y permisos del
   directorio sin crear archivos permanentes.
6. Recuperar readiness antes de considerar cerrado el incidente.

No hacer:

- ejecutar operaciones destructivas;
- mostrar rutas internas, SQL o secretos;
- confundir estado `degraded` con caida total.

### 23.3 Errores `5xx` repetidos

Senales:

- Metrica `http.response.5xx.count` aumenta repetidamente.
- Alerta `http_5xx_repeated` activa.
- Logs `unhandled_exception` con request/correlation ID.

Acciones:

1. Agrupar por ruta normalizada, metodo y ventana temporal.
2. Revisar clase segura del error en logs.
3. Reproducir la operacion en entorno controlado si es posible.
4. Verificar si readiness tambien esta afectado.
5. Aplicar correccion puntual o rollback operativo segun impacto.

No hacer:

- registrar payloads completos;
- devolver stack traces al usuario;
- clasificar errores esperables `4xx` como incidente critico.

### 23.4 Fallo de base de datos

Senales:

- Check `database` o `database_schema` en estado `unhealthy`.
- Errores operativos de conexion.
- Divergencias detectadas por `check_database_schema.py`.

Acciones:

1. Confirmar host y base objetivo sin exponer credenciales.
2. Probar conectividad con operacion read-only.
3. Ejecutar `check_database_schema.py`.
4. Si hay divergencia, detener despliegues y no cerrar etapa con schema
   inconsistente.
5. Usar procedimientos de ETAPA 92 para backup/restore si se requiere
   recuperacion.

No hacer:

- modificar datos como diagnostico;
- ejecutar `drop_all`;
- corregir schema manualmente sin decision y respaldo operativo.

### 23.5 Backup o restore fallido

Senales:

- Metrica `backup.run.count` o `restore.run.count` con `result=failed`.
- Alertas `backup_failed` o `restore_failed`.
- Evidencia de backup/restore ausente, ilegible o no exitosa.

Acciones:

1. Verificar manifiesto, gzip y SHA-256.
2. Revisar salida operativa del script sin exponer credenciales.
3. Confirmar que directorios operativos esten fuera del repositorio.
4. No sobrescribir `mitienda` durante pruebas de restore.
5. Ejecutar restore solo en base temporal controlada cuando corresponda.
6. Conservar evidencia JSON del resultado.

No hacer:

- borrar backups validos;
- restaurar sobre la base runtime;
- declarar RPO/RTO cumplidos sin prueba real.

### 23.6 Uploads rechazados o storage degradado

Senales:

- Metrica `upload.rejected.count` aumenta repetidamente.
- Alerta `uploads_rejected_repeated` activa.
- Check `uploads_storage` degraded o unhealthy.

Acciones:

1. Distinguir rechazo esperado por tipo o tamano de falla de storage.
2. Verificar permisos del directorio de uploads.
3. Revisar configuracion de tamano permitido y MIME permitido.
4. Confirmar que la respuesta al usuario sea clara y segura.
5. Registrar como deuda operativa si se detectan archivos huerfanos o falta de
   asociacion persistente.

No hacer:

- aceptar tipos arbitrarios;
- guardar nombres originales sensibles en observabilidad;
- crear tablas de archivos sin auditoria del modelo de datos.

## 24. Cierre tecnico de ETAPA 93

ETAPA 93 queda cerrada tecnicamente.

Capacidades cerradas:

- arquitectura operativa mediante contratos estables;
- logging central seguro;
- manejo homogeneo de errores;
- Request Context y correlation ID;
- health checks separados de liveness y readiness;
- metricas operativas minimas con sink local;
- alertas internas mediante contratos, deduplicacion y cooldown;
- runbooks iniciales de operacion.

Validaciones de cierre:

- suite backend completa;
- `compileall app`;
- ESLint de frontend cuando corresponde;
- build frontend;
- `git diff --check`;
- revision de ausencia de caches, secretos y artefactos generados en el
  repositorio.

Limites del cierre:

- no se implementan proveedores externos;
- no se implementan dashboards;
- no se implementa persistencia historica de metricas o alertas;
- no se implementan politicas de guardia ni escalamiento;
- no se crean tablas ni migraciones;
- ownership y ciclo de vida persistente de uploads quedan diferidos.

## 25. Evoluciones operativas futuras

Las siguientes capacidades quedan documentadas como evolucion futura de la
infraestructura creada en ETAPA 93.

No estan implementadas.

No autorizan endpoints, dashboards, tablas, proveedores externos ni
integraciones nuevas sin auditoria y etapa aprobada.

### 25.1 Operations Dashboard

`Operations Dashboard` sera un panel interno de operacion para visualizar el
estado operativo de FeedGo.

Debe reutilizar la infraestructura existente de ETAPA 93.

No debe crear una arquitectura paralela.

Fuentes permitidas:

- Health;
- Metrics;
- Alerts;
- evidencia de backup;
- evidencia de restore;
- estado seguro de componentes.

Vista minima esperada:

- liveness y readiness;
- estado de componentes;
- metricas operativas principales;
- alertas activas o suprimidas;
- ultimo backup valido;
- ultima evidencia de restore;
- estado general del sistema.

Limites:

- no reemplaza runbooks;
- no ejecuta operaciones destructivas;
- no muestra secretos, rutas internas sensibles, SQL ni stack traces;
- no mezcla analytics de producto con metricas operativas;
- no introduce proveedores externos por defecto;
- no constituye panel administrativo general.

### 25.2 AI Operations Console

`AI Operations Console` sera una evolucion futura para operacion asistida por
IA.

Cualquier asistente, incluyendo ChatGPT, Codex u otra herramienta futura,
debera diagnosticar y auditar exclusivamente a partir de las fuentes
operativas oficiales.

Fuentes permitidas:

- `OperationEvent`;
- Request Context;
- Health;
- Metrics;
- Alerts.

Reglas:

- no debe usar memoria conversacional como fuente de verdad operativa;
- no debe consultar datos de negocio privados sin finalidad aprobada;
- no debe leer payloads completos, secretos, tokens ni credenciales;
- no debe duplicar logs, metricas, alertas ni health;
- no debe crear una arquitectura de diagnostico paralela;
- no debe ejecutar acciones correctivas sin autorizacion explicita y flujo
  operativo aprobado.

La consola asistida por IA puede explicar estado, correlacionar senales y
proponer pasos de diagnostico, pero no reemplaza decisiones humanas,
procedimientos oficiales, runbooks ni controles de seguridad.

La proxima etapa oficial es ETAPA 94 - QA Integral y Hardening Funcional.

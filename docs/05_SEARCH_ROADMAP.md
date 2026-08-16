# Roadmap Oficial de Evolucion de FeedGo

Estado del documento: Documento Oficial del Sistema de Gobierno FeedGo v1.0.
Version: 1.0.
Categoria: Sistema de Gobierno.
Nivel de autoridad: Alto para secuencia oficial de etapas y alcance aprobado
por etapa.
Documento dueno: `docs/05_SEARCH_ROADMAP.md`.
Responsable funcional: Roadmap de producto y arquitectura.
Documentos relacionados: `00_GOVERNANCE.md`, `04_CURRENT_STAGE.md`,
`07_DECISIONS.md`, `15_LEGAL_AND_OPERATIONAL.md`,
`16_DATA_INTEGRITY_AND_RECOVERY.md`.
Cuando debe consultarse: antes de proponer, iniciar, diferir, cerrar o
reordenar etapas.

El Roadmap representa el plan oficial de evolucion de FeedGo.

Debe mantenerse actualizado durante todo el proyecto.

Cualquier evolucion del roadmap debe seguir el procedimiento formal definido en
`00_GOVERNANCE.md`.

La busqueda sigue siendo uno de los dominios principales de FeedGo, pero el
roadmap gobierna tambien disponibilidad, agenda, reservas, notificaciones,
comunicaciones, inventario, productos, IA, lanzamiento y futuras capacidades.

No documenta conversaciones.

No documenta hipotesis.

No documenta auditorias.

Documenta unicamente trabajo aprobado.

## Estados

☑ Cerrado

◐ En curso

☐ Pendiente

⊘ Pospuesto

## Prioridades

P0

Obligatorio.

P1

Importante.

P2

Mejora futura.

## Regla

Solo la etapa actual podra estar completamente desarrollada.

Las etapas futuras deberan contener unicamente:

- nombre
- objetivo
- estado

Se desarrollaran cuando pasen a ser la etapa activa.

Toda etapa cerrada debera reflejarse tambien en:

- documentacion tecnica;
- decisiones permanentes;
- principios de ingenieria;

cuando corresponda.

## Roadmap

### ☑ ETAPA 83

Sistema de Indexacion y Knowledge Base.

Estado:

Cerrada.

---

### ☑ ETAPA 84

Consolidacion de arquitectura del Buscador.

Estado:

Cerrada.

---

### ☑ ETAPA 85

Documento de Indice e Indices Sintetizados.

Estado:

Cerrada.

P0

- ☑ Crear Documentos de Gobierno.
- ☑ Definir filosofia del Documento de Indice.
- ☑ Definir que representa una entidad indexable.
- ☑ Definir identidad principal y cobertura secundaria.
- ☑ Definir que las publicaciones enriquecen el espacio.
- ☑ Definir origen, evidencia, confianza y peso.
- ☑ Definir runtime liviano e indexacion pesada.
- ☑ Crear documentacion oficial.
- ☑ Definir separacion entre Taxonomia estable y Knowledge System dinamico.
- ☑ Definir naturaleza del Documento de Indice.
- ☑ Definir que el Documento de Indice es un artefacto derivado.
- ☑ Definir la regeneracion mediante el Indexador.
- ☑ Definir que el Buscador consume conocimiento y no lo genera.
- ☑ Aprobar el contrato conceptual basado en bloques de conocimiento.
- ☑ Auditar componentes existentes reutilizables para Conceptos y Relaciones.
- ☑ Disenar el contrato conceptual de Concepto.
- ☑ Disenar el contrato conceptual de Relacion.
- ☑ Implementar contrato inicial de Concept.
- ☑ Implementar contrato inicial de Relation.
- ☑ Implementar Graph Service inicial en memoria.
- ☑ Auditar integracion entre Taxonomia estable y Knowledge Graph.
- ☑ Implementar proyeccion inicial Taxonomia a Knowledge Graph en memoria.
- ☑ Disenar el contrato conceptual del Documento de Indice de Comercio.
- ☑ Disenar contrato del Documento de Indice.
- ☑ Disenar el pipeline conceptual de construccion del Commerce Index Document.
- ☑ Definir bloques conceptuales del Commerce Index Document.
- ☑ Definir reglas de regeneracion e invalidacion del Commerce Index Document.
- ☑ Definir estrategia conceptual de escalabilidad del proceso de indexacion.
- ☑ Disenar estrategia conceptual de actualizacion.
- ☑ Disenar estrategia conceptual de reindexacion.
- ☑ Auditoria final documental.
- ☑ Cierre de ETAPA 85.

No forman parte del cierre de ETAPA 85:

- implementacion interna del modulo Indexador;
- implementacion del Commerce Index Document;
- Documento de Indice de Publicacion;
- Indices Sintetizados fisicos;
- persistencia;
- integracion con Discovery, Candidate Engine y Ranking.

---

### ☑ ETAPA 86 - Implementacion del Indexador

Estado:

Cerrada.

Objetivo:

Construir progresivamente el modulo Indexador sobre los contratos y decisiones
aprobados en ETAPA 85.

P0

- ☑ Auditar arquitectura existente para disenar el modulo Indexador.
- ☑ Disenar arquitectura interna del modulo Indexador.
- ☑ Implementar estructura base del modulo `backend/app/modules/indexer/`.
- ☑ Implementar contratos de dominio del `CommerceIndexDocument`.
- ☑ Implementar `SourceSnapshots`.
- ☑ Implementar contratos de evidencias y trazabilidad.
- ☑ Implementar contrato compartido de normalizacion de texto.
- ☑ Implementar Collectors de Comercio, Taxonomia, Contenido, Senales y Knowledge Graph.
- ☑ Implementar Builders de Identidad, Perfil Publico y Cobertura Geografica.
- ☑ Implementar Builders de Conocimiento Semantico y Contexto Derivado.
- ☑ Implementar Builders de Intenciones y Representacion de Busqueda.
- ☑ Implementar Builders de Senales, Evidencias y Trazabilidad.
- ☑ Implementar `IndexDocumentValidationService`.
- ☑ Implementar `CommerceIndexerService`.
- ☑ Validar auditoria final de integracion.
- ☑ Corregir duplicacion del contrato `TextNormalizationContract`.
- ☑ Actualizar documentacion oficial de cierre.

Fuera de alcance:

- persistencia;
- reindexacion;
- Indices Sintetizados fisicos;
- scheduler;
- colas;
- integracion con Discovery;
- integracion con Candidate Engine;
- integracion con Ranking.

---

### ☑ ETAPA 87

Sistema de Disponibilidad.

Estado:

Cerrada.

P0

- ☑ Auditar disponibilidad, frontend, UX y permisos.
- ☑ Definir estado publico del espacio: `Activo` / `En pausa`.
- ☑ Definir estado horario: `Abierto` / `Cerrado` / `No hay horarios declarados`.
- ☑ Definir que horarios declarados son fuente de verdad.
- ☑ Definir que el estado horario no excluye de busqueda.
- ☑ Disenar implementacion tecnica del Sistema de Disponibilidad.
- ☑ Implementar persistencia y contratos de horarios habituales.
- ☑ Implementar servicio de lectura, reemplazo, solapamientos y estado horario.
- ☑ Implementar endpoints `GET` y `PUT` bajo `/comercios/{comercio_id}/horarios`.
- ☑ Integrar estado horario en detalle, `/comercios/mis` y `/comercios/activos`.
- ☑ Implementar visualizacion frontend y editor del propietario.
- ☑ Validar schema fisico contra `Base.metadata` y MySQL.
- ☑ Cerrar tecnicamente ETAPA 87.

---

### ☑ ETAPA 88

Agenda y Reservas.

Estado:

Cerrada.

Objetivo:

Disenar e implementar progresivamente una Agenda privada para propietarios y un
sistema de Reservas/Solicitudes opcional, manteniendo separados Availability,
Agenda y Reservas.

P0

- ☑ 88.1 - Infraestructura reutilizable de modal y ActiveLayer - Cerrada.
- ☑ 88.2 - Diseno funcional y modularidad - Cerrada.
- ☑ 88.3 - Documento tecnico definitivo - Cerrada.
- ☑ 88.4 - Auditoria de modelo de datos y contratos conceptuales - Cerrada a
  nivel de arquitectura y modelo conceptual.
- ☑ 88.5.1 - Base del modulo Agenda: `ContextoAgendable` y
  `ElementoAgenda`.
- ☑ 88.5.2 - Correccion del ciclo de vida y borrado no destructivo.
- ☑ 88.5.3 - Auditoria final y creacion fisica de tablas Agenda mediante el
  mecanismo oficial.
- ☑ 88.5.4 - Contratos privados de Agenda.
- ☑ 88.5.5 - Repositorios y servicios internos de Agenda.
- ☑ 88.5.6 - Auditoria arquitectonica del nucleo Agenda.
- ☑ 88.6.1 - Correccion transaccional de Agenda para transacciones compuestas.
- ☑ 88.6.2 - Auditoria del modelo de integracion FeedGo-Agenda.
- ☑ 88.6.3 - Modelo `FeedGoAgendaContexto`.
- ☑ 88.6.4 - Auditoria final y creacion fisica de
  `feedgo_agenda_contextos`.
- ☑ 88.6.5 - Repositorio de integracion FeedGo-Agenda.
- ☑ 88.6.6 - Diseno del servicio de integracion.
- ☑ 88.6.7 - Servicio interno de integracion FeedGo-Agenda.
- ☑ 88.7 - Diseno de integridad, concurrencia y recuperacion de Agenda.
- ☑ 88.8 - Control optimista de concurrencia en `ElementoAgenda`.
- ☑ 88.9 - Deteccion minima e informativa de solapamientos tecnicos.
- ☑ 88.10 - Endpoints privados minimos de Agenda.
- ☑ 88.11 - Interfaz privada minima de Agenda.
- ☑ 88.11.1 - Auditoria de accesos y Agenda general.
- ☑ 88.11.2 - Endpoint agregado, Agenda general y accesos multiples.
- ☑ 88.11.3 - Auditoria de navegacion y UX de Agenda.
- ☑ 88.11.4 - Correccion de navegacion, botones y cambios sin guardar.
- ☑ 88.12 - Diseno transversal del sistema de notificaciones - Cerrada a
  nivel de arquitectura, sin implementacion.
- [cerrado] 88.13 - Auditoria funcional y arquitectonica profunda de Agenda privada y
  Agenda general.
- [cerrado] 88.14 - Correcciones necesarias de Agenda detectadas por auditoria
  funcional.
- [cerrado] 88.15 - Validacion tecnica integral y decision informada sobre el cierre
  formal de Agenda privada y Agenda general.
- [pospuesto] Notificaciones locales, campana global, contador, listado, marcado
  como leido, configuracion local e integracion minima con Agenda - Diferidas
  fuera del cierre actual de ETAPA 88.
- [pospuesto] Reservas publicas, solicitudes, servicios reservables, recursos,
  capacidad y flujo publico - Diferidas fuera del cierre actual de ETAPA 88.

Alcance final de cierre de ETAPA 88:

- Agenda Core.
- Integracion FeedGo-Agenda.
- Agenda privada por comercio.
- Agenda general del propietario.
- Crear, editar, completar y cancelar elementos.
- Filtros por comercio, tipo, estado y rango temporal.
- Permisos y ownership.
- Versionado optimista y conflictos `409`.
- Solapamientos informativos.
- Manejo correcto de fechas, UTC y elementos de todo el dia.
- Cache e invalidaciones TanStack Query.
- Integracion con ActiveLayer.
- Separacion respecto de Disponibilidad, visibilidad y estado del comercio.

Observaciones no bloqueantes:

- `npm run lint` global mantiene errores ajenos a ETAPA 88.
- No existe suite formal especifica de tests automatizados de Agenda.
- La validacion manual en navegador no fue ejecutada.

Fuera de alcance inicial:

- Reservas publicas;
- notificaciones locales;
- campana global;
- Vista Semana;
- Vista Mes;
- persistencia de ultima vista, filtros o contexto;
- pagos;
- sincronizacion con calendarios externos;
- integraciones externas;
- envio real de correo y WhatsApp;
- web push o mobile push;
- planes comerciales, suscripciones y bloqueo efectivo por plan;
- recursos complejos;
- multiples empleados o profesionales;
- filtros o ranking por agenda;
- exponer la agenda privada completa al cliente.

Pendiente transversal aproximado para una etapa futura de arquitectura
enterprise:

- evaluar la creacion de `docs/09_ARCHITECTURE.md` con una vista enterprise
  del backend, sin duplicar gobierno, decisiones ni documentos tecnicos
  especificos.

### ☑ ETAPA 89

Reorganizacion del Roadmap y Gobierno de Lanzamiento.

Objetivo:

Reorganizar formalmente el roadmap para priorizar un lanzamiento publico
seguro, estable, legalmente preparado y operable.

Estado:

Cerrada.

Incluye:

- convertir Productos e Inventario en trabajo posterior al lanzamiento;
- crear el gobierno legal y operativo transversal;
- ordenar las etapas previas al lanzamiento controlado;
- mantener ETAPA 88 cerrada e iniciar documentalmente ETAPA 90.

### ☑ ETAPA 90

Seguridad, Ownership y Permisos.

Objetivo:

Auditar y endurecer permisos, ownership, rutas privadas, acciones sensibles y
superficies de acceso antes de exponer FeedGo publicamente.

Estado:

Cerrada.

Incluye:

- auditoria integral de endpoints, autenticacion, ownership y superficies
  sensibles;
- aplicacion del contrato `Usuario -> Comercio -> Recurso`;
- ownership backend en publicaciones, historias, secciones, analytics,
  metricas sociales, snapshots, comparacion y score;
- helper central minimo para validar comercio propio;
- logout con autenticacion valida obligatoria;
- bloqueo de mutaciones legacy de Productos hasta definir ownership oficial;
- tests automatizados de autorizacion.

### ☑ ETAPA 91

Cumplimiento Legal, Privacidad y Moderacion.

Objetivo:

Preparar criterios legales, privacidad, contenido publico, denuncias,
moderacion y consentimiento necesarios para operar una aplicacion publica.

Estado:

Cerrada.

Pendiente programado desde ETAPA 90:

- separar schema publico y privado de usuario para no exponer email en
  respuestas publicas.

Subetapas aprobadas:

- 91.1 - Contratos publicos y privados de Usuario: cerrada.
- 91.2 - Clasificacion de datos y contratos de Comercio: cerrada.
- 91.3A - Decision documental y modelo de evidencia: cerrada.
- 91.3B - Implementacion minima de aceptacion y persistencia: cerrada.
- 91.4A - Decision documental de denuncias: cerrada.
- 91.4B - Canal minimo persistente de denuncias: cerrada.
- 91.5 - Auditoria final, limpieza, creacion fisica controlada y cierre:
  cerrada.

Alcance de persistencia autorizado:

- ETAPA 91 mantiene fuera de alcance las modificaciones estructurales generales
  de base de datos.
- 91.3B queda autorizada exclusivamente para una entidad persistente minima,
  separada y de responsabilidad unica para registrar evidencia versionada de
  aceptacion de documentos publicos aplicables a un usuario.
- La decision permanente que define el dueno de esa evidencia queda registrada
  en `DEC-041`.
- La autorizacion no incluye consentimientos comerciales, comunicaciones
  externas, marketing, preferencias avanzadas, paneles administrativos ni
  auditoria general.
- 91.4B queda autorizada exclusivamente para una entidad persistente minima,
  separada y de responsabilidad unica para registrar denuncias de usuarios
  autenticados sobre recursos publicos existentes.
- La decision permanente que define el dueno de esa denuncia queda registrada en
  `DEC-042`.
- La autorizacion de 91.4B no incluye decisiones administrativas de moderacion,
  retiro o restauracion por plataforma, sanciones, roles de moderador, panel
  administrativo, cola operativa compleja, apelaciones, automatizacion, IA ni
  ocultamiento automatico por volumen de denuncias.

Diferidos con dueno:

- ETAPA 92: backups, recuperacion, integridad fisica y procedimientos
  operativos de base de datos.
- ETAPA 93: ownership y asociacion persistente de uploads, eliminacion y
  limpieza de medios, validacion operativa de cargas.
- ETAPA 94: hardening de likes, guardados, seguidores y recursos inexistentes o
  inactivos; idempotencia y consistencia funcional adicional.
- Etapas legales u operativas futuras: documentos legales definitivos,
  reaceptacion por nuevas versiones, tratamiento de usuarios existentes, panel o
  flujo administrativo de moderacion, decisiones, sanciones, apelaciones y rate
  limiting avanzado de denuncias.

### ☑ ETAPA 92

Integridad de Datos, Backups y Recuperacion.

Objetivo:

Validar integridad de datos, estrategia de backups, restauracion, conservacion
y recuperacion operativa.

Estado:

Cerrada.

Subetapas:

- 92.1 - Blindaje operativo y matriz de datos criticos: cerrada.
- 92.2 - Estrategia y herramienta de backup: cerrada.
- 92.3 - Restore seguro y prueba de recuperacion: cerrada.
- 92.3A - Arquitectura extensible de backup/restore: cerrada.
- 92.4 - Prueba real de backup, alineacion y restore temporal: cerrada.
- 92.5 - Auditoria final, documentacion, CHANGELOG y cierre: cerrada.

Documento dueno:

- `16_DATA_INTEGRITY_AND_RECOVERY`.

Alcance confirmado de 92.1:

- scripts de base sin efectos laterales al importar;
- proteccion explicita para operaciones destructivas de desarrollo;
- verificacion read-only de metadata contra base fisica;
- matriz de tablas criticas;
- objetivos iniciales RPO/RTO;
- procedimientos conceptuales de backup y restore para implementar en 92.2 y
  92.3.

Alcance confirmado de 92.2:

- procedimiento oficial de backup MySQL mediante `mysqldump`;
- backup consistente con `--single-transaction`;
- dump restaurable sobre base temporal, sin `--databases`;
- compresion gzip;
- SHA-256 del archivo comprimido;
- manifiesto operativo con duracion, tamano, resultado y estado de copia
  externa;
- manifiesto con conteos criticos para validar restores;
- retencion y rotacion local;
- preparacion para copia externa sin implementarla aun;
- tests con mocks sin ejecutar backups reales.

Alcance confirmado de 92.3:

- procedimiento oficial de restore MySQL mediante cliente `mysql`;
- rechazo del destino runtime `mitienda`;
- aceptacion exclusiva de bases temporales `feedgo_restore_tmp_*`;
- validacion de manifiesto, gzip y SHA-256;
- creacion de base temporal sin sobrescribir bases existentes;
- verificacion de schema mediante herramienta read-only;
- comparacion de conteos de tablas criticas;
- evidencia JSON de restore;
- limpieza de base temporal solo mediante accion explicita;
- tests con mocks sin ejecutar restores reales.

Alcance confirmado de 92.3A:

- contrato `BackupProvider`;
- provider inicial `MySQLDumpBackupProvider`;
- contrato `RestoreProvider`;
- provider inicial `MySQLClientRestoreProvider`;
- contrato `BackupStorage`;
- storage local inicial;
- servicios de backup y restore como orquestadores;
- manifiesto versionado y neutral compatible con el formato previo;
- preparacion para futuros providers sin implementar RDS, Percona,
  almacenamiento externo ni PITR.

Alcance confirmado de 92.4:

- auditoria segura del entorno MySQL local `mitienda`;
- backup precautorio real previo a cambios de schema;
- alineacion fisica de `comercios.rubro_id -> rubros.id` mediante script
  controlado y confirmacion explicita;
- checker profundo con 27 tablas metadata, 27 tablas fisicas y cero diferencias
  de columnas, FKs, indices y uniques;
- backup oficial posterior a la alineacion;
- restore real en base temporal `feedgo_restore_tmp_*`;
- validacion de schema profundo, conteos criticos y smoke checks;
- medicion de duracion de backup, restore y antiguedad del punto recuperado;
- evidencia JSON conservada fuera del repositorio;
- limpieza explicita de base temporal aprobada.

Resultado de cierre:

- Backup oficial validado:
  `C:\FeedGoOps\backups\mysql\mitienda_20260801T181443Z.sql.gz`.
- Evidencia de restore exitoso:
  `C:\FeedGoOps\restore_tmp\evidence\feedgo_restore_tmp_20260801_183100_20260801T182747Z_restore.json`.
- RTO observado: 3.336 s.
- Antiguedad observada del punto recuperado: ~13 minutos, sin declararlo RPO
  garantizado.
- `mitienda` quedo intacta.
- No quedaron bases temporales activas.
- Tests backend: 119 OK.

Diferidos con dueno:

- ETAPA 93: automatizacion operativa inicial, logs, monitoreo, diagnostico,
  configuracion productiva y ownership/ciclo de vida de uploads.
- ETAPA 94: pruebas recurrentes de restore, hardening funcional y validacion de
  relaciones sociales y recursos inexistentes o inactivos.
- Etapas operativas futuras: copia externa cifrada, retencion monitoreada,
  PITR/binlogs, providers RDS/Percona/cloud y simulacros recurrentes.

### ☑ ETAPA 93

Observabilidad y Operacion.

Objetivo:

Preparar logs, monitoreo, diagnostico, configuracion productiva y operacion
minima sin introducir deuda de infraestructura innecesaria.

Estado:

Cerrada.

Subetapas:

- 93.1 - Arquitectura Operativa: cerrada documentalmente.
- 93.2 - Logging Enterprise y Error Handling: cerrada tecnicamente.
- 93.3 - Contexto Operativo y Correlacion: cerrada tecnicamente.
- 93.4 - Health, Readiness y Estado del Sistema: cerrada tecnicamente.
- 93.5 - Metricas y Senales Operativas: cerrada tecnicamente.
- 93.6 - Alertas mediante Contratos: cerrada tecnicamente.
- 93.7 - Runbooks, Validacion y Cierre: cerrada.

Documento dueno tecnico-operativo:

- `docs/17_OBSERVABILITY_AND_OPERATIONS.md`.

Resultado de 93.1:

- arquitectura operativa minima aprobada;
- contratos conceptuales para eventos operativos, contextos, sinks, health y
  registry;
- politica de minimizacion y datos prohibidos;
- separacion entre observabilidad, auditoria, analytics y evidencia de
  backup/restore;
- matriz inicial de configuracion productiva;
- modelo conceptual de health, readiness, liveness y startup;
- catalogo minimo de metricas y alertas sin proveedores externos;
- destino arquitectonico para uploads/storage dentro de ETAPA 93, sin crear
  tablas ni modelos antes de auditar el modelo de datos.

Resultado de 93.2:

- logger central basado en `logging` estandar;
- handlers centrales para excepciones HTTP, validacion y errores no
  controlados;
- sanitizacion de errores para no exponer secretos, tokens, passwords,
  `.env`, payloads ni stack traces al frontend;
- cliente HTTP frontend ajustado para no propagar cuerpos crudos del backend;
- contexto preparado para RequestContext futuro sin iniciar 93.3.

Resultado de 93.3:

- middleware unico de Request Context;
- generacion de `request_id` por request;
- reutilizacion segura de `X-Correlation-ID` recibido o generacion de uno nuevo;
- propagacion contextual durante la request mediante `contextvars`;
- incorporacion automatica de IDs al logger y errores registrados;
- respuesta con headers `X-Request-ID` y `X-Correlation-ID`;
- sin health checks, metricas, alertas, endpoints ni OpenTelemetry.

Resultado de 93.4:

- endpoints `GET /health/live` y `GET /health/ready`;
- checks read-only de API, base de datos, schema, uploads/storage, embeddings,
  evidencia de backup y evidencia de restore;
- mensajes seguros sin secretos, rutas internas, SQL ni stack traces;
- integracion con logger central y Request Context;
- sin metricas, alertas, Prometheus, Grafana, OpenTelemetry, tablas ni
  migraciones.

Resultado de 93.5:

- contratos minimos para metricas `counter`, `duration` y `gauge`;
- sink local inicial en memoria, sin almacenamiento persistente ni exportador;
- catalogo estable de metricas operativas;
- instrumentacion de requests, latencia, `4xx`, `5xx`, errores no controlados,
  autenticacion, autorizacion, readiness, backup, restore, uploads y busquedas
  sin resultados;
- separacion entre metricas, logs, alertas, analytics y evidencia operativa;
- sin Prometheus, Grafana, Sentry, OpenTelemetry, tablas, migraciones ni
  endpoints de metricas.

Resultado de 93.6:

- contratos minimos `AlertRule`, `AlertEvent`, `AlertSeverity` y `AlertSink`;
- engine interno de evaluacion de reglas;
- sink local inicial en memoria, sin proveedor externo;
- reglas iniciales para readiness `unhealthy`, errores `5xx` repetidos,
  backup fallido o evidencia no saludable, restore fallido y rechazos repetidos
  de uploads;
- deduplicacion y cooldown por contexto seguro;
- sin email, Slack, Discord, Telegram, Sentry, servicios cloud, dashboards,
  endpoints, tablas ni migraciones.

Pendiente programado desde ETAPA 90:

- endurecer uploads con tamano real permitido, cuota, asociacion con usuario o
  recurso, validacion, limpieza y auditoria.

Resultado de cierre:

- arquitectura operativa mediante contratos estables;
- logging central y manejo homogeneo de errores;
- Request Context con `request_id` y `correlation_id`;
- endpoints separados `GET /health/live` y `GET /health/ready`;
- metricas operativas minimas con sink local;
- alertas internas mediante contratos, deduplicacion y cooldown;
- runbooks iniciales para incidentes operativos minimos.

Limites del cierre:

- sin proveedores externos;
- sin dashboards;
- sin endpoints de metricas o alertas;
- sin tablas ni migraciones;
- sin persistencia historica de metricas o alertas;
- ownership y ciclo de vida persistente de uploads quedan diferidos.

### ☑ ETAPA 94

QA Integral y Hardening Funcional.

Objetivo:

Ejecutar validacion integral, corregir defectos comprobados y endurecer los
flujos principales existentes antes del lanzamiento.

Estado:

Cerrada.

Pendientes programados desde ETAPA 90:

- validar existencia y estado de publicaciones antes de operar likes: cerrado;
- validar existencia y estado de comercios antes de operar seguidores: cerrado;
- definir comportamiento `404` o idempotente en relaciones sociales: cerrado.

Subetapas cerradas:

- 94.0 - Matriz de Contratos Funcionales.
- 94.1 - Hardening de Relaciones e Interacciones Persistentes.
- 94.2 - Hardening de Visibilidad Publica.
- 94.3 - Integracion Frontend y Cache.
- 94.4 - QA Integral Basado en Riesgo.
- 94.5 - Estabilizacion y Limpieza Final.

Resultado:

- Relaciones persistentes endurecidas con validacion backend, `404`,
  idempotencia y tests.
- Publicaciones e historias publicas unificadas bajo contratos de visibilidad
  del dominio.
- Frontend alineado para manejar cache, rollback y `404` sin definir reglas de
  negocio.
- Lint frontend sin errores, build OK y suite backend completa OK.

Residuos diferidos no bloqueantes:

- 5 warnings de ESLint.
- Ausencia de infraestructura frontend de tests.
- Posible carrera extrema de likes de historias.
- Browserslist desactualizado y advertencia de chunk grande.
- Warnings historicos de SQLite y `datetime.utcnow()`.

### ☑ ETAPA 95

Experiencia de Lanzamiento y Design System Critico.

Objetivo:

Ajustar la experiencia central de lanzamiento, accesibilidad, responsive y
consistencia visual critica sin convertirlo en una reescritura del sistema de
diseno.

Estado:

Cerrada tecnica y documentalmente.

Pendientes programados desde ETAPA 90:

- corregir funcionamiento, precision, seleccion y persistencia del mapa de
  ubicacion;
- mejorar visualizacion del mapa, marcadores, controles e informacion
  contextual preservando funcionalidades existentes;
- aplicar Cache-First cuando corresponda y evitar recargas o bloqueos
  innecesarios;
- completar revision visual general: efecto burbuja pendiente, fondos,
  contraste, jerarquia visual, legibilidad, identidad visual y accesibilidad.

Subetapa tecnica prevista:

- Sistema global de temas y tokens semanticos, previo al lanzamiento.

Sprints oficiales y estado:

- 95.1 - Integridad funcional del mapa y ubicacion: cerrado tecnicamente. Su
  implementacion consolidada tambien resolvio privacidad geografica,
  geocoding backend, Search territorial, ubicacion dinamica, Cache-First
  geografico, documentos publicos y hardening relacionado;
- 95.2 - UX del mapa, permisos y privacidad: alcance absorbido y validado en
  95.1. No se abre como sprint de implementacion independiente;
- 95.3 - Inventario visual e infraestructura global del tema: cerrado
  tecnicamente;
- 95.4 - Tokens semanticos y componentes compartidos: cerrado tecnicamente;
- 95.5 - Migracion controlada de pantallas criticas: cerrado tecnicamente;
- 95.6 - Consolidacion de accesibilidad, overlays, responsive y consistencia:
  cerrado tecnicamente; accesibilidad, overlays/modales, responsive y
  consistencia final quedaron validados sin modificar comportamiento;
- 95.7 - QA integral, hardening, `Frontend Ownership Audit`, auditoria de
  residuos tecnicos y cierre documental: cerrado. 95.7-A queda respaldado por
  `docs/24_FRONTEND_OWNERSHIP_AUDIT.md`; 95.7-B por
  `docs/25_TECHNICAL_RESIDUE_AUDIT.md`, con siete entradas categoria D
  retiradas y cero residuos reales pendientes; 95.7-C confronto gates,
  riesgos, working tree, suites y documentacion final. Resultado: GO tecnico y
  documental para cerrar ETAPA 95;

Alcance neto de 95.3:

- construir primero un inventario visual completo y trazable de backgrounds,
  textos, bordes, estados, superficies, overlays, navegacion, formularios,
  cards, modales y skeletons existentes;
- identificar el owner natural de la infraestructura global de tema y auditar
  inicializacion, persistencia y aplicacion al documento;
- definir, en un bloque posterior del mismo sprint, el controlador global de
  tema compatible con modo oscuro, claro y configuracion del dispositivo;
- no crear todavia tokens semanticos ni migrar componentes o pantallas: esas
  tareas pertenecen a 95.4 y 95.5;
- no modificar LocationPicker, geocoding, permisos, privacidad, Search
  territorial, ubicacion dinamica ni Cache-First geografico salvo regresion
  objetiva demostrada.

Documento tecnico propietario del inventario y evidencia de 95.3-A:

- `docs/20_FRONTEND_VISUAL_INVENTORY.md`.

Estado interno:

- 95.3-A - Inventario visual completo: cerrado documentalmente;
- 95.3-B - Contrato global del tema, persistencia, inicializacion y estrategia
  anti-flash: cerrado documentalmente en `docs/21_THEME_CONTRACT.md`;
- 95.3-C - Implementacion de infraestructura global y tests del contrato:
  implementada y validada;
- 95.3-D - Auditoria de cierre y hardening de infraestructura: completada;
- Sprint 95.3 - Inventario visual e infraestructura global del tema: cerrado
  tecnicamente;
- 95.4 - Tokens semanticos y componentes compartidos: cerrado tecnicamente;
- 95.4-A - Contrato de tokens semanticos: cerrado documentalmente en
  `docs/22_SEMANTIC_TOKENS_CONTRACT.md`;
- 95.4-B - Fuente CSS, aliases Tailwind, validacion de contraste y adaptacion
  cromatica del efecto burbuja: implementado y validado, sin migracion de
  pantallas;
- 95.4-C - contrato y base compartida de botones/primitives: implementado y
  validado con Button, Surface, controles, Alert y Skeleton,
  sin adopcion de consumidores;
- 95.4-D - validacion final, hardening de API compartida y cierre tecnico de
  95.4: completado con 63 tests frontend, lint sin errores y build productivo
  correcto, sin adopcion de consumidores;
- 95.5 - Migracion controlada de pantallas criticas: cerrado tecnicamente;
- 95.5-A - primera migracion controlada: debe implementar obligatoriamente el
  selector visible de apariencia en `Perfil -> Editar perfil`, consumiendo solo
  `preference` y `setPreference(...)`; su ausencia bloquea el cierre de ETAPA
  95. Estado: implementado y validado junto con la migracion semantica de la
  superficie Editar perfil, sin migrar otras pantallas;
- 95.5-B - Registro y autenticacion relacionada: implementado y validado con
  checkboxes y enlaces legales, submit, login y navegacion preservados; no se
  migraron superficies ajenas a Auth;
- 95.5-C - Explorar: implementado y validado visualmente; preserva Search,
  contexto territorial, privacidad, Cache-First, query keys y navegacion, y
  migra solo los owners visuales compartidos necesarios; evidencia: 83 tests
  frontend correctos, lint sin errores y build productivo correcto;
- 95.5-D - Feed: implementado y validado mediante tokens/primitives en Feed,
  cards, barra de historias, estados e interacciones; preserva Cache-First,
  optimistic updates, requests, historias, media y navegacion; evidencia: 93
  tests frontend correctos, lint sin errores y build productivo correcto;
- 95.5-E - Ranking / Tendencias: implementado y validado en su shell y estados,
  reutilizando `PublicacionCard` y preservando query key, orden, Cache-First,
  optimistic updates y rollback; incluye correccion central del alias Tailwind
  de roles de texto; evidencia: 101 tests frontend correctos, lint sin errores
  y build productivo correcto;
- 95.5-F - Seguidos: implementado y validado en shell, tabs, cards y estados;
  reutiliza `GeographicContextControls` y preserva query key,
  `positionRevision`, `staleTime`, Cache-First, permisos, distancia y privacidad;
  evidencia: 107 tests frontend correctos, lint sin errores y build productivo
  correcto;
- 95.5-G - Perfil / identidad visible de usuario: implementado sobre `/perfil`
  mediante tokens y primitives, preservando carga, avatar, edicion, logout,
  navegacion y acciones; el sistema no posee perfil publico de terceros y el
  bloque no inventa esa funcionalidad; evidencia: 114 tests frontend correctos,
  lint sin errores y build productivo correcto;
- 95.5-H - Alta, edicion y administracion de espacios: implementado en el
  formulario compartido, listado, `LocationPicker` y editor de horarios;
  preserva payloads, endpoints, privacidad, Geoapify, branding, ownership y
  Cache-First existente; evidencia: 123 tests frontend correctos, lint sin
  errores y build productivo correcto;
- 95.5-I - Perfil publico de espacio: implementado mediante tokens/primitives
  en shell, identidad, informacion publica, acciones, publicaciones, estados y
  overlays propios; preserva detalle, privacidad backend-owned, seguimiento,
  Cache-First y los owners independientes de Historias, Agenda y Moderacion;
  evidencia: 129 tests frontend correctos, lint sin errores y build productivo
  correcto;
- 95.5-J - Historias: implementado con `HistoriasViewer` bajo contrato local de
  apariencia fija validada y formulario de creacion tematizado; preserva RAF,
  navegacion, media, likes, upload, payload y callbacks; evidencia: 140 tests
  frontend correctos, lint sin errores y build productivo correcto;
- 95.5-K - Agenda y reservas: implementado en Agenda general y privada sobre
  `ActiveLayer`, con vista diaria, filtros, formulario, listados y estados
  semanticos; preserva Cache-First, fechas, versionado, mutaciones e
  invalidaciones; evidencia: 147 tests frontend correctos, lint sin errores y
  build productivo correcto;
- 95.5-L - Superficies legales: implementado en Terminos y Politica de
  Privacidad mediante un shell compartido, tokens, `Surface` y `Alert`;
  preserva contenido juridico, rutas, versionado backend-owned, enlaces y
  aceptaciones de Registro; evidencia: 152 tests frontend correctos, lint sin
  errores y build productivo correcto;
- 95.5-M - Auditoria visual transversal: revalida light/dark por superficie,
  corrige centralmente la precedencia CSS de `interactive-bubble` sobre las
  variantes de Button y registra exactamente tres superficies residuales:
  Home, detalle de publicacion y DenunciaModal;
- 95.5-N - Detalle de publicacion y DenunciaModal: migrados con tokens,
  primitives y ActiveLayer, preservando query cache, interacciones, media,
  payload de denuncia y bloqueo durante mutaciones; queda Home como unica
  superficie visual pendiente;
- la cobertura acumulada, excepciones y pendientes se controlan en
  `23_FRONTEND_VISUAL_COVERAGE.md`;
- gate acumulado de 95.5: antes de cerrar debe existir una matriz exhaustiva
  `migrado / excepcion justificada / pendiente` para todas las superficies
  reales; cualquier pendiente bloquea el cierre y la mezcla visual solo es
  transitoriamente valida mientras el sprint permanece abierto;
- el QA final de 95.5 debe validar light, dark, cambio runtime, contraste,
  navegacion, layouts, formularios, cards, capas, estados, loaders, skeletons,
  responsive y botones; defectos compartidos se corrigen por owner desde
  tokens y primitives, no con colores fisicos locales;
- migracion de pantallas y creacion de primitives permanecen fuera de 95.4-B.

El refinamiento visual residual del mapa no reabre 95.1: se evalua junto con
accesibilidad, responsive y consistencia transversal en 95.6. La
`Frontend Ownership Audit` permanece obligatoria en 95.7 antes del cierre de
ETAPA 95 y no se ejecuta durante este checkpoint. En el mismo gate debe
ejecutarse una auditoria separada de residuos creados durante la etapa:
scripts y archivos temporales, tests/mocks auxiliares, debugging e
instrumentacion, TODO/FIXME introducidos, imports/codigo/helpers/componentes
sin uso, CSS/clases antiguas, duplicados, adapters/providers abandonados,
artefactos Nominatim, validacion Geoapify y migraciones one-shot. Cada elemento
debe clasificarse con evidencia como `conservar permanentemente`,
`mover/reubicar`, `documentar` o `eliminar por residuo`. No se autoriza una
eliminacion automatica ni remover tests que mantengan valor de regresion. La
auditoria y la limpieza/documentacion resultante bloquean el cierre final de
ETAPA 95, pero no se ejecutan durante 95.5.

Alcance:

- auditar el frontend completo antes de modificar colores;
- localizar colores rigidos de fondo, texto y borde, clases utilitarias de
  blanco/negro, hexadecimales directos, estilos inline de color, overlays,
  portales, modales y componentes con colores locales;
- disenar tokens semanticos para `background`, `foreground`, `surface`,
  `surface-elevated`, `border`, `muted`, `primary`, `danger`, `success`,
  `warning`, `overlay`, `input`, `disabled`, `focus` y `skeleton`;
- definir valores consistentes para modo oscuro, modo claro y configuracion del
  dispositivo;
- implementar un controlador global del tema con tema seleccionado, tema
  resuelto, aplicacion al documento, persistencia local, deteccion de
  `prefers-color-scheme`, respuesta a cambios del sistema y prevencion de
  destellos incorrectos al cargar;
- ofrecer las opciones usar configuracion del dispositivo, modo claro y modo
  oscuro;
- mantener modo oscuro como valor predeterminado inicial salvo decision
  documental posterior;
- migrar primero componentes compartidos como botones, inputs, modales, cards,
  headers, navegacion, menus, skeletons, overlays, estados vacios y mensajes de
  error o exito;
- migrar pantallas por grupos controlados, sin reemplazos automaticos masivos;
- validar feed, buscador, historias, perfiles, agenda, disponibilidad, mapa,
  cards, formularios, menus, modales, elementos deshabilitados, hover, focus,
  errores, advertencias, skeletons, contraste y legibilidad.

Regla futura:

- ningun componente nuevo debera usar colores rigidos de fondo, texto o borde
  cuando esos colores pertenezcan al tema; debera usar tokens semanticos
  compatibles con modo claro y oscuro.

Persistencia:

- la primera implementacion usara `localStorage`;
- la sincronizacion entre dispositivos queda como evolucion posterior;
- antes de agregar columnas o tablas para preferencias de apariencia debera
  auditarse el modelo de usuarios y justificarse el dueno natural conforme al
  Gobierno del Modelo de Datos.

Criterios de cierre:

- inicio directo validado en modo oscuro;
- inicio directo validado en modo claro;
- modo del sistema validado;
- cambio en tiempo real validado;
- persistencia tras recargar validada;
- navegacion entre pantallas validada;
- modales y portales validados;
- contraste y accesibilidad validados;
- ausencia de destellos blancos validada;
- ausencia de regresiones funcionales validada.

Diferenciacion:

- esta subetapa no reemplaza la correccion funcional del mapa;
- no reemplaza la mejora visual del mapa;
- no reemplaza la revision general de colores de fondo;
- no reemplaza la aplicacion del efecto burbuja en botones faltantes;
- esas tareas pueden preparar la consistencia visual, pero el sistema de temas
  tendra alcance tecnico propio.

### ☑ ETAPA 96

Plataforma Instalable y PWA Enterprise.

Objetivo:

Convertir FeedGo en una PWA completa, segura, actualizable, resiliente y
verificable, apta como primer canal oficial de distribucion multiplataforma y
preparada para pruebas masivas, beta publica y lanzamiento controlado.

Estado:

Cerrada. Sprints 96.1, 96.2 y 96.3 completados. La infraestructura PWA,
identidad instalada, runtime, offline controlado, actualizacion, recuperacion y
harness browser quedaron implementados y validados. Los gates que requieren
dominio, HTTPS, hosting, API/CORS productivos y despliegue real pertenecen a
ETAPA 100. El defecto especifico de videos de Historias en iOS/Safari/PWA no se
declara resuelto: queda diferido a ETAPA 114 con su evidencia diagnostica
preservada.

### ☐ ETAPA 97

Administracion Operativa Minima.

Objetivo:

Implementar o preparar las capacidades minimas para operar, revisar y resolver
incidentes de una primera version publica controlada.

Incluye como evolucion futura posible, sin implementacion aprobada todavia, un
Operations Dashboard interno y una AI Operations Console basados en la
infraestructura operativa creada en ETAPA 93.

Estado:

Pendiente.

### ☐ ETAPA 98

Correccion y Pulido Visual del Frontend.

Objetivo:

Revisar y emprolijar como producto terminado todo lo que realmente ve el
usuario, sin agregar funcionalidades ni cambiar logica de negocio.

Alcance:

- recorrer mediante render real todas las superficies vigentes, incluyendo
  Home, autenticacion, perfiles, Explorar, Feed, Ranking, Seguidos, espacios,
  publicaciones, creacion/edicion, Agenda, Historias, legales, navegacion,
  formularios, modales, overlays y estados loading/error/empty;
- revisar botones, textos, tipografia, spacing, alineacion, cards, iconos,
  formularios, navegacion, modales, estados, light/dark, responsive visible y
  consistencia general en movil y desktop;
- corregir desde `tokens -> primitives -> shared -> dominio -> pantalla`, sin
  parches repetidos ni refactors masivos;
- exigir evidencia humana/renderizada y capturas/comparaciones cuando sea
  tecnicamente posible; tests estaticos complementan pero no reemplazan esa
  evidencia;
- clasificar por separado cualquier bug funcional y resolverlo desde su owner,
  sin usar esta etapa para cambiar Search, ranking, privacidad,
  geolocalizacion o arquitectura.

Gate:

- todas las superficies reales revisadas;
- cero defectos visuales bloqueantes conocidos;
- botones, textos y controles legibles;
- movil/desktop y light/dark consistentes;
- todos los hallazgos corregidos o justificados;
- tests, lint y build correctos.

Estado:

Pendiente.

### ☐ ETAPA 99

Identidad, Registro y Autenticacion.

Objetivo:

Auditar, disenar e implementar de forma controlada una identidad FeedGo
central con registro personal de minima friccion y metodos de acceso seguros,
sin mezclar la cuenta de usuario con la creacion o administracion de espacios.

Alcance inicial sujeto a auditoria:

- registro y login existentes, compatibilidad con usuarios actuales y
  hardening backend;
- normalizacion y unicidad de email;
- verificacion de email mediante codigo/token de un solo uso, expiracion,
  reenvio controlado, limites de intentos, rate limiting, antiabuso,
  antienumeracion, observabilidad y recuperacion;
- seleccion futura de proveedor e infraestructura de correo mediante contrato
  desacoplado, sin proveedor predeterminado por este roadmap;
- `Continuar con Google` mediante identidad verificada por backend, vinculada a
  una cuenta FeedGo normal y sin convertir Google en fuente de verdad
  funcional ni en emisor de la sesion FeedGo;
- vinculacion segura de multiples metodos de acceso a una misma identidad,
  evitando usuarios duplicados;
- recuperacion de contrasena si la auditoria confirma que pertenece al mismo
  dominio;
- aceptacion y trazabilidad de Terminos y Privacidad conforme al owner legal;
- revision critica de los datos minimos necesarios para crear una cuenta.

Principios y exclusiones:

- debe comenzar con auditoria de modelo, seguridad, proveedores, privacidad,
  compatibilidad y arquitectura;
- `Usuario FeedGo` es la identidad central; email/password, email verificado y
  Google son credenciales o proveedores vinculados;
- backend conserva validacion, identidad, autorizacion y emision de la sesion
  FeedGo; frontend conserva interaccion y UX;
- no se incorporan secretos OAuth al frontend ni se confian identidades
  declaradas solamente por el cliente;
- registrarse no crea un espacio. El onboarding comercial/profesional de un
  espacio conserva sus datos, reglas y owners propios;
- Google Sign-In no es fuente de ubicacion. GPS, ciudad declarada y fallback
  geografico conservan los owners vigentes;
- no pertenecen a esta etapa datos de disponibilidad, agenda, facturacion,
  catalogo, clasificados ni otros dominios futuros.

Dependencias:

- ETAPA 96 debe cerrar sin incorporar esta reforma de Auth;
- antes de implementar correo real debe coordinarse el contrato transversal de
  comunicaciones sin duplicar la futura ETAPA 104;
- cualquier modelo, tabla, proveedor o tratamiento personal nuevo requiere la
  auditoria y aprobacion documental aplicable.

Estado:

Pendiente. No iniciada.

### ☐ ETAPA 100

Infraestructura y Lanzamiento Controlado.

Objetivo:

Preparar despliegue, configuracion productiva, checklist final y publicacion
controlada de FeedGo.

Estado:

Pendiente.

### ☐ ETAPA 101

Analytics y Aprendizaje de Uso Real.

Objetivo:

Medir uso real de manera respetuosa de privacidad para orientar decisiones
posteriores al lanzamiento.

Estado:

Pendiente.

### ☐ ETAPA 102

Calidad de Datos y Conocimiento Administrable.

Objetivo:

Mejorar datos, conocimiento administrable y trazabilidad de informacion usada
por busqueda, descubrimiento y futuras capacidades inteligentes.

Estado:

Pendiente.

### ☐ ETAPA 103

Reservas Publicas y Carrito de Reserva.

Objetivo:

Disenar e implementar solicitudes publicas, servicios reservables y flujo de
reserva sin pagos, sin exponer la agenda privada completa del propietario.

Estado:

Pendiente.

### ☐ ETAPA 104

Mensajeria y Cotizaciones.

Objetivo:

Disenar e implementar comunicaciones externas transversales y reutilizables
para FeedGo, incluyendo correo, WhatsApp, destinos verificables, proveedores,
plantillas, infraestructura asincronica, reintentos, idempotencia, webhooks,
observabilidad y futuras politicas de capacidades comerciales.

Estado:

Pendiente.

### ☐ ETAPA 105

Catalogo de Productos y Disponibilidad Simple.

Objetivo:

Disenar e implementar productos o catalogo comercial simple, disponibilidad no
marketplace y datos comerciales minimos solo si la evidencia de uso lo
justifica.

Estado:

Pendiente.

Pendiente programado desde ETAPA 90:

- revisar Productos legacy y definir ownership oficial antes de habilitar
  mutaciones de catalogo o inventario.

### ☐ ETAPA 106

Promociones y Fidelizacion.

Objetivo:

Explorar promociones, beneficios y mecanismos de fidelizacion posteriores al
lanzamiento basados en uso real.

Estado:

Pendiente.

### ☐ ETAPA 107

Opiniones y Motor de Reputacion.

Objetivo:

Disenar reputacion, opiniones y senales publicas con moderacion, seguridad y
prevencion de abuso.

Estado:

Pendiente.

### ☐ ETAPA 108

Notificaciones Inteligentes.

Objetivo:

Disenar e implementar notificaciones locales y futuras notificaciones
inteligentes, reutilizando la infraestructura transversal que corresponda.

Estado:

Pendiente.

### ☐ ETAPA 109

Preferencias, Recomendaciones y Contexto.

Objetivo:

Incorporar preferencias, contexto y recomendaciones basadas en uso real,
privacidad y control del usuario.

Estado:

Pendiente.

### ☐ ETAPA 110

IA Conversacional.

Objetivo:

Evaluar e incorporar IA conversacional cuando existan datos, gobernanza y
necesidades de producto suficientes.

Estado:

Pendiente.

### ☐ ETAPA 111

Tendencias, Oferta, Demanda y Motor Predictivo.

Objetivo:

Construir senales predictivas y analiticas avanzadas posteriores al
lanzamiento.

Estado:

Pendiente.

### ☐ ETAPA 112

Ranking Dinamico y Descubrimiento Proactivo.

Objetivo:

Evolucionar ranking y descubrimiento con senales reales, trazabilidad y
controles de calidad.

Estado:

Pendiente.

### ☐ ETAPA 113

Plataforma Comercial y Backend Universal.

Objetivo:

Evaluar la expansion hacia capacidades comerciales y backend universal despues
de validar uso real, operacion y necesidades del producto.

Estado:

Pendiente.

### ☐ ETAPA 114

Compatibilidad Multimedia iOS/Safari/PWA.

Objetivo:

Retomar mediante diagnostico reproducible y dispositivos fisicos la
compatibilidad multimedia de Historias con video, sin reabrir la arquitectura
PWA general ni aplicar workarounds por hipotesis.

Alcance inicial obligatorio:

- Historias con video en Safari de iPhone e iPad y en PWA instalada iOS/iPadOS;
- comparacion entre Safari normal y modo standalone;
- lifecycle de `<video>`, autoplay, muted, playsInline, preload, source,
  cleanup, background/foreground y cambios entre Historias;
- contenedor, MIME, codecs, URLs, assets locales/remotos y Range requests
  cuando la evidencia los haga relevantes;
- reproduccion despues de navegar, abrir, cerrar y reabrir el viewer;
- reanudacion del diagnostico Caso B preservado en
  `frontend/.pwa-fixtures/story-video-case-b.html`;
- validacion en dispositivos fisicos y regresiones Android y desktop.

Estado:

Pendiente. Defecto conocido diferido; etapa no iniciada.

## Vision futura complementaria

Esta seccion registra una vision futura de evolucion enterprise posterior o
complementaria al roadmap vigente.

No modifica el roadmap actual.

No renombra etapas ya aprobadas.

No autoriza implementacion.

Propuesta conceptual:

- Optimizacion Enterprise.
- Administracion Multi-Espacio.
- Growth, Marketing y Adopcion.
- Frontend Enterprise.
- Frontend Comercial.

La administracion multi-espacio basica ya es posible con el ownership actual:
un usuario puede administrar varios espacios vinculados a su cuenta. La futura
Administracion Multi-Espacio debera resolver transferencia, delegacion,
colaboradores, permisos compartidos y administracion multiusuario sin asumir
que esas capacidades existen hoy.

Esta vision debera revisarse formalmente antes de cualquier reorganizacion del
roadmap. Mientras no exista decision posterior, prevalecen las etapas 102 a 114
ya definidas en este documento.

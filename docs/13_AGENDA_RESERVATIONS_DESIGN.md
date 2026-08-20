# Diseno de Agenda y Reservas

Estado del documento: Documento Tecnico Oficial de FeedGo v1.0.
Version: 1.0.
Categoria: Documento Tecnico.
Nivel de autoridad: Tecnico especializado para Agenda, FeedGo-Agenda y futura
integracion de Reservas.
Documento dueno: `docs/13_AGENDA_RESERVATIONS_DESIGN.md`.
Responsable funcional: Agenda y Reservas.
Documentos relacionados: `00_GOVERNANCE.md`, `01_ENGINEERING.md`,
`02_PRODUCT.md`, `05_SEARCH_ROADMAP.md`,
`12_AVAILABILITY_DESIGN.md`, `14_NOTIFICATIONS_DESIGN.md`.
Cuando debe consultarse: antes de modificar Agenda Core, FeedGo-Agenda,
Agenda privada, Agenda general, ActiveLayer aplicado a Agenda, concurrencia de
Agenda, solapamientos, integracion futura con Reservas o cualquier frontera
entre Availability, Agenda, Reservas y Notificaciones.

## Estado

ETAPA 88 esta cerrada formalmente.

Estado comprobado:

- ETAPA 88.1 - Infraestructura reutilizable de modal y ActiveLayer: cerrada.
- ETAPA 88.2 - Diseno funcional y modularidad: cerrada.
- ETAPA 88.3 - Diseno tecnico definitivo: cerrada.
- ETAPA 88.4 - Auditoria de modelo de datos y contratos conceptuales: cerrada.
- ETAPA 88.5 - Nucleo backend de Agenda privada: implementado.
- ETAPA 88.6 - Integracion FeedGo-Agenda: implementada.
- ETAPA 88.7 - Diseno de integridad, concurrencia y recuperacion: registrado.
- ETAPA 88.8 - Optimistic locking de `ElementoAgenda`: implementado.
- ETAPA 88.9 - Deteccion tecnica informativa de solapamientos: implementada.
- ETAPA 88.10 - Endpoints privados minimos: implementados.
- ETAPA 88.11 - Frontend privado, Agenda general y accesos multiples:
  implementados y validados.
- ETAPA 88.13 - Auditoria funcional y arquitectonica profunda de Agenda
  privada y Agenda general: completada.
- ETAPA 88.14 - Correcciones necesarias detectadas por auditoria funcional:
  completada sin defectos bloqueantes pendientes.
- ETAPA 88.15 - Validacion tecnica integral y decision informada sobre cierre
  formal de Agenda privada y Agenda general: aprobada con observaciones no
  bloqueantes.

Resumen operativo:

- Agenda Core: implementada.
- Integracion FeedGo-Agenda: implementada.
- Agenda privada: implementada y validada.
- Agenda general: implementada y validada.
- Arquitectura por capas: corregida para Agenda general.
- Schema fisico MySQL: validado contra modelos.
- Validacion tecnica y funcional integral: aprobada con observaciones no
  bloqueantes.
- Reservas publicas: no iniciadas, fuera del cierre actual de ETAPA 88 y
  planificadas para ETAPA 113 - Reservas Publicas y Carrito de Reserva.
- Notificaciones: disenadas como trabajo futuro, no implementadas.
- Cierre formal de ETAPA 88: completado.

ETAPA 88 esta cerrada.

Observaciones no bloqueantes:

- `npm run lint` global falla por errores ajenos a ETAPA 88;
- no existe suite formal especifica de tests automatizados de Agenda;
- la validacion manual en navegador no fue ejecutada durante la validacion
  automatizada integral.

## Alcance implementado de Agenda privada

Agenda es una herramienta privada de organizacion para propietarios.

El MVP privado implementado permite:

- crear y reutilizar un contexto de Agenda para un comercio propio;
- listar elementos privados por comercio;
- listar una vista general integrada sobre todos los comercios del propietario;
- crear elementos;
- actualizar elementos con control optimista de concurrencia;
- completar o cancelar elementos;
- detectar solapamientos tecnicos e informarlos sin bloquear;
- acceder desde Perfil, tarjetas de espacios y Perfil de comercio;
- usar Agenda individual y Agenda general mediante modales basados en
  ActiveLayer.

No implementa Reservas publicas.

## Arquitectura aprobada

Agenda es un modulo propio y reutilizable dentro del monorepo.

Backend:

```text
backend/app/modules/agenda/
```

Frontend:

```text
frontend/src/features/agenda/
```

Integracion FeedGo:

```text
backend/app/modules/feedgo_agenda/
```

Agenda Core no depende de FeedGo.

FeedGo consume Agenda mediante una frontera explicita de integracion.

Backend es propietario de:

- reglas de negocio;
- validaciones;
- estados;
- permisos;
- conflictos concurrentes;
- consultas;
- persistencia.

Frontend es propietario de:

- UX;
- componentes;
- vistas;
- navegacion;
- formularios;
- consumo de contratos.

El frontend no calcula permisos, ownership, disponibilidad reservable,
solapamientos como politica de negocio ni conflictos concurrentes.

## Modularidad y reutilizacion

Agenda debe poder reutilizarse en otra aplicacion sin reconstruirse desde cero.

La reutilizacion es tecnica, no solo conceptual.

Agenda Core no puede depender fisicamente de tablas, modelos ni migraciones de
FeedGo.

Esta decision no implica:

- microservicio;
- libreria externa;
- otro repositorio;
- arquitectura generica excesiva.

La modularidad se logra con limites internos claros.

No se utiliza el termino `Agenda Engine`.

## Contexto agendable

Agenda pertenece a un `ContextoAgendable`.

En FeedGo, el primer recurso externo vinculado a un contexto agendable es un
`Comercio`.

El nucleo de Agenda no debe nombrar ese contexto como `comercio`.

`ContextoAgendable` es la identidad estable y autonoma del dominio Agenda.

Responsabilidades:

- ser el padre directo de los elementos de Agenda;
- sostener integridad interna sin depender de modelos externos;
- permitir pruebas y migraciones de Agenda sin requerir tablas de una
  aplicacion host;
- permitir que otra aplicacion vincule sus recursos sin modificar el nucleo;
- actuar como frontera estable para futuras Reservas.

`ContextoAgendable` no copia datos del recurso externo.

No copia:

- nombre;
- rubro;
- direccion;
- propietario;
- estado publico;
- datos comerciales del espacio.

Una futura aplicacion medica podria vincular medico, consultorio, profesional,
sede o recurso con `ContextoAgendable` sin modificar Agenda Core.

## Modelo de datos implementado

La auditoria del modelo de datos concluyo que no existia una tabla propietaria
natural para Agenda.

Crear tablas nuevas quedo justificado porque:

- ninguna tabla existente era dueña natural del contexto interno de Agenda;
- extender `comercios` habria acoplado Agenda a FeedGo;
- extender publicaciones, productos, taxonomy, availability o search habria
  mezclado responsabilidades;
- cada tabla creada tiene una unica responsabilidad;
- no se creo una segunda fuente de verdad para datos de comercios.

Tablas implementadas:

### `agenda_contextos_agendables`

Clasificacion: fuente de verdad del nucleo Agenda.

Responsabilidad unica:

- representar el contexto interno y autonomo contra el cual se organizan
  elementos de Agenda.

No contiene datos del comercio ni del host.

Estado:

- `activo`;
- `archivado`.

El archivado no elimina elementos.

### `agenda_elementos`

Clasificacion: fuente de verdad del nucleo Agenda.

Responsabilidad unica:

- representar elementos privados de Agenda asociados a un
  `ContextoAgendable`.

Tipos del MVP:

- `evento`;
- `tarea`;
- `recordatorio`;
- `bloqueo`.

Estados:

- `activo`;
- `completado`;
- `cancelado`.

Incluye `version` para optimistic locking.

`ElementoAgenda` depende unicamente de `ContextoAgendable`.

No tiene FK directa a:

- `comercios`;
- medicos;
- consultorios;
- sedes;
- recursos externos de una aplicacion host.

### `feedgo_agenda_contextos`

Clasificacion: relacion de integracion.

Responsabilidad unica:

- vincular un `Comercio` de FeedGo con un `ContextoAgendable` autonomo.

No duplica:

- usuario;
- propietario;
- nombre;
- rubro;
- direccion;
- estado del comercio.

Restricciones conceptuales:

- relacion inicial 1:1;
- `UNIQUE(comercio_id)`;
- `UNIQUE(agenda_contexto_id)`;
- FK restrictivas;
- sin cascada destructiva hacia Agenda.

## Contratos y schemas

Los contratos privados de Agenda separan:

- lectura interna de contexto;
- cambio de estado de contexto;
- creacion de elemento;
- lectura de elemento;
- actualizacion parcial de elemento;
- cambio de estado;
- filtros de consulta.

Reglas aplicadas:

- titulo no vacio;
- normalizacion minima de espacios;
- datetimes timezone-aware;
- normalizacion interna a UTC;
- rechazo de datetimes ingenuos;
- `fin > inicio` cuando ambos existen;
- `evento` requiere `inicio`;
- `bloqueo` requiere `inicio` y `fin`;
- `recordatorio` requiere `inicio`;
- `tarea` puede no tener fechas;
- `todo_el_dia=True` requiere `inicio`;
- no se aceptan campos externos como `comercio_id`, `medico_id`, `owner_id`,
  `resource_type` o `external_resource_id` dentro de Agenda Core.

## Repositorios, servicios y transacciones

Repositorios Agenda:

- encapsulan ORM;
- ejecutan consultas;
- hacen `flush`;
- no hacen `commit`;
- no hacen `rollback`.

Servicios Agenda:

- aplican reglas de negocio;
- reutilizan repositorios;
- normalizan fechas;
- hacen composicion interna;
- no hacen `commit`;
- no hacen `rollback`.

Caller, ruta o integracion:

- controla `commit`;
- controla `rollback`;
- puede combinar operaciones de Agenda con operaciones del host en una
  transaccion atomica.

No se introdujo Unit of Work global.

La `Session` SQLAlchemy es la unidad transaccional.

## Integracion FeedGo

FeedGo integra sus comercios con Agenda mediante `feedgo_agenda`.

Modelo conceptual:

```text
Comercio
  |
FeedGoAgendaContexto
  |
ContextoAgendable
  |
ElementoAgenda
```

La integracion FeedGo puede conocer:

- `Comercio`;
- usuario autenticado;
- ownership del espacio;
- permisos de FeedGo;
- rutas de FeedGo.

Agenda Core no conoce esos detalles.

El servicio de integracion implementa:

- `obtener_contexto_agenda_para_comercio`;
- `obtener_o_crear_contexto_agenda_para_comercio`.

Reglas:

- consulta `Comercio` directamente por `id`;
- no filtra por `activo`;
- permite comercios pausados;
- valida ownership con `comercio.usuario_id == usuario_autenticado.id`;
- no reactivar automaticamente contextos archivados;
- no crear un segundo contexto si ya existe vinculo;
- crear contexto y vinculo en una unica transaccion;
- recuperar la carrera esperada por `UNIQUE(comercio_id)` sin ocultar otros
  `IntegrityError`.

## Endpoints privados implementados

Router:

```text
/feedgo-agenda
```

Endpoints privados:

```text
POST /feedgo-agenda/comercios/{comercio_id}/contexto
GET  /feedgo-agenda/comercios/{comercio_id}/contexto
GET  /feedgo-agenda/comercios/{comercio_id}/elementos
POST /feedgo-agenda/comercios/{comercio_id}/elementos
PATCH /feedgo-agenda/comercios/{comercio_id}/elementos/{elemento_id}
PATCH /feedgo-agenda/comercios/{comercio_id}/elementos/{elemento_id}/estado
GET  /feedgo-agenda/mis/elementos
```

El endpoint agregado `GET /feedgo-agenda/mis/elementos` devuelve, en una unica
request, elementos de Agenda pertenecientes a todos los comercios del usuario
autenticado.

Esto evita N requests desde el frontend para construir Agenda general.

La Agenda general debe seguir resolviendose desde backend como consulta
agregada estable. El frontend no debe consultar cada comercio de forma
descontrolada ni consolidar ownership, permisos o reglas de negocio.

Las rutas validan ownership en backend.

Los errores de dominio se traducen a HTTP controlado, incluyendo conflicto de
version como `409`.

## Concurrencia

Agenda no usa "ultima escritura gana".

`ElementoAgenda` incluye `version`.

Toda mutacion de elemento debe enviar `version_esperada`.

La actualizacion ocurre solo si:

```text
id coincide
AND contexto_id coincide
AND version coincide con version_esperada
```

Al actualizar, la version se incrementa en uno.

Si la version cambio, la operacion falla con conflicto de concurrencia.

El frontend debe refrescar datos y no reintentar automaticamente.

## Solapamientos tecnicos

Agenda detecta solapamientos tecnicos mediante:

```text
nuevo_inicio < fin_existente
AND
nuevo_fin > inicio_existente
```

Intervalos contiguos no solapan.

Participan inicialmente:

- `bloqueo`;
- `evento` con `inicio` y `fin`.

No participan:

- elementos cancelados;
- recordatorios;
- tareas sin intervalo completo;
- elementos sin `fin`;
- elementos de otro contexto.

La deteccion es informativa.

Agenda no bloquea automaticamente creacion ni actualizacion por solapamiento.

Las politicas de bloqueo, advertencia confirmable, capacidad o doble reserva
pertenecen al modulo consumidor, especialmente Reservas.

## Frontend privado

Feature:

```text
frontend/src/features/agenda/
```

Componentes principales:

- `AgendaPrivadaModal`;
- `AgendaGeneralModal`.

Servicios y hooks:

- servicio HTTP especifico de FeedGo Agenda;
- hooks TanStack Query para contexto, elementos individuales, Agenda general,
  creacion, actualizacion y cambio de estado.

Accesos privados implementados:

1. `ProfilePage` -> tarjeta de cada espacio -> `Agenda`.
2. `/comercios/{comercio_id}` -> propietario -> `Agenda`.
3. `ProfilePage` -> bloque de acciones personales -> `Agenda general`.

Agenda individual permite:

- listar;
- crear;
- editar;
- completar;
- cancelar;
- ver advertencias de solapamiento;
- manejar conflictos `409`.

Agenda general permite:

- opcion `Todos los espacios`;
- seleccion de espacio;
- listado cronologico integrado;
- identificacion visual del comercio de origen;
- filtro por fecha;
- filtros de tipo y estado;
- apertura de Agenda individual del espacio seleccionado.

## Validacion de cierre de Agenda

La validacion tecnica y funcional integral confirmo:

- creacion de elementos;
- listado de elementos por comercio;
- listado agregado de Agenda general del propietario;
- edicion de elementos;
- completar elementos;
- cancelar elementos;
- filtros por comercio, tipo, estado y rango temporal;
- ownership backend para propietario autorizado y usuario no propietario
  rechazado;
- versionado optimista y conflicto `409`;
- solapamientos tecnicos informativos;
- fechas timezone-aware normalizadas a UTC;
- rechazo de datetimes ingenuos;
- elementos de todo el dia;
- comercio pausado sin ruptura de Agenda;
- separacion respecto de Availability, visibilidad publica y estado del
  comercio;
- cache e invalidaciones TanStack Query;
- uso de ActiveLayer para capas activas.

Evidencia registrada:

- `python -m compileall backend/app/modules/agenda backend/app/modules/feedgo_agenda`: OK.
- schema fisico MySQL coincide con `Base.metadata` para tablas de Agenda y
  FeedGo-Agenda.
- validacion funcional backend automatizada con datos temporales revertidos:
  OK.
- ESLint especifico de archivos de Agenda y ActiveLayer: OK.
- build frontend: OK.
- `git diff --check`: OK.

Observaciones no bloqueantes:

- el lint global mantiene errores ajenos a ETAPA 88;
- no existe suite formal especifica de Agenda;
- no se ejecuto validacion manual en navegador.

## Cache-First

El frontend usa query keys deterministicas por:

- agenda;
- comercio;
- rango o fecha;
- filtros reales.

Reglas:

- mostrar cache cuando exista;
- refrescar en segundo plano;
- evitar requests duplicados;
- invalidar solo queries afectadas;
- no consolidar ownership ni reglas de negocio en frontend;
- no construir Agenda general mediante requests descontrolados por comercio.

## Navegacion y capas activas

Agenda utiliza `ActiveLayer`.

Reglas UX:

- la capa activa bloquea el fondo;
- el fondo permanece visible pero relegado;
- Escape cierra solo la capa superior;
- backdrop cierra la capa correspondiente cuando esta permitido;
- el foco debe restaurarse al disparador correcto;
- el indicador accesible de foco debe usar estilos `focus-visible`, evitando
  que el mouse o toque dejen botones con apariencia presionada o seleccionada;
- el scroll de fondo debe conservarse.

Navegacion implementada:

- Agenda general abierta desde Perfil tiene `Cerrar`.
- Agenda individual abierta directamente tiene `Cerrar`.
- Agenda individual abierta desde Agenda general tiene `Atras` o
  `Volver a agenda general`.
- Crear o editar elemento permite `Cancelar` para volver al listado sin cerrar
  toda la Agenda.

La proteccion de cambios sin guardar es local al formulario de Agenda.

## Availability, Agenda y Reservas

Availability, Agenda y Reservas permanecen separadas.

Availability:

- define horarios habituales;
- no modela agenda;
- no modela reservas;
- no modela cupos;
- no calcula slots reservables.

Agenda:

- administra organizacion privada;
- administra eventos, tareas, recordatorios y bloqueos;
- detecta solapamientos tecnicos;
- no define disponibilidad publica;
- no importa modelos internos de Availability.

Reservas:

- administrara solicitudes publicas;
- administrara disponibilidad publica reservable;
- debera combinar informacion de Availability y Agenda mediante fronteras
  aprobadas;
- no debe exponer la agenda privada completa.
- no forma parte del cierre actual de ETAPA 88;
- debera implementarse en ETAPA 113 - Reservas Publicas y Carrito de Reserva,
  segun el roadmap vigente.

Formula conceptual futura:

```text
Disponibilidad reservable
=
Availability
-
ocupaciones relevantes de Agenda
-
reservas confirmadas
```

Esta formula es conceptual y no esta implementada.

## Reservas y solicitudes publicas

Roadmap vigente: ETAPA 113 - Reservas Publicas y Carrito de Reserva.

Durante el MVP futuro, turno y reserva seran variantes funcionales de una
solicitud publica comun.

La solicitud conserva identidad propia.

La solicitud no se transforma irreversiblemente en un elemento de Agenda.

Puede generar o reflejar un elemento vinculado dentro de Agenda.

La aprobacion inicial prevista es manual.

Estados funcionales minimos propuestos:

- pendiente;
- confirmada;
- rechazada;
- cancelada por cliente;
- cancelada por propietario;
- completada.

Estos estados no estan implementados.

## Servicios reservables

Los servicios reservables no pertenecen a Agenda Core.

Pertenecen a Reservas o configuracion reservable.

Informacion funcional minima prevista:

- nombre;
- duracion;
- modalidad visible;
- habilitado o deshabilitado;
- reglas simples de anticipacion y cancelacion, solo si se aprueban despues.

No existe todavia modelo persistente definitivo de servicios reservables.

## Respaldo, historial y recuperacion

Agenda debe contemplar tres responsabilidades separadas:

1. backup fisico y restauracion de MySQL;
2. historial funcional de cambios;
3. ciclo de vida no destructivo.

Backup y restauracion pertenecen a infraestructura.

Historial funcional o auditoria de cambios solo debe agregarse si existe una
necesidad funcional demostrada.

El ciclo de vida no destructivo actual se resuelve mediante estados como:

- `archivado`;
- `cancelado`;
- `completado`.

Agenda no copia registros manualmente en cada operacion como sustituto de
backup, auditoria o restauracion.

Antes de Reservas se debe disenar la prevencion transaccional de doble reserva.

## Busqueda e Indexador

Durante ETAPA 88, Agenda y Reservas no participan en filtros, ranking ni
exclusion de resultados.

Un comercio debe seguir apareciendo aunque no tenga Agenda, turnos o reservas.

Cualquier impacto futuro en Discovery, Candidate Engine, Ranking o Indexador
requiere decision arquitectonica documentada.

## Notificaciones

La necesidad de notificaciones detectada desde Agenda general queda aprobada
como diseno transversal, no como responsabilidad interna de Agenda.

Documento tecnico dueno:

```text
docs/14_NOTIFICATIONS_DESIGN.md
```

Agenda general sera el primer punto de entrada previsto mediante:

```text
Configurar notificaciones
```

Ese acceso debera abrir una capa secundaria compacta sobre Agenda general,
reutilizando ActiveLayer o la infraestructura transversal vigente, sin cerrar
Agenda general ni duplicar overlays.

Agenda podra producir sucesos notificables relacionados con eventos, tareas,
recordatorios y bloqueos cuando corresponda, pero Agenda Core no debe:

- enviar correo;
- enviar WhatsApp;
- depender de proveedores externos;
- almacenar preferencias transversales de usuario;
- decidir capacidades comerciales futuras;
- convertir notificaciones en politicas de bloqueo.

La campana de notificaciones pertenece al layout global autenticado o
encabezado principal existente de FeedGo, no a una pantalla especifica de
Agenda.

La integracion local minima queda fuera del cierre actual de ETAPA 88. La
necesidad permanece disenada y trazable, pero no existe implementacion runtime
de notificaciones.

Correo, WhatsApp, verificacion de destinos, proveedores, plantillas, workers,
schedulers, reintentos y webhooks no pertenecen a Agenda ni a la
implementacion de ETAPA 88. Quedan diferidos a una infraestructura transversal
de comunicaciones externas documentada por `docs/14_NOTIFICATIONS_DESIGN.md`
y planificada para una etapa futura.

## Documento unico durante MVP

Durante el MVP se mantiene este documento unico:

```text
docs/13_AGENDA_RESERVATIONS_DESIGN.md
```

No se divide todavia en documentos separados.

Criterio de division futura:

- separar Agenda y Reservas cuando Reservas tenga suficiente diseno y evolucion
  independiente en servicios, solicitudes publicas, clientes, cupos y reglas
  reservables.

## Fuera de alcance actual

- Reservas publicas;
- notificaciones locales;
- campana global;
- Vista Semana;
- Vista Mes;
- persistencia de ultima vista, filtros o contexto;
- turnos publicos;
- servicios reservables;
- recursos;
- capacidad;
- doble reserva;
- aprobacion automatica;
- pagos;
- sincronizacion con calendarios externos;
- integraciones externas;
- multiples empleados o profesionales;
- recurrencias avanzadas;
- filtros o ranking por agenda;
- exponer la agenda privada completa al cliente;
- auditoria historica funcional;
- backup implementado desde la aplicacion.

## Trabajo futuro diferido

- Reservas publicas y solicitudes.
- Servicios reservables, recursos y capacidad.
- Diseno transaccional de doble reserva.
- Notificaciones locales y campana global.
- Vista Semana y Vista Mes.
- Persistencia de ultima vista, filtros o contexto.

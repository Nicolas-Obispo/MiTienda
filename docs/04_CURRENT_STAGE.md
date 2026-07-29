# Estado actual

Estado del documento: Documento Oficial del Sistema de Gobierno FeedGo v1.0.
Version: 1.0.
Categoria: Sistema de Gobierno.
Nivel de autoridad: Alto para etapa vigente, ultimo cierre formal y proximo
trabajo autorizado.
Documento dueno: `docs/04_CURRENT_STAGE.md`.
Responsable funcional: Gobierno de etapa.
Documentos relacionados: `00_GOVERNANCE.md`, `05_SEARCH_ROADMAP.md`,
`07_DECISIONS.md`, `CHANGELOG.md`.
Cuando debe consultarse: antes de iniciar cualquier tarea para confirmar etapa
vigente, alcance actual, restricciones y estado de cierre.

Proyecto:

FeedGo

## ETAPA 85

Estado:

Cerrada.

## ETAPA 86

Estado:

Cerrada.

## Resultado ETAPA 86

- Modulo Indexador implementado en `backend/app/modules/indexer/`.
- Contratos de dominio del `CommerceIndexDocument` implementados.
- `SourceSnapshots` implementados como frontera entre fuentes y builders.
- Collectors implementados para Comercio, Taxonomia, Contenido, Senales y Knowledge Graph.
- Builders implementados para los diez bloques del `CommerceIndexDocument`.
- `IndexDocumentValidationService` implementado.
- `CommerceIndexerService` implementado como orquestador del flujo completo.
- Contrato compartido de normalizacion de texto implementado.
- Flujo completo del Indexador implementado sin persistencia.

## Fuera de alcance de ETAPA 86

- Persistencia del Documento de Indice.
- Reindexacion.
- Indices Sintetizados fisicos.
- Scheduler.
- Colas.
- Integracion con Discovery.
- Integracion con Candidate Engine.
- Integracion con Ranking.

## ETAPA 87

Sistema de Disponibilidad.

Estado:

Cerrada.

## Resultado ETAPA 87

- Persistencia de horarios habituales semanales en `comercios_horarios_atencion`.
- Modelo backend en `backend/app/modules/availability/`.
- Endpoints oficiales `GET /comercios/{comercio_id}/horarios` y `PUT /comercios/{comercio_id}/horarios`.
- Calculo backend de estado `abierto`, `cerrado` o `sin_horarios`.
- Texto contextual listo para mostrar generado por backend.
- Integracion informativa en detalle publico, `/comercios/mis` y `/comercios/activos`.
- Compatibilidad hacia atras en endpoints historicos de Spaces ante fallas de infraestructura de Availability.
- Visualizacion frontend del estado horario.
- Editor del propietario para horarios semanales, multiples franjas por dia, lista vacia y validaciones UX.
- Acceso a horarios desde el flujo de edicion del comercio.

## Fuera de alcance de ETAPA 87

- Agenda.
- Reservas.
- Turnos.
- Profesionales.
- Servicios con horarios independientes.
- Feriados.
- Excepciones por fecha.
- Cruces de medianoche.
- Filtros o ranking por disponibilidad.

## Deuda visual controlada

Queda registrada para ETAPA 95 - Experiencia de Lanzamiento y Design System
Critico:

- Unificar botones secundarios restantes con el Design System oficial.
- Revisar alineaciones y espaciados del perfil, formularios y tarjetas.
- Unificar estados hover, focus y active.
- Revisar iconografia y jerarquia visual de acciones secundarias.
- Validar responsive visual de formularios largos y modales.

## Ultima etapa cerrada

ETAPA 90 - Seguridad, Ownership y Permisos.

Estado:

Cerrada.

## Estado ETAPA 89

ETAPA 89 se encuentra cerrada.

Alcance cerrado:

- El roadmap oficial queda reorganizado desde ETAPA 89 hasta ETAPA 110.
- Productos e Inventario queda postergado hasta ETAPA 102.
- El lanzamiento controlado queda proyectado alrededor de ETAPA 97.
- ETAPAS 90-96 quedan ordenadas como preparacion de seguridad, legalidad,
  datos, operacion, calidad, experiencia y administracion.
- `docs/15_LEGAL_AND_OPERATIONAL.md` queda creado y oficializado como
  documento transversal del Sistema de Gobierno.
- Las decisiones permanentes asociadas al gobierno de lanzamiento quedan
  registradas.

Estado final actual:

- ETAPA 89 esta cerrada formalmente.
- ETAPA 90 queda cerrada formalmente.

## Estado ETAPA 90

ETAPA 90 se encuentra cerrada.

Alcance cerrado:

- Auditoria integral de endpoints, autenticacion, ownership, mutaciones
  privadas y superficies sensibles.
- Correccion de ownership en publicaciones, historias, secciones, analytics,
  metricas sociales, snapshots, comparacion y score.
- Creacion de un helper central minimo de ownership de comercio propio en
  `backend/app/modules/spaces/services/comercios_ownership_services.py`.
- Aplicacion del contrato `Usuario -> Comercio -> Recurso` para recursos
  derivados de comercio.
- Endurecimiento de logout para exigir autenticacion valida y evitar revocar
  tokens ausentes o invalidos.
- Bloqueo de mutaciones legacy de Productos hasta que el dominio oficial defina
  ownership.
- Tests automatizados de autorizacion para publicaciones, historias,
  secciones, analytics, helper de ownership, logout y productos legacy.

Decisiones aprobadas:

- Las mutaciones privadas requieren autenticacion backend obligatoria.
- El backend valida ownership; el frontend no es barrera de seguridad.
- Los recursos derivados deben resolver su propietario natural desde
  `Usuario -> Comercio -> Recurso`.
- No se crean roles, permisos, tablas ni relaciones nuevas sin necesidad
  comprobada.
- Un recurso sin dueno modelado no puede tener mutaciones globales habilitadas
  para cualquier usuario autenticado.
- Los endpoints de score, snapshot y comparacion quedan protegidos por
  propietario como solucion segura minima hasta que una etapa futura defina
  flujos internos o administrativos.

Pendientes no bloqueantes programados:

- ETAPA 91: separar schema publico y privado de usuario para no exponer email
  en lecturas publicas.
- ETAPA 93: endurecer uploads con tamano real permitido, cuota, asociacion con
  usuario o recurso, validacion, limpieza y auditoria.
- ETAPA 94: validar existencia y estado de publicaciones en likes, existencia y
  estado de comercios en seguidores, y definir comportamiento `404` o
  idempotente en relaciones sociales.
- ETAPA 95: corregir mapa de ubicacion y realizar revision visual general,
  incluyendo coherencia del efecto burbuja, fondos, contraste, jerarquia visual
  y legibilidad.
- ETAPA 102: revisar Productos legacy cuando el dominio oficial de Catalogo de
  Productos y Disponibilidad Simple defina ownership.

Estado final actual:

- ETAPA 90 esta cerrada formalmente.
- No quedan brechas criticas dentro del alcance de ETAPA 90.
- No se crearon tablas, modelos ni relaciones nuevas.

## Estado ETAPA 88

ETAPA 88 se encuentra cerrada.

Decisiones aprobadas:

- Agenda sera un modulo propio.
- Backend: `backend/app/modules/agenda/`.
- Frontend: `frontend/src/features/agenda/`.
- Agenda sera privada para el propietario.
- Agenda pertenece a un contexto agendable.
- En FeedGo, el primer contexto agendable sera un espacio.
- Agenda tendra entidades propias minimas: `ContextoAgendable` y
  `ElementoAgenda`.
- `ElementoAgenda` dependera unicamente de `ContextoAgendable`.
- El nucleo de Agenda no tendra FK directa a `comercios`, medicos,
  consultorios ni recursos externos de ninguna aplicacion host.
- Cada aplicacion host vinculara sus recursos con `ContextoAgendable` mediante
  una capa de integracion propia.
- FeedGo vinculara `Comercio` con `ContextoAgendable` fuera del nucleo de
  Agenda.
- Agenda no copiara nombre, rubro, direccion, propietario ni datos del
  comercio.
- Un propietario con varios espacios tendra una agenda por contexto y una vista
  unificada sobre sus espacios.
- El nucleo de Agenda no debe nombrar ese contexto como `comercio`.
- Agenda y Reservas son conceptos distintos.
- Availability, Agenda y Reservas permanecen separadas.
- Las preferencias de interfaz de Agenda permanecen en frontend durante el MVP.
- Mi Perfil sera el punto de entrada inicial, pero Agenda no pertenece a Mi
  Perfil.
- La vista inicial sera `Hoy`, en formato cronologico.
- Vista Semana, Vista Mes y persistencia de ultima vista, filtros o contexto
  quedan diferidas fuera del cierre actual.
- ActiveLayer queda como infraestructura transversal reutilizable para capas
  activas.
- La modularidad se resolvera dentro del monorepo actual, sin microservicio ni
  repositorio separado.
- ETAPA 88.2 - Diseno funcional y modularidad queda cerrada.
- ETAPA 88.3 - Diseno tecnico definitivo queda cerrada.
- ETAPA 88.4 - Auditoria de modelo de datos y contratos conceptuales queda
  cerrada a nivel de arquitectura y modelo conceptual.
- ETAPA 88.5 - Base backend de Agenda privada queda implementada.
- ETAPA 88.6 - Integracion FeedGo-Agenda queda implementada.
- ETAPA 88.7 - Diseno de integridad, concurrencia y recuperacion queda
  registrado.
- ETAPA 88.8 - Control optimista de concurrencia de `ElementoAgenda` queda
  implementado.
- ETAPA 88.9 - Deteccion tecnica informativa de solapamientos queda
  implementada.
- ETAPA 88.10 - Endpoints privados minimos de Agenda quedan implementados.
- ETAPA 88.11 - Interfaz privada minima, Agenda general, accesos multiples y
  correcciones de navegacion quedan implementadas y validadas.
- La arquitectura por capas de Agenda general fue corregida: la consulta
  agregada vive en la capa de repositorio/servicio de `feedgo_agenda`, no en el
  router HTTP.
- El schema fisico de MySQL fue validado contra `Base.metadata` para
  `agenda_contextos_agendables`, `agenda_elementos` y
  `feedgo_agenda_contextos`, sin diferencias bloqueantes.
- La validacion tecnica y funcional integral de Agenda fue aprobada con
  observaciones no bloqueantes.
- Agenda general queda resuelta mediante endpoint agregado backend, sin N
  requests desde frontend.
- El frontend de Agenda sigue politica cache-first mediante query keys
  especificas.
- La navegacion modal implementa `Cerrar`, `Atras` y `Cancelar`.
- Los botones y capas de Agenda deben restaurar foco de forma accesible usando
  estilos `focus-visible`, sin apariencia persistente de boton presionado.
- Los formularios de Agenda tienen proteccion local de cambios sin guardar.
- La propuesta de notificaciones de Agenda general queda aprobada como diseno
  futuro con ajustes: se divide en un sistema transversal de notificaciones y
  una infraestructura futura de comunicaciones externas.
- `docs/14_NOTIFICATIONS_DESIGN.md` queda como documento tecnico dueno del
  diseno de notificaciones.
- El acceso `Configurar notificaciones` pertenece a Agenda general como punto
  de entrada inicial, pero la configuracion no queda limitada a Agenda.
- La campana de notificaciones debe pertenecer al layout global autenticado o
  encabezado principal existente, sin duplicarse por pantalla.
- Agenda Core no debe depender de correo, WhatsApp ni proveedores externos.
- Correo electronico, WhatsApp, verificacion de destinos, proveedores,
  plantillas, workers, colas, schedulers productivos, webhooks e intentos de
  entrega externa quedan diferidos a una etapa futura de comunicaciones
  externas transversales.
- El sistema de notificaciones debera consultar una futura politica externa de
  capacidades o feature access cuando existan planes comerciales; hoy no se
  implementan pagos, planes ni bloqueos por plan.

Observaciones no bloqueantes antes del cierre formal:

- `npm run lint` global falla por errores ajenos a ETAPA 88.
- No existe suite formal especifica de tests automatizados de Agenda.
- La validacion manual en navegador no fue ejecutada durante la validacion
  automatizada integral.

Fuera del cierre actual:

- Reservas publicas, turnos publicos, servicios reservables, recursos,
  capacidad y disponibilidad publica reservable no comenzaron y quedan
  diferidos a una etapa futura.
- Notificaciones locales, campana global y configuracion local quedan
  disenadas, pero no implementadas en el cierre actual de ETAPA 88.
- Correo electronico, WhatsApp, verificacion de destinos, proveedores,
  plantillas, workers, colas, schedulers productivos, webhooks e intentos de
  entrega externa quedan diferidos a ETAPA 101 - Mensajeria y Cotizaciones.
- Vista Semana, Vista Mes y persistencia de ultima vista, filtros o contexto
  quedan diferidas.

Pendiente inmediato:

- No hay pendientes bloqueantes para ETAPA 88.

Estado final actual:

- ETAPA 88 esta cerrada formalmente.
- Agenda privada y Agenda general estan implementadas y validadas.
- El cierre formal se limita al alcance Agenda definido en este documento.

## ETAPA vigente

ETAPA 91 - Cumplimiento Legal, Privacidad y Moderacion.

Estado:

Vigente.

Objetivo:

Preparar criterios legales, privacidad, contenido publico, denuncias,
moderacion y consentimiento necesarios para operar una aplicacion publica.

Alcance:

- auditar cumplimiento legal, privacidad y moderacion existentes;
- revisar datos personales expuestos en superficies publicas;
- definir controles previos al lanzamiento relacionados con contenido publico,
  consentimiento, denuncias y privacidad;
- corregir unicamente defectos comprobados y necesarios para el alcance legal y
  operativo de la etapa.

Fuera del alcance:

- modificar base de datos;
- crear tablas;
- implementar funcionalidades nuevas ajenas al alcance legal, privacidad y
  moderacion;
- redactar contratos legales definitivos de usuario final sin revision
  profesional;
- cerrar ETAPA 91;
- reabrir ETAPA 88.

## Recordatorio

Toda nueva decision permanente debera actualizar los Documentos de Gobierno antes de continuar implementando.

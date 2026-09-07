# Estado actual

Estado del documento: Documento Oficial del Sistema de Gobierno FeedGo v1.0.
Version: 1.0.
Categoria: Sistema de Gobierno.
Nivel de autoridad: Alto para etapa vigente, ultimo cierre formal y proximo
trabajo autorizado.
Documento dueno: `docs/04_CURRENT_STAGE.md`.
Responsable funcional: Gobierno de etapa.
Documentos relacionados: `00_GOVERNANCE.md`, `05_SEARCH_ROADMAP.md`,
`07_DECISIONS.md`, `16_DATA_INTEGRITY_AND_RECOVERY.md`, `CHANGELOG.md`.
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

## Historial previo de ETAPA 90

ETAPA 90 - Seguridad, Ownership y Permisos.

Estado:

Cerrada.

## Estado ETAPA 89

ETAPA 89 se encuentra cerrada.

Alcance cerrado:

- El roadmap oficial queda reorganizado desde ETAPA 89 hasta ETAPA 112.
- Productos e Inventario queda postergado hasta ETAPA 104.
- El lanzamiento controlado queda proyectado alrededor de ETAPA 99.
- ETAPAS 90-98 quedan ordenadas como preparacion de seguridad, legalidad,
  datos, operacion, calidad, experiencia, plataforma PWA, administracion y
  pulido visual final.
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
  y legibilidad. Dentro de ETAPA 95 debera existir una subetapa tecnica propia
  para sistema global de temas y tokens semanticos compatible con modo oscuro,
  modo claro y configuracion del dispositivo, diferenciada de la correccion del
  mapa y de la revision visual general.
- ETAPA 115: revisar Productos legacy cuando el dominio oficial de Catalogo de
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
  entrega externa quedan diferidos a ETAPA 114 - Mensajeria y Cotizaciones.
- Vista Semana, Vista Mes y persistencia de ultima vista, filtros o contexto
  quedan diferidas.

Pendiente inmediato:

- No hay pendientes bloqueantes para ETAPA 88.

Estado final actual:

- ETAPA 88 esta cerrada formalmente.
- Agenda privada y Agenda general estan implementadas y validadas.
- El cierre formal se limita al alcance Agenda definido en este documento.

## ETAPA 95 - cierre formal

ETAPA 95 - Experiencia de Lanzamiento y Design System Critico.

Estado:

Cerrada tecnica y documentalmente por 95.7-C.

Objetivo:

Ajustar la experiencia central de lanzamiento, accesibilidad, responsive y
consistencia visual critica sin convertirlo en una reescritura del sistema de
diseno.

Gate previo a implementar cambios de ubicacion precisa en Sprint 95.1:

- expediente tecnico: `docs/19_LOCATION_LEGAL_GATE.md`;
- estado vigente: `GO condicionado` para implementar Sprint 95.1 conforme al
  contrato y a los controles registrados en el expediente;
- la integracion de geocoding productiva permanece condicionada a un proveedor
  compatible y los documentos publicos siguen siendo gate de activacion y
  lanzamiento;
- el expediente no adelanta ETAPA 96.

Evidencia de Sprint 95.1:

- 95.1-A - Contrato de datos y compatibilidad historica: implementado y
  validado;
- 95.1-B - Privacidad de respuestas: implementada y validada en contratos
  publicos, de administracion, Explorar y espacios seguidos;
- 95.1-C - Integridad del selector: implementada y validada con borrador local,
  seleccion explicita, confirmacion/cancelacion y proteccion ante respuestas
  asincronas obsoletas;
- 95.1-D - Geocoding backend y correccion de ownership: contratos y owner
  implementados; `LocationPicker` queda desacoplado de Nominatim;
- 95.1-D2 - adapter Geoapify: implementado con configuracion backend, endpoint
  EU, normalizacion, atribucion, timeout, rate limit y fallback seguro;
- 95.1-D3 - validacion real argentina: Geoapify queda `APROBADO CON
  LIMITACIONES` como proveedor actual reemplazable; 35 requests reales en
  Rafaela/Sunchales y reverse, sin errores ni 429, con controles posteriores de
  ciudad y confidence validados;
- 95.1-D queda cerrado;
- 95.1-E - Search territorial y privacidad geografica: implementado y validado
  en backend con identidad `city_key + province_code + country_code`, alcances
  explicitos local/50 km/100 km, frontera previa a paginacion, distancia publica
  preservada y banda privada interna de 1 km sin exposicion;
- 95.1-F - Ubicacion dinamica del usuario y Cache-First: implementada y validada
  con owner frontend de sesion, permiso contextual, fallback manual/perfil
  explicito, frescuras territorial/distancia independientes, `positionRevision`,
  claves territoriales sin coordenadas crudas y ampliacion 50/100 km explicita;
- 95.1-G - Documentos publicos, hardening y cierre tecnico: implementado y
  validado con rutas separadas, version backend unica, switch de privacidad,
  presentacion segura, attribution y matriz final de controles;
- Sprint 95.1 queda tecnicamente cerrado. La activacion productiva y el
  lanzamiento permanecen condicionados a los datos institucionales, derechos,
  retencion y formalizaciones registrados en el gate;
- 95.2 - UX del mapa, permisos y privacidad: su alcance funcional original
  quedo absorbido y validado dentro de 95.1. No debe abrirse como sprint de
  implementacion ni duplicar selector, geocoding, permisos, privacidad,
  Search territorial, ubicacion dinamica o Cache-First geografico;
- siguiente sprint oficial: 95.3 - Inventario visual e infraestructura global
  del tema;
- primer bloque autorizado de 95.3: inventario visual completo y trazable del
  frontend vigente. Todavia no autoriza crear tokens, migrar pantallas ni
  modificar componentes;
- 95.3-A - Inventario visual completo: cerrado documentalmente en
  `docs/20_FRONTEND_VISUAL_INVENTORY.md`, sin cambios de UI ni tema;
- 95.3-B - Contrato global del tema: cerrado documentalmente en
  `docs/21_THEME_CONTRACT.md` con owner `frontend/src/core/theme/`, preferencia
  separada de tema resuelto, `data-theme`, bootstrap previo a React y contrato
  PWA compatible;
- 95.3-C - Infraestructura global de tema: implementada y validada con kernel
  bloqueante local, bridge canonico, owner `frontend/src/core/theme/`, API
  React minima, persistencia tolerante a fallas, listener unico, sincronizacion
  del documento y 41 tests frontend correctos;
- 95.3-D - Validacion y hardening: completado con correccion CSP del fondo
  anti-flash hacia un asset CSS local, 18 tests contractuales, 46 tests
  frontend globales, lint sin errores y build correcto;
- Sprint 95.3 queda tecnicamente cerrado;
- 95.4-A - Contrato de tokens semanticos: cerrado documentalmente en
  `docs/22_SEMANTIC_TOKENS_CONTRACT.md`, sin crear tokens, primitives ni migrar
  pantallas;
- 95.4-B - Infraestructura real de tokens semanticos: implementada y validada
  con fuente fisica unica dark/light, aliases Tailwind v4, canvas compartido por
  anti-flash y `theme-color`, `interactive-bubble` semantico y 52 tests
  frontend correctos;
- 95.4-C - Base compartida de componentes visuales: implementada y validada con
  Button, Surface, controles de formulario, Alert y Skeleton semanticos;
  `InteraccionButton`, `interactive-bubble` y `ActiveLayer` conservan sus
  responsabilidades y no se migraron pantallas;
- 95.4-D - Validacion, hardening y cierre tecnico: completado con contrato
  accesible obligatorio para Button iconografico, API publica minima,
  bundle acotado sin dependencias nuevas, 63 tests frontend correctos, lint sin
  errores y build productivo correcto;
- Sprint 95.4 queda tecnicamente cerrado, sin migrar consumidores;
- 95.5 - Migracion controlada de pantallas criticas: cerrado tecnicamente;
- 95.5-A - Perfil / Editar perfil y selector visible de apariencia:
  implementado y validado con consumo exclusivo de `preference` y
  `setPreference(...)`, primitives semanticas, 70 tests frontend correctos,
  lint sin errores y build productivo correcto;
- 95.5-B - Registro y superficies de autenticacion relacionadas: implementado
  y validado con contratos legales y funcionales preservados, primitives
  semanticas, 77 tests frontend correctos, lint sin errores y build productivo
  correcto;
- 95.5-C - Explorar: implementado y validado visualmente mediante tokens y
  primitives, incluyendo los owners compartidos MainLayout, contexto
  geografico, estado horario y guardia de inactividad estrictamente necesarios;
  83 tests frontend correctos, lint sin errores y build productivo correcto;
- correccion visual post 95.5-C: `Input` incorpora un slot trailing compartido
  y los toggles de password de Registro/Login vuelven a quedar integrados sin
  alterar su logica;
- 95.5-D - Feed: implementado y validado visualmente, incluyendo
  `PublicacionCard`, `HistoriasBar`, estados, bienvenida e
  `InteraccionButton`; Cache-First, optimistic updates, historias, media y
  navegacion preservados; 93 tests frontend correctos, lint sin errores y
  build productivo correcto;
- 95.5-E - Ranking / Tendencias: implementado y validado visualmente; reutiliza
  `PublicacionCard` sin variantes paralelas y preserva query key, orden,
  Cache-First, merge, locks, optimistic updates y rollback; se corrigio en el
  owner CSS la generacion real de aliases `text-primary/secondary/muted/inverse`;
  101 tests frontend correctos, lint sin errores y build productivo correcto;
- la matriz acumulada de cobertura vive en
  `23_FRONTEND_VISUAL_COVERAGE.md`; mantiene pendientes que bloquean el cierre
  de 95.5;
- 95.5-F - Seguidos: implementado y validado visualmente; migra shell, tabs,
  cards y estados, reutiliza el contexto geografico compartido y preserva
  Cache-First, `positionRevision`, permisos y privacidad; evidencia: 107 tests
  frontend correctos, lint sin errores y build productivo correcto;
- 95.5-G - Perfil / identidad visible de usuario: implementado visualmente
  sobre la superficie real protegida `/perfil`; no existe perfil público de
  terceros y no se inventaron rutas, contratos, publicaciones ni acciones;
  evidencia: 114 tests frontend correctos, lint sin errores y build productivo
  correcto;
- 95.5-H - Alta, edicion y administracion de espacios: implementado
  visualmente en formulario compartido, listado, LocationPicker y editor de
  horarios, preservando contratos, privacidad, geocoding y branding;
  evidencia: 123 tests frontend correctos, lint sin errores y build productivo
  correcto;
- 95.5-I - Perfil publico de espacio: implementado visualmente en shell,
  identidad, informacion publica, acciones, publicaciones, estados y overlays
  propios; reutiliza `PublicacionCard`, `EstadoHorarioBadge` y los owners de
  Historias/Agenda/Moderacion sin absorber sus superficies independientes;
  preserva detalle, Cache-First, privacidad, seguimiento y contratos; evidencia:
  129 tests frontend correctos, lint sin errores y build productivo correcto;
- 95.5-J - Historias: `HistoriasViewer` integrado como superficie migrada de
  apariencia fija, aislada del tema global sin rediseño; formulario de creacion
  migrado a tokens/primitives con upload y payload preservados; evidencia: 140
  tests frontend correctos, lint sin errores y build productivo correcto;
- 95.5-K - Agenda y reservas: Agenda general y privada migradas a
  tokens/primitives sobre `ActiveLayer`, preservando fechas, formularios,
  estados, Cache-First, versionado, endpoints e invalidaciones; evidencia: 147
  tests frontend correctos, lint sin errores y build productivo correcto;
- 95.5-L - Superficies legales: Terminos y Politica de Privacidad migrados
  mediante el shell compartido, tokens, `Surface` y `Alert`, preservando texto,
  rutas, versionado backend-owned, enlaces y aceptaciones de Registro;
  evidencia: 152 tests frontend correctos, lint sin errores y build productivo
  correcto;
- 95.5-M - Auditoria visual transversal: detecta y corrige en el owner comun
  la precedencia de `interactive-bubble` que anulaba superficies/foreground de
  Button, valida nuevamente las superficies migradas y concreta el residual en
  tres superficies: Home, detalle de publicacion y DenunciaModal;
- 95.5-N - Detalle de publicacion y DenunciaModal: migrados y validados en
  light/dark con owners compartidos, media preservada y contratos funcionales,
  cache e interacciones intactos; queda Home como unica superficie pendiente;
- correccion acotada posterior a 95.5-N en Editar perfil: el selector de
  apariencia queda oculto tras el disclosure `Color de fondo`, mantiene
  aplicacion y persistencia inmediatas mediante `core/theme` y no participa del
  submit; se retiro de esta UI el editor historico `color_fondo` y el PATCH de
  perfil queda limitado a provincia y ciudad, sin eliminar su contrato backend;
- se corrigio la asociacion accidental del decorador `PATCH /usuarios/me` con
  el endpoint de documentos vigentes, causa del HTTP 500 al guardar un perfil
  valido; handler, payload y persistencia quedaron cubiertos por test;
- 95.5-O - Home: ruta publica `/`, hero, tres cards y tres CTAs-enlace migrados
  y validados mediante tokens, `Surface`, `MainLayout` y bubble compartida, sin
  alterar autenticacion, destinos ni responsive; la matriz queda con cero
  superficies pendientes de migracion;
- QA visual global final de 95.5: completado sobre las 22 filas, con evidencia
  renderizada publica light/dark desktop/movil, confrontacion de superficies
  protegidas/modales y correccion responsive compartida `min-w-0` en Surface y
  controles; resultado 0 pendientes, 0 correcciones requeridas, 0 sin validar y
  0 defectos visuales bloqueantes conocidos;
- Sprint 95.5 queda tecnicamente cerrado;
- sprint vigente: 95.6 - Consolidacion de accesibilidad, overlays, responsive
  y consistencia;
- 95.6-A - Accesibilidad transversal: implementado y validado. `ActiveLayer`
  concentra semantica modal, foco inicial, trap, Escape, scroll lock y retorno
  de foco tambien para bienvenida, inactividad, Crear Historia, estadisticas y
  Crear publicacion; su backdrop queda fuera del orden de tabulacion. Se
  corrigieron labels del formulario de espacios, selector de portada con
  boton nativo, enlaces de detalle en `PublicacionCard`, activacion por teclado
  en `HistoriasViewer`, nombres de producto y reduced motion compartido. La
  logica funcional, tema y backend permanecen intactos;
- 95.6-B - Overlays, modales y consistencia: implementado y validado.
  `ActiveLayer` queda como owner canonico y unico de portal, backdrop, foco,
  trap, Escape, restauracion, scroll lock y stacking base; se consolida el
  backdrop del editor de horarios, cancelacion segura de timers de foco y
  desplazamiento de capas altas en viewport reducido. `HistoriasViewer` sigue
  como excepcion fullscreen fija y `LocationPicker` como superficie inline;
- 95.6-C - hardening responsive transversal: implementado y validado. Se
  consolidaron contraccion, wrapping, grupos de acciones y viewport de overlays
  desde primitives/owners compartidos, sin cambiar breakpoints ni funcionalidad;
- 95.6-D - consistencia y hardening final: implementado y validado. Owners,
  API publica de primitives, bubble, ActiveLayer, responsive, accesibilidad y
  tema permanecen coherentes; no se detectaron duplicaciones ni residuos
  estructurales nuevos del sprint;
- Sprint 95.6 queda tecnicamente cerrado;
- siguiente sprint oficial: 95.7 - QA integral, hardening, Frontend Ownership
  Audit, auditoria de residuos tecnicos y cierre documental;
- gate de cierre de 95.5: matriz exhaustiva sin pendientes de todas las
  pantallas, layouts, navegacion, formularios, cards, capas, estados, loaders,
  skeletons, superficies compartidas y botones en light/dark; solo se admiten
  excepciones documentadas de branding de contenido, mapa/proveedor externo,
  media o necesidad de dominio;
- los defectos compartidos de contraste deben corregirse en tokens/primitives
  antes que mediante parches fisicos locales y requieren QA visual global en
  light, dark y cambio runtime;
- criterio obligatorio previo al cierre de ETAPA 95 satisfecho por 95.5-A: el
  selector de apariencia vive en `Perfil -> Editar perfil`, cambia de forma
  inmediata y persiste mediante el owner global, sin controles alternativos;
- el trabajo visual residual del mapa se limita a consistencia, accesibilidad y
  responsive y se tratara con las mismas reglas transversales de 95.6, sin
  reabrir su contrato funcional;
- cierre de ETAPA 95: queda registrada una `Frontend Ownership Audit`
  transversal, sin ampliar el alcance de 95.1-D;
- cierre de ETAPA 95: queda registrada una auditoria especifica de residuos
  tecnicos generados durante la etapa. Debe relevar scripts, temporales, tests
  auxiliares, mocks, logs/debug, TODO/FIXME introducidos, codigo muerto,
  helpers/componentes sin consumidores, CSS/clases reemplazadas, duplicados,
  adapters abandonados, residuos Nominatim, validacion Geoapify y migraciones
  one-shot. Cada hallazgo se clasifica con evidencia como `conservar`,
  `mover/reubicar`, `documentar` o `eliminar por residuo`; no se elimina
  automaticamente ni se descartan tests con valor permanente. Este gate no se
  ejecuta durante 95.5 y bloquea el cierre final hasta quedar resuelto.

Plan restante oficial de ETAPA 95:

- 95.3 - Inventario visual e infraestructura global del tema: cerrado
  tecnicamente;
- 95.4 - Tokens semanticos y componentes compartidos: cerrado tecnicamente;
- 95.5 - Migracion controlada y cobertura visual global: cerrado tecnicamente;
- 95.6 - Consolidacion de accesibilidad, overlays, responsive y consistencia:
  cerrado tecnicamente;
- 95.7 - QA integral, hardening, `Frontend Ownership Audit`, auditoria de
  residuos tecnicos y cierre documental. 95.7-A Frontend Ownership Audit
  completado: owners principales aprobados, bypass directo de Auth corregido y
  deuda historica de token, query keys, transporte y doble estado documentada
  en `docs/24_FRONTEND_OWNERSHIP_AUDIT.md`; 95.7-B auditoria integral de
  residuos completada con evidencia en `docs/25_TECHNICAL_RESIDUE_AUDIT.md`,
  siete entradas categoria D retiradas y cero residuos reales demostrados
  pendientes. 95.7-C - QA tecnico final y cierre documental queda completado:
  241 tests backend y 190 tests frontend correctos, `compileall`, lint sin
  errores, build productivo y `git diff --check` correctos; gates tecnicos y
  documentales satisfechos. ETAPA 95 queda cerrada sin adelantar ETAPA 96;

Estado de continuidad:

- Ultima etapa cerrada: ETAPA 98 - Correccion y Pulido Visual del Frontend.
- Etapa vigente: ETAPA 99 - Identidad, Registro y Autenticacion. Sus bloques
  99.1, 99.2, 99.3, 99.4, 99.5 y 99.6 quedan formalmente cerrados. El
  siguiente sprint oficial es 99.7 - Enforcement en Spaces y Publicaciones,
  pendiente y no iniciado.
- Checkpoint intermedio aprobado: sistema visual Liquid consolidado y bloque
  correctivo incidental de publicaciones e interacciones validado. Este
  checkpoint no constituyo por si solo el cierre posterior de ETAPA 98.
- Checkpoint previo a la prueba de densidad responsive: los labels e iconos
  inactivos de `InteraccionButton` adoptan texto principal adaptativo en
  light/dark y los activos conservan los simbolos sociales compartidos. Los
  disparadores publicos de denuncia muestran `...` con nombre accesible y se
  ocultan cuando el ownership vigente demuestra que el recurso es propio. El
  perfil publico alinea identidad y acciones en columnas superiores, agrupa
  direccion sobre estado horario a la derecha, oculta las metricas publicas
  del encabezado y conserva su consulta privada mediante Estadisticas; sus
  contactos y acciones de administracion usan el patron compacto aprobado.
- La auditoria global de escala responsive rechazo `transform: scale()` y
  `zoom` globales y el escalado literal proporcional por resultar incompatible
  con legibilidad, areas tactiles, inputs, portales, fixed, Leaflet, historias
  y multimedia. La direccion recomendada es hibrida: densidad global moderada
  mediante tokens y `clamp()`, complementada por container queries y reflow
  solo cuando sea necesario. Ese owner global no fue implementado; la prueba
  reversible permanece pendiente y debe tratar mapas, historias, multimedia y
  overlays como casos especificos. El experimento fue retirado sin integrar
  densidad global al producto.
- Decision documental previa aprobada: `DEC-057` distingue cuenta basica de la
  capacidad para crear o administrar espacios y publicar contenido asociado.
  La cuenta basica no excluye automaticamente a menores de 18 anos; la politica
  vigente exige 18 anos o mas para esas capacidades de Espacios. ETAPA 99,
  ahora vigente con 99.1 a 99.6 cerrados y 99.7 pendiente, absorbe
  `fecha_nacimiento` privada y nullable, perfil y
  capabilities backend, borrador seguro de Registro y flujo Google conforme a
  `DEC-048`; el backend de Espacios conserva el enforcement. No se implemento
  ninguna de estas funciones en ETAPA 98, los documentos publicos `v1`
  permanecen intactos y la revision juridica profesional previa al lanzamiento
  sigue siendo bloqueante para el lanzamiento.
- Diseño futuro formalizado durante ETAPA 98: `DEC-058` y
  `docs/28_DYNAMIC_FEED_DESIGN.md` fijan el contrato de Dynamic Feed e Historias,
  incluido Candidate Generation acotado, contexto territorial no bloqueante,
  memoria temporal de exposición, Premium limitado por diversity/fairness,
  Advertising separado, snapshots estables, cursor e infinite pagination. No
  se modificó el comportamiento actual: ETAPA 106 implementará plataforma
  comercial y Advertising, ETAPA 119 preferencias/privacidad/exposición y
  ETAPA 122 candidatos/ranking/ubicación/paginación. Esta formalización no
  constituye implementación.
- 97.1 - Contrato administrativo y autorizacion: cerrada. FeedGo dispone de un
  catalogo inicial de cuatro capacidades administrativas persistidas fuera del
  JWT, eventos append-only de otorgamiento/revocacion, bootstrap local
  auditado, autorizacion backend reutilizable, endpoint autenticado de
  capacidades propias y consumidor frontend compartido. `modo_activo` y el
  ownership de Espacios no conceden acceso administrativo.
- No se asignaron operadores durante el cierre y no se construyeron bandeja de
  denuncias, consola ni dashboard.
- 97.2 - Bandeja y consulta de denuncias: cerrada. Incorpora listado y detalle
  administrativos read-only protegidos por `moderation.reports.read`,
  paginacion keyset, filtros controlados, minimizacion total del denunciante y
  disponibilidad actual del recurso sin presentarla como evidencia historica.
  El frontend consume estos contratos mediante una bandeja compartida de solo
  lectura con estados de carga, vacio, error y concurrencia controlada.
- 97.3 - Decisiones y acciones de moderacion: cerrada. Incorpora decisiones
  append-only protegidas por `moderation.decisions.write`, version de denuncia,
  revision de moderacion del recurso, idempotencia por clave y fingerprint,
  trazabilidad del operador y acciones de ocultamiento/restauracion delegadas
  a los services propietarios. La visibilidad de moderacion permanece separada
  de `activo` e `is_activa`; no se incorporaron sanciones, apelaciones,
  asignaciones ni automatizacion.
- 97.4 - Gestion minima de incidentes: cerrada. Incorpora expediente durable,
  lifecycle controlado, cronologia append-only, severidad SEV1-SEV4, owner,
  plazos operativos configurables, concurrencia, idempotencia, riesgo residual
  y evaluacion legal, protegido por `operations.incidents.manage`. La evidencia
  se limita a referencias opacas tipadas; no se modificaron Observabilidad ni
  Recovery y no se incorporaron dashboard, automatizacion o borrado.
- 97.5 - Operacion segura de contratos existentes: cerrada. Incorpora estado
  operativo seguro protegido por `operations.status.read`, compuesto desde
  Health, agregados allowlisted y alertas sanitizadas. El contrato declara
  alcance local, volatil, no historico y no global; la evidencia de Recovery no
  declara freshness ni RPO. Comercio, Publicacion e Historia conservan el
  ownership de sus inspecciones puntuales read-only. No se incorporaron
  mutaciones, red externa, barridos, modelos, migraciones, dashboard ni acciones
  de backup/restore.
- 97.6 - Gate integral: cerrada. El gate automatizado cubre autorizacion,
  privacidad, trazabilidad, concurrencia, idempotencia, migraciones,
  visibilidad publica, incidentes, estado operativo, errores administrativos y
  regresiones backend/frontend/PWA. La outbox operativa y el canal
  `Notificaciones -> Comunicaciones -> EmailProvider` permanecen desacoplados;
  el smoke controlado `operations.email.smoke` quedo validado con estado
  `sent`, un unico intento, sin error sanitizado, con `sent_at` y referencia
  externa generica. No se documentan destinatario, credenciales, payload ni
  respuesta del provider.
- El canal operativo automatico completo quedo validado sobre MySQL local. La
  migracion aditiva de `operational_notification_outbox` incorporo claims,
  leases, supresion e indice de despacho y su segunda ejecucion fue idempotente.
  Las intenciones sinteticas correspondientes a las denuncias 2, 3 y 4 fueron
  marcadas `suppressed` con motivo controlado, sin eliminar filas, denuncias,
  payloads ni deduplicacion. La denuncia real 5 permanecio elegible y fue
  entregada automaticamente por el worker dedicado en un unico intento, sin
  duplicados, con recepcion humana confirmada. Canal y dispatcher fueron
  restaurados a `false` despues de la prueba.
- El cierre integral revalido el launcher local unico con API y worker como
  procesos separados. La denuncia real 6 paso exactamente una vez de `pending`
  a `sent`, con `attempt_count=1`, una unica intencion, `sent_at` y referencia
  externa generica; la recepcion humana en Operaciones fue confirmada. El
  heartbeat del worker registro `active -> stopped`, el apagado fue limpio, no
  quedaron procesos huerfanos y ambos gates fueron restaurados a `false`.
- Los bloques funcionales manuales de portada, bandeja, moderacion, incidentes,
  estado operativo y control 422 estan aprobados. El
  cierre transversal de lenguaje, diferenciacion de campos/acciones,
  navegacion, foco y responsive fue implementado y validado. La guia practica
  interna de Administracion quedo incorporada en su owner legal-operativo y en
  una superficie privada para operadores. La consolidacion final revalido las
  suites completas, concurrencia MySQL aislada, esquema fisico y migraciones,
  worker, canal operativo, compileall, lint, build/PWA, Playwright, secretos y
  diff. La auditoria de tests y residuos no detecto un bloqueo funcional.
- Matriz manual 97.6, bloque Portada administrativa: **APROBADO**. Quedaron
  validados anonimato, usuario comun, operador con capacidades parciales,
  revocacion y restauracion durante la misma sesion sin reemitir JWT, y la
  proteccion coherente de navegacion global, portada y acceso directo. La
  consulta de capacidades revalida al montar, recuperar foco y reconectar, y
  su contrato HTTP impide reutilizar una respuesta cacheada. El bootstrap
  auditado conserva eventos persistentes append-only y no crea roles ni cambia
  el mecanismo de autorizacion.
- Matriz manual 97.6, bloque Bandeja de denuncias: **APROBADO**. Quedaron
  validados listado y filtros, vacio filtrado, detalle con y sin texto
  adicional, privacidad total del denunciante, ausencia de controles de
  decision para un operador de solo lectura, error de conexion recuperable y
  cancelacion de consulta obsoleta bajo red 3G. No se aplicaron decisiones ni
  efectos sobre recursos durante este bloque.
- Matriz manual 97.6, bloque Decisiones de moderacion: **APROBADO**. Se valido
  `resolver_sin_accion` unico y sin derecho a restaurar, ocultamiento publico,
  rechazo 409 de una decision concurrente obsoleta, restauracion causal y
  trazabilidad append-only. La verificacion read-only confirmo Comercio 1 con
  `activo=true` y revision 0, y Publicacion 9 e Historia 37 con
  `is_activa=true`, visibles, revision 2 y sin decision de ocultamiento vigente.
  No hubo eliminacion ni desactivacion del lifecycle owner.
- Matriz manual 97.6, bloque Incidentes: **APROBADO**. Se validaron evaluacion
  legal, conflicto 409 mediante probe local con `expected_version` congelada,
  ausencia del evento rechazado, lifecycle completo hasta `reviewed`, riesgo
  residual medio con owner y fecha, cronologia append-only y terminalidad. La
  verificacion read-only confirmo en
  `INC-5090E87615484E53BCCBD5A4E82499B5` las versiones consecutivas 1 a 6 y
  las transiciones `opened`, `record_legal_assessment`,
  `start_investigation`, `contain`, `resolve` y `review`. El expediente previo
  se conserva integro como evidencia del defecto corregido de ajuste sin
  efecto.
- Matriz manual 97.6, bloque Estado Operativo: **APROBADO**. Se validaron
  alcance local, volatil y no historico; ausencia de afirmaciones globales,
  freshness o RPO; Health y Recovery sanitizados; ausencia de acciones de
  backup, restore o reparacion; agregados y alertas sin payloads ni datos
  privados; inspeccion correcta de Comercio 1, Publicacion 9 e Historia 37;
  assets externos clasificados sin exponer referencias; 404 controlado; y
  fallo de conexion con recuperacion posterior y componentes `healthy`.
- Usabilidad administrativa 97.6: **APROBADA** para lenguaje, diferenciacion
  de campos y acciones, ownership visual de errores, navegacion, foco y
  responsive movil/escritorio. La validacion incluye formularios y acciones
  adaptables, detalles sin desborde y acceso global a Administracion sin
  superposiciones en anchos moviles. La guia practica interna queda disponible
  solo para identidades con capacidades administrativas y no expone contratos,
  credenciales ni evidencia de prueba.
- Matriz manual 97.6, control 422: **APROBADO**. El formulario existente de
  reasignacion rechazo un owner sintetico inexistente con el mensaje sanitizado
  `Los datos enviados no son validos`. La verificacion read-only confirmo que
  `INC-2BE9B24CEFF94E4E9CEB87A8A17C9FCA` conserva estado `open`, SEV4, owner
  32, version 1 y un unico evento `opened`; no se persistio `assign_owner` ni
  se modificaron denuncias, otros incidentes o recursos.
- ETAPA 96 - Plataforma Instalable y PWA Enterprise queda cerrada tecnica y
  documentalmente. Sprints 96.1, 96.2 y 96.3 quedan completados.
- Resultado PWA: identidad FeedGo, manifest e iconos; build reproducible con
  `injectManifest`; app shell y precache restrictivo; firewall network-only;
  lifecycle y actualizacion controlados; proteccion multitab; offline,
  reconexion y recovery acotados; harness Playwright y validacion real de
  Chrome/Edge sobre Windows.
- 96.3 incorpora contexto geografico automatico, fallback territorial sin
  coordenadas, lectura anonima, gate de detalle y la correccion acotada de
  lifecycle visible para videos de publicaciones. La eliminacion de una
  Historia vigente se integra como intervencion funcional acotada con ownership
  backend y soft delete, sin iniciar el resto de ETAPA 97.
- Dominio `feedgo.com.ar`: reservado. DNS, HTTPS, hosting, API/CORS productivos,
  mixed content real, fallback SPA, deep links y refresh desplegados no poseen
  actualmente una etapa numerada. Solo se planificaran cuando el owner humano
  abra expresamente una evaluacion de lanzamiento.
- DEFECTO CONOCIDO DIFERIDO: determinados videos de Historias no inician en
  iPhone/Safari/PWA. No se declara resuelto ni validado. Caso B queda preservado
  en `frontend/.pwa-fixtures/story-video-case-b.html` y la investigacion pasa a
  ETAPA 124 - Compatibilidad Multimedia iOS/Safari/PWA.
- ETAPA 99 - Identidad, Registro y Autenticacion se encuentra en curso con 99.1,
  99.2, 99.3, 99.4 y 99.5 cerrados. El sprint 99.6 es el siguiente oficial,
  pendiente y no iniciado; la compatibilidad JWT legacy permanece hasta su
  retiro gobernado.
- FeedGo Clasificados queda incorporado documentalmente como vertical futura
  de primer nivel en ETAPAS 101 a 105; ETAPAS 106 y 107 preparan Plataforma
  Comercial, Advertising, Payments y Billing transversal. Ninguna fue iniciada.
- Documentos tecnicos propietarios: `docs/26_CLASSIFIEDS_CONTRACT.md` y
  `docs/27_COMMERCIAL_PLATFORM_CONTRACT.md`.
- Documento tecnico propietario: `docs/18_PWA_ENTERPRISE.md`.

## Etapa vigente

ETAPA 99 - Identidad, Registro y Autenticacion.

Estado:

En curso.

Bloque vigente:

99.7 - Enforcement en Spaces y Publicaciones. Pendiente y no iniciado.

Objetivo inmediato:

ET99.6 queda cerrada tecnica y funcionalmente. El siguiente trabajo es ET99.7:
enforcement backend uniforme en Spaces y Publicaciones, sin iniciar Google ni
cleanup legacy.

Restricciones:

- no iniciar ET99.8 ni ET99.9;
- no convertir Google en owner de identidad, sesion o autorizacion;
- no aplicar auto-link por coincidencia de email;
- no persistir edad ni inferir capabilities en frontend;
- no aplicar grandfathering, periodo de gracia o excepciones comerciales a
  datos existentes;
- preservar los owners de Spaces, Publicaciones, Ubicacion, Legal, PWA y
  Observabilidad.

Decisiones permanentes propietarias: `DEC-059` para arquitectura de identidad,
perfil y capabilities, `DEC-060` para descomposicion y ejecucion de ETAPA 99 y
`DEC-061` para acceso anonimo e interacciones protegidas. `DEC-062` registra el
diseno aprobado de 99.3 y remite al criterio transversal de comunicacion visible
propiedad de `docs/02_PRODUCT.md`. `DEC-063` aprueba telefono privado
verificado y un unico motor de recuperacion multicanal, implementados en su
  alcance backend de 99.5; 99.6 es owner de UX y remediation y 99.7 owner del
  enforcement. La UX publica exacta de seleccion de canal de recovery
  multicanal permanece deliberadamente pendiente y no puede mostrar hints de
  cuenta por anticipado.

Estado de cierre de 99.3:

Cerrado tecnica, funcional y documentalmente tras auditoria final, gates
automaticos y validacion manual aprobados. La implementacion adopta tokens de
accion de un uso con digest persistido, expiraciones de
24 horas para verificacion y 30 minutos para reset, reenvio con cooldown de 60
segundos, limites persistentes y defensa local, canal transaccional de identidad
independiente del correo administrativo, `FakeEmailProvider` para la primera
validacion y Resend deshabilitado hasta rotar la credencial y validar la
configuracion segura. La obligatoriedad de email verificado no se activa.

Riesgo transitorio aprobado: reset y cambio actualizan la credencial e
invalidan tokens de accion y sesiones FeedGo segun el contrato de 99.4, sin
agregar `credential_version`. Los JWT legacy ya emitidos pueden sobrevivir
hasta su expiracion maxima actual de 60 minutos y continúan dependiendo de
`tokens_revocados` hasta su retirada controlada en la transicion/99.9.

Estado de cierre de 99.4:

Cerrado tecnica, funcional y documentalmente. `FeedGoSession` es owner de los
JWT nuevos con claims exactos `sub`, `sid`, `iat`, `exp`, `issuer`, `audience`
y `version`; el frontend conserva el bearer opaco y Login deja de emitir JWT
legacy. Logout revoca la sesion nueva sin persistir el bearer completo. Reset
revoca todas las sesiones FeedGo sin auto-login; el cambio autenticado con JWT
nuevo conserva la sesion actual y revoca las demas, mientras el cambio con JWT
legacy revoca las sesiones FeedGo existentes sin migrar el token en caliente.
Google Auth no fue implementado: solo queda preparado el contrato de sesion
para el metodo `google`.

La validacion final registro backend completo 568 OK y 6 skips, MySQL aislado
ET99.4 7/7, E2E MySQL 1/1, frontend/PWA contractual 20/20, schema 37/37 y
`git diff --check` correcto. Permanecen 656 revocaciones legacy sin limpiar;
la retirada del contrato JWT anterior, su blacklist y ese cleanup corresponde
a la transicion/99.9.

Estado de cierre de 99.5:

Cerrado tecnica, funcional y documentalmente. Backend incorpora telefono
privado E.164 y verificacion mediante OTP, deriva `perfil_completo`,
`campos_perfil_faltantes`, aceptaciones legales vigentes y las capabilities
comerciales, y conserva un unico `PasswordRecoveryService` multicanal. Email
es el unico canal operativo; SMS y WhatsApp permanecen preparados pero
deshabilitados y sin provider real. La activacion externa real de email sigue
sujeta a configuracion y provider aprobados. Las capabilities no se persisten,
no integran JWT y todavia no aplican enforcement.

La validacion final registro backend completo 603 OK y 9 skips, focales 99.5
78/78, MySQL 10/10, PWA 25/25 y `git diff --check` correcto. La DB local
`mitienda` coincide con metadata en 38/38 tablas; la migracion de
`phone_verification_challenges` y su segunda ejecucion idempotente quedaron
aprobadas.

Estado de cierre de 99.6:

Cerrado tecnica y funcionalmente. El frontend centraliza `GET /usuarios/me` en
`useCurrentUser` sobre TanStack Query en memoria; AuthContext consume ese owner
y ProfilePage no mantiene copias paralelas. `Datos personales` incorpora fecha
de nacimiento y telefono privado, con telefono verificado en solo lectura y
backend como autoridad. La UX OTP mantiene challenge y codigo en memoria,
refresca `/usuarios/me`, usa respuestas `private, no-store` y un harness fake
restringido a local/dev/test, opt-in y loopback. Perfil, faltantes,
capabilities y pendientes comerciales se presentan desde derivados backend, sin
recalculo ni enforcement.

`ProtectedActionProvider` es el owner central de DEC-061: el Auth Wall usa
`ActiveLayer`, el gate temporal de cinco segundos se integra al mismo owner y
las interacciones no pasivas quedan protegidas por default-deny. `returnTo`
acepta solo contexto interno saneado; Login y Registro restauran ese contexto
sin persistir tokens ni datos sensibles.

Hardening final aprobado: frontend focal 61/61, backend focal 27/27, build
produccion/PWA correcto, ESLint focal sin errores (un warning preexistente en
`PerfilComercioPage`), arquitectura por capas y privacidad/PWA validadas.
El canal real de email aun requiere activacion operativa; Fake Email es solo
desarrollo/test. ET99.7 debe verificar esta dependencia antes de activar
enforcement que requiera email verificado.

Resultado de la primera implementacion:

- `usuarios` incorpora de forma nullable `email_canonical`,
  `email_verified_at`, `email_verification_source` y `fecha_nacimiento`;
- se incorporan `password_credentials`, `external_identities` y
  `feedgo_sessions`, registradas en metadata pero todavia sin consumo funcional;
- el preflight de 15 usuarios encontro 15 emails canonicos unicos, sin
  colisiones ni emails invalidos;
- el backfill copio exactamente los 15 hashes legacy y completo los 15 emails
  canonicos; no creo identidades externas ni sesiones y mantuvo verificacion y
  fecha de nacimiento en `null`;
- la migracion es opt-in, idempotente y compatible; una segunda ejecucion no
  produjo cambios;
- schema fisico y metadata coinciden en 35 tablas, sin diferencias de columnas,
  foreign keys, indices o restricciones unicas;
- 99.2 convirtio `email_canonical` y `PasswordCredential` en owners efectivos
  de Registro y Login, preservando dual-write, fallback controlado, JWT,
  revocacion y evidencia legal para compatibilidad y rollback.

Estado de cierre de 99.1:

Cerrado. La auditoria integral confirmo coherencia entre implementacion,
migracion, tests, schema fisico, `DEC-059`, `DEC-060`, documentacion y roadmap.
La secuencia oficial 99.1 a 99.9, sus dependencias, gates, rollback y reglas de
ejecucion pertenecen a `docs/05_SEARCH_ROADMAP.md`.

Estado de cierre de 99.2:

Cerrado tecnica, funcional y documentalmente tras validacion manual aprobada.
Registro canonicaliza y crea atomicamente Usuario, `PasswordCredential` y
evidencia legal, con dual-write legacy compatible; Login resuelve por email
canonico y verifica la credencial nueva, conservando fallback acotado para
rollback. La politica backend unica exige ocho caracteres, mayuscula, minuscula,
numero, ausencia de whitespace y limite tecnico bcrypt. Registro consume una
comprobacion anticipada minima y rate-limited sin reemplazar la constraint final,
y presenta feedback FeedGo inline. La base reparada no conserva filas sin email
canonico o credencial ni divergencias de hash. JWT, logout y revocacion legacy
permanecen vigentes hasta sus sprints owner. Tests backend y frontend, schema,
build/PWA, lint, `git diff --check` y validacion manual quedaron aprobados.

Cuando un sprint produzca comportamiento visible o flujo interactivo, la
validacion automatica de Codex no reemplaza la validacion manual del usuario.
Tras implementar y ejecutar tests deben informarse resultados, realizarse esa
validacion cuando corresponda y recibirse aprobacion. El cierre documental,
commit y push requieren orden expresa posterior; nunca son automaticos por
finalizar un sprint.

## Ultima etapa cerrada

ETAPA 98 - Correccion y Pulido Visual del Frontend.

Estado:

Cerrada tecnica y documentalmente.

Resultado:

FeedGo consolido Liquid como sistema visual compartido; recorrio y corrigio
superficies, navegacion, publicaciones, perfiles, interacciones, Historias,
formularios, responsive, light/dark y accesibilidad; estabilizo incidentalmente
fronteras transaccionales y caches sociales; y formalizo sin implementar el
futuro Dynamic Feed mediante `DEC-058` y `docs/28_DYNAMIC_FEED_DESIGN.md`.

Validacion final: ESLint sin errores y con cuatro advertencias preexistentes,
440 tests frontend correctos, 440 tests backend correctos con 1 omitido, build
productivo/PWA y `git diff --check` correctos.

ETAPA 99 - Identidad, Registro y Autenticacion es la etapa vigente; sus bloques
99.1, 99.2, 99.3 y 99.4 quedan cerrados y 99.5 es el siguiente sprint oficial,
pendiente y no iniciado.

## Etapa cerrada historica anterior a ETAPA 95

ETAPA 94 - QA Integral y Hardening Funcional.

Estado:

Cerrada.

Resultado:

ETAPA 94 queda cerrada con hardening funcional de relaciones persistentes,
visibilidad publica, contratos `404` e idempotencia, integracion frontend/cache,
QA basado en riesgo y estabilizacion final de lint. El cierre no implica una
reescritura general de API, frontend, agenda, productos, disponibilidad,
busqueda, uploads ni ETAPA 95.

Alcance:

- Matriz funcional de contratos para likes, guardados, seguidores,
  publicaciones, historias, feed, ranking, busqueda candidate source y
  consumidores frontend directos.
- Likes de publicaciones, guardados y seguidores endurecidos contra recursos
  inexistentes, inactivos o no visibles.
- Relaciones persistentes idempotentes: crear solo sobre recursos validos y
  visibles; eliminar permite limpiar relaciones existentes aunque el recurso
  haya quedado inactivo cuando el contrato lo requiere.
- Publicaciones visibles definidas como publicacion activa con comercio
  existente y activo.
- Historias visibles definidas como historia activa con comercio existente y
  activo.
- Colecciones publicas excluyen recursos no visibles; detalles no visibles
  responden `404` sin efectos secundarios como incremento de vistas.
- Feed, ranking y `PublicacionCandidateSource` excluyen publicaciones de
  comercios inactivos sin modificar algoritmos, scoring, limites ni orden.
- Frontend ajustado para manejar `404`, rollback, cache e invalidaciones sin
  decidir reglas de visibilidad ni reconstruir logica de dominio.
- Separacion de `AuthContextCore.js` para conservar Fast Refresh sin cambiar la
  API publica de autenticacion.
- Limpieza final de errores de ESLint; persisten warnings no bloqueantes
  documentados.

Subetapas de trabajo:

- 94.0 - Matriz de Contratos Funcionales: cerrada.
- 94.1 - Hardening de Relaciones e Interacciones Persistentes: cerrada.
- 94.2 - Hardening de Visibilidad Publica: cerrada.
- 94.3 - Integracion Frontend y Cache: cerrada.
- 94.4 - QA Integral Basado en Riesgo: cerrada.
- 94.5 - Estabilizacion y Limpieza Final: cerrada.

Validaciones de cierre:

- `python -m unittest tests.test_social_hardening`: OK, 24 tests.
- `python -m unittest tests.test_public_visibility_hardening`: OK, 14 tests.
- Suite backend completa: OK, 190 tests.
- `compileall app`: OK.
- `npm run lint`: OK, 0 errores y 5 warnings.
- Build frontend: OK.
- `git diff --check`: OK.

Limites del cierre:

- No se crearon tablas, migraciones ni endpoints nuevos.
- No se redisenaron agenda, disponibilidad, productos, uploads, discovery,
  knowledge, indexer ni ranking.
- No se modificaron algoritmos de feed, ranking o busqueda.
- No se agrego infraestructura de tests frontend.
- No se implemento ETAPA 95 dentro de ETAPA 94.

Pendientes derivados:

- ETAPA 95: experiencia de lanzamiento, design system critico, mapa y sistema
  de temas.
- ETAPA 96: plataforma instalable y PWA Enterprise, obligatoria antes de
  administracion operativa, infraestructura, pruebas masivas, beta y
  lanzamiento.
- ETAPA 97: administracion operativa minima, incluyendo capacidades de
  operacion manual que no forman parte de observabilidad base.
- ETAPA 98: correccion y pulido visual completo del frontend, posterior a PWA
  y operacion minima y previo al lanzamiento controlado.
- ETAPA 99: identidad, registro y autenticacion, vigente con 99.1 a 99.5
  cerrados y 99.6 pendiente/no iniciado.
- ETAPA 100: fundacion de validacion y staging aislado.
- ETAPAS 101 a 105: FeedGo Clasificados, desde dominio y experiencia hasta
  Search, IA multimodal, Historias, promocion y beneficios.
- ETAPA 106: plataforma comercial base y Advertising.
- ETAPA 107: monetizacion, Payments y Billing transversal operativos.
- ETAPA 108: calidad y validacion funcional integral.
- ETAPA 109: seguridad y hardening integral.
- ETAPA 110: confiabilidad, capacidad y resiliencia integral.
- No existe actualmente una etapa numerada de lanzamiento.
- Etapas futuras: infraestructura frontend de tests, carrera extrema potencial
  en likes de historias, actualizacion de Browserslist, optimizacion de chunks,
  warnings historicos de SQLite y migracion de `datetime.utcnow()` a timestamps
  timezone-aware.

## Integracion de Clasificados y roadmap previa a ETAPA 97

Estado:

Cerrada documentalmente. Ninguna etapa nueva fue iniciada.

Resultado:

- FeedGo Espacios y FeedGo Clasificados quedan como verticales de primer nivel
  bajo identidad FeedGo unica y arquitectura por capas;
- ETAPA 100 resuelve primero reproducibilidad, datos sinteticos, observabilidad
  base y staging aislado para evitar dependencias circulares;
- ETAPAS 101 a 105 construyen Clasificados mediante fronteras cerrables;
- ETAPAS 106 y 107 construyen Advertising, Payments y Billing transversal;
- ETAPAS 108 a 110 consolidan calidad, seguridad y capacidad/resiliencia;
- cada etapa funcional debe producir tests y controles progresivos;
- herramientas concretas permanecen candidatas sujetas a auditoria y politica
  local-first;
- completar etapas no autoriza apertura. No existe etapa numerada de
  lanzamiento; solo una instruccion humana expresa puede abrir su auditoria y
  un futuro GO / NO-GO basado en evidencia y riesgos residuales.

El trabajo previo a ETAPA 97 queda formalmente cerrado. ETAPA 96 permanece
cerrada. ETAPA 97 - Administracion Operativa Minima queda formalmente cerrada
con 97.1, 97.2, 97.3, 97.4, 97.5 y 97.6 cerradas. ETAPA 98 - Correccion y
Pulido Visual del Frontend queda formalmente cerrada. ETAPA 99 es la etapa
oficial vigente con 99.1 a 99.5 cerrados y 99.6 pendiente/no iniciado.

## Estado ETAPA 92

ETAPA 92 - Integridad de Datos, Backups y Recuperacion.

Estado:

Cerrada.

Resultado:

ETAPA 92 queda cerrada con blindaje operativo de scripts, verificacion profunda
de schema, backup oficial, restore real temporal y evidencia de recuperacion. El
cierre no implica automatizacion periodica, copia externa cifrada ni PITR.

Alcance:

- `create_tables.py` protegido contra efectos laterales al importar.
- `reset_db.py` protegido contra ejecucion destructiva accidental.
- `check_database_schema.py` implementado como verificacion read-only profunda
  de tablas, columnas, FKs, indices y restricciones unicas.
- `model_registry` registra los modelos necesarios para `Base.metadata`.
- Backup y restore desacoplados mediante providers y storage local inicial.
- `backup_database.py` implementado como procedimiento oficial inicial de backup
  MySQL con `mysqldump`, `--single-transaction`, `--quick`, gzip, SHA-256,
  manifiesto versionado y conteos criticos.
- `restore_database.py` implementado como procedimiento oficial inicial de
  restore sobre base temporal `feedgo_restore_tmp_*`, con streaming por `stdin`
  al cliente MySQL, validacion de manifiesto, gzip, SHA-256, schema y conteos.
- Metadata SQLAlchemy y MySQL local quedaron alineados en 27 tablas metadata y
  27 tablas fisicas, sin diferencias estructurales.
- FK fisica `comercios.rubro_id -> rubros.id` creada mediante script controlado
  y confirmacion explicita.
- Backup oficial posterior a la alineacion generado y validado en
  `C:\FeedGoOps\backups\mysql\mitienda_20260801T181443Z.sql.gz`.
- Restore real exitoso en base temporal y evidencia JSON conservada en
  `C:\FeedGoOps\restore_tmp\evidence\feedgo_restore_tmp_20260801_183100_20260801T182747Z_restore.json`.
- Base temporal eliminada con confirmacion explicita tras validar el restore.
- `mitienda` quedo intacta despues de la prueba.

Subetapas de trabajo:

- 92.1 - Blindaje operativo y matriz de datos criticos: cerrada.
- 92.2 - Estrategia y herramienta de backup: cerrada.
- 92.3 - Restore seguro y prueba de recuperacion: cerrada.
- 92.3A - Arquitectura extensible de backup/restore: cerrada.
- 92.4 - Prueba real de backup, alineacion y restore temporal: cerrada.
- 92.5 - Auditoria final, documentacion, CHANGELOG, commit y push: cerrada.

Mediciones de cierre:

- Backup oficial: 0.444 s, 147405 bytes, SHA-256
  `70c7bd53002c6ac646891a989b1da96181cc1cdde3bef9d5f6b47e9667119970`.
- RTO observado del restore temporal y validacion: 3.336 s.
- Antiguedad observada del punto recuperado al iniciar el restore: ~13 minutos.
  Esto no constituye RPO garantizado.
- Tests backend: 119 OK.
- `compileall app`: OK.
- ESLint de archivos frontend modificados: 0 errores, 1 warning preexistente.
- Build frontend: OK con warnings preexistentes de entorno/assets/tamano.
- `git diff --check`: OK.

Bloqueantes de lanzamiento publico:

- automatizacion periodica de backups;
- copia externa cifrada y verificada;
- retencion operativa real y monitoreada;
- PITR/binlogs evaluados y probados si se requiere RPO menor;
- pruebas recurrentes de restore con evidencia;
- operacion y observabilidad productiva.

Pendientes derivados:

- ETAPA 93: logs, monitoreo, diagnostico, configuracion productiva,
  automatizacion operativa inicial, ownership y ciclo de vida de uploads.
- ETAPA 94: pruebas recurrentes, hardening funcional, relaciones sociales y
  validaciones de recursos inexistentes o inactivos.
- Etapas operativas futuras: copia externa cifrada, PITR/binlogs, providers RDS,
  Percona o cloud, automatizacion avanzada y simulacros recurrentes.

## Estado ETAPA 93

Nombre:

ETAPA 93 - Observabilidad y Operacion.

Objetivo:

Preparar logs, monitoreo, diagnostico, configuracion productiva y operacion
minima sin introducir deuda de infraestructura innecesaria.

Documento dueno tecnico-operativo:

- `docs/17_OBSERVABILITY_AND_OPERATIONS.md`.

Estado:

Cerrada.

Subetapas:

- 93.1 - Arquitectura Operativa: cerrada documentalmente.
- 93.2 - Logging Enterprise y Error Handling: cerrada tecnicamente.
- 93.3 - Contexto Operativo y Correlacion: cerrada tecnicamente.
- 93.4 - Health, Readiness y Estado del Sistema: cerrada tecnicamente.
- 93.5 - Metricas y Senales Operativas: cerrada tecnicamente.
- 93.6 - Alertas mediante Contratos: cerrada tecnicamente.
- 93.7 - Runbooks, Validacion y Cierre: cerrada tecnicamente.

Resultado de 93.1:

- Se define una arquitectura operativa minima basada en contratos estables.
- Se separan logs, metricas, alertas, health, auditoria, analytics y evidencia
  de backup/restore.
- Se aprueba el modelo conceptual de `OperationEvent` y contextos asociados.
- Se define la politica de datos permitidos y prohibidos para observabilidad.
- Se define matriz inicial de configuracion productiva.
- Se define modelo conceptual de liveness, readiness, startup y estado
  degradado.
- Se define catalogo minimo de metricas y alertas sin proveedores externos.
- Uploads queda asignado a ETAPA 93 como deuda operativa a resolver con
  auditoria previa del modelo de datos.

Restricciones de 93.1:

- No se implemento logging productivo.
- No se creo middleware.
- No se crearon endpoints de health.
- No se crearon tablas ni migraciones.
- No se integraron Prometheus, Grafana, Sentry, OpenTelemetry, cloud storage ni
  proveedores externos.
- `CHANGELOG.md` no se actualiza hasta el cierre operativo del sprint o etapa
  segun corresponda.

Resultado de 93.2:

- Se implementa logger central reutilizable basado en `logging` estandar.
- Se define politica tecnica de niveles `DEBUG`, `INFO`, `WARNING`, `ERROR` y
  `CRITICAL`.
- Se registra handler central para `HTTPException`,
  `RequestValidationError` y excepciones no controladas.
- Los errores no controlados devuelven mensaje generico al frontend.
- Los errores de validacion devuelven respuesta generica sin eco de payload.
- Los detalles sensibles en `HTTPException` se reemplazan por mensajes
  publicos seguros.
- `http_service.js` deja de propagar cuerpos crudos de error del backend y
  conserva solo status y mensaje publico.
- El contexto queda preparado para RequestContext futuro sin implementar todavia
  correlation ID.

Restricciones de 93.2:

- No se implemento middleware.
- No se implemento correlation ID.
- No se crearon endpoints.
- No se crearon tablas ni migraciones.
- No se integraron proveedores externos.
- No se reemplazaron scripts CLI por logger de aplicacion.

Resultado de 93.3:

- Se implementa un middleware unico de Request Context.
- Cada request recibe un `request_id` unico.
- `X-Correlation-ID` entrante se reutiliza cuando es seguro; si falta o es
  invalido se genera uno nuevo.
- `request_id` y `correlation_id` quedan disponibles durante la request mediante
  contexto operativo.
- El logger central incorpora automaticamente ambos identificadores cuando
  existen.
- Los handlers globales registran ambos identificadores en errores HTTP,
  validacion y errores no controlados.
- Todas las respuestas procesadas por el middleware devuelven `X-Request-ID` y
  `X-Correlation-ID`.
- Los errores no controlados conservan headers de correlacion sin exponer
  secretos ni stack traces.

Restricciones de 93.3:

- No se implementaron health checks.
- No se crearon endpoints.
- No se implementaron metricas ni alertas.
- No se integro OpenTelemetry.
- No se crearon tablas ni migraciones.

Resultado de 93.4:

- Se implementan endpoints separados `GET /health/live` y
  `GET /health/ready`.
- Liveness verifica que la API responde.
- Readiness ejecuta checks read-only de API, conexion a base de datos,
  compatibilidad de schema, uploads/storage, configuracion de embeddings,
  evidencia de backup y evidencia de restore.
- Cada check devuelve estado, componente, tiempo de respuesta y mensaje seguro.
- Readiness devuelve `503` solo cuando algun componente queda `unhealthy`.
- Estados degradados se informan sin impedir liveness ni exponer detalles
  sensibles.
- Los endpoints se integran con logger central y Request Context, por lo que
  devuelven `X-Request-ID` y `X-Correlation-ID`.
- No se ejecutan backups, restores, escrituras, `create_all`, `drop_all`,
  migraciones ni operaciones destructivas.
- No se exponen secretos, rutas internas, SQL, stack traces ni configuracion
  sensible.

Restricciones de 93.4:

- No se implementaron metricas.
- No se implementaron alertas.
- No se integro Prometheus, Grafana ni OpenTelemetry.
- No se crearon tablas ni migraciones.
- No se resolvio todavia ownership ni ciclo de vida persistente de uploads.

Resultado de 93.5:

- Se implementan contratos minimos para metricas `counter`, `duration` y
  `gauge`.
- Se implementa `MetricSample`, `MetricsRecorder` y `LocalMetricsSink` como
  sink inicial en memoria, sin proveedor externo.
- Se registra un catalogo inicial de nombres estables de metricas.
- Se instrumentan request count, latencia, respuestas `4xx` y `5xx`, errores no
  controlados, fallos de autenticacion y autorizacion.
- Se instrumentan readiness, duracion de checks, backup, restore, uploads
  aceptados/rechazados y busquedas sin resultados.
- Las metricas quedan desacopladas de logs, alertas y analytics de producto.
- Las etiquetas se sanitizan para no registrar secretos, tokens, payloads
  completos ni datos personales.

Restricciones de 93.5:

- No se implementaron alertas.
- No se crearon endpoints de metricas.
- No se integro Prometheus, Grafana, Sentry ni OpenTelemetry.
- No se crearon tablas ni migraciones.
- No se resolvio todavia ownership ni ciclo de vida persistente de uploads.

Resultado de 93.6:

- Se implementan contratos minimos `AlertRule`, `AlertEvent`, `AlertSeverity` y
  `AlertSink`.
- Se implementa `AlertEngine` como evaluador interno de reglas.
- Se implementa `LocalAlertSink` como sink inicial en memoria, sin proveedor
  externo.
- Las alertas se evaluan desde metricas y health existentes, sin parsear logs.
- Se implementa deduplicacion por regla y contexto seguro.
- Se implementa cooldown por clave de deduplicacion.
- Se registran estados `active` y `suppressed`.
- Se incorpora catalogo inicial para readiness `unhealthy`, errores `5xx`
  repetidos, backup fallido o evidencia no saludable, restore fallido y
  rechazos repetidos de uploads.

Restricciones de 93.6:

- No se integraron email, Slack, Discord, Telegram, Sentry ni servicios cloud.
- No se crearon dashboards.
- No se crearon endpoints de alertas.
- No se crearon tablas ni migraciones.
- No se implemento persistencia historica de alertas.
- No se implementaron politicas de guardia, escalamiento ni resolucion manual.
- No se resolvio todavia ownership ni ciclo de vida persistente de uploads.

## Recordatorio

Toda nueva decision permanente debera actualizar los Documentos de Gobierno antes de continuar implementando.

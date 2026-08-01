# Roadmap Oficial de Evolucion de FeedGo

Estado del documento: Documento Oficial del Sistema de Gobierno FeedGo v1.0.
Version: 1.0.
Categoria: Sistema de Gobierno.
Nivel de autoridad: Alto para secuencia oficial de etapas y alcance aprobado
por etapa.
Documento dueno: `docs/05_SEARCH_ROADMAP.md`.
Responsable funcional: Roadmap de producto y arquitectura.
Documentos relacionados: `00_GOVERNANCE.md`, `04_CURRENT_STAGE.md`,
`07_DECISIONS.md`, `15_LEGAL_AND_OPERATIONAL.md`.
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

### ◐ ETAPA 92

Integridad de Datos, Backups y Recuperacion.

Objetivo:

Validar integridad de datos, estrategia de backups, restauracion, conservacion
y recuperacion operativa.

Estado:

Vigente.

### ☐ ETAPA 93

Observabilidad y Operacion.

Objetivo:

Preparar logs, monitoreo, diagnostico, configuracion productiva y operacion
minima sin introducir deuda de infraestructura innecesaria.

Estado:

Pendiente.

Pendiente programado desde ETAPA 90:

- endurecer uploads con tamano real permitido, cuota, asociacion con usuario o
  recurso, validacion, limpieza y auditoria.

### ☐ ETAPA 94

QA Integral y Hardening Funcional.

Objetivo:

Ejecutar validacion integral, corregir defectos comprobados y endurecer los
flujos principales existentes antes del lanzamiento.

Estado:

Pendiente.

Pendientes programados desde ETAPA 90:

- validar existencia y estado de publicaciones antes de operar likes;
- validar existencia y estado de comercios antes de operar seguidores;
- definir comportamiento `404` o idempotente en relaciones sociales.

### ☐ ETAPA 95

Experiencia de Lanzamiento y Design System Critico.

Objetivo:

Ajustar la experiencia central de lanzamiento, accesibilidad, responsive y
consistencia visual critica sin convertirlo en una reescritura del sistema de
diseno.

Estado:

Pendiente.

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

### ☐ ETAPA 96

Administracion Operativa Minima.

Objetivo:

Implementar o preparar las capacidades minimas para operar, revisar y resolver
incidentes de una primera version publica controlada.

Estado:

Pendiente.

### ☐ ETAPA 97

Infraestructura y Lanzamiento Controlado.

Objetivo:

Preparar despliegue, configuracion productiva, checklist final y publicacion
controlada de FeedGo.

Estado:

Pendiente.

### ☐ ETAPA 98

Analytics y Aprendizaje de Uso Real.

Objetivo:

Medir uso real de manera respetuosa de privacidad para orientar decisiones
posteriores al lanzamiento.

Estado:

Pendiente.

### ☐ ETAPA 99

Calidad de Datos y Conocimiento Administrable.

Objetivo:

Mejorar datos, conocimiento administrable y trazabilidad de informacion usada
por busqueda, descubrimiento y futuras capacidades inteligentes.

Estado:

Pendiente.

### ☐ ETAPA 100

Reservas Publicas y Carrito de Reserva.

Objetivo:

Disenar e implementar solicitudes publicas, servicios reservables y flujo de
reserva sin pagos, sin exponer la agenda privada completa del propietario.

Estado:

Pendiente.

### ☐ ETAPA 101

Mensajeria y Cotizaciones.

Objetivo:

Disenar e implementar comunicaciones externas transversales y reutilizables
para FeedGo, incluyendo correo, WhatsApp, destinos verificables, proveedores,
plantillas, infraestructura asincronica, reintentos, idempotencia, webhooks,
observabilidad y futuras politicas de capacidades comerciales.

Estado:

Pendiente.

### ☐ ETAPA 102

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

### ☐ ETAPA 103

Promociones y Fidelizacion.

Objetivo:

Explorar promociones, beneficios y mecanismos de fidelizacion posteriores al
lanzamiento basados en uso real.

Estado:

Pendiente.

### ☐ ETAPA 104

Opiniones y Motor de Reputacion.

Objetivo:

Disenar reputacion, opiniones y senales publicas con moderacion, seguridad y
prevencion de abuso.

Estado:

Pendiente.

### ☐ ETAPA 105

Notificaciones Inteligentes.

Objetivo:

Disenar e implementar notificaciones locales y futuras notificaciones
inteligentes, reutilizando la infraestructura transversal que corresponda.

Estado:

Pendiente.

### ☐ ETAPA 106

Preferencias, Recomendaciones y Contexto.

Objetivo:

Incorporar preferencias, contexto y recomendaciones basadas en uso real,
privacidad y control del usuario.

Estado:

Pendiente.

### ☐ ETAPA 107

IA Conversacional.

Objetivo:

Evaluar e incorporar IA conversacional cuando existan datos, gobernanza y
necesidades de producto suficientes.

Estado:

Pendiente.

### ☐ ETAPA 108

Tendencias, Oferta, Demanda y Motor Predictivo.

Objetivo:

Construir senales predictivas y analiticas avanzadas posteriores al
lanzamiento.

Estado:

Pendiente.

### ☐ ETAPA 109

Ranking Dinamico y Descubrimiento Proactivo.

Objetivo:

Evolucionar ranking y descubrimiento con senales reales, trazabilidad y
controles de calidad.

Estado:

Pendiente.

### ☐ ETAPA 110

Plataforma Comercial y Backend Universal.

Objetivo:

Evaluar la expansion hacia capacidades comerciales y backend universal despues
de validar uso real, operacion y necesidades del producto.

Estado:

Pendiente.

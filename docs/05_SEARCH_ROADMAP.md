# Objetivo

El Roadmap representa el plan oficial de construccion del buscador.

Debe mantenerse actualizado durante todo el proyecto.

Cualquier evolucion del roadmap debe seguir el procedimiento formal definido en
`00_GOVERNANCE.md`.

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

Pendiente transversal aproximado para ETAPAS 95-100:

- evaluar la creacion de `docs/09_ARCHITECTURE.md` con una vista enterprise
  del backend, sin duplicar gobierno, decisiones ni documentos tecnicos
  especificos.

### ☐ ETAPA 89

Productos e Inventario.

### ☐ ETAPA 90

Pedidos, Carrito y Pagos.

### ☐ ETAPA 91

Mensajeria y Comunicaciones Externas.

Objetivo:

Disenar e implementar comunicaciones externas transversales y reutilizables
para FeedGo, incluyendo correo, WhatsApp, destinos verificables, proveedores,
plantillas, infraestructura asincronica, reintentos, idempotencia, webhooks,
observabilidad y futuras politicas de capacidades comerciales.

Estado:

Pendiente.

Incluye el trabajo diferido de correo, WhatsApp, proveedores externos,
verificacion de destinos, workers, colas, schedulers productivos, plantillas,
reintentos, webhooks e intentos de entrega externa.

### [pendiente] ETAPA futura - Reservas publicas

Objetivo:

Disenar e implementar Reservas/Solicitudes publicas, servicios reservables,
recursos, capacidad y flujo publico sin exponer la agenda privada completa del
propietario.

Estado:

Pendiente.

### [pendiente] ETAPA futura - Notificaciones locales

Objetivo:

Disenar e implementar el sistema transversal de notificaciones locales dentro
de FeedGo, incluyendo campana global, contador, listado, marcado como leido,
configuracion local e integracion inicial con sucesos de Agenda.

Estado:

Pendiente.

### ☐ ETAPA 92

Reputacion.

### ☐ ETAPA 93

IA Conversacional.

### ☐ ETAPA 94

Recomendaciones.

### ☐ ETAPA 95

Analytics.

### ☐ ETAPA 96

Inteligencia Global.

### ☐ ETAPA 97

Calidad de Datos.

### ☐ ETAPA 98

Moderacion.

### ☐ ETAPA 99

Observabilidad.

### ☐ ETAPA 100

Backend Universal.

### ☐ ETAPA 101

Unificacion del Design System.

Objetivo:

Auditar y unificar la interfaz visual de FeedGo sin modificar logica de negocio,
contratos, backend ni funcionalidades.

Estado:

Pendiente.

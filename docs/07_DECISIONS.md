# Decisiones Arquitectónicas

Este documento registra decisiones arquitectónicas permanentes aprobadas.

No reemplaza la documentación oficial existente.

## DEC-001

- ID: DEC-001
- Título: Backend First
- Estado: Aprobada
- Decisión: Toda la lógica de negocio vive en backend.
- Motivo: El backend es dueño del negocio y debe preservar las reglas del sistema.
- Impacto: El frontend no implementa lógica de negocio.

## DEC-002

- ID: DEC-002
- Título: Frontend responsable únicamente de interacción y UX
- Estado: Aprobada
- Decisión: El frontend se limita a interacción, renderizado y experiencia de usuario.
- Motivo: La separación de responsabilidades evita duplicar reglas y lógica de negocio.
- Impacto: Las decisiones de producto, negocio, búsqueda e indexación permanecen en backend.

## DEC-003

- ID: DEC-003
- Título: Runtime sin construcción de conocimiento
- Estado: Aprobada
- Decisión: El Runtime nunca construye conocimiento; solo consume conocimiento preparado.
- Motivo: El buscador debe permanecer liviano durante la lectura.
- Impacto: La inteligencia pesada ocurre antes del runtime.

## DEC-004

- ID: DEC-004
- Título: Indexador como preparador de conocimiento
- Estado: Aprobada
- Decisión: El Indexador prepara el conocimiento que consumirá el buscador.
- Motivo: La indexación concentra el trabajo pesado y mantiene simple el runtime.
- Impacto: Discovery, Candidate Engine y Ranking consumen conocimiento preparado.

## DEC-005

- ID: DEC-005
- Título: Commerce Index Document no editable
- Estado: Aprobada
- Decisión: El Commerce Index Document nunca se edita manualmente; siempre se reconstruye.
- Motivo: Evita inconsistencias entre fuentes oficiales y artefactos derivados.
- Impacto: Todo cambio debe provenir de fuentes oficiales y del Indexador.

## DEC-006

- ID: DEC-006
- Título: Commerce Index Document derivado
- Estado: Aprobada
- Decisión: El Commerce Index Document es derivado y no constituye la fuente primaria de verdad.
- Motivo: Las fuentes oficiales son las entidades, la Taxonomía, el Knowledge System y las señales aprobadas.
- Impacto: El Documento puede regenerarse sin pérdida de autoridad.

## DEC-007

- ID: DEC-007
- Título: Taxonomía como estructura oficial
- Estado: Aprobada
- Decisión: La Taxonomía constituye la estructura oficial del buscador.
- Motivo: Debe existir un esqueleto estable, jerárquico y controlado.
- Impacto: La Taxonomía no se convierte en una lista gigante de términos.

## DEC-008

- ID: DEC-008
- Título: Knowledge Graph derivado
- Estado: Aprobada
- Decisión: El Knowledge Graph representa conocimiento derivado y nunca reemplaza la Taxonomía.
- Motivo: El conocimiento dinámico debe crecer sin modificar la estructura oficial.
- Impacto: El Knowledge Graph complementa a la Taxonomía sin redefinirla.

## DEC-009

- ID: DEC-009
- Título: Documento antes de Índices Sintetizados
- Estado: Aprobada
- Decisión: El Commerce Index Document se construye antes de los Índices Sintetizados.
- Motivo: Los índices deben derivar de conocimiento ya consolidado.
- Impacto: Los Índices Sintetizados no son fuente de conocimiento.

## DEC-010

- ID: DEC-010
- Título: Índices Sintetizados derivados del Documento
- Estado: Aprobada
- Decisión: Los Índices Sintetizados se generan desde el Commerce Index Document, nunca directamente desde las tablas originales.
- Motivo: El Documento concentra la interpretación semántica aprobada.
- Impacto: La búsqueda consume índices derivados de conocimiento preparado.

## DEC-011

- ID: DEC-011
- Título: Documentar antes de implementar
- Estado: Aprobada
- Decisión: Toda decisión arquitectónica aprobada debe documentarse antes de implementarse.
- Motivo: La documentación gobierna el proyecto.
- Impacto: Ninguna implementación relevante debe avanzar sin decisión registrada.

## DEC-012

- ID: DEC-012
- Título: `/docs` como memoria técnica oficial
- Estado: Aprobada
- Decisión: La carpeta `/docs` constituye la memoria técnica oficial del proyecto.
- Motivo: El proyecto no debe depender del historial de chats ni de memoria externa.
- Impacto: Toda continuidad debe reconstruirse desde el repositorio.

## DEC-013

- ID: DEC-013
- Título: Prompt Maestro desde documentación oficial
- Estado: Aprobada
- Decisión: Los Prompt Maestro deben generarse exclusivamente a partir de la documentación oficial.
- Motivo: El historial conversacional no es fuente de verdad.
- Impacto: Cada Prompt Maestro debe poder reconstruirse desde `/docs`.

## DEC-014

- ID: DEC-014
- Título: Nuevo chat desde documentación oficial
- Estado: Aprobada
- Decisión: Toda nueva conversación debe reconstruir el contexto leyendo la documentación oficial.
- Motivo: La continuidad del proyecto vive en el repositorio.
- Impacto: Ninguna conversación debe depender de la memoria del modelo.

## DEC-015

- ID: DEC-015
- Título: Integraciones externas desacopladas
- Estado: Aprobada
- Decisión: Los sistemas externos se integran mediante contratos y adaptadores. Nunca forman parte del dominio central.
- Motivo: FeedGo debe conservar la lógica del dominio y evitar acoplarse a proveedores específicos.
- Impacto: Las integraciones externas deben poder reemplazarse sin reescribir el dominio principal.

## DEC-016

- ID: DEC-016
- Título: Seguridad por diseño
- Estado: Aprobada
- Decisión: Toda arquitectura e implementación debe considerar seguridad desde el inicio, nunca como una etapa posterior.
- Motivo: La seguridad forma parte del diseño técnico y no puede agregarse al final sin generar riesgos.
- Impacto: Cada decisión técnica debe evaluar riesgos de seguridad antes de implementarse.

## DEC-017

- ID: DEC-017
- Título: Defensa en profundidad
- Estado: Aprobada
- Decisión: FeedGo debe diseñarse suponiendo que cualquier integración, entrada o dependencia puede fallar o ser comprometida. La arquitectura debe limitar el impacto de esos escenarios.
- Motivo: El sistema debe minimizar daños ante fallas, entradas maliciosas o dependencias comprometidas.
- Impacto: Los componentes deben validar, aislar permisos y fallar de manera segura.

## DEC-019

- ID: DEC-019
- Título: Secure by Default
- Estado: Aprobada
- Decisión: Todo componente debe nacer con la configuración más segura posible. Las excepciones deberán habilitarse explícitamente. Nunca al revés.
- Motivo: Las configuraciones permisivas por defecto aumentan el riesgo operativo y técnico.
- Impacto: El comportamiento inicial de módulos, endpoints e integraciones debe priorizar protección, mínimo privilegio y acceso denegado.

## DEC-020

- ID: DEC-020
- Título: Documentación autoclasificada
- Estado: Aprobada
- Decisión: Toda documentación oficial deberá declarar explícitamente su categoría y responsabilidad.
- Motivo: Permitir que cualquier IA pueda descubrir automáticamente qué documentos debe leer y en qué orden.
- Impacto: El Sistema de Gobierno deja de depender de listas fijas de archivos y pasa a ser escalable.

## DEC-021

- ID: DEC-021
- Título: El Sistema de Gobierno gobierna a la IA
- Estado: Aprobada
- Decisión: Los prompts nunca deberán reemplazar el Sistema de Gobierno. Los prompts únicamente ordenan seguir el procedimiento oficial.
- Motivo: El conocimiento debe vivir en el proyecto y no en instrucciones externas.
- Impacto: Cualquier cambio futuro del procedimiento deberá realizarse modificando la documentación oficial y no los prompts.

## DEC-022

- ID: DEC-022
- Título: Normalización de texto compartida
- Estado: Aprobada
- Decisión: La normalización de texto debe existir como contrato compartido reutilizable del backend.
- Motivo: Evitar implementaciones paralelas entre Indexador, Discovery, Embeddings y futuros consumidores.
- Impacto: SearchRepresentationBuilder y futuros consumidores deben depender del contrato compartido, no de contratos locales duplicados.

## DEC-023

- ID: DEC-023
- Título: Estado público y horarios de atención separados
- Estado: Aprobada
- Decisión: El estado público del espacio usa exclusivamente `Activo` y `En pausa`; el estado horario usa exclusivamente `Abierto`, `Cerrado` y `No hay horarios declarados`.
- Motivo: Separar publicación y visibilidad del espacio de los horarios de atención evita mezclar `Comercio.activo` con disponibilidad operativa.
- Impacto: El backend debe ser propietario de la regla de cálculo del estado horario; el frontend no lo inventa; el estado horario no modifica automáticamente `Activo` o `En pausa`; pasar a `En pausa` no elimina ni modifica horarios; al volver a `Activo` se reutilizan los horarios existentes.

## DEC-024

- ID: DEC-024
- Titulo: Gobierno del Modelo de Datos
- Estado: Aprobada
- Decision: Antes de crear cualquier tabla nueva debe auditarse el modelo de datos existente y demostrarse que no hay una tabla propietaria natural, que no corresponde ampliar una tabla o relacion existente y que la nueva tabla tendra una unica responsabilidad sin duplicar datos.
- Motivo: Preservar responsabilidad unica, evitar segundas fuentes de verdad y sostener una arquitectura enterprise.
- Impacto: Toda nueva tabla debe justificar su responsabilidad, propietario del dato, clasificacion y compatibilidad con el modelo existente antes de implementarse.

## DEC-025

- ID: DEC-025
- Titulo: Compatibilidad hacia atras obligatoria
- Estado: Aprobada
- Decision: Toda nueva funcionalidad debe auditar su impacto sobre endpoints, servicios, tablas, contratos y pantallas existentes antes de cerrar una etapa.
- Motivo: Evitar regresiones sobre funcionalidades historicas cuando se incorporan modulos nuevos.
- Impacto: Una etapa no puede cerrarse sin evidencia de que las funcionalidades anteriores siguen funcionando o degradan de forma controlada.

## DEC-026

- ID: DEC-026
- Titulo: Tablas derivadas no son fuente de verdad
- Estado: Aprobada
- Decision: Caches, indices, embeddings, snapshots, eventos y tablas analiticas nunca reemplazan a la fuente oficial del dominio.
- Motivo: Mantener consistencia, regenerabilidad y trazabilidad de la informacion.
- Impacto: La documentacion tecnica debe declarar que tablas son fuente de verdad, relaciones, configuracion, indices, IA, eventos, historicas, caches o analiticas.

## DEC-027

- ID: DEC-027
- Titulo: Validacion obligatoria de schema fisico
- Estado: Aprobada
- Decision: Antes de cerrar una etapa que agregue o use tablas nuevas debe compararse `Base.metadata` contra las tablas reales de MySQL.
- Motivo: Evitar regresiones donde una tabla registrada en metadata sea usada por runtime pero no exista fisicamente.
- Impacto: Una etapa no puede cerrarse si existen diferencias entre metadata y MySQL que afecten endpoints o servicios existentes.

## DEC-028

- ID: DEC-028
- Titulo: Design System oficial para acciones secundarias
- Estado: Aprobada
- Decision: Los botones secundarios de FeedGo deben mostrarse sin borde, capsula ni marco permanente en estado normal, usando icono y texto cuando corresponda, y mostrar resaltado solo en hover, focus o interaccion.
- Motivo: Mantener una experiencia visual uniforme, moderna y accesible en toda la aplicacion.
- Impacto: Nuevas pantallas y ajustes visuales deben respetar este criterio; los botones primarios pueden conservar un tratamiento diferenciado cuando su jerarquia lo justifique.

## DEC-029

- ID: DEC-029
- Titulo: Agenda como modulo autonomo dentro del monorepo
- Estado: Aprobada
- Decision: Agenda se disenara como modulo propio y potencialmente reutilizable dentro del monorepo actual, con backend en `backend/app/modules/agenda/` y frontend en `frontend/src/features/agenda/`.
- Motivo: Agenda tiene dominio propio y no debe quedar atada a Mi Perfil, Comercios, Discovery, publicaciones ni navegacion especifica de FeedGo.
- Impacto: FeedGo consumira Agenda mediante una capa de integracion. El nucleo de Agenda no debe depender de Profile, Spaces, Discovery, Search, Ranking, Posts, Stories, Availability ni rutas concretas de FeedGo.

## DEC-030

- ID: DEC-030
- Titulo: Separacion entre Availability, Agenda y Reservas
- Estado: Aprobada
- Decision: Availability, Agenda y Reservas son capacidades distintas. Availability modela horarios habituales; Agenda organiza eventos privados del propietario; Reservas utiliza Agenda sin exponerla completa al cliente.
- Motivo: Evitar mezclar horarios habituales, organizacion interna y solicitudes publicas en una unica fuente de verdad.
- Impacto: Las reglas, estados y permisos de cada capacidad deben mantenerse separados. El frontend no debe inferir disponibilidad reservable desde horarios habituales ni exponer la agenda privada.

## DEC-031

- ID: DEC-031
- Titulo: ActiveLayer como infraestructura transversal de capas activas
- Estado: Aprobada
- Decision: ActiveLayer es la infraestructura transversal reutilizable para modales, overlays y capas activas nuevas de FeedGo.
- Motivo: Evitar sistemas paralelos de overlays y mantener una sola regla UX para bloquear fondo, foco e interaccion cuando existe una capa activa.
- Impacto: Agenda debe reutilizar ActiveLayer y no crear un sistema propio de overlays.

## DEC-032

- ID: DEC-032
- Titulo: Contexto agendable y solicitud publica desacoplados
- Estado: Aprobada
- Decision: La Agenda pertenece a un contexto agendable. En FeedGo, el primer contexto agendable sera un espacio, pero el nucleo de Agenda no debe nombrarlo como `comercio`. Un propietario con varios espacios tendra una agenda por contexto y una vista unificada. Turno y reserva seran variantes funcionales de una solicitud publica comun durante el MVP; la solicitud conserva identidad propia y puede reflejarse como elemento vinculado de Agenda.
- Motivo: Evitar acoplar el nucleo de Agenda al modelo de Comercio y evitar que Reservas se mezcle irreversiblemente con elementos internos de Agenda.
- Impacto: La integracion FeedGo resolvera la relacion entre contexto agendable y espacio. Reservas mantendra su frontera propia y no convertira solicitudes en elementos de Agenda como unica fuente de verdad.

## DEC-033

- ID: DEC-033
- Titulo: Persistencia autonoma del nucleo de Agenda
- Estado: Aprobada
- Decision: El nucleo de Agenda tendra entidades propias `ContextoAgendable` y `ElementoAgenda`. `ElementoAgenda` dependera unicamente de `ContextoAgendable` y no tendra FK directa a `comercios`, medicos, consultorios ni otros recursos externos de una aplicacion host.
- Motivo: Agenda debe ser un modulo realmente reutilizable e independiente. Una FK directa a un recurso de FeedGo haria que sus modelos, migraciones y pruebas dependan de Spaces y bloquearia su uso en otra aplicacion, como una aplicacion medica sin comercios.
- Impacto: Cada aplicacion host debera implementar su propia capa de integracion entre sus recursos y `ContextoAgendable`. FeedGo vinculara `Comercio` con `ContextoAgendable` fuera del nucleo de Agenda. Agenda no copiara nombre, rubro, direccion, propietario ni datos del comercio. No se implementa microservicio en esta etapa.

## DEC-034

- ID: DEC-034
- Titulo: Agenda sin sobrescritura silenciosa
- Estado: Aprobada
- Decision: Toda mutacion concurrente sobre `ElementoAgenda` debe exigir una version esperada y rechazar la operacion cuando la version persistida haya cambiado. No se permite la politica "ultima escritura gana" para Agenda.
- Motivo: La Agenda puede ser usada desde varios usuarios, equipos o sesiones. Sobrescribir silenciosamente cambios remotos produciria perdida de informacion y decisiones operativas incorrectas.
- Impacto: Los contratos privados de Agenda deben exponer la version actual y las mutaciones deben enviar `version_esperada`. Los conflictos deben traducirse a errores controlados y el frontend debe refrescar datos sin reintentar automaticamente.

## DEC-035

- ID: DEC-035
- Titulo: Solapamientos informativos en Agenda
- Estado: Aprobada
- Decision: Agenda detecta solapamientos tecnicos entre intervalos, pero no aplica por si sola politicas bloqueantes. Las politicas de advertencia, bloqueo, capacidad y doble reserva pertenecen al modulo consumidor, especialmente Reservas, o a la aplicacion host.
- Motivo: Un solapamiento privado puede ser valido en Agenda, mientras que una reserva publica puede requerir reglas estrictas de capacidad y recurso. Mezclar ambas politicas acoplaria dominios distintos.
- Impacto: Los endpoints privados pueden informar solapamientos guardados sin convertirlos en error. Reservas debera revalidar disponibilidad dentro de transacciones propias antes de confirmar solicitudes.

## DEC-036

- ID: DEC-036
- Titulo: Respaldo, historial y ciclo de vida separados
- Estado: Aprobada
- Decision: FeedGo separa backup/restauracion fisica, historial funcional de cambios y ciclo de vida no destructivo. Agenda no debe copiar registros manualmente por operacion como sustituto de backup o auditoria.
- Motivo: Backup pertenece a infraestructura, historial funcional requiere justificacion de dominio y los estados no destructivos protegen el ciclo de vida operativo sin crear tablas prematuras.
- Impacto: Agenda debe contemplar restauracion de MySQL como responsabilidad de infraestructura, versionado/concurrencia para evitar perdida por edicion simultanea y estados como `archivado`, `cancelado` o `completado` cuando correspondan.

## DEC-037

- ID: DEC-037
- Titulo: Prompts del proyecto desde documentacion oficial completa
- Estado: Aprobada
- Decision: Todo Prompt Maestro, Prompt Universal, Prompt de Continuidad o prompt tecnico del proyecto debe mantenerse bajo el unico estandar documental definido por la gobernanza vigente, entregarse en Markdown puro e indicar la lectura completa de todos los documentos existentes dentro de `/docs`, respetando el orden logico definido por el Sistema de Gobierno, y luego `CHANGELOG.md` solo como historial cronologico. No debe enumerar manualmente archivos especificos de `/docs` como sustituto de esa lectura.
- Motivo: La documentacion oficial crece continuamente; las listas fijas se desactualizan y pueden convertir el prompt en una segunda fuente de verdad. El estandar debe ser portable y no depender de una IA, proveedor o herramienta especifica.
- Impacto: Futuros prompts deben mantenerse breves, copiables, trazables, reutilizables y compatibles con la evolucion documental y con futuras herramientas. `00_GOVERNANCE.md` gobierna el procedimiento y `06_CHAT_CONTINUATION.md` aplica la regla de continuidad.

## DEC-038

- ID: DEC-038
- Titulo: Sistema transversal de notificaciones desacoplado
- Estado: Aprobada
- Decision: Las notificaciones de FeedGo se disenaran como una capacidad transversal separada de Agenda, Reservas, autenticacion, planes comerciales, infraestructura de comunicaciones y proveedores externos. Agenda podra ser el primer productor de sucesos notificables, pero no sera duena del sistema. La notificacion local dentro de FeedGo sera el primer canal implementable, mediante campana global autenticada. Correo y WhatsApp quedan diferidos a una infraestructura transversal de comunicaciones externas, con proveedores reemplazables y contratos reutilizables.
- Motivo: Agenda y futuras Reservas necesitan notificaciones, pero acoplarlas a proveedores, verificaciones o una pantalla generaria duplicacion, riesgos de entrega y una frontera incorrecta para futuros canales, modulos y planes.
- Impacto: El cierre actual de ETAPA 88 no implementa notificaciones. La notificacion local queda como canal base futuro de FeedGo. Correo, WhatsApp, verificacion de destinos, plantillas, intentos de entrega, reintentos, webhooks e infraestructura asincronica pertenecen a una etapa futura de comunicaciones externas. Ningun modulo debe reimplementar proveedores ni verificacion por su cuenta. La futura monetizacion se resolvera mediante una politica externa de capacidades o feature access, no con condiciones rigidas dentro de notificaciones ni comunicaciones.

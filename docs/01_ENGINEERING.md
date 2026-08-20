# Engineering

Estado del documento: Documento Oficial del Sistema de Gobierno FeedGo v1.0.
Version: 1.0.
Categoria: Sistema de Gobierno.
Nivel de autoridad: Alto para reglas de ingenieria y arquitectura tecnica.
Documento dueno: `docs/01_ENGINEERING.md`.
Responsable funcional: Ingenieria.
Documentos relacionados: `00_GOVERNANCE.md`,
`08_ENGINEERING_PRINCIPLES.md`, `07_DECISIONS.md`,
`15_LEGAL_AND_OPERATIONAL.md`, `16_DATA_INTEGRITY_AND_RECOVERY.md`,
`18_PWA_ENTERPRISE.md`, `26_CLASSIFIEDS_CONTRACT.md`,
`27_COMMERCIAL_PLATFORM_CONTRACT.md`.
Cuando debe consultarse: antes de disenar, implementar, validar, refactorizar
o cerrar cambios tecnicos.

## Arquitectura por capas

Frontend
→ Services
→ Backend Routes
→ Backend Services
→ Models / DB

## Responsabilidades

Backend:

- dueño del negocio
- búsqueda
- ranking
- Discovery
- Candidate Engine
- Knowledge
- IA
- indexación
- validaciones
- performance

Frontend:

- UX
- interacción
- renderizado
- cache y experiencia PWA dentro de contratos aprobados

Nunca mover lógica de negocio al frontend.

## Reutilización

- reutilizar servicios existentes
- no duplicar lógica
- no crear implementaciones paralelas

## Compatibilidad PWA

FeedGo es una aplicacion multiplataforma y su primer canal oficial de
distribucion sera una PWA.

Toda nueva funcionalidad debe preservar, cuando corresponda:

- navegador de escritorio;
- navegador movil;
- aplicacion instalada PWA;
- navegacion standalone;
- actualizacion y recuperacion controladas;
- privacidad de cache, sesiones y datos locales.

Ningun cambio puede degradar la experiencia instalada sin una decision
arquitectonica explicita y documentada.

`18_PWA_ENTERPRISE.md` gobierna la arquitectura y validacion PWA.

## Gobierno del Modelo de Datos

Antes de crear una tabla nueva debe auditarse el modelo de datos existente.

La auditoria debe confirmar que:

- no existe una tabla propietaria natural del dato;
- extender una tabla o relacion existente no es mas correcto;
- la tabla nueva tendra responsabilidad unica;
- no se generara una segunda fuente de verdad;
- la decision es consistente con la arquitectura enterprise de FeedGo.

## Refactors

- prohibidos sin auditoría y aprobación
- no reorganizar carpetas innecesariamente

## Cache First

- mostrar cache inmediatamente
- refrescar en segundo plano
- evitar loaders innecesarios
- reutilizar queryKeys
- reutilizar prefetch
- mantener experiencia fluida

## Validaciones

- git status
- git diff
- compileall cuando corresponda
- build frontend cuando corresponda
- validaciones funcionales
- compatibilidad hacia atras de endpoints, servicios, tablas, contratos y pantallas existentes

## Calidad y seguridad progresivas

Cada etapa funcional debe incorporar tests, integracion, autorizacion,
validacion, controles de seguridad y regresion proporcionales a sus cambios.
Las etapas finales de Calidad y Seguridad consolidan evidencia, ejecutan
validaciones integrales y cierran brechas; no sustituyen la responsabilidad de
construir controles desde el owner original.

La matriz de riesgos y flujos criticos prevalece sobre un porcentaje aislado
de cobertura. Unitarias, contratos, integracion, frontend runtime, E2E,
compatibilidad y pruebas manuales se combinan segun el riesgo real; ninguna
categoria demuestra por si sola la calidad completa.

Dependencias, builds y herramientas deben poder ejecutarse de forma
reproducible y automatizable sin imponer una plataforma CI/CD concreta antes
de su auditoria. Secret scanning, SCA, inventario y SBOM se incorporan cuando
corresponda, evitando herramientas solapadas sin beneficio demostrado.

## Fuente unica de verdad

Cada dato debe tener un unico propietario.

Las tablas derivadas, caches, indices, embeddings, snapshots y eventos deben
ser tratadas como artefactos regenerables o historicos, nunca como fuente
oficial del dominio.

El dominio posee la decision y el estado oficial; el servicio de aplicacion
coordina el caso de uso; un provider ejecuta solamente el mecanismo externo.
Solo el owner escribe la fuente oficial. Los providers no activan capacidades,
no aplican permisos o ranking y no leen ni escriben libremente tablas FeedGo.

## Concurrencia y transacciones compuestas

Los dominios con edicion concurrente no deben usar la politica "ultima
escritura gana" cuando exista riesgo de sobrescritura silenciosa.

Toda mutacion concurrente de Agenda debe exigir una version esperada y rechazar
la operacion cuando la version persistida haya cambiado.

Los repositorios encapsulan ORM, consultas y `flush`.

Los servicios de nucleo aplican reglas de negocio y pueden participar en una
transaccion compuesta, pero no deben ocultar `commit` ni `rollback` cuando una
capa de integracion necesite combinar varias operaciones atomicas.

La capa orquestadora o de integracion controla `commit` y `rollback` cuando la
operacion involucra mas de un dominio.

## Respaldo, historial y ciclo de vida

El respaldo fisico y la restauracion de MySQL son responsabilidad de
infraestructura.

El historial funcional de cambios pertenece al dominio solo cuando exista una
necesidad funcional demostrada.

El ciclo de vida no destructivo de entidades del dominio se modela con estados
cuando alcanza para proteger la informacion.

Estas tres responsabilidades no deben mezclarse:

- backup y restauracion fisica;
- historial funcional o auditoria de cambios;
- estados no destructivos como `archivado`, `cancelado` o `completado`.

## Separación interna

Mantener separación entre Discovery, Candidate Engine, Ranking, Knowledge System e Indexador.

## Verticales y capacidades transversales

FeedGo Espacios y FeedGo Clasificados comparten identidad, autenticacion y
capacidades transversales correctas, pero no duplican ni fusionan forzadamente
sus dominios. Clasificados conserva modelos, lifecycle, Search, Candidate
Engine, Ranking, IndexDocument, exposicion y reglas comerciales propios cuando
el contrato lo requiera.

Una operacion que cree exposiciones en mas de un dominio debe ser orquestada
por backend. Publicacion, Clasificado, Historia de Espacio e Historia de
Clasificado conservan lifecycle independiente. La reutilizacion de media y
datos compatibles debe minimizar cargas repetidas sin convertir una superficie
en owner de otra ni introducir propagaciones implicitas desde frontend.

Advertising, Payments y Billing son capacidades transversales. Los dominios
producen operaciones o conceptos comerciales; backend conserva precios,
politicas, estados, permisos y activacion. Billing es unico para FeedGo y los
providers externos son adaptadores reemplazables sin acceso a la DB ni
ownership funcional.

## Modulos autonomos reutilizables

Cuando una capacidad tenga dominio propio y pueda evolucionar sin pertenecer a
una pantalla concreta, debe modelarse como modulo autonomo dentro del monorepo.

Esto no implica microservicio, libreria externa ni otro repositorio.

FeedGo es un monolito modular por defecto. Usuarios/Auth, Espacios,
Publicaciones, Historias, Clasificados, Availability, Agenda, Reservas,
Discovery, Candidate Engine, Ranking, Knowledge, promociones y entitlements
permanecen internos salvo evidencia futura suficiente. Un modulo no requiere
una DB propia.

La modularidad debe lograrse con limites internos claros:

- nucleo de dominio sin dependencias innecesarias de pantallas o navegacion;
- integracion con FeedGo mediante servicios, adaptadores o capas de entrada;
- frontend organizado por feature y componentes reutilizables;
- backend como propietario de reglas, validaciones, estados, permisos y
  persistencia.

Cuando exista una frontera real, la preparacion para evolucion futura puede
incluir services desacoplados del router, inputs y outputs explicitos, DTOs o
comandos utiles, idempotencia, efectos encapsulados, contratos versionables y
posibilidad de ejecutar jobs. No exige red ni deployment independiente.

Si un modulo se extrae fisicamente en el futuro, no podra usar como contrato
principal conectarse a la DB FeedGo para modificar tablas ajenas. Debera
integrarse mediante contratos controlados, como DTOs, comandos, APIs o eventos
solo cuando correspondan. No se introduce arquitectura event-driven por
anticipacion.

Providers reemplazables pueden cubrir embeddings, geocoding, pagos,
facturacion, correo, entrega WhatsApp, storage de assets, backup, restore,
observabilidad o IA especializada. Su existencia no implica microservicio. No
deben crearse abstracciones equivalentes en cada metodo interno sin una
dependencia reemplazable, efecto externo, frontera de seguridad, procesamiento
pesado o necesidad real de idempotencia o asincronia.

Para ETAPA 88, Agenda debe vivir como modulo propio:

- backend: `backend/app/modules/agenda/`;
- frontend: `frontend/src/features/agenda/`.

El nucleo de Agenda no debe depender de Profile, Spaces, Discovery, Search,
Ranking, Posts, Stories, Availability ni navegacion especifica de FeedGo. Esas
dependencias pertenecen a la capa de integracion.

## Validacion de schema y clasificacion de tablas

Cuando una etapa agrega o usa tablas nuevas, el cierre tecnico debe comparar
`Base.metadata` contra las tablas reales de MySQL.

No puede cerrarse una etapa con tablas usadas por runtime ausentes en la base
fisica.

La auditoria del modelo de datos debe clasificar cada tabla como:

- fuente de verdad;
- relacion;
- configuracion;
- indice;
- IA;
- evento;
- historica;
- cache;
- analitica.

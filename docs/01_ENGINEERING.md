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

Antes de Internet, los manifests backend y frontend deben permitir una
instalacion limpia reproducible sin depender del entorno de un desarrollador
(`SUPPLY-01`). La estrategia de pins/lock, SCA, secret scanning, SAST, SBOM o
su `N/A` justificado, y actualizacion/rollback pertenece a `SUPPLY-02`.

El artefacto productivo debe ser reproducible e inmutable, ejecutarse con
usuario no-root y permisos/filesystem minimos, excluir `.env`, secretos, dumps,
backups, historial Git y herramientas de desarrollo innecesarias, y exponer
health/readiness y shutdown controlado (`RUNTIME-01`). El repositorio completo
no es un artefacto de despliegue.

CI/CD no posee las reglas de negocio: aplica gates reproducibles sobre owners
existentes. Antes de deploy debe ejecutar tests, lint/build, scans aprobados,
validacion de migraciones, separacion de secretos/ambientes, identificacion del
artefacto y rollback probado (`CICD-01`). Los estados y criterios centrales de
estos findings viven en `15_LEGAL_AND_OPERATIONAL` 27.8.1 y 28.6.

### Baseline reproducible ET100.2

El baseline inicial aprobado por `DEC-068` es CPython x64 3.13.15, Node
24.21.0, npm 12.1.0 y `uv` 0.12.19. `backend/pyproject.toml` es el manifest
Python, `backend/uv.lock` su lock universal acotado a CPython 3.13 sobre Windows
x86-64 y Linux x86-64, y `frontend/package-lock.json` v3 es el lock frontend.
`uv` es tooling y no dependencia runtime. El backend separa runtime minimo,
grupo `test`, grupo `security` y extra opcional `embeddings`; el provider local
se conserva, pero `sentence-transformers` no pertenece al runtime minimo.

El runner canonico es `python tools/feedgo.py <comando>`; en Windows puede
invocarse mediante `tools/feedgo.ps1`. Instalacion backend: `uv sync --locked
--no-default-groups`; tests completos: `uv run --locked --group test --extra
embeddings python -m unittest discover -s tests`; frontend: `npm ci`, `npm run
lint` y `npm run build`. `.env.example` es solo contrato sanitizado: nunca se
reutilizan sus placeholders como secretos.

Una actualizacion requiere editar el manifest, regenerar el lock solamente
desde registries aprobados, revisar lifecycle scripts, ejecutar instalacion
limpia, SCA, tests/build y conservar el diff. El rollback consiste en restaurar
manifest y lock juntos al commit aprobado y repetir la instalacion limpia; no
se mezcla un manifest nuevo con un lock anterior.

Inventario host observado en ET100.2: Git 2.50.1, MySQL client/mysqldump 8.0.44,
Chrome 153, Edge 154 y browsers Playwright versionados por su package. Son
prerrequisitos de host, no dependencias Python/Node ni decisiones permanentes.
Los modelos de embeddings no se descargan durante la instalacion del extra y
permanecen artefactos opcionales externos al lock. Se observo en el host el
cache `sentence-transformers/all-MiniLM-L6-v2`, pero su revision y checksum aun
no estan gobernados; `MODEL-LOCK-001` exige fijarlos antes de habilitar el
provider local en staging aislado.

El contrato JWT HS256 usa PyJWT 2.15.1. `python-jose` y la dependencia
vulnerable `ecdsa` no pertenecen al manifest ni al lock; la autoridad de
sesion continua en `FeedGoSession`, con JWT versionado y SID obligatorio. El
frontend genera su SBOM production CycloneDX JSON 1.6 mediante
`@cyclonedx/cyclonedx-npm` 6.0.1 como dev-tool; `libxmljs2` queda explicitamente
denegado en `allowScripts` porque la salida JSON validada no requiere ejecutar
su lifecycle nativo. Los SBOM generados siguen siendo artefactos ignorados y
no fuente versionada.

### Toolchain y frontera MySQL de ET100.3

`DEC-069` conserva `tools/feedgo.py` como runner unico y elimina la dependencia
de una instalacion residual de `uv`. `tools/toolchain.json` fija version,
artefactos oficiales Windows/Linux x86-64 y SHA-256. La instalacion parte de un
archivo local obtenido explicitamente, verifica checksum antes de extraer y
genera un receipt con el hash del ejecutable. Toda resolucion posterior exige
receipt, hash y `uv --version` exactos. El runner no descarga herramientas y no
usa automaticamente un `uv` encontrado en PATH.

El prerequisito local de ET100.3 acepto expresamente que el instalador oficial
de CPython actualizara la instalacion registrada existente de 3.13.5 a 3.13.15
en su misma ubicacion; no se modificaron PATH, launcher o asociaciones ni se
realizaran reinstalaciones adicionales. Node 24.21.0 permanece side-by-side en
la cache ignorada del proyecto para no alterar Node global; su ZIP se verifica
contra `SHASUMS256.txt` oficial. npm 12.1.0 se instala solo dentro de ese arbol
desde `registry.npmjs.org`, con lifecycle deshabilitado y la integridad oficial
registrada en `tools/toolchain.json`.

Los comandos sinteticos usan exclusivamente `mitienda_stage100_test`. La
configuracion requiere tres usuarios distintos: materializador/validador con
`SELECT`, `INSERT`, `UPDATE`, `DELETE`; reset tecnico con `CREATE`, `DROP`,
`ALTER`, `INDEX`, `REFERENCES`; y observer read-only limitado por columna a las
vistas necesarias de Performance Schema. Las guardas comprueban driver
`mysql+pymysql`, host local, DB configurada y seleccionada, identidad efectiva
y conjunto exacto de grants. `USAGE` global sin privilegios es la unica
declaracion `*.*` admitida; cualquier permiso sobre `mitienda`, otro schema, un
rol, `ALL PRIVILEGES` o `GRANT OPTION` bloquea la operacion. El reset conserva
por separado la capacidad minima de `KILL QUERY`; el observer nunca recibe
`PROCESS`, `CONNECTION_ADMIN`, `SUPER` ni capacidad de cancelar conexiones.

La fundacion logica de ET100.3 es pura y no importa ORM ni abre conexiones. El
input obligatorio combina `dataset_version`, profile, seed y una politica de
reloj fija con anchor UTC; aliases y relaciones se validan antes de compilar.
Los UUID deterministas son opt-in por entidad y los IDs autoincrementales de DB
quedan fuera de identidad y fingerprint logicos. El fingerprint usa JSON
canonico y SHA-256 con version de contrato. Un valor criptografico aleatorio
solo puede excluir su material opaco mediante una categoria cerrada y sus
invariantes funcionales explicitas; cambios de algoritmo, costo, estado o dato
funcional siguen alterando el fingerprint. No existe ignore por nombre de
campo ni fallback al reloj real.

ET100.3 queda cerrada con un materializador de transaccion unica, reset tecnico
limitado al laboratorio y certificacion read-only. `smoke` contiene 20 filas,
`functional` 93 y `representative` 129; este ultimo permanece blueprint puro y
su materializacion pertenece al gate de ET100.4. El schema HEAD se reproduce
mediante un plan canonico de 39 tablas y 115 indices y todo DDL usa lifecycle
con timeout, killer/observer segregados, estado UNKNOWN fail-closed y cero
retry automatico.

Los medios se describen mediante recetas versionadas
`synthetic-media-recipe-v1`; nunca se leen ni copian uploads ordinarios. El
validador canonico certifica blueprint o materializacion MySQL con guards de
PII, secretos, rutas y sentencias read-only. ET100.4 debe consumir estos
contratos, materializar `representative` y resolver `MODEL-LOCK-001` antes de
habilitar embeddings locales. Hasta entonces el unico provider permitido es
`SimulatedEmbeddingProvider`.

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

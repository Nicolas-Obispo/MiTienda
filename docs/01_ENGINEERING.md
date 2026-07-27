# Engineering

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

Nunca mover lógica de negocio al frontend.

## Reutilización

- reutilizar servicios existentes
- no duplicar lógica
- no crear implementaciones paralelas

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

## Fuente unica de verdad

Cada dato debe tener un unico propietario.

Las tablas derivadas, caches, indices, embeddings, snapshots y eventos deben
ser tratadas como artefactos regenerables o historicos, nunca como fuente
oficial del dominio.

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

## Modulos autonomos reutilizables

Cuando una capacidad tenga dominio propio y pueda evolucionar sin pertenecer a
una pantalla concreta, debe modelarse como modulo autonomo dentro del monorepo.

Esto no implica microservicio, libreria externa ni otro repositorio.

La modularidad debe lograrse con limites internos claros:

- nucleo de dominio sin dependencias innecesarias de pantallas o navegacion;
- integracion con FeedGo mediante servicios, adaptadores o capas de entrada;
- frontend organizado por feature y componentes reutilizables;
- backend como propietario de reglas, validaciones, estados, permisos y
  persistencia.

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

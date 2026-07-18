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

## Separación interna

Mantener separación entre Discovery, Candidate Engine, Ranking, Knowledge System e Indexador.

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

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

## Separación interna

Mantener separación entre Discovery, Candidate Engine, Ranking, Knowledge System e Indexador.

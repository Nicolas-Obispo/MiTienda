# Reglas de gobierno del proyecto

- FeedGo se gobierna mediante documentos vivos.
- Estos documentos son la fuente oficial de verdad.
- La carpeta `/docs` constituye la memoria técnica oficial del proyecto.
- Si una instrucción o sugerencia contradice estos documentos, prevalecen los documentos.
- CHANGELOG.md registra el historial técnico y funcional de lo implementado.
- CHANGELOG.md no constituye la fuente de verdad del estado actual.
- CHANGELOG.md no reemplaza al Sistema de Gobierno.
- CHANGELOG.md no reemplaza el Roadmap.
- CHANGELOG.md no reemplaza la documentación técnica.
- PROJECT.md, NUEVOPROJECT.md, HISTORY.md y NUEVOHISTORY.md pasan a ser documentación histórica.
- Nunca utilizar esos documentos históricos como referencia principal.
- Toda decisión arquitectónica aprobada debe quedar registrada en `/docs` antes de continuar implementando.
- Los chats son herramientas de trabajo.
- La documentación oficial es la fuente de verdad.
- Si se inicia un nuevo chat, cualquier Prompt Maestro deberá construirse exclusivamente a partir de la documentación oficial del repositorio.
- El Prompt Maestro no deberá depender del historial del chat anterior.
- Cualquier conversación debe poder continuar exactamente donde terminó la anterior únicamente leyendo `/docs`.
- Cuando se incorpore un nuevo documento oficial al Sistema de Gobierno, deberán actualizarse también el orden de lectura, el procedimiento de continuidad, la generación de Prompt Maestro y cualquier referencia cruzada afectada.
- El Sistema de Gobierno debe permanecer siempre sincronizado.

Antes de cualquier auditoría o modificación, Codex debe seguir obligatoriamente el Procedimiento Universal de Reconstrucción del Proyecto definido por este documento.

## Sistema de Gobierno

El Sistema de Gobierno de FeedGo está compuesto por:

- `00_GOVERNANCE`
- `01_ENGINEERING`
- `02_PRODUCT`
- `03_SEARCH`
- `04_CURRENT_STAGE`
- `05_SEARCH_ROADMAP`
- `06_CHAT_CONTINUATION`
- `07_DECISIONS`
- `08_ENGINEERING_PRINCIPLES`

Los documentos `10+` son documentos técnicos especializados.

## Clasificación Oficial de Documentos

Todo documento nuevo incorporado al directorio `/docs` deberá declarar explícitamente su categoría.

Las categorías oficiales iniciales son:

### Sistema de Gobierno

Documentos que gobiernan el funcionamiento general del proyecto.

Ejemplos:

- Gobierno
- Ingeniería
- Producto
- Estado actual
- Roadmap
- Continuidad
- Decisiones
- Principios de Ingeniería

### Documento Técnico

Documentos que describen arquitectura, diseño o funcionamiento de componentes específicos.

Ejemplos:

- Index Design
- Knowledge Design
- futuros documentos del Indexador
- Discovery
- Candidate Engine
- Ranking

### Documento Operativo

Documentos que describan procesos operativos, despliegues, herramientas o mantenimiento.

### Documento Histórico

Documentos conservados únicamente como referencia histórica.

Reglas permanentes:

- Todo documento nuevo deberá indicar su categoría.
- Todo documento nuevo deberá indicar su objetivo.
- Todo documento nuevo deberá indicar si forma parte del Sistema de Gobierno.
- Todo documento técnico deberá indicar claramente qué componente documenta.
- La clasificación deberá mantenerse actualizada.

## Procedimiento Universal de Reconstrucción del Proyecto

Toda IA deberá seguir este procedimiento antes de realizar cualquier tarea de desarrollo.

La IA debe:

- descubrir automáticamente toda la documentación oficial;
- identificar la categoría de cada documento;
- determinar el orden de lectura según el propio Sistema de Gobierno;
- reconstruir completamente el estado del proyecto;
- identificar la etapa vigente;
- identificar el roadmap;
- identificar decisiones permanentes;
- identificar principios de ingeniería;
- identificar la documentación técnica necesaria para la tarea solicitada;
- verificar consistencia documental antes de continuar.

Este procedimiento es independiente de la estructura futura del repositorio.

Los prompts nunca reemplazan este procedimiento.

Cualquier evolución del procedimiento deberá realizarse modificando la documentación oficial.

## Flujo oficial de trabajo

El flujo oficial de trabajo de FeedGo es único y obligatorio:

1. Auditoría.
2. Evidencia.
3. Diseño.
4. Documentación.
5. Implementación.
6. Validación.
7. CHANGELOG.
8. Commit.
9. Push.

No debe existir ningún otro flujo alternativo.

CHANGELOG siempre ocurre antes del Commit.

## Reglas

- Nunca modificar código sin auditoría.
- Nunca hacer refactors masivos sin evidencia.
- Nunca romper arquitectura aprobada.
- Toda auditoría técnica debe considerar explícitamente aspectos de seguridad.
- Todo diseño arquitectónico debe considerar explícitamente aspectos de seguridad.
- La seguridad forma parte del proceso de diseño.
- La seguridad no constituye una etapa posterior.
- Backend dueño del negocio.
- Frontend solo UX.

ChatGPT define arquitectura, producto y estrategia junto al usuario.

Codex audita, inspecciona archivos y realiza cambios acotados respetando estos documentos.

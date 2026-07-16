# Reglas de gobierno del proyecto

- FeedGo se gobierna mediante documentos vivos.
- Estos documentos son la fuente oficial de verdad.
- La carpeta `/docs` constituye la memoria técnica oficial del proyecto.
- Si una instrucción o sugerencia contradice estos documentos, prevalecen los documentos.
- CHANGELOG.md continúa siendo únicamente el historial ejecutivo.
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

Antes de cualquier auditoría o modificación, Codex debe leer obligatoriamente:

1. `/docs/00_GOVERNANCE.md`
2. `/docs/01_ENGINEERING.md`
3. `/docs/02_PRODUCT.md`
4. `/docs/03_SEARCH.md`
5. `/docs/04_CURRENT_STAGE.md`
6. `/docs/05_SEARCH_ROADMAP.md`
7. `/docs/06_CHAT_CONTINUATION.md`
8. `/docs/07_DECISIONS.md`
9. `/docs/08_ENGINEERING_PRINCIPLES.md`

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

## Proceso obligatorio

1. Auditar.
2. Mostrar evidencia.
3. Analizar.
4. Diseñar.
5. Aprobar.
6. Implementar.
7. Validar.
8. Commit.
9. CHANGELOG.
10. Push.

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

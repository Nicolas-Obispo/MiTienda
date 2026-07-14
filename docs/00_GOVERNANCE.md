# Reglas de gobierno del proyecto

- FeedGo se gobierna mediante documentos vivos.
- Estos documentos son la fuente oficial de verdad.
- Si una instrucción o sugerencia contradice estos documentos, prevalecen los documentos.
- CHANGELOG.md continúa siendo únicamente el historial ejecutivo.
- PROJECT.md, NUEVOPROJECT.md, HISTORY.md y NUEVOHISTORY.md pasan a ser documentación histórica.
- Nunca utilizar esos documentos históricos como referencia principal.

Antes de cualquier auditoría o modificación, Codex debe leer obligatoriamente:

1. `/docs/00_GOVERNANCE.md`
2. `/docs/01_ENGINEERING.md`
3. `/docs/02_PRODUCT.md`
4. `/docs/03_SEARCH.md`
5. `/docs/04_CURRENT_STAGE.md`

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
- Backend dueño del negocio.
- Frontend solo UX.

ChatGPT define arquitectura, producto y estrategia junto al usuario.

Codex audita, inspecciona archivos y realiza cambios acotados respetando estos documentos.

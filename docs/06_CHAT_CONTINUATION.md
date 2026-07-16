# Continuidad de Conversaciones

## 1. Objetivo

Este documento existe para garantizar la continuidad del proyecto entre conversaciones con IA.

El objetivo es que FeedGo nunca dependa del historial de un chat.

Toda conversación debe poder reconstruir el estado del proyecto desde la documentación oficial del repositorio.

## 2. Regla permanente

Antes de responder cualquier consulta sobre FeedGo, la IA debe leer obligatoriamente:

1. `/docs/00_GOVERNANCE.md`
2. `/docs/01_ENGINEERING.md`
3. `/docs/02_PRODUCT.md`
4. `/docs/03_SEARCH.md`
5. `/docs/04_CURRENT_STAGE.md`
6. `/docs/05_SEARCH_ROADMAP.md`
7. `/docs/06_CHAT_CONTINUATION.md`
8. `/docs/07_DECISIONS.md`
9. `/docs/08_ENGINEERING_PRINCIPLES.md`

Luego, cuando corresponda, debe leer:

- `/docs/10_INDEX_DESIGN.md`
- `/docs/11_KNOWLEDGE_DESIGN.md`
- cualquier otro documento técnico relacionado con la tarea solicitada

## 3. Fuente oficial de verdad

El historial del chat no constituye la fuente principal del proyecto.

La documentación oficial del repositorio prevalece siempre.

Si existe una contradicción entre una conversación y la documentación, prevalece la documentación.

## 4. Construcción del Prompt Maestro

Cuando el usuario solicite un Prompt Maestro para continuar el proyecto, la IA deberá construirlo exclusivamente utilizando la documentación oficial.

Todo Prompt Maestro deberá construirse leyendo primero:

1. `/docs/00_GOVERNANCE.md`
2. `/docs/01_ENGINEERING.md`
3. `/docs/02_PRODUCT.md`
4. `/docs/03_SEARCH.md`
5. `/docs/04_CURRENT_STAGE.md`
6. `/docs/05_SEARCH_ROADMAP.md`
7. `/docs/06_CHAT_CONTINUATION.md`
8. `/docs/07_DECISIONS.md`
9. `/docs/08_ENGINEERING_PRINCIPLES.md`

Luego deberá leer automáticamente toda la documentación técnica relacionada con la etapa o tarea solicitada.

Para el Buscador, deberá incluir:

- `/docs/10_INDEX_DESIGN.md`
- `/docs/11_KNOWLEDGE_DESIGN.md`

Para el Indexador, deberá incluir todos los documentos de diseño del Indexador cuando existan.

Nunca generar un Prompt Maestro únicamente con documentos de gobierno.

Siempre incorporar también la documentación técnica vigente.

El Prompt Maestro deberá incluir como mínimo:

- estado actual del proyecto
- etapa actual
- etapas completadas
- objetivos pendientes
- arquitectura vigente
- reglas de gobierno
- restricciones permanentes
- próximos pasos del roadmap
- responsabilidades de los módulos involucrados

El Prompt Maestro no deberá depender del historial conversacional.

## 5. Inicio de un nuevo chat

Toda conversación nueva debería comenzar:

1. leyendo la documentación oficial;
2. reconstruyendo el contexto desde `/docs`;
3. identificando la etapa actual;
4. continuando exactamente donde quedó el proyecto.

Nunca reinterpretar arquitectura ya aprobada.

Nunca volver a auditar decisiones oficialmente cerradas salvo solicitud explícita del usuario.

## 6. Memoria del proyecto

La memoria del proyecto vive en el repositorio.

No vive en la memoria del modelo.

No vive en el historial del chat.

Los chats son herramientas temporales.

La documentación oficial constituye la memoria permanente del proyecto.

## 7. Evolución de la documentación

Cada vez que:

- se apruebe una decisión arquitectónica;
- cambie el roadmap;
- se implemente una funcionalidad importante;
- cambie una regla permanente;

deberá actualizarse la documentación correspondiente antes de continuar implementando.

## 8. Responsabilidad de la IA

La IA debe:

- respetar la arquitectura vigente;
- respetar la documentación oficial;
- evitar rediseños innecesarios;
- reutilizar componentes existentes;
- mantener coherencia entre documentos, roadmap, changelog y código.

## 9. Principio final

> La documentación oficial no describe el proyecto.
>
> La documentación oficial gobierna el proyecto.
>
> El código implementa las decisiones documentadas.
>
> Los chats únicamente ayudan a construir esas decisiones.

# Continuidad de Conversaciones

## 1. Objetivo

Este documento existe para garantizar la continuidad del proyecto entre conversaciones con IA.

El objetivo es que FeedGo nunca dependa del historial de un chat.

Toda conversación debe poder reconstruir el estado del proyecto desde la documentación oficial del repositorio.

## 2. Regla permanente

Antes de responder cualquier consulta sobre FeedGo, la IA debe seguir el Procedimiento Universal de Reconstrucción del Proyecto definido por el Sistema de Gobierno.

El procedimiento oficial indica cómo:

- descubrir la documentación oficial;
- identificar categorías;
- definir el orden de lectura;
- reconstruir el estado del proyecto;
- identificar la documentación técnica relevante para la tarea solicitada.

Ningún chat nuevo debe depender de listas fijas de documentos ni de nombres concretos de archivos.

## 3. Fuente oficial de verdad

El historial del chat no constituye la fuente principal del proyecto.

La documentación oficial del repositorio prevalece siempre.

Si existe una contradicción entre una conversación y la documentación, prevalece la documentación.

## 4. Construcción del Prompt Maestro

Cuando el usuario solicite un Prompt Maestro para continuar el proyecto, la IA deberá construirlo exclusivamente utilizando la documentación oficial.

Todo Prompt Maestro deberá construirse siguiendo el Procedimiento Universal de Reconstrucción del Proyecto.

El Prompt Maestro es una instrucción operativa de arranque.

El Prompt Maestro guía el inicio del trabajo, pero no define arquitectura, roadmap ni estado detallado del proyecto.

El Prompt Maestro nunca reemplaza la lectura directa de la documentación oficial.

Toda implementación debe volver a consultar la documentación vigente antes de modificar el sistema.

El Prompt Maestro deberá derivarse de:

- el Sistema de Gobierno descubierto por categoría;
- el estado vigente del proyecto;
- el roadmap vigente;
- las decisiones permanentes;
- los principios de ingeniería;
- la documentación técnica relacionada con la tarea solicitada.

Nunca generar un Prompt Maestro únicamente con documentos de gobierno.

Siempre incorporar también la documentación técnica vigente.

El Prompt Maestro debe ser breve.

Extensión recomendada:

- entre 40 y 80 líneas.

El Prompt Maestro deberá incluir únicamente:

- procedimiento de reconstrucción;
- prevalencia de `/docs`;
- tarea inicial;
- restricciones operativas;
- obligación de reportar contradicciones.

El Prompt Maestro no debe:

- definir arquitectura;
- definir roadmap;
- definir el estado detallado del proyecto;
- copiar decisiones permanentes;
- resumir extensamente etapas cerradas;
- duplicar documentación oficial.

El Prompt Maestro no deberá depender del historial conversacional.

`04_CURRENT_STAGE` define la etapa vigente.

`05_SEARCH_ROADMAP` define la posición y secuencia de la etapa.

Cualquier contradicción entre un prompt y la documentación oficial se resuelve a favor de `/docs`.

## 5. Inicio de un nuevo chat

Toda conversación nueva debería comenzar:

1. siguiendo el Procedimiento Universal de Reconstrucción del Proyecto;
2. reconstruyendo el contexto desde la documentación oficial;
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

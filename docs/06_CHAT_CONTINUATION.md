# Continuidad de Conversaciones

Estado del documento: Documento Oficial del Sistema de Gobierno FeedGo v1.0.
Version: 1.0.
Categoria: Sistema de Gobierno.
Nivel de autoridad: Alto para continuidad entre conversaciones y generacion de
prompts de arranque.
Documento dueno: `docs/06_CHAT_CONTINUATION.md`.
Responsable funcional: Continuidad documental.
Documentos relacionados: `00_GOVERNANCE.md`, `04_CURRENT_STAGE.md`,
`05_SEARCH_ROADMAP.md`, `07_DECISIONS.md`,
`08_ENGINEERING_PRINCIPLES.md`, `15_LEGAL_AND_OPERATIONAL.md`,
`16_DATA_INTEGRITY_AND_RECOVERY.md`,
`17_OBSERVABILITY_AND_OPERATIONS.md`.
Cuando debe consultarse: antes de generar prompts de continuidad, iniciar
trabajo desde un nuevo chat o decidir entre bootstrap completo, continuidad
controlada y relectura selectiva.

## 1. Objetivo

Este documento existe para garantizar la continuidad del proyecto entre conversaciones con IA.

El objetivo es que FeedGo nunca dependa del historial de un chat.

Toda conversación debe poder reconstruir el estado del proyecto desde la documentación oficial del repositorio.

## 2. Aplicación de la política de continuidad

`00_GOVERNANCE.md` es el único documento dueño de la política de continuidad
documental. Este documento explica su aplicación operativa y no crea una
definición paralela.

La documentación oficial es autoridad permanente. El contexto de una sesión
es únicamente memoria de trabajo temporal y nunca sustituye, completa ni
prevalece sobre `/docs`.

Al iniciar una nueva sesión, un nuevo chat o una nueva etapa debe ejecutarse el
bootstrap documental completo definido por Gobierno.

Dentro de la misma sesión y etapa puede aplicarse continuidad controlada si el
contexto oficial ya fue reconstruido, la documentación relevante no cambió,
no existe contradicción y la tarea no incorpora un dominio documental todavía
no verificado.

Si cambia documentación durante la etapa o la tarea ingresa en un nuevo
dominio, corresponde releer selectivamente el documento propietario y sus
dependencias directas. Si el alcance no puede determinarse con seguridad,
corresponde volver al bootstrap completo.

Antes de una auditoría, diseño, propuesta o implementación siempre deben estar
verificados los documentos propietarios del tema. La continuidad controlada no
permite decidir desde memoria una regla documental concreta.

Los prompts de continuidad no deben enumerar manualmente archivos específicos
de `/docs` como sustituto del procedimiento oficial.

## 3. Fuente oficial de verdad

El historial del chat no constituye la fuente principal del proyecto.

La documentación oficial del repositorio prevalece siempre.

Si existe una contradicción entre una conversación y la documentación, prevalece la documentación.

## 4. Construcción del Prompt Maestro

Cuando el usuario solicite un Prompt Maestro para continuar el proyecto, la IA deberá construirlo exclusivamente utilizando la documentación oficial.

Todo Prompt Maestro deberá construirse siguiendo el Procedimiento Universal de
Reconstrucción del Proyecto y provocar un bootstrap documental completo.

Los Prompt Maestro, Prompt Universal, Prompt de Continuidad y prompts técnicos del proyecto deberán mantenerse bajo el único estándar documental definido por la gobernanza vigente.

Todo Prompt Maestro deberá entregarse en Markdown puro, sin explicaciones externas al contenido copiable, para garantizar reutilización, trazabilidad, portabilidad y compatibilidad con futuras herramientas.

El Prompt Maestro es una instrucción operativa de arranque.

El Prompt Maestro guía el inicio del trabajo, pero no define arquitectura, roadmap ni estado detallado del proyecto.

El Prompt Maestro nunca reemplaza la lectura directa de la documentación oficial.

Toda implementación debe verificar la documentación propietaria vigente antes
de modificar el sistema, mediante bootstrap completo o relectura selectiva
según la política de Gobierno.

El Prompt Maestro deberá derivarse de:

- el Sistema de Gobierno descubierto por categoría;
- el estado vigente del proyecto;
- el roadmap vigente;
- las decisiones permanentes;
- los principios de ingeniería;
- el gobierno legal y operativo vigente;
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

Cuando la tarea involucre datos personales, permisos, geolocalizacion,
contenido publico, moderacion, mensajeria, reservas, productos, pagos,
notificaciones, IA, backups, seguridad, proveedores externos u operacion en
produccion, el Prompt Maestro debe recordar que la implementacion debera
consultar tambien el documento legal y operativo vigente.

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

## 6. Continuaciones dentro de una sesión y etapa

Los prompts sucesivos pueden indicar que continúa la misma sesión y etapa y
solicitar la aplicación de la política vigente de continuidad documental.

No necesitan repetir íntegramente la regla ni exigir automáticamente otra
lectura completa si siguen cumpliéndose las condiciones oficiales.

La instrucción del prompt no acredita por sí misma que el contexto sea válido.
Si existe incertidumbre, contradicción, cambio documental no acotable o un
nuevo dominio no verificado, debe consultarse la documentación según Gobierno.

## 7. Memoria del proyecto

La memoria del proyecto vive en el repositorio.

No vive en la memoria del modelo.

No vive en el historial del chat.

Los chats son herramientas temporales.

La documentación oficial constituye la memoria permanente del proyecto.

## 8. Evolución de la documentación

Cada vez que:

- se apruebe una decisión arquitectónica;
- cambie el roadmap;
- se implemente una funcionalidad importante;
- cambie una regla permanente;

deberá actualizarse la documentación correspondiente antes de continuar implementando.

## 9. Responsabilidad de la IA

La IA debe:

- respetar la arquitectura vigente;
- respetar la documentación oficial;
- evitar rediseños innecesarios;
- reutilizar componentes existentes;
- mantener coherencia entre documentos, roadmap, changelog y código.

## 10. Principio final

> La documentación oficial no describe el proyecto.
>
> La documentación oficial gobierna el proyecto.
>
> El código implementa las decisiones documentadas.
>
> Los chats únicamente ayudan a construir esas decisiones.

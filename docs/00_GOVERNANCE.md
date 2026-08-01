# Reglas de gobierno del proyecto

Estado del documento: Documento Oficial del Sistema de Gobierno FeedGo v1.0.
Version: 1.0.
Categoria: Sistema de Gobierno.
Nivel de autoridad: Maximo dentro de la documentacion del proyecto.
Documento dueno: `docs/00_GOVERNANCE.md`.
Responsable funcional: Gobierno documental.
Documentos relacionados: `01_ENGINEERING.md`, `02_PRODUCT.md`,
`03_SEARCH.md`, `04_CURRENT_STAGE.md`, `05_SEARCH_ROADMAP.md`,
`06_CHAT_CONTINUATION.md`, `07_DECISIONS.md`,
`08_ENGINEERING_PRINCIPLES.md`, `15_LEGAL_AND_OPERATIONAL.md`,
`16_DATA_INTEGRITY_AND_RECOVERY.md`.
Cuando debe consultarse: antes de cualquier auditoria, diseno, propuesta,
prompt, implementacion, validacion, cierre de etapa o cambio documental.

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
- El Prompt Maestro es una instrucción operativa de arranque.
- El Prompt Maestro debe ser breve y no debe duplicar la documentación oficial.
- El Prompt Maestro no define arquitectura, roadmap ni estado detallado del proyecto.
- Cualquier conversación debe poder continuar exactamente donde terminó la anterior únicamente leyendo `/docs`.
- Cuando se incorpore un nuevo documento oficial al Sistema de Gobierno, deberán actualizarse también el orden de lectura, el procedimiento de continuidad, la generación de Prompt Maestro y cualquier referencia cruzada afectada.
- El Sistema de Gobierno debe permanecer siempre sincronizado.

El Sistema de Gobierno gobierna decisiones permanentes del proyecto.

No es documentacion historica.

Las decisiones permanentes se incorporan primero al Sistema de Gobierno y luego
se implementan.

Antes de cualquier auditoría, diseño o modificación, toda IA asistente del proyecto debe seguir obligatoriamente el Procedimiento Universal de Reconstrucción del Proyecto definido por este documento.

La lectura obligatoria antes de actuar es la lectura completa de todos los documentos existentes dentro de `/docs`.

La lectura debe respetar el orden lógico definido por el propio Sistema de Gobierno:

- primero documentos de gobierno;
- luego decisiones y principios;
- luego documentos técnicos, diseños y documentos `10+` aplicables.

Después de reconstruir `/docs`, debe leerse `CHANGELOG.md` únicamente como historial cronológico.

La carpeta `/docs` siempre prevalece sobre la memoria del modelo, prompts anteriores y el historial conversacional.

Ningún Prompt Maestro, Prompt Universal, Prompt de Continuidad o prompt técnico del proyecto debe enumerar manualmente archivos específicos de `/docs` como sustituto de este procedimiento, porque la documentación crece y una lista fija puede quedar desactualizada.

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
- `15_LEGAL_AND_OPERATIONAL`
- `16_DATA_INTEGRITY_AND_RECOVERY`

Los documentos `10+` pueden ser documentos tecnicos especializados o
documentos transversales incorporados explicitamente al Sistema de Gobierno.

## Arbol de Autoridad del Sistema Documental

La jerarquia documental oficial es:

1. Normativa vigente aplicable.
2. `00_GOVERNANCE`.
3. Documentos del Sistema de Gobierno:
   - `01_ENGINEERING`;
   - `02_PRODUCT`;
   - `03_SEARCH`;
   - `04_CURRENT_STAGE`;
   - `05_SEARCH_ROADMAP`;
   - `06_CHAT_CONTINUATION`;
   - `07_DECISIONS`;
   - `08_ENGINEERING_PRINCIPLES`;
   - `15_LEGAL_AND_OPERATIONAL`;
   - `16_DATA_INTEGRITY_AND_RECOVERY`.
4. Decisiones permanentes registradas en `07_DECISIONS`.
5. Documentos tecnicos especializados.
6. CHANGELOG como historial cronologico.
7. Prompts, conversaciones y memoria de asistentes.

Reglas:

- `04_CURRENT_STAGE` define la etapa vigente.
- `05_SEARCH_ROADMAP` define la secuencia oficial de etapas.
- `07_DECISIONS` registra decisiones permanentes aprobadas.
- `15_LEGAL_AND_OPERATIONAL` gobierna riesgos legales, privacidad,
  compliance, seguridad operativa y lanzamiento.
- `16_DATA_INTEGRITY_AND_RECOVERY` gobierna integridad fisica de datos,
  backup, restore, recuperacion y validacion de schema.
- Los documentos tecnicos gobiernan su componente especifico siempre que no
  contradigan documentos de mayor jerarquia.
- CHANGELOG no define estado vigente ni alcance futuro.

## Gobierno por Consulta Obligatoria

Antes de emitir opiniones tecnicas, realizar auditorias, disenar
funcionalidades, generar prompts o implementar cambios, deberan consultarse los
documentos oficiales aplicables del Sistema de Gobierno.

Los documentos oficiales prevalecen sobre:

- memoria del asistente;
- conversaciones anteriores;
- prompts reutilizados;
- recomendaciones genericas;
- buenas practicas externas;
- decisiones no documentadas.

Si un tema no esta documentado podra proponerse una nueva decision, pero
unicamente despues de verificar que no contradice el Sistema de Gobierno.

## Fuente unica documental

Cada decision permanente debera tener un unico documento propietario.

Los demas documentos deberan referenciar esa fuente.

No deben:

- copiarla;
- reinterpretarla;
- mantener versiones paralelas;
- convertir una referencia en una segunda fuente de verdad.

## Estabilidad documental

El Sistema de Gobierno debe evolucionar lentamente.

No debe modificarse por mejoras menores.

Solo debera actualizarse cuando exista una decision permanente de:

- arquitectura;
- ingenieria;
- producto;
- gobierno;
- cumplimiento;
- operacion.

Las correcciones documentales menores deben limitarse a consistencia,
referencias cruzadas, estado, version o errores comprobados.

## Indice de consulta

Antes de trabajar sobre un dominio debe identificarse el documento dueno y los
documentos relacionados que lo gobiernan.

La cabecera de cada documento indica cuando debe consultarse.

Si el dominio no tiene documento dueno, debe proponerse una decision o
documentacion nueva solo despues de verificar que no contradice el Sistema de
Gobierno.

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

### Documento Legal y Operativo

Documento transversal del Sistema de Gobierno que define criterios obligatorios
de producto, ingeniería y operación antes de modificar funciones relacionadas
con datos personales, permisos, geolocalización, contenido público,
moderación, mensajería, reservas, productos, pagos, notificaciones, IA,
backups, seguridad, proveedores externos u operación en producción.

No reemplaza revisión profesional legal ni redacta contratos definitivos.

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

## Evolución controlada del Roadmap

El Sistema de Gobierno representa el estado oficial vigente del proyecto y debe respetarse en todo momento.

Sin embargo, tanto el Sistema de Gobierno como el Roadmap representan la mejor planificación conocida al momento de su aprobación.

Su propósito es guiar la evolución del proyecto, no limitarla cuando la evidencia demuestra un camino arquitectónicamente superior.

Cuando una auditoría, la evidencia técnica o el diseño conceptual demuestren que la planificación vigente debe evolucionar para preservar una arquitectura más correcta, simple, consistente, escalable o preparada para capacidades futuras, el procedimiento correcto no será ignorar el Sistema de Gobierno ni modificar informalmente el roadmap.

El procedimiento correcto será:

1. reunir evidencia;
2. evaluar la necesidad del cambio;
3. confirmar, mediante la auditoría, la evidencia y el análisis arquitectónico, que mantener la planificación vigente resulta arquitectónicamente inferior a la propuesta de evolución;
4. formalizar la decisión arquitectónica;
5. actualizar formalmente la documentación oficial;
6. continuar el proyecto utilizando la nueva documentación como única fuente oficial de verdad.

Esta evolución podrá incluir, entre otros casos:

- incorporar una etapa intermedia;
- subdividir una etapa existente;
- modificar el orden originalmente previsto;
- desplazar capacidades hacia etapas posteriores;
- anticipar dependencias técnicas necesarias.

Este principio:

- no modifica el flujo oficial de trabajo;
- no constituye una excepción permanente al roadmap;
- no habilita cambios arbitrarios;
- exige evidencia suficiente y documentación oficial antes de continuar con el desarrollo.

La evolución del roadmap constituye una actualización del estado oficial del proyecto y reemplaza la planificación anterior.

A partir de ese momento, toda auditoría, diseño, implementación y documentación deberá tomar como referencia exclusivamente la nueva versión oficial.

## Regla del Prompt Maestro

El Prompt Maestro obliga a reconstruir el contexto desde `/docs`.

Todo Prompt Maestro, Prompt Universal, Prompt de Continuidad o prompt técnico del proyecto deberá mantenerse bajo el único estándar documental definido por la gobernanza vigente.

Todo prompt destinado a una IA asistente del proyecto deberá entregarse en Markdown puro, sin explicaciones externas al contenido copiable, para garantizar reutilización, trazabilidad, portabilidad y compatibilidad con futuras herramientas.

Todo prompt destinado a una IA asistente del proyecto deberá indicar la lectura completa de todos los documentos existentes dentro de `/docs`, respetando el orden lógico definido por el Sistema de Gobierno, y la lectura posterior de `CHANGELOG.md` únicamente como historial cronológico.

Todo prompt destinado a una IA asistente del proyecto deberá mantenerse compatible con la evolución futura de `/docs` y no deberá enumerar manualmente archivos específicos como reemplazo de la lectura completa.

El Prompt Maestro no reemplaza ningún documento oficial.

El Prompt Maestro no debe:

- definir arquitectura;
- definir roadmap;
- definir el estado detallado del proyecto;
- copiar decisiones permanentes;
- resumir extensamente etapas cerradas;
- duplicar documentación oficial.

Debe contener únicamente:

- procedimiento de reconstrucción;
- prevalencia de `/docs`;
- tarea inicial;
- restricciones operativas;
- obligación de reportar contradicciones.

Extensión recomendada:

- entre 40 y 80 líneas.

`04_CURRENT_STAGE` define la etapa vigente.

`05_SEARCH_ROADMAP` define la posición y secuencia de la etapa.

Cualquier contradicción entre un prompt y la documentación oficial se resuelve a favor de `/docs`.

## Flujo oficial de trabajo

El flujo oficial de trabajo de FeedGo es único y obligatorio:

1. Idea.
2. Auditoría.
3. Evidencia.
4. Diseño.
5. Actualización documental.
6. Implementación.
7. Validación.
8. CHANGELOG.
9. Commit.
10. Push.

No debe existir ningún otro flujo alternativo.

CHANGELOG siempre ocurre antes del Commit.

## Reglas

- Nunca modificar código sin auditoría.
- Nunca hacer refactors masivos sin evidencia.
- Nunca romper arquitectura aprobada.
- Nunca crear una tabla nueva sin auditoria previa del modelo de datos.
- Nunca cerrar una etapa sin validar compatibilidad hacia atras.
- Nunca cerrar una etapa con diferencias entre `Base.metadata` y las tablas fisicas usadas por runtime.
- Toda auditoría técnica debe considerar explícitamente aspectos de seguridad.
- Todo diseño arquitectónico debe considerar explícitamente aspectos de seguridad.
- La seguridad forma parte del proceso de diseño.
- La seguridad no constituye una etapa posterior.
- Backend dueño del negocio.
- Frontend solo UX.

La IA utilizada para definición estratégica acompaña al usuario en arquitectura, producto y estrategia.

La IA utilizada para ejecución técnica audita, inspecciona archivos y realiza cambios acotados respetando estos documentos.

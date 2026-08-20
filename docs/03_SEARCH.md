# Search

Estado del documento: Documento Oficial del Sistema de Gobierno FeedGo v1.0.
Version: 1.0.
Categoria: Sistema de Gobierno.
Nivel de autoridad: Alto para busqueda, Discovery, Candidate Engine, Ranking,
Knowledge, Indexador y runtime de busqueda.
Documento dueno: `docs/03_SEARCH.md`.
Responsable funcional: Busqueda y descubrimiento.
Documentos relacionados: `00_GOVERNANCE.md`, `10_INDEX_DESIGN.md`,
`11_KNOWLEDGE_DESIGN.md`, `07_DECISIONS.md`,
`08_ENGINEERING_PRINCIPLES.md`, `26_CLASSIFIEDS_CONTRACT.md`.
Cuando debe consultarse: antes de modificar busqueda, descubrimiento,
indexacion, ranking, taxonomia, conocimiento, senales o recomendaciones.

## Objetivo

- El buscador conecta necesidades con soluciones.
- Debe interpretar intención, no solamente palabras.
- Debe ser escalable y evolucionar sin rediseñar la arquitectura.

## Principio fundamental

- Toda la inteligencia pesada ocurre durante la indexación.
- El runtime de búsqueda debe ser lo más liviano posible.

## Pipeline de Escritura

Comercio / Publicación

↓

Knowledge System

↓

Indexador

↓

Documento de Índice

↓

Índices Sintetizados

↓

Persistencia

## Pipeline de Lectura

Usuario

↓

Discovery

↓

Candidate Engine

↓

Ranking

↓

Respuesta

## Responsabilidades

Discovery

- interpreta lenguaje natural
- identifica intención
- transforma consultas en conceptos

Knowledge System

- administra conocimiento
- relaciones
- taxonomía
- sinónimos
- conceptos

Indexador

- analiza entidades
- genera Documentos de Índice
- mantiene conocimiento actualizado

Documento de Índice

- representa una entidad indexable
- no es una copia de la base de datos
- representa conocimiento enriquecido
- mantiene identidad y cobertura

Índices Sintetizados

- derivados optimizados para búsqueda
- no generan conocimiento
- reutilizan conocimiento previamente preparado

Candidate Engine

- genera candidatos relevantes

Ranking

- ordena candidatos
- no genera conocimiento

## Principios

- Discovery interpreta.
- El índice responde.
- Candidate Engine selecciona.
- Ranking ordena.
- El runtime nunca crea conocimiento nuevo.
- El runtime nunca construye conocimiento.
- El runtime únicamente consume conocimiento previamente preparado.
- Todo conocimiento pesado se construye durante la indexación.
- El Indexador prepara.

## Disponibilidad en búsqueda

Durante ETAPA 87, el estado horario es únicamente información contextual para el usuario.

Durante ETAPA 87, el estado horario no participa en filtros, ranking ni exclusión de resultados.

Esta decisión no constituye una restricción permanente del buscador.

Una etapa futura podrá incorporar búsquedas específicas relacionadas con horarios sin contradecir esta decisión.

Un espacio `Activo` puede aparecer en búsqueda aunque esté `Cerrado` por horario.

Un espacio `En pausa` no debe aparecer públicamente, independientemente de los horarios que tenga guardados.

La búsqueda podrá mostrar información horaria como dato informativo:

- `Abierto`;
- `Cerrado`;
- `No hay horarios declarados`.

La regla de cálculo del estado horario pertenece al backend y al Sistema de Disponibilidad.

## Agenda y Reservas en busqueda

Durante ETAPA 88, Agenda y Reservas no participan en filtros, ranking ni
exclusion de resultados.

El buscador no debe depender de la agenda privada del propietario.

Una etapa futura podra incorporar busquedas contextuales relacionadas con
turnos, reservas o disponibilidad reservable solo si existe una decision
arquitectonica aprobada y documentada.

Un espacio debe seguir pudiendo aparecer en busqueda aunque no tenga reservas
publicas habilitadas.

## Universos de Espacios y Clasificados

Explorar busca Espacios y Clasificados busca Clasificados. Ambos universos no
deben mezclarse silenciosamente; pueden existir sugerencias cruzadas claramente
identificadas cuando sean pertinentes.

Clasificados requiere `ClassifiedIndexDocument`, collectors, Candidate Engine
y Ranking propios cuando los contratos de `CommerceIndexDocument` no apliquen.
Puede reutilizar primitives de Taxonomia, Knowledge, normalizacion, geografia e
indexacion sin heredar ownership o restricciones de Espacios.

El inventario publico de Clasificados es globalmente elegible. Ubicacion y
distancia pueden ser dato, filtro, orden o senal, pero el scope territorial de
Espacios no limita por defecto los candidatos de Clasificados.

En ambos universos rige ausencia antes que irrelevancia. Una promocion solo
puede ordenar o destacar candidatos ya pertinentes; nunca vuelve relevante un
resultado que no lo es.

## Fronteras tecnicas y evolucion

Search, Candidate Engine y Ranking permanecen bajo ownership de cada vertical.
No se crea un Search Service generico que absorba sus reglas. El Indexador es
una capacidad tecnica controlada y los embeddings, indices sintetizados y
documentos de indice son artefactos derivados reconstruibles.

La frontera preparada para posible evolucion se concentra en construccion
masiva, reindexacion, embeddings, persistencia o consulta pesada y ejecucion
asincronica. El motor de persistencia/consulta puede incorporarse mediante un
contrato reemplazable sin adquirir ownership de relevancia, elegibilidad o
Ranking. Una extraccion fisica solo se evalua ante backlog sostenido, costo de
rebuild, CPU/GPU, volumen de indice, latencia fuera de SLO o necesidad real de
escalar lectura e indexacion de manera diferente.

Los casos de IA no comparten obligatoriamente un servicio universal. Embeddings,
creacion multimodal e IA conversacional deben conservar contratos especializados
cuando sus entradas, salidas, riesgos o validaciones difieran.

## Pipeline conceptual de indexación

Fuente Oficial

↓

Evento de Indexación

↓

Indexador

↓

Commerce Index Document

↓

Validación

↓

Persistencia futura

↓

Índices Sintetizados

↓

Runtime

La persistencia es un detalle de implementación.

El Documento existe porque el Indexador lo construye.

Luego podrá persistirse utilizando cualquier estrategia futura.

### Discovery Pasivo

El sistema de Discovery no comienza únicamente cuando el usuario escribe.

También puede actuar antes de la búsqueda mostrando información relevante obtenida desde el sistema de conocimiento y los índices.

Las sugerencias iniciales forman parte del Buscador Inteligente y podrán construirse utilizando, entre otras fuentes:

- taxonomía
- índices sintetizados
- historial
- tendencias
- popularidad
- contexto
- ubicación
- campañas

Estas sugerencias no constituyen una funcionalidad separada del buscador, sino una extensión natural del sistema de Discovery.

### Taxonomía y Knowledge System

- La Taxonomía es el esqueleto estructural oficial del buscador.
- Debe ser pequeña, estable, jerárquica y administrada de forma controlada.
- Define rubros, categorías, especialidades y relaciones estructurales principales.
- No debe convertirse en una lista gigante de palabras, productos, problemas o términos.
- El Knowledge System es la capa dinámica y extensible del conocimiento.
- Administra conceptos, sinónimos, aliases, productos, servicios, problemas, necesidades, acciones, atributos y relaciones semánticas.
- El Knowledge System puede crecer continuamente sin modificar la estructura principal de la Taxonomía.
- La IA, los embeddings, Search Events y las publicaciones pueden generar evidencias o propuestas de conocimiento.
- Esas propuestas no modifican automáticamente la Taxonomía ni el conocimiento oficial.
- El Indexador combina Taxonomía + Knowledge System + evidencias de la entidad para generar el Documento de Índice.
- Regla conceptual:
  - Taxonomía = esqueleto estable.
  - Knowledge System = conocimiento dinámico.
  - Indexador = componente que combina ambos.

Un concepto como “luces LED”, “domótica” o “panel solar” puede relacionarse con Electricidad desde el Knowledge System sin convertirse necesariamente en un nodo taxonómico.

La Taxonomía solo se modifica cuando existe una decisión estructural aprobada.

# Documento de Índice

## Definición

El Documento de Índice es la representación del conocimiento que FeedGo posee sobre una entidad para permitir:

- búsqueda
- descubrimiento
- recomendaciones
- futuras capacidades inteligentes

El Documento de Índice no representa la base de datos.

Representa conocimiento preparado para ser consumido.

## Fuente de verdad

El Documento de Índice NO es la fuente de verdad.

Las fuentes oficiales son:

- Espacios
- Publicaciones
- Historias
- Taxonomía
- Knowledge System
- Señales del sistema

El Documento de Índice es un artefacto derivado.

## Regeneración

El Documento de Índice nunca se modifica manualmente.

Siempre se reconstruye completamente mediante el Indexador.

Puede regenerarse cuando cambie:

- un Espacio
- una Publicación
- una Historia
- la Taxonomía
- el Knowledge System
- el algoritmo del Indexador
- una reindexación global

## Responsabilidad del Indexador

El Indexador:

- recopila todas las fuentes
- interpreta el conocimiento
- aplica las reglas aprobadas
- genera una nueva versión del Documento de Índice

El Indexador no modifica las fuentes originales.

El Indexador es el constructor del Commerce Index Document.

Cada bloque del Documento posee una fuente de verdad claramente definida.

El Documento nunca obtiene información desde el frontend.

El Documento nunca es construido por Discovery.

El Documento nunca es construido por Candidate Engine.

El Documento nunca es construido por Ranking.

## Arquitectura conceptual

El Documento de Índice se organiza mediante bloques de conocimiento.

Los bloques oficiales son:

1. Identidad
2. Cobertura
3. Conceptos y Relaciones
4. Evidencias
5. Confianza y Peso Base
6. Promovibilidad
7. Cobertura Geográfica
8. Señales
9. Trazabilidad y Versión

Estos bloques representan el contrato conceptual permanente del Documento de Índice.

La implementación física podrá cambiar sin modificar este contrato.

Los bloques generales definidos en este documento representan el contrato común de cualquier Documento de Índice.

`/docs/10_INDEX_DESIGN.md` contiene la especialización vigente del Commerce Index Document.

Ante mayor nivel de detalle, prevalece el documento técnico especializado, siempre que no contradiga la arquitectura general.

## Consumo

El Buscador Inteligente no genera conocimiento.

Consume el Documento de Índice.

El Ranking utiliza el Documento de Índice junto con el contexto de la búsqueda para calcular el orden final de los resultados.

## Inspiración del modelo

FeedGo debe aproximarse al modelo de razonamiento utilizado por los asistentes modernos de IA.

El objetivo no es comparar únicamente palabras clave.

El sistema debe:

- interpretar intención
- comprender contexto
- relacionar conceptos
- identificar necesidades
- encontrar la mejor solución disponible

La búsqueda por palabras constituye únicamente una de las señales utilizadas por el sistema.

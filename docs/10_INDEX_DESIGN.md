# Diseno del Documento de Indice

Este documento constituye la fuente oficial de diseno del Documento de Indice.

No define tablas.

No define persistencia fisica.

No define endpoints.

Su responsabilidad es documentar las decisiones de diseno aprobadas y el estado tecnico vigente del Documento de Indice y del modulo Indexador.

## Estado

Diseno conceptual cerrado en ETAPA 85.

Implementacion inicial del modulo Indexador cerrada en ETAPA 86.

## Objetivo

Disenar y mantener el modelo conceptual que representa el conocimiento de una entidad dentro de FeedGo.

El Documento de Indice constituye la representacion preparada para consumo por parte del Buscador Inteligente y de futuros sistemas inteligentes.

## Decisiones aprobadas

- El Documento de Indice es un artefacto derivado.
- Nunca constituye la fuente de verdad.
- Siempre puede regenerarse completamente.
- Es construido exclusivamente por el Indexador.
- El Buscador consume el Documento de Indice.
- El Documento de Indice representa conocimiento y no estructuras de base de datos.
- El Documento de Indice nunca se edita manualmente.
- El Documento de Indice no es una copia de la base de datos.
- El Documento de Indice representa la interpretacion semantica de una entidad.
- El Documento de Indice constituye la fuente desde la cual posteriormente se generan los Indices Sintetizados.
- La persistencia es un detalle de implementacion.
- El Documento existe porque el Indexador lo construye.
- Luego podra persistirse utilizando cualquier estrategia futura.
- La Taxonomia constituye el esqueleto estable.
- El Knowledge System constituye el conocimiento dinamico.
- El Indexador combina ambas capas para construir el Documento de Indice.
- El Commerce Index Document quedo disenado conceptualmente en ETAPA 85.
- El contrato de dominio ejecutable del Commerce Index Document quedo implementado en ETAPA 86.
- El pipeline conceptual del Indexador esta aprobado.
- La arquitectura interna inicial del modulo Indexador quedo implementada en ETAPA 86.

## Arquitectura conceptual

Espacios

↓

Publicaciones

↓

Historias

↓

Taxonomia

↓

Knowledge System

↓

Senales

↓

Indexador

↓

Documento de Indice

↓

Indices Sintetizados

↓

Buscador

## Contrato conceptual comun

Los bloques conceptuales generales del Documento de Indice son:

1. Identidad
2. Cobertura
3. Conceptos y Relaciones
4. Evidencias
5. Confianza y Peso Base
6. Promovibilidad
7. Cobertura Geografica
8. Senales
9. Trazabilidad y Version

Estos bloques constituyen el contrato conceptual permanente y son independientes de cualquier implementacion fisica.

## Commerce Index Document

El Commerce Index Document representa la interpretacion semantica que FeedGo posee sobre un Comercio.

Es derivado.

Es regenerable.

Nunca se edita manualmente.

No constituye la fuente de verdad.

No es una copia de la base de datos.

Es construido por el Indexador.

Constituye la fuente desde la cual posteriormente se generan los Indices Sintetizados.

## Bloques del Commerce Index Document

### 1. Identidad

Representa la entidad indexable, su estado indexable y su identidad principal.

Fuente de verdad:

- Comercio
- TaxonomyAssignment cuando define identidad principal aprobada

Responsable:

- Indexador

### 2. Perfil Publico

Representa la informacion publica minima necesaria para busqueda, descubrimiento y respuesta.

No copia todos los datos del perfil.

Fuente de verdad:

- Comercio

Responsable:

- Indexador

### 3. Conocimiento Semantico

Representa la interpretacion semantica del Comercio.

Incluye:

- conceptos
- relaciones
- cobertura principal
- cobertura secundaria
- capacidades
- restricciones relevantes para busqueda
- identidad derivada
- promovibilidad

Fuente de verdad:

- Taxonomia
- Knowledge System
- TaxonomyAssignment
- Publicaciones como evidencia

Responsable:

- Knowledge System
- Indexador

### 4. Representacion de Busqueda

Representa las formas preparadas para que el buscador consuma el documento.

Puede incluir:

- texto normalizado
- tokens
- aliases
- terminos derivados
- claves de matching
- referencias o versiones de representaciones vectoriales

El Search Text es un artefacto completamente derivado.

Lo construye exclusivamente `SearchRepresentationBuilder`.

No pertenece al modelo Comercio.

No constituye una fuente de verdad.

Puede regenerarse completamente.

Podra utilizarse como fuente para embeddings futuros sin convertirse en el embedding.

Discovery consumira este artefacto, pero nunca lo construira.

Fuente de verdad:

- Identidad
- Perfil Publico
- Conocimiento Semantico
- Contexto Derivado
- Intenciones y Casos de Uso

Responsable:

- Indexador

### 5. Cobertura Geografica

Representa la ubicacion y cobertura geografica base del Comercio.

No incluye distancia al usuario porque la distancia depende del contexto runtime.

Fuente de verdad:

- Comercio

Responsable:

- Indexador

### 6. Contexto Derivado

Representa informacion derivada de publicaciones, historias y actividad reciente.

Las publicaciones enriquecen el conocimiento del Comercio.

Una publicacion nunca redefine automaticamente la identidad principal del Comercio.

Fuente de verdad:

- Publicaciones
- Historias
- Actividad del Comercio

Responsable:

- Indexador

### 7. Senales

Representa senales agregadas y livianas utiles para busqueda, descubrimiento y futuras recomendaciones.

No representa ranking final.

Fuente de verdad:

- metricas
- actividad
- interacciones agregadas
- senales consolidadas

Responsable:

- Indexador
- futuros agregadores de senales

### 8. Intenciones y Casos de Uso

Representa necesidades, problemas o usos para los cuales el Comercio puede ser candidato.

Fuente de verdad:

- Knowledge System
- Conocimiento Semantico
- Publicaciones como evidencia
- Search Events consolidados
- revision humana cuando corresponda

Responsable:

- Knowledge System
- Indexador

### 9. Evidencias

Representa el origen, evidencia, confianza y peso de las decisiones del Documento.

Toda relacion agregada debe conservar:

- origen
- evidencia
- confianza
- peso

Fuente de verdad:

- todas las fuentes utilizadas por el Indexador

Responsable:

- Indexador

### 10. Trazabilidad

Representa version, fecha de generacion, fuentes utilizadas, advertencias y version del proceso de indexacion.

Fuente de verdad:

- proceso de indexacion

Responsable:

- Indexador

## Pipeline implementado

Fuente Oficial

↓

Collectors

↓

SourceSnapshots

↓

Builders

↓

Commerce Index Document

↓

ValidationService

↓

Resultado en memoria

## Arquitectura interna implementada del Indexador

La implementacion inicial vive en:

`backend/app/modules/indexer/`

### Contratos

Se implementaron contratos Pydantic independientes de persistencia para:

- `CommerceIndexDocument`
- `CommerceIndexBlocks`
- bloques del documento
- `SourceSnapshots`
- evidencias
- trazabilidad
- resultado de validacion
- contrato compartido de normalizacion de texto

### SourceSnapshots

Los `SourceSnapshots` son la frontera entre fuentes oficiales y builders.

Representan datos preparados para construccion del Documento sin exponer modelos fisicos a los builders.

### Collectors

Se implementaron collectors para:

- Comercio
- Taxonomia
- Contenido
- Senales
- Knowledge Graph

Responsabilidad:

- obtener datos desde fuentes oficiales disponibles;
- convertirlos en `SourceSnapshots`;
- no interpretar conocimiento;
- no construir bloques;
- no generar Search Text;
- no decidir indexabilidad global.

### Builders

Se implementaron builders para los diez bloques:

1. `IdentityBuilder`
2. `PublicProfileBuilder`
3. `GeographicCoverageBuilder`
4. `SemanticKnowledgeBuilder`
5. `DerivedContextBuilder`
6. `SignalBuilder`
7. `IntentUseCaseBuilder`
8. `SearchRepresentationBuilder`
9. `EvidenceBuilder`
10. `TraceBuilder`

Responsabilidad:

- recibir snapshots o bloques aprobados;
- construir un unico bloque;
- no consultar fuentes;
- no usar modelos fisicos;
- no modificar bloques construidos por otro builder.

### ValidationService

Se implemento `IndexDocumentValidationService`.

Responsabilidad:

- validar un `CommerceIndexDocument` completo;
- devolver `IndexValidationResult`;
- no construir;
- no corregir;
- no consultar fuentes;
- no modificar el documento.

### CommerceIndexerService

Se implemento `CommerceIndexerService`.

Responsabilidad:

- orquestar collectors;
- ejecutar builders en el orden aprobado;
- acumular warnings;
- ensamblar el `CommerceIndexDocument`;
- ejecutar `IndexDocumentValidationService`;
- devolver documento y resultado de validacion.

No persiste.

No publica eventos.

No dispara procesos posteriores.

No contiene logica de negocio.

## Normalizacion compartida

La normalizacion existe como contrato compartido reutilizable del backend.

No pertenece exclusivamente al Indexador.

No pertenece exclusivamente a Discovery.

No pertenece exclusivamente a Embeddings.

El Indexador adopta ese contrato mediante `TextNormalizationContract`.

No existe una implementacion concreta de normalizacion en esta etapa.

## Orden de construccion

1. Identidad.
2. Perfil Publico.
3. Cobertura Geografica.
4. Conocimiento Semantico.
5. Contexto Derivado.
6. Senales.
7. Intenciones y Casos de Uso.
8. Representacion de Busqueda.
9. Evidencias.
10. Trazabilidad.

La Representacion de Busqueda se construye despues del conocimiento, contexto e intenciones porque depende de ellos.

## Regeneracion

Para V1 se aprueba reconstruccion completa por Comercio.

En el futuro podra existir regeneracion parcial por bloques.

El Documento sigue siendo derivado tanto en reconstruccion completa como en regeneracion parcial.

## Invalidacion

Un cambio en las fuentes oficiales puede invalidar el Documento.

Los Search Events no provocan reindexacion inmediata.

Solo el conocimiento consolidado puede provocar reconstruccion.

## Escalabilidad

Se aprueba para V1 un documento unico por Comercio.

El Documento y los Indices Sintetizados permanecen conceptualmente separados.

La indexacion debe minimizar trabajo runtime.

El runtime unicamente consume documentos e indices previamente preparados.

## Implementado en ETAPA 86

- Contrato de dominio ejecutable del Commerce Index Document.
- Contratos de bloques.
- SourceSnapshots.
- Evidencias.
- Trazabilidad.
- Contrato compartido de normalizacion.
- Collectors.
- Builders de los diez bloques.
- ValidationService.
- CommerceIndexerService.
- Flujo completo del Indexador en memoria.

## Fuera de alcance de ETAPA 86

- Persistencia.
- Reindexacion.
- Indices Sintetizados fisicos.
- Scheduler.
- Colas.
- Integracion con Discovery.
- Integracion con Candidate Engine.
- Integracion con Ranking.
- Documento de Indice de Publicacion.
- Documento de Indice de Historia.

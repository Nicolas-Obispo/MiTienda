# Diseño del Documento de Índice

Este documento constituye la fuente oficial de diseño del Documento de Índice.

No contiene implementación.

No contiene tablas.

No contiene modelos físicos.

No contiene código.

Su responsabilidad es documentar las decisiones de diseño aprobadas durante la construcción del nuevo Buscador Inteligente.

Cada vez que una decisión conceptual sea aprobada durante la ETAPA 85, este documento deberá actualizarse.

## Estado

Diseño conceptual cerrado en ETAPA 85.

Implementación pendiente para ETAPA 86.

# Objetivo

Diseñar el modelo conceptual que representa el conocimiento de una entidad dentro de FeedGo.

El Documento de Índice constituye la representación preparada para consumo por parte del Buscador Inteligente y de futuros sistemas inteligentes.

# Decisiones aprobadas

- El Documento de Índice es un artefacto derivado.
- Nunca constituye la fuente de verdad.
- Siempre puede regenerarse completamente.
- Es construido exclusivamente por el Indexador.
- El Buscador consume el Documento de Índice.
- El Documento de Índice representa conocimiento y no estructuras de base de datos.
- El Documento de Índice nunca se edita manualmente.
- El Documento de Índice no es una copia de la base de datos.
- El Documento de Índice representa la interpretación semántica de una entidad.
- El Documento de Índice constituye la fuente desde la cual posteriormente se generan los Índices Sintetizados.
- La persistencia es un detalle de implementación.
- El Documento existe porque el Indexador lo construye.
- Luego podrá persistirse utilizando cualquier estrategia futura.
- La Taxonomía constituye el esqueleto estable.
- El Knowledge System constituye el conocimiento dinámico.
- El Indexador combina ambas capas para construir el Documento de Índice.
- El Commerce Index Document quedó diseñado conceptualmente en ETAPA 85.
- La implementación física y el contrato de dominio ejecutable corresponden a ETAPA 86.
- El pipeline conceptual del Indexador está aprobado.
- La arquitectura interna del módulo Indexador sigue pendiente para ETAPA 86.

# Arquitectura conceptual

Espacios

↓

Publicaciones

↓

Historias

↓

Taxonomía

↓

Knowledge System

↓

Señales

↓

Indexador

↓

Documento de Índice

↓

Índices Sintetizados

↓

Buscador

# Contrato conceptual aprobado

1. Identidad
2. Cobertura
3. Conceptos y Relaciones
4. Evidencias
5. Confianza y Peso Base
6. Promovibilidad
7. Cobertura Geográfica
8. Señales
9. Trazabilidad y Versión

Estos bloques constituyen el contrato conceptual permanente y son independientes de cualquier implementación física.

# Commerce Index Document

El Commerce Index Document representa la interpretación semántica que FeedGo posee sobre un Comercio.

Es derivado.

Es regenerable.

Nunca se edita manualmente.

No constituye la fuente de verdad.

No es una copia de la base de datos.

Es construido por el Indexador.

Constituye la fuente desde la cual posteriormente se generan los Índices Sintetizados.

## Bloques conceptuales

### 1. Identidad

Representa la entidad indexable, su estado indexable y su identidad principal.

Fuente de verdad:

- Comercio
- TaxonomyAssignment cuando define identidad principal aprobada

Responsable:

- Indexador

### 2. Perfil Público

Representa la información pública mínima necesaria para búsqueda, descubrimiento y respuesta.

No copia todos los datos del perfil.

Fuente de verdad:

- Comercio

Responsable:

- Indexador

### 3. Conocimiento Semántico

Representa la interpretación semántica del Comercio.

Incluye:

- conceptos
- relaciones
- cobertura principal
- cobertura secundaria
- capacidades
- restricciones relevantes para búsqueda
- identidad derivada
- promovibilidad

Fuente de verdad:

- Taxonomía
- Knowledge System
- TaxonomyAssignment
- Publicaciones como evidencia

Responsable:

- Knowledge System
- Indexador

### 4. Representación de Búsqueda

Representa las formas preparadas para que el buscador consuma el documento.

Puede incluir:

- texto normalizado
- tokens
- aliases
- términos derivados
- claves de matching
- referencias o versiones de representaciones vectoriales

No obliga a una implementación física específica.

Fuente de verdad:

- Identidad
- Perfil Público
- Conocimiento Semántico
- Contexto Derivado
- Intenciones y Casos de Uso

Responsable:

- Indexador

### 5. Cobertura Geográfica

Representa la ubicación y cobertura geográfica base del Comercio.

No incluye distancia al usuario porque la distancia depende del contexto runtime.

Fuente de verdad:

- Comercio

Responsable:

- Indexador

### 6. Contexto Derivado

Representa información derivada de publicaciones, historias y actividad reciente.

Las publicaciones enriquecen el conocimiento del Comercio.

Una publicación nunca redefine automáticamente la identidad principal del Comercio.

Fuente de verdad:

- Publicaciones
- Historias
- Actividad del Comercio

Responsable:

- Indexador

### 7. Señales

Representa señales agregadas y livianas útiles para búsqueda, descubrimiento y futuras recomendaciones.

No representa ranking final.

Fuente de verdad:

- métricas
- actividad
- interacciones agregadas
- señales consolidadas

Responsable:

- Indexador
- futuros agregadores de señales

### 8. Intenciones y Casos de Uso

Representa necesidades, problemas o usos para los cuales el Comercio puede ser candidato.

Fuente de verdad:

- Knowledge System
- Conocimiento Semántico
- Publicaciones como evidencia
- Search Events consolidados
- revisión humana cuando corresponda

Responsable:

- Knowledge System
- Indexador

### 9. Evidencias

Representa el origen, evidencia, confianza y peso de las decisiones del Documento.

Toda relación agregada debe conservar:

- origen
- evidencia
- confianza
- peso

Fuente de verdad:

- todas las fuentes utilizadas por el Indexador

Responsable:

- Indexador

### 10. Trazabilidad

Representa versión, fecha de generación, fuentes utilizadas, motivo de regeneración y versión del proceso de indexación.

Fuente de verdad:

- proceso de indexación

Responsable:

- Indexador

# Pipeline aprobado

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

# Orden de construcción

1. Identidad.
2. Perfil Público.
3. Cobertura Geográfica.
4. Conocimiento Semántico.
5. Contexto Derivado.
6. Señales.
7. Intenciones y Casos de Uso.
8. Representación de Búsqueda.
9. Evidencias.
10. Trazabilidad.

La Representación de Búsqueda se construye después del conocimiento, contexto e intenciones porque depende de ellos.

# Regeneración

Para V1 se aprueba reconstrucción completa por Comercio.

En el futuro podrá existir regeneración parcial por bloques.

El Documento sigue siendo derivado tanto en reconstrucción completa como en regeneración parcial.

Los bloques que podrán regenerarse de forma independiente en el futuro son:

- Cobertura Geográfica
- Contexto Derivado
- Señales
- Intenciones y Casos de Uso
- Representación de Búsqueda
- Trazabilidad

Identidad y Perfil Público se reconstruyen juntos.

Conocimiento Semántico y Evidencias semánticas se reconstruyen juntos.

# Invalidación

Un cambio en Comercio invalida:

- Identidad
- Perfil Público
- Cobertura Geográfica
- Representación de Búsqueda
- Trazabilidad

Si el cambio afecta rubro, descripción o identidad, también invalida:

- Conocimiento Semántico
- Intenciones y Casos de Uso
- Evidencias

Un cambio en Publicación invalida:

- Contexto Derivado
- Señales
- Evidencias
- Intenciones y Casos de Uso cuando la publicación aporta cobertura
- Representación de Búsqueda

Un cambio en Historia invalida:

- Contexto Derivado
- Señales
- Representación de Búsqueda cuando las historias participan en descubrimiento

Un cambio en TaxonomyNode invalida:

- Conocimiento Semántico
- Intenciones y Casos de Uso
- Representación de Búsqueda
- Evidencias

Un cambio en una relación del Knowledge Graph invalida:

- Conocimiento Semántico
- Intenciones y Casos de Uso
- Representación de Búsqueda
- Evidencias

Una nueva evidencia invalida el bloque afectado cuando supera los umbrales aprobados.

Los Search Events no provocan reindexación inmediata.

Solo el conocimiento consolidado puede provocar reconstrucción.

# Escalabilidad

Se aprueba para V1 un documento único por Comercio.

El Documento y los Índices Sintetizados permanecen conceptualmente separados.

El proceso de indexación debe soportar:

- reindexación por entidad
- deduplicación de eventos
- reconstrucción incremental futura
- reindexación masiva solo ante cambios estructurales
- separación conceptual entre Documento e Índices Sintetizados

La indexación debe minimizar trabajo runtime.

El runtime únicamente consume documentos e índices previamente preparados.

# Principios aprobados

- El Documento de Índice no se modifica; se reconstruye.
- El Runtime debe permanecer liviano.
- El trabajo pesado ocurre durante la indexación.
- El Buscador interpreta intención y consume conocimiento.
- FeedGo busca aproximarse al razonamiento utilizado por los asistentes modernos de IA, comprendiendo intención, contexto, relaciones y necesidades, en lugar de limitarse a comparar palabras clave.

# Aprobado conceptualmente

Quedaron aprobados conceptualmente en ETAPA 85:

- Commerce Index Document.
- Bloques conceptuales del Commerce Index Document.
- Pipeline conceptual del Indexador.
- Orden de construcción del Documento.
- Reglas de regeneración.
- Reglas de invalidación.
- Estrategia conceptual de escalabilidad.
- Separación conceptual entre Documento e Índices Sintetizados.

# Pendiente de implementación

Corresponde a ETAPA 86:

☐ Arquitectura interna del módulo Indexador.

☐ Contrato de dominio ejecutable del Commerce Index Document.

☐ Builders por bloque.

☐ CommerceIndexerService.

☐ Integración del Indexador con Taxonomía y Knowledge Graph.

☐ Generación del primer documento completo de un Comercio.

☐ Validaciones funcionales del Indexador.

Corresponde a etapas posteriores:

☐ Documento de Índice de Publicación.

☐ Documento de Índice de Historia.

☐ Índices Sintetizados físicos.

☐ Persistencia.

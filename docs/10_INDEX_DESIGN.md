# Diseño del Documento de Índice

Este documento constituye la fuente oficial de diseño del Documento de Índice.

No contiene implementación.

No contiene tablas.

No contiene modelos físicos.

No contiene código.

Su responsabilidad es documentar las decisiones de diseño aprobadas durante la construcción del nuevo Buscador Inteligente.

Cada vez que una decisión conceptual sea aprobada durante la ETAPA 85, este documento deberá actualizarse.

## Estado

En construcción.

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
- La Taxonomía constituye el esqueleto estable.
- El Knowledge System constituye el conocimiento dinámico.
- El Indexador combina ambas capas para construir el Documento de Índice.

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

# Principios aprobados

- El Documento de Índice no se modifica; se reconstruye.
- El Runtime debe permanecer liviano.
- El trabajo pesado ocurre durante la indexación.
- El Buscador interpreta intención y consume conocimiento.
- FeedGo busca aproximarse al razonamiento utilizado por los asistentes modernos de IA, comprendiendo intención, contexto, relaciones y necesidades, en lugar de limitarse a comparar palabras clave.

# Pendientes de Diseño

☐ Documento de Índice de Comercio.

☐ Documento de Índice de Publicación.

☐ Documento de Índice de Historia.

☐ Índices Sintetizados.

☐ Estrategia de Reindexación.

☐ Estrategia de Versionado.

☐ Persistencia.

☐ Contrato del Indexador.

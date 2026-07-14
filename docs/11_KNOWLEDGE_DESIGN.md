# Knowledge Design

## Estado

En construcción.

## Objetivo

Construir una red de conocimiento capaz de conectar necesidades, problemas, productos, servicios y entidades de FeedGo.

## Principios aprobados

- FeedGo busca conceptos, no solamente palabras.
- Un Concepto es la unidad mínima de conocimiento reutilizable.
- La Taxonomía es el esqueleto jerárquico estable.
- El Knowledge System es una red dinámica de Conceptos y Relaciones.
- El conocimiento puede crecer sin modificar la Taxonomía.
- El Knowledge System alimenta al Indexador.
- El runtime de búsqueda no crea conocimiento nuevo.
- Las propuestas automáticas nunca se convierten directamente en conocimiento oficial.

## Tipos iniciales de Concepto

- Rubro
- Especialidad
- Servicio
- Producto
- Marca
- Material
- Problema
- Necesidad
- Intención
- Acción
- Atributo

## Relaciones iniciales

- ES_UN
- PERTENECE_A
- OFRECE
- VENDE
- UTILIZA
- RESUELVE
- SATISFACE
- REQUIERE
- COMPLEMENTA
- RELACIONADO_CON

## Fuentes del conocimiento

- Taxonomía
- Datos declarados por el espacio
- Publicaciones
- Productos futuros
- Search Events
- Embeddings
- Propuestas automáticas
- Revisión humana

## Estados conceptuales

- detectado
- propuesto
- validado
- oficial
- deprecado

Un término detectado no crea automáticamente un Concepto oficial.

## Confianza

- muy alta
- alta
- media
- baja
- experimental

Toda relación debe conservar:

- origen
- evidencia
- confianza
- estado
- versión

## Aprendizaje

El sistema puede aprender de publicaciones, búsquedas e interacciones.

Ese aprendizaje puede:

- generar propuestas
- reforzar relaciones
- ajustar pesos
- detectar conocimiento faltante

Nunca debe modificar automáticamente la identidad principal de un espacio ni el conocimiento oficial.

# Evidencia del sistema actual

- `TaxonomyNode` es la base reutilizable de la Taxonomía estable.
- No debe convertirse en el modelo completo del Knowledge System dinámico.
- `TaxonomyAssignment` ya relaciona entidades con nodos y conserva `source`, `confidence` y `principal`.
- `KnowledgeProposal` ya soporta propuestas, confianza y revisión humana.
- Search Events son fuente de señales y aprendizaje, no conocimiento oficial automático.
- Embeddings son señales semánticas y no conocimiento oficial.
- Candidate Engine conserva evidencias en runtime, pero no debe convertirse en fuente persistente de conocimiento.
- La lógica legacy de intención es adaptable, no debe ampliarse con más hardcode.

## Huecos confirmados

- contrato formal de Concepto;
- contrato formal de Relación;
- relación Concepto–Entidad;
- estados conceptuales;
- evidencia obligatoria;
- trazabilidad;
- versionado;
- promoción y deprecación;
- contrato de lectura para el futuro Indexador.

## Restricciones

- no rediseñar `TaxonomyNode`;
- no reemplazar `TaxonomyAssignment`;
- no modificar Candidate Engine;
- no modificar Search Events;
- no modificar embeddings;
- no mover lógica al frontend.

# Contrato Conceptual de Concepto

## Definición

Un Concepto representa la unidad mínima de significado reutilizable dentro del Knowledge System.

No representa una palabra.

No representa una categoría obligatoriamente.

Representa significado.

Los Conceptos son reutilizados por:

- Discovery
- Documento de Índice
- Candidate Engine
- Ranking
- Recomendaciones
- futuros sistemas inteligentes

## Bloques del Concepto

### 1. Identidad

Debe representar:

- identidad estable
- nombre canónico
- tipo conceptual
- estado
- versión

### 2. Lenguaje

Debe representar las formas mediante las cuales un usuario puede llegar al Concepto.

Ejemplos:

- sinónimos
- aliases
- variantes
- errores frecuentes
- expresiones habituales

Las palabras no constituyen necesariamente Conceptos independientes.

### 3. Tipo Conceptual

- Rubro
- Especialidad
- Servicio
- Producto
- Marca
- Material
- Problema
- Necesidad
- Intención
- Acción
- Atributo

### 4. Estado Conceptual

- Detectado
- Propuesto
- Validado
- Oficial
- Deprecado

Ningún Concepto pasa automáticamente a Oficial.

### 5. Evidencia

Todo Concepto debe conservar:

- origen
- evidencia
- fecha
- confianza
- versión

### 6. Confianza

- Muy Alta
- Alta
- Media
- Baja
- Experimental

La implementación física podrá utilizar escalas numéricas.

### 7. Trazabilidad

- cuándo nació
- por qué
- cómo evolucionó
- quién lo validó
- cuándo fue deprecado
- versión vigente

# Contrato Conceptual de Relación

## Definición

Una Relación conecta dos Conceptos o un Concepto con una Entidad.

No representa solamente jerarquía.

Representa conocimiento.

## Bloques

### Origen

### Destino

### Tipo de Relación

Tipos iniciales:

- ES_UN
- PERTENECE_A
- OFRECE
- VENDE
- UTILIZA
- RESUELVE
- SATISFACE
- REQUIERE
- COMPLEMENTA
- RELACIONADO_CON

### Dirección

Una Relación puede ser:

- unidireccional
- bidireccional

según su significado.

### Evidencia

Toda Relación debe conservar:

- origen
- evidencia
- confianza
- estado
- versión

### Peso Base

Representa la importancia estructural de la relación.

No representa el ranking final.

### Promovibilidad

- no promovible
- evaluable
- promovible mediante validación
- identidad oficial

### Estado

- detectada
- propuesta
- validada
- oficial
- deprecada

# Separación conceptual

Concepto
→ representa significado.

Relación
→ conecta significados.

Entidad
→ representa elementos reales del sistema.

Documento de Índice
→ representa el conocimiento relevante de una entidad.

# Principio permanente

FeedGo organiza su conocimiento alrededor de Conceptos y Relaciones.

Las entidades no constituyen el centro del sistema.

El centro del sistema es el Knowledge Graph construido mediante Conceptos y Relaciones.

# Implementación inicial

- Se implementó el contrato de dominio `Concept`.
- Se implementó el contrato de dominio `Relation`.
- Se implementó el servicio en memoria `KnowledgeGraphService`.
- La ausencia de persistencia es intencional.
- El objetivo del servicio es validar el modelo antes de definir almacenamiento.

## Relación con el Documento de Índice

El Indexador combina:

Taxonomía
+ Knowledge System
+ entidad
+ publicaciones
+ señales

para generar el Documento de Índice.

El Knowledge System es fuente de conocimiento.

El Documento de Índice es un artefacto derivado y regenerable.

## Pendientes de diseño

- contrato definitivo de Concepto
- contrato definitivo de Relación
- reglas de creación
- reglas de validación
- reglas de promoción
- reglas de deprecación
- estrategia de evolución
- integración con el Indexador
- persistencia futura

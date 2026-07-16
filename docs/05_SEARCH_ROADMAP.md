# Objetivo

El Roadmap representa el plan oficial de construccion del buscador.

Debe mantenerse actualizado durante todo el proyecto.

No documenta conversaciones.

No documenta hipotesis.

No documenta auditorias.

Documenta unicamente trabajo aprobado.

## Estados

☑ Cerrado

◐ En curso

☐ Pendiente

⊘ Pospuesto

## Prioridades

P0

Obligatorio.

P1

Importante.

P2

Mejora futura.

## Regla

Solo la etapa actual podra estar completamente desarrollada.

Las etapas futuras deberan contener unicamente:

- nombre
- objetivo
- estado

Se desarrollaran cuando pasen a ser la etapa activa.

Toda etapa cerrada debera reflejarse tambien en:

- documentacion tecnica;
- decisiones permanentes;
- principios de ingenieria;

cuando corresponda.

## Roadmap

### ☑ ETAPA 83

Sistema de Indexacion y Knowledge Base.

Estado:

Cerrada.

---

### ☑ ETAPA 84

Consolidacion de arquitectura del Buscador.

Estado:

Cerrada.

---

### ☑ ETAPA 85

Documento de Indice e Indices Sintetizados.

Estado:

Cerrada.

P0

- ☑ Crear Documentos de Gobierno.
- ☑ Definir filosofia del Documento de Indice.
- ☑ Definir que representa una entidad indexable.
- ☑ Definir identidad principal y cobertura secundaria.
- ☑ Definir que las publicaciones enriquecen el espacio.
- ☑ Definir origen, evidencia, confianza y peso.
- ☑ Definir runtime liviano e indexacion pesada.
- ☑ Crear documentacion oficial.
- ☑ Definir separacion entre Taxonomia estable y Knowledge System dinamico.
- ☑ Definir naturaleza del Documento de Indice.
- ☑ Definir que el Documento de Indice es un artefacto derivado.
- ☑ Definir la regeneracion mediante el Indexador.
- ☑ Definir que el Buscador consume conocimiento y no lo genera.
- ☑ Aprobar el contrato conceptual basado en bloques de conocimiento.
- ☑ Auditar componentes existentes reutilizables para Conceptos y Relaciones.
- ☑ Disenar el contrato conceptual de Concepto.
- ☑ Disenar el contrato conceptual de Relacion.
- ☑ Implementar contrato inicial de Concept.
- ☑ Implementar contrato inicial de Relation.
- ☑ Implementar Graph Service inicial en memoria.
- ☑ Auditar integracion entre Taxonomia estable y Knowledge Graph.
- ☑ Implementar proyeccion inicial Taxonomia → Knowledge Graph en memoria.
- ☑ Disenar el contrato conceptual del Documento de Indice de Comercio.
- ☑ Disenar contrato del Documento de Indice.
- ☑ Disenar el pipeline conceptual de construccion del Commerce Index Document.
- ☑ Definir bloques conceptuales del Commerce Index Document.
- ☑ Definir reglas de regeneracion e invalidacion del Commerce Index Document.
- ☑ Definir estrategia conceptual de escalabilidad del proceso de indexacion.
- ☑ Disenar estrategia conceptual de actualizacion.
- ☑ Disenar estrategia conceptual de reindexacion.
- ☑ Auditoria final documental.
- ☑ Cierre de ETAPA 85.

No forman parte del cierre de ETAPA 85:

- implementacion interna del modulo Indexador;
- implementacion del Commerce Index Document;
- Documento de Indice de Publicacion;
- Indices Sintetizados fisicos;
- persistencia;
- integracion con Discovery, Candidate Engine y Ranking.

---

### ☑ ETAPA 86 — Implementacion del Indexador

Estado:

Cerrada.

Objetivo:

Construir progresivamente el modulo Indexador sobre los contratos y decisiones aprobados en ETAPA 85.

P0

- ☑ Auditar arquitectura existente para disenar el modulo Indexador.
- ☑ Disenar arquitectura interna del modulo Indexador.
- ☑ Implementar estructura base del modulo `backend/app/modules/indexer/`.
- ☑ Implementar contratos de dominio del `CommerceIndexDocument`.
- ☑ Implementar `SourceSnapshots`.
- ☑ Implementar contratos de evidencias y trazabilidad.
- ☑ Implementar contrato compartido de normalizacion de texto.
- ☑ Implementar Collectors de Comercio, Taxonomia, Contenido, Senales y Knowledge Graph.
- ☑ Implementar Builders de Identidad, Perfil Publico y Cobertura Geografica.
- ☑ Implementar Builders de Conocimiento Semantico y Contexto Derivado.
- ☑ Implementar Builders de Intenciones y Representacion de Busqueda.
- ☑ Implementar Builders de Senales, Evidencias y Trazabilidad.
- ☑ Implementar `IndexDocumentValidationService`.
- ☑ Implementar `CommerceIndexerService`.
- ☑ Validar auditoria final de integracion.
- ☑ Corregir duplicacion del contrato `TextNormalizationContract`.
- ☑ Actualizar documentacion oficial de cierre.

Fuera de alcance:

- persistencia;
- reindexacion;
- Indices Sintetizados fisicos;
- scheduler;
- colas;
- integracion con Discovery;
- integracion con Candidate Engine;
- integracion con Ranking.

---

### ☐ ETAPA 87

Sistema de Disponibilidad.

### ☐ ETAPA 88

Agenda y Reservas.

### ☐ ETAPA 89

Productos e Inventario.

### ☐ ETAPA 90

Pedidos, Carrito y Pagos.

### ☐ ETAPA 91

Mensajeria.

### ☐ ETAPA 92

Reputacion.

### ☐ ETAPA 93

IA Conversacional.

### ☐ ETAPA 94

Recomendaciones.

### ☐ ETAPA 95

Analytics.

### ☐ ETAPA 96

Inteligencia Global.

### ☐ ETAPA 97

Calidad de Datos.

### ☐ ETAPA 98

Moderacion.

### ☐ ETAPA 99

Observabilidad.

### ☐ ETAPA 100

Backend Universal.

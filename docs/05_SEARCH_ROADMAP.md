# Objetivo

El Roadmap representa el plan oficial de construcción del buscador.

Debe mantenerse actualizado durante todo el proyecto.

No documenta conversaciones.

No documenta hipótesis.

No documenta auditorías.

Documenta únicamente trabajo aprobado.

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

Solo la etapa actual podrá estar completamente desarrollada.

Las etapas futuras deberán contener únicamente:

- nombre
- objetivo
- estado

Se desarrollarán cuando pasen a ser la etapa activa.

Toda etapa cerrada deberá reflejarse también en:

- documentación técnica;
- decisiones permanentes;
- principios de ingeniería;

cuando corresponda.

## Roadmap

### ☑ ETAPA 83

Sistema de Indexación y Knowledge Base.

Estado:

Cerrada.

---

### ☑ ETAPA 84

Consolidación de arquitectura del Buscador.

Estado:

Cerrada.

---

### ☑ ETAPA 85

Documento de Índice e Índices Sintetizados.

Estado:

Cerrada.

P0

- ☑ Crear Documentos de Gobierno.
- ☑ Definir filosofía del Documento de Índice.
- ☑ Definir que representa una entidad indexable.
- ☑ Definir identidad principal y cobertura secundaria.
- ☑ Definir que las publicaciones enriquecen el espacio.
- ☑ Definir origen, evidencia, confianza y peso.
- ☑ Definir runtime liviano e indexación pesada.
- ☑ Crear documentación oficial.
- ☑ Definir separación entre Taxonomía estable y Knowledge System dinámico.
- ☑ Definir naturaleza del Documento de Índice.
- ☑ Definir que el Documento de Índice es un artefacto derivado.
- ☑ Definir la regeneración mediante el Indexador.
- ☑ Definir que el Buscador consume conocimiento y no lo genera.
- ☑ Aprobar el contrato conceptual basado en bloques de conocimiento.
- ☑ Auditar componentes existentes reutilizables para Conceptos y Relaciones.
- ☑ Diseñar el contrato conceptual de Concepto.
- ☑ Diseñar el contrato conceptual de Relación.
- ☑ Implementar contrato inicial de Concept.
- ☑ Implementar contrato inicial de Relation.
- ☑ Implementar Graph Service inicial en memoria.
- ☑ Auditar integración entre Taxonomía estable y Knowledge Graph.
- ☑ Implementar proyección inicial Taxonomía → Knowledge Graph en memoria.
- ☑ Diseñar el contrato conceptual del Documento de Índice de Comercio.
- ☑ Diseñar contrato del Documento de Índice.
- ☑ Diseñar el pipeline conceptual de construcción del Commerce Index Document.
- ☑ Definir bloques conceptuales del Commerce Index Document.
- ☑ Definir reglas de regeneración e invalidación del Commerce Index Document.
- ☑ Definir estrategia conceptual de escalabilidad del proceso de indexación.
- ☑ Diseñar estrategia conceptual de actualización.
- ☑ Diseñar estrategia conceptual de reindexación.
- ☑ Auditoría final documental.
- ☑ Cierre de ETAPA 85.

No forman parte del cierre de ETAPA 85:

- implementación interna del módulo Indexador;
- implementación del Commerce Index Document;
- Documento de Índice de Publicación;
- Índices Sintetizados físicos;
- persistencia;
- integración con Discovery, Candidate Engine y Ranking.

---

### ☐ ETAPA 86 — Implementación del Indexador

Estado:

Pendiente.

Objetivo:

Construir progresivamente el módulo Indexador sobre los contratos y decisiones aprobados en ETAPA 85.

Objetivos resumidos:

- diseñar arquitectura interna del módulo Indexador;
- implementar CommerceIndexDocument como contrato de dominio;
- implementar builders por bloque;
- implementar CommerceIndexerService;
- integrar Taxonomía y Knowledge Graph;
- generar el primer documento completo de un Comercio;
- validar;
- actualizar documentación y changelog.

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

Mensajería.

### ☐ ETAPA 92

Reputación.

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

Moderación.

### ☐ ETAPA 99

Observabilidad.

### ☐ ETAPA 100

Backend Universal.

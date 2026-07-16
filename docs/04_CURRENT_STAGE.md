# Estado actual

Proyecto:

FeedGo

## ETAPA 85

Estado:

Cerrada.

## ETAPA 86

Estado:

Cerrada.

## Resultado

- Modulo Indexador implementado en `backend/app/modules/indexer/`.
- Contratos de dominio del `CommerceIndexDocument` implementados.
- `SourceSnapshots` implementados como frontera entre fuentes y builders.
- Collectors implementados para Comercio, Taxonomia, Contenido, Senales y Knowledge Graph.
- Builders implementados para los diez bloques del `CommerceIndexDocument`.
- `IndexDocumentValidationService` implementado.
- `CommerceIndexerService` implementado como orquestador del flujo completo.
- Contrato compartido de normalizacion de texto implementado.
- Flujo completo del Indexador implementado sin persistencia.

## Fuera de alcance de ETAPA 86

- Persistencia del Documento de Indice.
- Reindexacion.
- Indices Sintetizados fisicos.
- Scheduler.
- Colas.
- Integracion con Discovery.
- Integracion con Candidate Engine.
- Integracion con Ranking.

## Etapa actual siguiente

ETAPA 87 — Sistema de Disponibilidad.

Estado:

Pendiente de inicio.

## Recordatorio

Toda nueva decision permanente debera actualizar los Documentos de Gobierno antes de continuar implementando.

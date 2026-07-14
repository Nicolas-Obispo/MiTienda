# Search

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

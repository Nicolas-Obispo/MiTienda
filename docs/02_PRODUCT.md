# Product

## Visión

- FeedGo conecta personas, necesidades y soluciones.
- FeedGo no es únicamente un marketplace.
- Debe servir para comercios, profesionales, oficios y servicios.
- El buscador es la capacidad principal del producto.

## Principios de Producto

- Pedir la menor cantidad posible de información estructurada.
- Obtener la mayor cantidad posible de conocimiento mediante indexación.
- No cansar al usuario con formularios largos.
- El usuario no debe completar datos que el sistema pueda inferir con alta confianza.
- Guiar al usuario mediante ayudas contextuales.
- Cada dato solicitado debe aportar valor al buscador.

## Design System

FeedGo debe mantener una experiencia visual uniforme en toda la aplicación.

Toda nueva pantalla, componente o flujo visible debe respetar el Design System oficial antes de introducir estilos nuevos.

No deben incorporarse nuevos estilos de botones sin justificación arquitectónica o de producto.

### Botones de acción

El estilo oficial para botones secundarios es:

- no mostrar borde, cápsula ni marco permanente;
- en estado normal mostrar únicamente icono, cuando corresponda, y texto;
- mostrar fondo suave o resaltado solo en hover, focus o interacción;
- mantener área de click cómoda y accesible;
- usar transiciones suaves y consistentes;
- conservar comportamiento uniforme en toda la aplicación.

Esta regla aplica a:

- botones de navegación;
- acciones secundarias;
- acciones sociales;
- acciones de perfil;
- acciones del buscador;
- acciones de publicaciones;
- acciones de historias;
- acciones de comercios;
- futuras funcionalidades.

La regla no aplica automáticamente a botones primarios cuya jerarquía visual requiera un tratamiento diferente.

### Descubrimiento Guiado

El buscador debe ayudar al usuario incluso antes de que escriba.

Cuando no exista una búsqueda activa, FeedGo podrá mostrar elementos de descubrimiento como:

- rubros
- categorías
- búsquedas frecuentes
- historial del usuario
- sugerencias inteligentes
- promociones o campañas
- recomendaciones relevantes

El objetivo es reducir el esfuerzo del usuario y facilitar el descubrimiento de comercios, profesionales, servicios y publicaciones.

El sistema debe poder evolucionar incorporando nuevas fuentes de descubrimiento sin modificar la arquitectura del buscador.

## Espacios

- El espacio posee una identidad principal.
- La identidad principal no cambia automáticamente.
- Las publicaciones enriquecen el conocimiento del espacio.

## Estado público y disponibilidad

- El estado público del espacio usa exclusivamente `Activo` y `En pausa`.
- `Activo` y `En pausa` representan publicación y visibilidad del espacio, no horarios de atención.
- Los horarios de atención pertenecen al Sistema de Disponibilidad.
- El estado horario visible usa exclusivamente `Abierto`, `Cerrado` y `No hay horarios declarados`.
- Un espacio `Activo` continúa siendo público aunque esté `Cerrado` por horario.

## Publicaciones

- Una publicación puede ampliar la cobertura del espacio.
- No redefine automáticamente la identidad principal.
- Toda relación incorporada debe conservar:
  - origen
  - evidencia
  - confianza
  - peso

## Evolución

- FeedGo evoluciona agregando conocimiento, no rediseñando arquitectura.
- La arquitectura debe crecer de menos a más.
- Toda nueva funcionalidad debe fortalecer el conocimiento reutilizable del sistema.

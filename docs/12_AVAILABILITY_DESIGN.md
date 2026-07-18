# Availability Design

Categoría:

Documento Técnico.

Forma parte del Sistema de Gobierno:

No.

Componente documentado:

Sistema de Disponibilidad.

## Objetivo

Este documento registra las decisiones de producto y arquitectura aprobadas para la ETAPA 87.

No contiene implementación.

No contiene tablas.

No contiene modelos físicos.

No contiene endpoints.

No contiene componentes frontend.

## Estado

En diseño.

## Estado público del espacio

El lenguaje oficial del estado público del espacio es exclusivamente:

- `Activo`
- `En pausa`

### Activo

`Activo` significa que el espacio está operativo y publicado en FeedGo.

Un espacio `Activo`:

- existe públicamente;
- puede aparecer en búsqueda;
- puede aparecer en Explorar;
- puede accederse desde su perfil público;
- continúa siendo público independientemente de si está `Abierto` o `Cerrado` por horario.

### En pausa

`En pausa` significa que el propietario decidió dejar de publicar temporalmente el espacio.

Un espacio `En pausa`:

- deja de aparecer públicamente;
- no debe aparecer en búsqueda;
- no debe aparecer en Explorar;
- no debe estar disponible para usuarios externos;
- puede seguir siendo visible para su propietario dentro de la administración o perfil privado.

`Activo` y `En pausa` representan publicación y visibilidad del espacio.

No representan horarios de atención.

No representan si el establecimiento está `Abierto` o `Cerrado` en ese momento.

## Horarios de atención

El propietario debe poder decidir si desea declarar horarios de atención.

Si decide declararlos, podrá cargar los días y rangos horarios habituales en los que atiende al público.

Los horarios declarados son la fuente de verdad.

El propietario no selecciona manualmente `Abierto` o `Cerrado`.

FeedGo determina automáticamente el estado comparando:

- fecha y hora actuales;
- zona horaria correspondiente;
- horarios declarados por el espacio.

## Fuente de verdad y dato derivado

### Fuente de verdad

Los horarios de atención declarados por el propietario son la fuente de verdad.

### Dato derivado

El estado horario calculado es un dato derivado.

Los valores visibles del estado horario son exclusivamente:

- `Abierto`
- `Cerrado`
- `No hay horarios declarados`

Reglas:

- Los horarios se persisten.
- El backend calcula el estado horario.
- El frontend solamente consume y representa el resultado.
- La cache puede conservar temporalmente el resultado calculado.
- La cache y el estado calculado nunca reemplazan los horarios como fuente de verdad.

## Estado horario

El lenguaje visible del estado horario es exclusivamente:

- `Abierto`
- `Cerrado`
- `No hay horarios declarados`

### Abierto

`Abierto` se muestra cuando la fecha y hora actuales se encuentran dentro de alguno de los horarios declarados.

Debe mostrarse en verde.

También debe mostrarse el horario correspondiente escrito, incluyendo las horas.

Ejemplo conceptual:

`Abierto · 08:00 a 12:00`

### Cerrado

`Cerrado` se muestra cuando existen horarios declarados, pero la fecha y hora actuales se encuentran fuera de ellos.

Debe mostrarse en rojo.

También debe mostrarse información horaria escrita que ayude a interpretar el estado, sin inventar información.

Ejemplo conceptual:

`Cerrado · Abre a las 16:00`

La redacción exacta será definida durante el diseño de UX, pero siempre deberá incluir información horaria cuando pueda calcularse correctamente.

### No hay horarios declarados

`No hay horarios declarados` se muestra cuando el propietario no configuró horarios.

Debe mostrarse en gris.

No debe interpretarse como `Abierto` ni como `Cerrado`.

## Ubicación visual

En el perfil del espacio ya existe un sector donde se muestra:

- burbuja verde para `Activo`;
- burbuja roja para `En pausa`, visible para el propietario.

En ese mismo sector deberá incorporarse, como información independiente, el estado calculado según los horarios:

- verde: `Abierto` y horario escrito;
- rojo: `Cerrado` e información horaria escrita;
- gris: `No hay horarios declarados`.

Los dos indicadores deben convivir sin mezclarse:

- estado de publicación: `Activo` / `En pausa`;
- estado horario: `Abierto` / `Cerrado` / `No hay horarios declarados`.

## Comportamiento en búsqueda

Durante ETAPA 87, el estado horario es únicamente información contextual para el usuario.

Durante ETAPA 87, el estado horario no participa en:

- filtros;
- ranking;
- exclusión de resultados.

Esta decisión no constituye una restricción permanente del buscador.

Una etapa futura podrá incorporar búsquedas específicas relacionadas con horarios sin contradecir esta decisión.

Un espacio `Activo` debe aparecer en la búsqueda aunque esté `Cerrado` por horario.

El resultado puede mostrar:

- `Abierto`;
- `Cerrado`;
- `No hay horarios declarados`;
- información horaria correspondiente.

Un espacio `En pausa` no debe aparecer públicamente, independientemente de los horarios que tenga guardados.

Regla:

```text
Activo:
puede aparecer públicamente, esté Abierto o Cerrado.

En pausa:
no aparece públicamente.
```

## Separación de responsabilidades

- `Activo` y `En pausa` pertenecen al estado de publicación del espacio.
- Los horarios pertenecen al Sistema de Disponibilidad.
- `Abierto` y `Cerrado` son resultados calculados.
- El frontend no calcula ni inventa el estado horario por su cuenta.
- El backend debe ser propietario de la regla de cálculo.
- La cache puede conservar el resultado calculado, pero no reemplaza a los horarios como fuente de verdad.
- El estado horario no modifica automáticamente `Activo` o `En pausa`.
- Pasar un espacio de `Activo` a `En pausa` no elimina ni modifica sus horarios.
- `En pausa` solamente cambia la publicación y visibilidad del espacio.
- Al volver de `En pausa` a `Activo`, se reutilizan los horarios existentes.
- El estado público del espacio y la configuración de horarios son dominios separados.

## Alcance de ETAPA 87

Pertenece a ETAPA 87:

- activación opcional de horarios;
- carga de horarios habituales;
- cálculo de `Abierto` o `Cerrado`;
- estado `No hay horarios declarados`;
- exposición del horario escrito;
- visualización en el perfil;
- futura exposición informativa en resultados de búsqueda;
- cache del resultado cuando corresponda.

No pertenece a ETAPA 87:

- turnos;
- agenda;
- reservas;
- cupos;
- disponibilidad por profesional;
- disponibilidad por servicio;
- stock;
- inventario;
- feriados automáticos;
- excepciones avanzadas;
- bloqueos de calendario;
- cambios de ranking por estar `Abierto` o `Cerrado`;
- exclusión de resultados por horario.

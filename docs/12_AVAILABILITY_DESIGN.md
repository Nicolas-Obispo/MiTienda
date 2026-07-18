# Availability Design

Categoria:

Documento Tecnico.

Forma parte del Sistema de Gobierno:

No.

Componente documentado:

Sistema de Disponibilidad.

## Objetivo

Este documento describe el diseno tecnico vigente del Sistema de Disponibilidad de FeedGo y su estado implementado luego del cierre de ETAPA 87.

No reemplaza a `04_CURRENT_STAGE.md`.

No reemplaza al roadmap.

No reemplaza al CHANGELOG.

No es un historial de cambios.

## Estado

ETAPA 87 cerrada.

El Sistema de Disponibilidad esta implementado como capacidad informativa para horarios habituales semanales de comercios.

La etapa actual siguiente es ETAPA 88 - Agenda y Reservas, registrada como pendiente en el roadmap.

## Responsabilidad del sistema

Availability modela unicamente horarios habituales semanales de atencion del comercio.

El sistema permite:

- declarar franjas horarias por dia de la semana;
- declarar varias franjas en un mismo dia;
- eliminar todos los horarios mediante una lista vacia;
- calcular si el comercio esta `abierto`, `cerrado` o `sin_horarios`;
- generar texto contextual listo para mostrar;
- exponer el estado horario como dato informativo en respuestas existentes.

El propietario declara horarios.

El backend calcula el estado.

El frontend representa el resultado.

## Estado publico del espacio

El lenguaje oficial del estado publico del espacio es exclusivamente:

- `Activo`
- `En pausa`

`Activo` significa que el espacio esta publicado en FeedGo.

Un espacio `Activo`:

- existe publicamente;
- puede aparecer en busqueda;
- puede aparecer en Explorar;
- puede accederse desde su perfil publico;
- continua siendo publico aunque este `cerrado` por horario.

`En pausa` significa que el propietario decidio dejar de publicar temporalmente el espacio.

Un espacio `En pausa`:

- deja de aparecer publicamente;
- no debe aparecer en busqueda;
- no debe aparecer en Explorar;
- no debe estar disponible para usuarios externos;
- puede seguir siendo visible para su propietario dentro de la administracion o perfil privado.

`Activo` y `En pausa` representan publicacion y visibilidad.

No representan horarios de atencion.

No representan si el establecimiento esta abierto o cerrado en ese momento.

## Fuente de verdad

Los horarios de atencion declarados por el propietario son la fuente de verdad del Sistema de Disponibilidad.

El estado horario calculado es un dato derivado.

Reglas:

- los horarios se persisten;
- el backend calcula el estado horario;
- el frontend no calcula horarios, proximas aperturas ni textos contextuales;
- la cache puede conservar temporalmente el resultado calculado;
- la cache y el estado calculado nunca reemplazan a los horarios declarados como fuente de verdad;
- pausar un comercio no elimina ni modifica sus horarios;
- reactivar un comercio reutiliza los horarios existentes.

## Modelo de datos implementado

La tabla implementada es:

```text
comercios_horarios_atencion
```

Clasificacion:

- fuente de verdad;
- configuracion operativa declarada por el propietario;
- no es cache;
- no es indice;
- no es analitica;
- no es historica;
- no es IA.

Responsabilidad:

- persistir franjas semanales habituales de atencion de un comercio.

Campos principales:

- `id`;
- `comercio_id`;
- `dia_semana`;
- `hora_apertura`;
- `hora_cierre`;
- timestamps segun la convencion real del backend.

Reglas fisicas y de dominio:

- `comercio_id` referencia a `comercios.id`;
- la eliminacion del comercio elimina sus horarios en cascada;
- `dia_semana` usa `0 = lunes` hasta `6 = domingo`;
- `hora_apertura` debe ser menor que `hora_cierre`;
- no se permiten cruces de medianoche;
- pueden existir varias franjas por comercio y dia;
- ausencia de filas significa que no hay horarios declarados;
- los solapamientos se validan en el servicio, no mediante una relacion ORM innecesaria en `Comercio`.

La tabla esta registrada en el mecanismo real de creacion de tablas del proyecto y fue validada contra `Base.metadata` y MySQL durante el cierre tecnico de ETAPA 87.

## Arquitectura backend implementada

El modulo backend vive en:

```text
backend/app/modules/availability/
```

Estructura funcional:

- modelos ORM para persistencia de franjas;
- schemas Pydantic para request y response;
- servicio de lectura, reemplazo, validacion y calculo;
- router FastAPI para los endpoints oficiales.

El backend es propietario de:

- validacion de reglas de dominio;
- rechazo de solapamientos;
- rechazo de cruces de medianoche;
- reemplazo completo de configuracion;
- calculo del estado horario;
- calculo de cierre actual y proxima apertura;
- generacion del texto contextual listo para mostrar.

La zona horaria oficial inicial es:

```text
America/Argentina/Buenos_Aires
```

La implementacion usa `ZoneInfo`.

El fallback UTC-03:00 existe solo como proteccion controlada cuando la infraestructura de zona horaria no esta disponible.

## Estados horarios

El contrato tecnico usa valores internos en minuscula:

- `abierto`;
- `cerrado`;
- `sin_horarios`.

Los textos publicos son generados por backend.

Ejemplos:

- `Abierto · Hasta las 20:00`;
- `Cerrado · Abre a las 16:00`;
- `Cerrado · Abre mañana a las 08:00`;
- `No hay horarios declarados`.

El frontend debe mostrar el texto recibido.

No debe reconstruirlo.

## Endpoints implementados

Los endpoints oficiales son:

```text
GET /comercios/{comercio_id}/horarios
PUT /comercios/{comercio_id}/horarios
```

No existen endpoints adicionales para esta capacidad.

No forman parte del diseno de ETAPA 87:

- `DELETE`;
- `PATCH`;
- `/availability`;
- rutas administrativas nuevas;
- rutas por agenda o reservas.

### GET

`GET /comercios/{comercio_id}/horarios` devuelve la configuracion completa de horarios y el estado calculado.

Reglas:

- responde para comercios activos publicos;
- no expone publicamente comercios en pausa;
- permite al propietario consultar sus comercios en pausa cuando existe autenticacion aplicable;
- devuelve `404` cuando el comercio no existe;
- devuelve `404` para consulta publica de comercio en pausa.

### PUT

`PUT /comercios/{comercio_id}/horarios` reemplaza la configuracion completa.

Reglas:

- requiere autenticacion;
- requiere que el usuario sea propietario del comercio;
- acepta multiples franjas;
- acepta `franjas=[]` para eliminar todos los horarios declarados;
- no modifica `Comercio.activo`;
- devuelve la configuracion persistida y el estado calculado posterior al guardado.

## Contrato de respuesta

El contrato envolvente de horarios contiene:

```text
comercio_id
zona_horaria
franjas
estado_horario
```

Cada franja contiene:

```text
id
dia_semana
hora_apertura
hora_cierre
```

El bloque `estado_horario` contiene:

```text
estado
texto
zona_horaria
evaluado_en
cierre_actual
proxima_apertura
```

Los campos temporales permiten `null` cuando no aplican.

Los datetimes devueltos por el backend son conscientes de zona horaria.

## Integracion backend con Spaces

Availability se integra como enriquecimiento informativo en respuestas historicas de Spaces.

Las respuestas afectadas son:

- detalle publico de comercio;
- `/comercios/mis`;
- `/comercios/activos`.

El campo agregado es:

```text
horario_atencion
```

Reglas de integracion:

- el campo es opcional;
- no cambia el significado de `activo`;
- no filtra resultados;
- no modifica ranking;
- no altera score;
- no altera el orden de busqueda;
- no excluye comercios cerrados;
- no excluye comercios sin horarios;
- en listados se calcula en lote para evitar N+1;
- el calculo batch se aplica sobre los comercios finales de la respuesta.

Compatibilidad:

- los endpoints historicos de Spaces no deben romperse si Availability falla temporalmente por infraestructura;
- en ese caso, el enriquecimiento puede degradar a `horario_atencion = null`;
- los endpoints propios de Availability conservan sus errores normales;
- no se devuelve `sin_horarios` cuando el problema real es infraestructura.

## Integracion frontend implementada

El frontend consume el estado horario entregado por backend.

Componentes y flujos implementados:

- badge reutilizable de estado horario;
- visualizacion en perfil publico del comercio;
- visualizacion en vista privada del propietario;
- visualizacion informativa en Explorar cuando existe espacio visual adecuado;
- editor privado de horarios semanales;
- acceso al editor desde el flujo de edicion del comercio.

El editor:

- carga la configuracion completa mediante `GET /comercios/{comercio_id}/horarios`;
- guarda mediante `PUT /comercios/{comercio_id}/horarios`;
- permite varias franjas por dia;
- permite eliminar franjas;
- permite guardar `franjas=[]`;
- usa identidad local estable para franjas nuevas durante la edicion;
- no envia campos auxiliares frontend al backend;
- mantiene validaciones UX sin reemplazar la autoridad del backend;
- oculta temporalmente el mapa de ubicacion mientras esta abierto para evitar superposicion visual.

El frontend no debe:

- usar `Date` para calcular disponibilidad;
- usar la zona horaria del navegador;
- buscar proxima apertura;
- interpretar dias;
- construir textos como `abre mañana`;
- decidir si un comercio esta abierto o cerrado.

## Comportamiento en busqueda y Explorar

Durante ETAPA 87, el estado horario es unicamente contextual.

No participa en:

- filtros;
- ranking;
- exclusion de resultados;
- score;
- reordenamiento.

Un comercio `Activo` puede aparecer publicamente aunque este `cerrado` por horario.

Un comercio `En pausa` no debe aparecer publicamente aunque tenga horarios cargados.

Esta decision no impide que una etapa futura incorpore busquedas especificas relacionadas con horarios.

## Reglas oficiales de horarios

Reglas implementadas para ETAPA 87:

- los horarios son semanales y habituales;
- cada franja pertenece a un dia de la semana;
- una franja no puede terminar al dia siguiente;
- `hora_apertura` debe ser menor que `hora_cierre`;
- los cruces de medianoche se rechazan explicitamente;
- no se interpretan ni corrigen automaticamente cruces de medianoche;
- las franjas contiguas estan permitidas;
- las franjas solapadas se rechazan;
- la semana se evalua circularmente de domingo a lunes;
- la misma referencia temporal se usa para calculos batch;
- no se consideran feriados ni excepciones.

## Fuera de alcance de ETAPA 87

No pertenecen al Sistema de Disponibilidad implementado en ETAPA 87:

- agenda;
- reservas;
- turnos;
- cupos;
- profesionales;
- calendarios de profesionales;
- disponibilidad por servicio;
- horarios independientes por servicio;
- productos;
- inventario;
- stock;
- feriados;
- excepciones por fecha;
- cierres extraordinarios;
- bloqueos de calendario;
- cruces de medianoche;
- filtros por abierto o cerrado;
- ranking por disponibilidad;
- exclusion de resultados por horario.

ETAPA 88 continua siendo Agenda y Reservas.

## Deuda diferida

La deuda visual no bloqueante queda diferida a ETAPA 101 - Unificacion del Design System.

Incluye:

- unificacion visual de botones secundarios restantes;
- revision de alineaciones;
- revision de espaciados;
- consistencia de hover, focus y active;
- consistencia de iconografia;
- jerarquia visual;
- formularios;
- responsive.

Esta deuda no modifica el contrato ni el alcance funcional del Sistema de Disponibilidad.

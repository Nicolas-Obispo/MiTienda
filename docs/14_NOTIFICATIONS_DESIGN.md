# Diseno del Sistema de Notificaciones

Estado del documento: Documento Tecnico Oficial de FeedGo v1.0.
Version: 1.0.
Categoria: Documento Tecnico.
Nivel de autoridad: Tecnico especializado para sistema transversal de
notificaciones y frontera futura con comunicaciones externas.
Documento dueno: `docs/14_NOTIFICATIONS_DESIGN.md`.
Responsable funcional: Notificaciones y comunicaciones futuras.
Documentos relacionados: `00_GOVERNANCE.md`, `01_ENGINEERING.md`,
`02_PRODUCT.md`, `05_SEARCH_ROADMAP.md`,
`13_AGENDA_RESERVATIONS_DESIGN.md`, `15_LEGAL_AND_OPERATIONAL.md`.
Cuando debe consultarse: antes de disenar o implementar notificaciones
locales, campana global, preferencias de notificacion, eventos notificables,
correo, WhatsApp, verificacion de destinos, proveedores de comunicaciones,
plantillas, reintentos, webhooks o capacidades comerciales asociadas a canales.

## Estado

Diseno aprobado, no implementado.

Este documento nace durante ETAPA 88 - Agenda y Reservas, luego de Agenda
Core, integracion FeedGo-Agenda, Agenda privada y Agenda general implementadas
a nivel tecnico, y antes de Reservas publicas.

ETAPA 88 esta cerrada y su alcance no incluye implementacion de
notificaciones.

Roadmap vigente:

- ETAPA 103 - Mensajeria y Cotizaciones: comunicaciones externas, correo,
  WhatsApp, proveedores, verificacion de destinos, plantillas, reintentos y
  webhooks.
- ETAPA 107 - Notificaciones Inteligentes: notificaciones locales, campana
  global, preferencias, integraciones locales e inteligencia futura de
  notificaciones.

No implementa:

- backend;
- frontend;
- tablas;
- campana;
- correo;
- WhatsApp;
- verificacion real por codigo;
- proveedores;
- workers;
- colas;
- schedulers productivos;
- pagos;
- planes comerciales;
- Reservas publicas.

## Necesidad de producto

Agenda general debera incorporar, cuando corresponda por alcance, un acceso
denominado:

```text
Configurar notificaciones
```

Ese acceso debera abrir una capa secundaria compacta sobre Agenda general. La
Agenda general no debe cerrarse ni reemplazarse innecesariamente. Mientras la
capa secundaria este activa, el fondo debe permanecer visible pero bloqueado
para interaccion y scroll.

La configuracion conceptual contempla tres canales:

1. notificacion local dentro de FeedGo;
2. correo electronico;
3. WhatsApp.

La notificacion local queda diferida fuera del cierre actual de ETAPA 88.

Correo electronico y WhatsApp quedan como diseno futuro trazable, fuera de la
implementacion actual.

## Veredicto arquitectonico

La propuesta tiene sentido dentro de FeedGo, pero debe dividirse en dos
capacidades:

- sistema transversal de notificaciones;
- infraestructura transversal de comunicaciones externas.

La notificacion local dentro de FeedGo es el canal base disenado, pero no
forma parte del cierre actual de ETAPA 88.

Agenda puede ser el primer productor de sucesos notificables, pero no es duena
del sistema de notificaciones.

Correo, WhatsApp, verificacion de destinos, proveedores, plantillas,
infraestructura asincronica, reintentos, webhooks e intentos de entrega quedan
diferidos a ETAPA 103 - Mensajeria y Cotizaciones.

## Separacion conceptual obligatoria

El diseno debe separar:

- suceso de dominio;
- notificacion interna;
- preferencia del usuario;
- notificacion local;
- destino externo;
- verificacion de destino;
- entrega de comunicacion;
- proveedor;
- intento de entrega;
- politica futura de capacidades.

Un evento de Agenda, una futura reserva o una cancelacion no son por si mismos
una notificacion ni un mensaje enviado.

El dominio emisor produce o expone un suceso. El sistema de notificaciones
decide si corresponde generar una notificacion interna, para que usuario, con
que estado, con que relacion a la entidad de origen y respetando preferencias.

Cuando existan comunicaciones externas, el sistema de notificaciones podra
solicitar una comunicacion a la infraestructura correspondiente mediante un
contrato estable. No debera enviar correo ni WhatsApp por su cuenta.

## Sistema transversal de notificaciones

Responsabilidades:

- decidir que suceso genera una notificacion;
- identificar destinatario;
- definir contenido conceptual;
- resolver preferencias del usuario;
- evaluar canales habilitados;
- consultar una politica futura de capacidades cuando exista;
- persistir y exponer notificaciones locales;
- administrar estados de notificacion local;
- relacionar la notificacion con la entidad de origen;
- sostener campana, contador, listado y marcado como leido.

No es responsable de:

- enviar correo real;
- enviar WhatsApp real;
- integrar proveedores externos;
- verificar destinos externos;
- gestionar plantillas externas;
- procesar webhooks de proveedor;
- ser dueno de planes, pagos, precios, suscripciones o facturacion.

## Infraestructura transversal de comunicaciones externas

Responsabilidad futura:

- enviar correo electronico;
- enviar mensajes de WhatsApp;
- integrar proveedores externos;
- normalizar destinos externos;
- verificar correo o telefono;
- gestionar plantillas;
- registrar intentos de entrega;
- procesar reintentos;
- aplicar idempotencia de envio;
- interpretar respuestas o webhooks del proveedor;
- exponer contratos reutilizables para otros modulos.

Esta infraestructura no debe implementarse exclusivamente para Agenda.

Debera poder ser consumida por:

- autenticacion;
- recuperacion o proteccion de cuenta;
- verificacion de identidad o contacto;
- Agenda;
- Reservas;
- Comercios;
- alertas de seguridad;
- comunicaciones operativas;
- futuras funciones del producto.

Cada proveedor debera tener un unico adaptador oficial.

Cada tipo de destino verificado debera tener un unico dueno natural.

Los modulos consumidores deberan solicitar operaciones mediante contratos
estables, sin conocer detalles internos del proveedor.

Operaciones conceptuales futuras:

- solicitar verificacion de un destino;
- validar un codigo;
- enviar una comunicacion basada en una plantilla;
- consultar el estado de una entrega;
- revocar o reemplazar un destino.

No se fijan todavia nombres definitivos de clases, endpoints ni tablas.

## Responsabilidades por modulo

### Agenda

Agenda administra organizacion privada:

- eventos;
- tareas;
- recordatorios;
- bloqueos;
- solapamientos tecnicos informativos.

Agenda puede producir sucesos notificables, pero no envia mensajes, no conoce
proveedores, no almacena preferencias transversales y no decide capacidades
comerciales.

### Reservas

Reservas administrara solicitudes publicas, estados, cambios, cancelaciones y
reprogramaciones cuando su diseno sea aprobado.

Reservas podra producir sucesos notificables, pero no debe enviar por canales
externos directamente.

### FeedGo

FeedGo es la aplicacion host inicial.

FeedGo es dueno natural de:

- campana global autenticada;
- experiencia local de notificaciones;
- navegacion hacia pantallas o capas existentes;
- integracion entre notificaciones locales y rutas reales de la aplicacion.

La campana debe pertenecer al layout global autenticado. No debe duplicarse por
pantalla ni agregarse una campana especifica de Agenda.

### Autenticacion y Perfil

Autenticacion es duena de identidad de usuario, login, password, JWT y tokens
revocados.

No existe evidencia de que `usuarios.email` este verificado para
notificaciones externas.

Perfil puede exponer datos del usuario, pero no debe absorber preferencias de
notificacion, entregas externas, proveedores ni colas.

## Destinos de contacto y verificacion

El diseno futuro debe distinguir:

- correo de identidad o inicio de sesion;
- correo de contacto;
- correo privado destinado a comunicaciones verificadas;
- WhatsApp publico de un comercio;
- telefono o WhatsApp privado verificado de un usuario.

No se debe reutilizar automaticamente `comercios.whatsapp` como destino
privado.

No se debe considerar automaticamente `usuarios.email` como habilitado para
notificaciones externas sin verificar la semantica y el estado real de
verificacion existente.

Cuando un destino existente pueda referenciarse correctamente, se debe evitar
duplicarlo.

Antes de aprobar nuevas tablas debe aplicarse nuevamente la auditoria
obligatoria del modelo de datos definida por el gobierno del proyecto.

## Modelo de datos auditado

Tablas existentes relacionadas:

- `usuarios`: fuente de verdad de identidad de usuario y email de login. No
  registra verificacion para notificaciones externas.
- `tokens_revocados`: autenticacion y sesiones revocadas. No corresponde
  reutilizarla para verificaciones ni notificaciones.
- `comercios`: fuente de verdad del espacio y datos publicos/de contacto.
  `whatsapp` es contacto publico del comercio, no destino privado verificado
  del usuario.
- `agenda_contextos_agendables`: fuente de verdad del contexto interno de
  Agenda. No debe absorber preferencias transversales.
- `agenda_elementos`: fuente de verdad de elementos privados de Agenda. No
  debe almacenar mensajes, leidos ni preferencias.
- `feedgo_agenda_contextos`: relacion Comercio-Agenda. No debe absorber
  configuracion de notificaciones.
- `search_events`: eventos de busqueda para conocimiento y analytics. No
  corresponde reutilizarlo para notificaciones.

Conclusion:

No existe una estructura propietaria natural para notificaciones locales. Una
futura implementacion podra justificar estructuras propias si la auditoria
confirma responsabilidad unica y ausencia de duplicacion.

Las estructuras de destinos verificables, desafios, intentos de entrega,
plantillas y webhooks pertenecen al diseno futuro de comunicaciones externas,
no al futuro MVP local de notificaciones.

## Diferido fuera del cierre actual de ETAPA 88

Quedan disenados, pero no implementados en el cierre actual de ETAPA 88 y
planificados para ETAPA 107 - Notificaciones Inteligentes:

- modulo transversal de notificaciones locales;
- campana global para usuarios autenticados;
- contador de notificaciones no leidas;
- listado paginado o incremental;
- marcado individual como leido;
- marcado masivo como leido;
- navegacion hacia el elemento relacionado;
- configuracion para activar o desactivar notificaciones locales;
- integracion inicial con eventos, tareas o recordatorios de Agenda;
- cache-first y actualizacion en segundo plano.

La notificacion local es una notificacion almacenada y mostrada dentro de
FeedGo.

No es:

- push del navegador;
- push movil;
- permiso del sistema operativo;
- Service Worker.

## Disenado para ETAPA 103

Quedan fuera de la implementacion de ETAPA 88 y asignados a ETAPA 103:

- envio real por correo;
- envio real por WhatsApp;
- verificacion real por codigo;
- destinos externos verificables;
- proveedores externos;
- adaptadores oficiales de proveedor;
- plantillas;
- workers;
- colas;
- schedulers productivos;
- reintentos;
- webhooks;
- observabilidad;
- intentos y resultados de entrega externa;
- capacidades comerciales para canales externos.

Durante ETAPA 88 no se implementaran codigos reales enviados por correo o
WhatsApp ni proveedores externos.

## Preferencias locales

El MVP local debe contemplar:

- canal local activado o desactivado;
- tipos de notificacion permitidos para el canal local;
- fecha de ultima modificacion;
- relacion futura con zona horaria, idioma, silenciamiento y anticipacion de
  recordatorios si la auditoria de Agenda lo justifica.

No se debe forzar una unica tabla para todos los conceptos antes de auditar el
modelo de datos vigente.

## Verificacion de destinos futura

La verificacion de correo o telefono no pertenece al futuro MVP local de
notificaciones.

Cuando se disene en ETAPA 103 debera contemplar:

- generacion segura de codigos;
- almacenamiento no reversible;
- vencimiento;
- limite de intentos;
- limite de reenvios;
- rate limiting;
- invalidacion de codigos anteriores;
- proteccion frente a enumeracion;
- proteccion frente a abuso;
- auditoria;
- cambio de correo o telefono;
- revocacion de una verificacion;
- politica para destinos ya asociados a otro usuario.

## Entrega externa futura

Correo y WhatsApp deberan depender de adaptadores reemplazables.

La infraestructura futura debera contemplar:

- contratos reutilizables;
- plantillas;
- outbox o mecanismo equivalente;
- tareas en segundo plano;
- reintentos;
- idempotencia;
- estados de entrega;
- errores permanentes;
- errores transitorios;
- registro de intentos;
- costos;
- observabilidad;
- proteccion de datos sensibles.

Agenda, Reservas y otros modulos no deberan acoplarse a proveedores.

## WhatsApp futuro

WhatsApp no debe disenarse como canal de texto libre irrestricto.

Limitaciones a considerar cuando se implemente:

- se requiere opt-in del destinatario;
- fuera de la ventana de atencion de 24 horas iniciada por el usuario, la
  empresa solo puede enviar plantillas aprobadas;
- Meta puede aprobar, pausar o rechazar plantillas;
- existen categorias como marketing, utility, authentication y service;
- la mensajeria tiene costos por mensaje entregado, mercado y categoria;
- usuarios pueden bloquear o reportar, afectando calidad y capacidad de envio;
- aplican politicas sobre datos, privacidad, rubros regulados y contenido;
- un proveedor externo puede agregar costos, reglas y estados propios.

Los recordatorios de Agenda y Reservas no deben asumirse como mensajes libres.

## Programacion temporal

La auditoria de codigo no encontro scheduler, worker, cola, Redis, Celery, RQ,
APScheduler ni proveedor equivalente.

Por lo tanto:

- no se debe prometer entrega externa exacta en segundo plano durante ETAPA 88;
- no se deben enviar recordatorios desde requests frontend;
- no se debe depender de que el usuario tenga abierta la Agenda para ejecutar
  trabajos diferidos;
- reprogramaciones y cancelaciones deberan invalidar notificaciones o entregas
  pendientes cuando exista infraestructura para ello.

El futuro MVP local de notificaciones debe limitarse a lo que pueda sostenerse
sin inventar infraestructura externa inexistente.

## Eventos notificables

Tipos iniciales contemplados para notificaciones locales:

- eventos de Agenda;
- tareas;
- recordatorios;
- bloqueos solo cuando exista necesidad funcional real.

Tipos futuros:

- reservas;
- cambios relevantes de reserva;
- cancelaciones;
- reprogramaciones;
- alertas de seguridad;
- comunicaciones operativas.

No todos los tipos deben notificarse igual.

## Experiencia de usuario

La UI futura debe respetar ActiveLayer y el Design System vigente.

Para la futura implementacion local:

- boton `Configurar notificaciones` en Agenda general;
- ventana secundaria compacta;
- fondo bloqueado para scroll e interaccion;
- foco atrapado en la capa activa;
- restauracion de foco al cerrar;
- `focus-visible`;
- `Cerrar`, `Atras` y `Cancelar` segun corresponda;
- proteccion ante cambios sin guardar;
- control para activar o desactivar notificaciones locales;
- mensajes de estado claros;
- mobile y desktop;
- no cerrar accidentalmente Agenda general;
- no perder datos ya cargados.

Los campos de correo, WhatsApp, ingreso de codigo y reenvio con espera
controlada pertenecen a etapas futuras.

## Preparacion para monetizacion futura

La arquitectura futura debe permitir que una politica externa determine
capacidades como:

- notificaciones locales;
- notificaciones por correo;
- notificaciones por WhatsApp;
- limites mensuales;
- prioridad de entrega;
- retencion;
- plantillas o automatizaciones avanzadas.

Hoy no existen planes pagos y no debe bloquearse ningun canal mediante logica
comercial.

No utilizar condiciones rigidas como:

```text
if premium
```

El sistema de notificaciones y la infraestructura de comunicaciones no seran
duenos de suscripciones, precios ni facturacion.

## Riesgos

Tecnicos:

- crear campanas duplicadas;
- acoplar Agenda al sistema transversal;
- mezclar notificacion local con push;
- disenar tablas antes de auditar el modelo;
- prometer comunicaciones externas sin infraestructura.

Seguridad:

- exponer datos privados en notificaciones;
- conceder canales por defecto sin preferencia clara;
- fuerza bruta futura de codigos;
- enumeracion futura de destinos;
- webhooks futuros sin validacion.

Privacidad y legales:

- consentimiento insuficiente;
- opt-out no respetado;
- tratamiento de datos personales;
- contenido sensible en email o WhatsApp;
- politicas de WhatsApp y rubros regulados.

Economicos:

- costos variables futuros por mensaje;
- abuso de reenvios;
- proveedores pagos;
- plantillas mal categorizadas.

Operativos:

- monitoreo de colas futuras;
- gestion de plantillas;
- soporte ante entregas fallidas;
- rotacion de credenciales;
- reputacion de remitentes.

UX:

- exceso de configuracion;
- estados poco claros;
- cierre accidental de Agenda;
- perdida de cambios;
- duplicacion visual de campanas.

## Mapa de trabajo

ETAPA 107 - Notificaciones Inteligentes:

1. Diseno detallado del MVP de notificaciones locales.
2. Implementacion del sistema transversal de notificaciones locales.
3. Implementacion de campana global.
4. Configuracion para activar o desactivar el canal local.
5. Integracion local minima con sucesos de Agenda.
6. Validacion final del alcance ejecutado.

ETAPA 103 - Mensajeria y Cotizaciones:

- servicio transversal de correo;
- servicio transversal de WhatsApp;
- destinos verificables;
- codigos de verificacion;
- consentimiento y revocacion;
- adaptadores de proveedores;
- plantillas;
- infraestructura asincronica;
- reintentos;
- idempotencia;
- estados e intentos de entrega;
- webhooks;
- observabilidad;
- politicas de capacidades comerciales.

Justificacion:

ETAPA 103 existe como etapa futura de Mensajeria y es el dueno natural mas
cercano para comunicaciones externas. Crear una etapa nueva antes de activar
ETAPA 103 aumentaria la fragmentacion del roadmap sin evidencia suficiente.

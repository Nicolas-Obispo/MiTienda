# Product

Estado del documento: Documento Oficial del Sistema de Gobierno FeedGo v1.0.
Version: 1.0.
Categoria: Sistema de Gobierno.
Nivel de autoridad: Alto para vision, alcance, experiencia y criterios de
producto.
Documento dueno: `docs/02_PRODUCT.md`.
Responsable funcional: Producto.
Documentos relacionados: `00_GOVERNANCE.md`, `05_SEARCH_ROADMAP.md`,
`07_DECISIONS.md`, `15_LEGAL_AND_OPERATIONAL.md`,
`18_PWA_ENTERPRISE.md`, `26_CLASSIFIEDS_CONTRACT.md`,
`27_COMMERCIAL_PLATFORM_CONTRACT.md`.
Cuando debe consultarse: antes de definir alcance funcional, experiencia de
usuario, jerarquia visual, datos solicitados al usuario o cambios de producto.

## Visión

- FeedGo conecta personas, necesidades y soluciones.
- FeedGo no es únicamente un marketplace.
- Debe servir para comercios, profesionales, oficios y servicios.
- El buscador es la capacidad principal del producto.
- FeedGo nace como vidriera digital y motor de descubrimiento, y evoluciona
  hacia una plataforma de presencia digital, descubrimiento y administracion de
  espacios.
- La administracion de espacios debe poder contemplar, en etapas futuras,
  personas que gestionan multiples espacios propios o de terceros.
- FeedGo es una aplicacion multiplataforma.
- Su primer canal oficial de distribucion sera una Progressive Web App (PWA).
- La aplicacion web no constituye un producto diferente ni una version
  temporal previa a aplicaciones moviles futuras.

## Casos de uso de administracion multi-espacio

FeedGo debe poder evolucionar para servir a:

- agencias de marketing;
- community managers;
- freelancers;
- disenadores;
- administradores de multiples clientes;
- franquicias;
- cadenas comerciales.

Una persona podra administrar multiples espacios propios o de terceros mediante
futuros permisos y delegaciones.

Esta vision no convierte a FeedGo en marketplace ni habilita automaticamente
roles, permisos empresariales, planes comerciales, facturacion, pagos o
administracion avanzada sin una etapa aprobada.

## Mi cuenta y ownership actual

La cuenta pertenece al usuario que la creo.

Los espacios creados desde esa cuenta permanecen vinculados a ese usuario.

Con el ownership actual, una misma cuenta ya puede administrar multiples
espacios. Esos espacios pueden representar negocios propios, clientes,
franquicias, cadenas, servicios profesionales o proyectos administrados por la
misma persona.

La comunicacion de producto debe evitar presentar la cuenta como si solo
representara a un consumidor individual.

Todavia no existen:

- transferencia de espacios entre cuentas;
- delegacion de administracion;
- colaboradores;
- permisos compartidos;
- roles empresariales.

Esas capacidades pertenecen a una etapa futura y requieren diseno especifico de
permisos, ownership, seguridad y operacion.

## Identidad personal y alta de espacios

Una cuenta personal FeedGo permite explorar, interactuar, guardar, seguir y
usar capacidades personales presentes o futuras sin exigir que la persona cree
un espacio.

El registro general debe tender a minima friccion y solicitar solamente datos
necesarios para identidad y funcionamiento de la cuenta. Crear o administrar un
espacio es un proceso separado, con sus propios datos comerciales,
profesionales, territoriales y operativos.

`Usuario FeedGo` es la identidad central. Los metodos de acceso presentes o
futuros, incluidos email/password, email verificado o Google, se vinculan a esa
identidad y no crean por si mismos cuentas funcionales paralelas. La decision
arquitectonica y su etapa futura se registran en `DEC-048` y
`docs/05_SEARCH_ROADMAP.md`.

## Principios de Producto

- Pedir la menor cantidad posible de información estructurada.
- Obtener la mayor cantidad posible de conocimiento mediante indexación.
- No cansar al usuario con formularios largos.
- El usuario no debe completar datos que el sistema pueda inferir con alta confianza.
- Guiar al usuario mediante ayudas contextuales.
- Cada dato solicitado debe aportar valor al buscador.
- La experiencia instalada debe comportarse como una aplicacion, con
  navegacion, carga, teclado, safe areas, overlays, actualizacion y recuperacion
  coherentes con una aplicacion movil.

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

## Verticales FeedGo

FeedGo integra dos verticales de primer nivel: FeedGo Espacios y FeedGo
Clasificados. Clasificados no es una aplicacion, identidad o base de usuarios
separada. Existe una unica cuenta FeedGo; un usuario puede publicar Clasificados
sin crear un Espacio y un visitante anonimo puede navegar, buscar, filtrar,
abrir contenido y utilizar el contacto publico habilitado.

Clasificados conecta comprador y vendedor, pero FeedGo no intermedia la
compraventa entre particulares. El contrato inicial no incluye checkout del
bien, carrito transaccional, escrow, custodia de fondos, logistica ni envios.
WhatsApp puede ser el contacto principal mediante un contrato publico
minimizado; FeedGo no necesita leer la conversacion externa.

Clasificados es globalmente navegable. Pais, provincia, ciudad y distancia
pueden informar, filtrar, ordenar o aportar una senal de ranking, pero no
restringen por defecto el inventario publico como ocurre con el contexto
territorial de Espacios.

El usuario no debe cargar innecesariamente el mismo contenido para una
Publicacion, un Clasificado y una Historia. FeedGo debe reutilizar media y datos
compatibles y pedir solo los complementarios, manteniendo una fuente de verdad
por dato, lifecycle independiente por superficie y propagaciones explicitas
decididas por backend.

La creacion de Clasificados se apoya en schemas estructurados por categoria.
Creacion manual e IA asistida consumen el mismo contrato: la IA propone,
backend valida, el usuario revisa y confirma, y recien entonces se publica e
indexa. La IA nunca es fuente de verdad ni publica por si sola.

Clasificados contempla contenido organico, destacado y premium como estados de
promocion separados del contenido. La promocion se aplica solo despues de
pertinencia y, al vencer, el mismo Clasificado vuelve a comportamiento organico
sin eliminarse ni pausarse. Historias de Clasificados conservan entidad y
lifecycle propios y navegan al Clasificado correspondiente.

Comentarios de Clasificados quedan expresamente posteriores a la primera
apertura publica. No se anticipa infraestructura especulativa para esa capacidad.

## Estado público y disponibilidad

- El estado público del espacio usa exclusivamente `Activo` y `En pausa`.
- `Activo` y `En pausa` representan publicación y visibilidad del espacio, no horarios de atención.
- Los horarios de atención pertenecen al Sistema de Disponibilidad.
- El estado horario visible usa exclusivamente `Abierto`, `Cerrado` y `No hay horarios declarados`.
- Un espacio `Activo` continúa siendo público aunque esté `Cerrado` por horario.

## Agenda y Reservas

- La Agenda es una herramienta privada de organizacion del propietario.
- Agenda y Reservas son conceptos distintos.
- La Agenda administra organizacion: eventos, tareas, recordatorios, bloqueos,
  turnos y reservas reflejadas.
- Las Reservas utilizan Agenda, pero no son la Agenda completa.
- Availability, Agenda y Reservas deben permanecer separadas.
- No todos los espacios habilitan reservas publicas.
- Mi Perfil es el punto de entrada inicial a Agenda, pero Agenda no pertenece a
  Mi Perfil.
- La vista inicial de Agenda es `Hoy`, en formato cronologico.
- Vista Semana, Vista Mes y persistencia de ultima vista, filtros o contexto
  quedan como evolucion futura.
- El cliente nunca debe ver la agenda privada completa del propietario.
- Agenda general podra exponer `Configurar notificaciones` como acceso inicial
  a la configuracion de notificaciones del usuario.
- Las notificaciones son una capacidad transversal de FeedGo, no una
  funcionalidad exclusiva de Agenda.
- La notificacion local dentro de FeedGo es el canal base futuro, pero queda
  fuera del cierre actual de ETAPA 88.
- Correo electronico y WhatsApp son canales futuros; requieren una
  infraestructura transversal de comunicaciones, verificacion de destino,
  consentimiento y configuracion independiente antes de habilitarse.

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
- Feed e Historias siguen siendo descubrimiento local mixto: seguir una cuenta
  aporta afinidad, pero no elimina contenido local relevante. Novedad,
  exposicion previa, diversidad, cercania y relevancia deben poder intervenir
  en el ranking backend para evitar repeticion constante.
- La monetizacion futura debe expresarse mediante politicas de capacidades y no
  mediante condiciones dispersas en pantallas o dominios. La cantidad de
  espacios administrables puede ser una capacidad futura, no un limite vigente
  definido por este documento.
- La preparacion arquitectonica para monetizacion es transversal y comienza
  antes de activar cobros: los contratos de usuarios, espacios, permisos,
  Clasificados, promociones, publicidad, features habilitables y limites de uso
  no deben asumir de forma irreversible que toda capacidad sera siempre gratuita
  e ilimitada. Preservar esa extensibilidad no autoriza planes, restricciones,
  pagos ni suscripciones antes de su etapa aprobada.
- La capacidad tecnica comercial aprobada, incluidos Payments y Billing, debe
  quedar realmente operativa dentro de sus etapas owner; no alcanza con
  interfaces vacias, placeholders o adapters ficticios como solucion final.
  La politica comercial decide por separado precios, gratuidad, beneficios,
  campanas y activacion efectiva.
- La facturacion de capacidades pagas debe permanecer desacoplada. FeedGo
  conserva planes, identidad y reglas funcionales; un componente o proveedor
  reemplazable recibe solo los datos minimos necesarios para emitir documentos
  fiscales y no se convierte en owner del negocio. Existe un unico Billing
  transversal para Espacios, Clasificados, Advertising, promociones y futuras
  capacidades aprobadas.

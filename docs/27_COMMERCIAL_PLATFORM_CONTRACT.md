# Contrato tecnico de Plataforma Comercial FeedGo

Estado del documento: Documento Tecnico oficial, implementacion no iniciada.
Categoria: Documento Tecnico.
Documento dueno: `docs/27_COMMERCIAL_PLATFORM_CONTRACT.md`.
Responsable funcional: Plataforma Comercial, Payments y Billing.
Documentos relacionados: `01_ENGINEERING.md`, `02_PRODUCT.md`,
`05_SEARCH_ROADMAP.md`, `15_LEGAL_AND_OPERATIONAL.md`,
`26_CLASSIFIEDS_CONTRACT.md`.
Cuando debe consultarse: antes de disenar o implementar capacidades,
promociones, Advertising, pagos, facturacion o providers comerciales.

## Frontera transversal

FeedGo posee una unica plataforma comercial reutilizable por Espacios,
Clasificados, Advertising, promociones y futuras capacidades aprobadas. No se
crean Payments o Billing independientes por vertical.

Los dominios producen operaciones y conceptos comerciales. La plataforma
comercial gobierna catalogo de capacidades, ordenes, pagos, referencias,
idempotencia y facturacion. Cada dominio conserva sus reglas y activa su
capacidad solo despues de una confirmacion confiable.

## Preparacion, capacidad y politica

Preservar extensibilidad no activa monetizacion. Sin embargo, las etapas
preparatorias aprobadas deben dejar Payments y Billing realmente operativos y
validados, no interfaces vacias, TODOs, placeholders ni adapters ficticios como
solucion final.

La capacidad tecnica construida se separa de la politica comercial activa.
Precios, gratuidad, beneficios, campanas, descuentos y disponibilidad son
decisiones configurables. Una capacidad puede estar lista y permanecer gratis,
bonificada o desactivada.

## Advertising

Advertising es un dominio transversal independiente; no representa anuncios
mediante Clasificados falsos. Gobierna campanas, creatividades, superficies,
vigencia, moderacion y metricas. Una superficie se muestra solo cuando tiene
campanas activas; sin campana no deja un bloque vacio.

## Beneficios promocionales

Beneficios y cupones pueden apoyar adquisicion, registro, publicacion, creacion
de Espacio, campanas y fidelizacion. No son dinero, no se retiran, no se
transfieren por defecto, no se reembolsan, son expirables, trazables y se
consumen idempotentemente. No constituyen billetera ni saldo financiero.

## Payments

Payments debe soportar operaciones comerciales reales aprobadas mediante:

- provider desacoplado seleccionado con evidencia;
- ordenes, intentos, estados y referencias propias;
- idempotencia;
- webhook autenticado y verificado cuando corresponda;
- conciliacion y recuperacion de estados;
- activacion exactamente una vez;
- no almacenamiento de datos sensibles de tarjetas;
- secretos y configuracion backend.

El provider no decide negocio ni activa directamente una entidad del dominio.

El flujo interno se especializa como:

`CommercialOperation -> PaymentOrder -> PaymentProvider -> referencia externa
-> callback/webhook verificado -> estado interno idempotente -> FeedGo
confirma o activa la capacidad`.

FeedGo conserva operacion, importe, moneda, concepto, beneficiario,
`idempotency_key`, estado, conciliacion, relacion con entitlement o promocion y
decision final. El provider nunca activa directamente Premium, Destacado ni
otra regla del producto.

## Billing unico

Billing es un unico owner transversal. Espacios, Clasificados, Advertising y
otras capacidades generan conceptos facturables, pero no sistemas fiscales
paralelos.

El `InvoiceProvider` es reemplazable, no accede a DB FeedGo, no recibe
credenciales, no consulta tablas y recibe solo los datos minimos necesarios.
FeedGo conserva en su DB referencias, estados, trazabilidad y decisiones
funcionales.

El flujo de facturacion es `CommercialOperation confirmada -> BillingService
-> InvoiceProvider`. FeedGo conserva sujeto facturable, concepto, importe,
relacion con la operacion, estado, referencia externa, reintentos e idempotencia.
Billing permanece interno, unico y transversal; no se construye una plataforma
fiscal universal para aplicaciones hipoteticas.

## Flujo conceptual

`Dominio -> operacion comercial -> catalogo/capacidad -> orden -> PaymentProvider -> confirmacion -> activacion del dominio -> Billing -> InvoiceProvider`.

Bonificaciones sin cobro pueden utilizar catalogo y entitlement sin fabricar
pagos o facturas inexistentes.

## Gate

Antes de una futura evaluacion humana de lanzamiento, el circuito aprobado debe
estar implementado y validado con provider real o sandbox representativo que
demuestre la integracion final, idempotencia, webhooks, conciliacion, seguridad,
fallos, rollback y facturacion. Activar credenciales productivas o cobrar desde
el primer dia requiere decision comercial, legal y operativa separada.

No se fijan aqui provider, medios de pago, precios, impuestos, duraciones,
productos ni infraestructura productiva definitiva.

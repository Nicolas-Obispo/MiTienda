# Contrato tecnico de FeedGo Clasificados

Estado del documento: Documento Tecnico oficial, implementacion no iniciada.
Categoria: Documento Tecnico.
Documento dueno: `docs/26_CLASSIFIEDS_CONTRACT.md`.
Responsable funcional: Producto Clasificados y arquitectura de dominio.
Documentos relacionados: `01_ENGINEERING.md`, `02_PRODUCT.md`, `03_SEARCH.md`,
`05_SEARCH_ROADMAP.md`, `15_LEGAL_AND_OPERATIONAL.md`,
`27_COMMERCIAL_PLATFORM_CONTRACT.md`.
Cuando debe consultarse: antes de auditar, disenar, implementar o validar
Clasificados, sus Historias, Search, IA, promociones o integraciones.

## Frontera

FeedGo Clasificados es una vertical de primer nivel del ecosistema FeedGo. No
es una aplicacion separada, una segunda plataforma de usuarios ni un
marketplace que intermedie la compraventa.

Existe una unica identidad `Usuario FeedGo`. Clasificados puede persistir datos
publicos complementarios vinculados a `usuario_id`, pero no duplica cuenta,
email, credenciales, autenticacion ni lifecycle de identidad. No se requiere un
Espacio para publicar un Clasificado.

El frontend representa e interactua. Services consumen Routes; Backend
Services validan ownership, estados, negocio, ranking, promocion e integraciones;
Models/DB persisten. Ninguna pantalla decide reglas funcionales.

## Acceso y privacidad

Un visitante anonimo puede navegar, buscar, filtrar, recorrer categorias,
abrir Clasificados, ver media e informacion publica y utilizar el contacto
publico habilitado. Publicar, editar, pausar, finalizar, eliminar, promocionar,
consumir beneficios o administrar exige identidad FeedGo y autorizacion
backend.

FeedGo conecta comprador y vendedor. El contrato inicial no incluye checkout
del bien, carrito transaccional, escrow, custodia de fondos, logistica ni
envios. WhatsApp puede ser el contacto inicial mediante datos publicos
especificos y minimizados; FeedGo no lee la conversacion externa.

## Lifecycle

El lifecycle conceptual es `draft`, `active`, `paused`, `sold/finalized` y
`deleted`. La eliminacion es no destructiva cuando corresponda. Solo `active`
participa del universo publico. No existe expiracion automatica inicial del
Clasificado organico.

## Schema por categoria

Cada categoria utiliza un schema estructurado y versionado. Columnas tipadas
representan datos estructurales estables y `attributes_json` puede contener
atributos variables validados por schema. El mismo contrato sirve a formulario
manual, IA asistida, validacion, filtros, Search, Indexador y Ranking.

No se fijan aqui categorias, atributos ni algoritmos definitivos. La etapa
owner debe auditarlos y versionarlos.

## IA multimodal

La creacion asistida respeta:

`IA propone -> backend valida -> usuario revisa -> usuario confirma -> publica -> indexa`.

IA no es fuente de verdad, no publica automaticamente y no reemplaza el flujo
manual. El provider se selecciona mediante benchmark y permanece desacoplado.
Backend gobierna schema, validacion, incertidumbre, limites, rate limiting,
privacidad y degradacion.

No se crea un `AIService` universal. La direccion conceptual es
`ClassifiedCreationUseCase -> contrato especializado de propuesta -> adapter
multimodal`. El provider devuelve una propuesta estructurada; Clasificados
conserva normalizacion, schema, permisos, validacion, revision, confirmacion,
publicacion e indexacion. La forma exacta se define en ETAPA 104.

## Search, Indexador y geografia

Explorar conserva Espacios; Clasificados conserva su universo. Sugerencias
cruzadas deben identificarse. Clasificados utiliza un `ClassifiedIndexDocument`
y contratos propios de candidatos y ranking cuando corresponda. Los artefactos
de indice son regenerables, no fuentes de verdad.

El inventario es globalmente navegable. Ubicacion del bien, pais, provincia,
ciudad y distancia pueden informar, filtrar, ordenar o aportar senales. No se
hereda el scope territorial obligatorio de Espacios.

Rige `pertinencia primero -> promocion despues`. Ausencia prevalece sobre
irrelevancia.

## Una carga y multiples superficies

El usuario no debe repetir cargas compatibles. Una operacion puede partir de
una Publicacion y ofrecer exposicion opcional como Clasificado y/o Historia.
Debe reutilizar media, titulo y descripcion compatibles y solicitar solamente
datos complementarios del schema de destino.

La etapa owner debe auditar la implementacion. La alternativa preferida es:

- assets con identidad y lifecycle tecnico propios;
- entidades de dominio independientes;
- relaciones explicitas de procedencia;
- orquestacion backend de operaciones multisupeficie;
- copia inicial confirmada de texto cuando los dominios requieran evolucion
  independiente;
- referencias compartidas a media sin borrado mientras existan consumidores.

Media permanece como modulo interno y no se convierte ahora en servicio
independiente. ETAPA 102 debe auditar identidad persistente del asset, metadata
oficial, ownership, referencias por superficie, autorizacion de asociacion,
`AssetStorageProvider`, lifecycle, validacion de contenido, garbage collection
segura y transformaciones idempotentes preparadas para trabajo pesado fuera del
request web. No se fijan proveedor de storage, CDN, deduplicacion ni
implementacion final antes de esa auditoria.

Publicacion, Clasificado, Historia de Espacio e Historia de Clasificado
conservan lifecycle independiente. Pausar o eliminar una superficie no modifica
otra. Toda propagacion, sincronizacion o reindexacion debe ser explicita,
idempotente, auditable y backend-owned. Un precio estructurado de Clasificados
es la fuente funcional; una cifra en texto libre no crea una segunda verdad.

## Historias de Clasificados

Historia de Clasificado es conceptualmente distinta de Historia de Espacio,
posee lifecycle propio y navega al Clasificado. Pueden compartir una experiencia
agregada con diferenciacion clara, sin forzar una unica entidad si rompe owners.

## Promocion

Contenido y promocion son entidades o estados conceptualmente separados. Un
Clasificado puede ser organico, destacado o premium sin duplicarse. La
contratacion inicial privilegia pago puntual por periodo. Al vencer la
promocion, termina su prioridad y el Clasificado vuelve automaticamente a
organico; no se elimina ni pausa.

Beneficios especificos y cupones se prefieren antes que saldo fungible. Deben
ser trazables, expirables, idempotentes, no retirables, no transferibles por
defecto, no reembolsables y no representan dinero.

## Fuera del contrato inicial

- comentarios, expresamente posteriores a la primera apertura publica;
- checkout del bien, escrow, logistica, custodia o intermediacion financiera;
- proveedor definitivo de IA, categorias finales, precios, duraciones o
  algoritmo final de ranking;
- infraestructura productiva no auditada.

## Criterio de validacion

Cada etapa de Clasificados debe cerrar tests funcionales, integracion,
autorizacion, privacidad, seguridad, Search y regresion proporcionales. Los
gates integrales posteriores consolidan FeedGo Espacios, FeedGo Clasificados y
las capacidades comerciales construidas; no reconstruyen controles desde cero.

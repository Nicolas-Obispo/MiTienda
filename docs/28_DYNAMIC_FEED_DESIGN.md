# Diseño técnico del Dynamic Feed de FeedGo

Estado del documento: diseño aprobado; implementación diferida.
Categoría: Documento Técnico.
Documento dueño: `docs/28_DYNAMIC_FEED_DESIGN.md`.
Responsable funcional: Feed, Historias, Candidate Engine y Ranking.
Etapas owner: ETAPA 119 para preferencias, privacidad y memoria de exposición;
ETAPA 122 para candidatos, ranking, contexto territorial, snapshots, cursores,
paginación y ranking de Historias; ETAPA 106 para entitlements Premium y
Advertising.
Documentos relacionados: `00_GOVERNANCE.md`, `01_ENGINEERING.md`,
`02_PRODUCT.md`, `03_SEARCH.md`,
`05_SEARCH_ROADMAP.md`, `07_DECISIONS.md`, `18_PWA_ENTERPRISE.md`,
`19_LOCATION_LEGAL_GATE.md`, `26_CLASSIFIEDS_CONTRACT.md` y
`27_COMMERCIAL_PLATFORM_CONTRACT.md`.
Cuándo debe consultarse: antes de modificar selección, ranking, paginación,
cache, exposición, ubicación, Premium o Advertising de Feed e Historias.

## Estado y frontera

Este documento formaliza durante ETAPA 98 el diseño futuro del Dynamic Feed.
No describe comportamiento ya implementado ni autoriza adelantar ETAPAS 106,
119 o 122. ETAPA 98 permanece abierta.

El backend es owner de elegibilidad, Candidate Generation, proximidad, ranking,
diversidad, exposición, snapshots y cursores. El frontend renderiza, pagina,
prefetchea y conserva cache de sesión; no reconstruye ni corrige el ranking.

## Objetivo de producto

FeedGo tendrá un Feed mixto propio para descubrir comercios, profesionales,
oficios y servicios. Seguir un espacio aporta una señal fuerte, pero no limita
el Feed a seguidos. La ubicación aporta una señal fuerte, pero no constituye un
filtro territorial rígido.

La pregunta de producto que guía su composición es: “¿Cuál es el siguiente
conjunto de contenido local que tiene más probabilidad de resultar útil,
interesante o novedoso para esta persona, aquí y ahora, sin mostrarle siempre
lo mismo?”. No es un ranking exclusivo por popularidad, un catálogo exclusivo
de seguidos ni un mecanismo pay-to-win.

La composición combina seguimiento, cercanía, afinidad, recencia, diversidad,
novedad, exposición previa, popularidad normalizada, underexposure y una
oportunidad controlada para espacios nuevos. Los espacios gratuitos no quedan
enterrados únicamente por no pagar.

## Pipeline contractual

```text
contexto autorizado
-> Candidate Generation por fuentes
-> elegibilidad, visibilidad y moderación
-> expansión territorial progresiva
-> hidratación bulk
-> scoring orgánico
-> penalización temporal por exposición
-> entitlement Premium
-> boost Premium acotado
-> reranking final diversity/fairness consciente de Premium
-> campañas Advertising elegibles
-> composición comercial con slots y frequency caps
-> snapshot estable
-> cursor opaco
-> infinite pagination
-> respuesta
```

Candidate Generation selecciona pools acotados; Ranking ordena candidatos y no
genera conocimiento. La elegibilidad nunca puede ser concedida por Premium o
Advertising. La hidratación debe ser bulk y evitar consultas por card.
Después de componer Advertising sólo corresponde validar la composición final;
no se rerankean juntos contenido orgánico y comercial.

## Señales backend-owned

El scoring y reranking pueden consumir, con evidencia y semántica aprobadas:

- seguimiento;
- likes;
- guardados;
- recencia;
- ubicación y proximidad;
- afinidad semántica;
- exposición previa;
- popularidad normalizada;
- novedad de la publicación y del espacio;
- underexposure;
- diversidad;
- señal Premium acotada;
- contexto temporal aprobado;
- historial y preferencias cuando exista evidencia suficiente.

No se fijan pesos numéricos antes de la auditoría de ETAPA 122. Seguir es una
señal fuerte, no un filtro exclusivo. Guardar puede expresar una intención más
fuerte que un like. La popularidad debe normalizarse para no monopolizar el
ranking y la ausencia de historial nunca equivale a desinterés.

## Ubicación y expansión territorial

La cercanía se prioriza inicialmente y el Candidate Engine expande bandas de
manera progresiva cuando el usuario avanza o falta inventario. El recorrido
puede alcanzar toda la ciudad: no crea una burbuja geográfica permanente.

La expansión parte de candidatos cercanos y seguidos relevantes, continúa por
zonas contiguas y puede cubrir el resto de la ciudad. Si sigue faltando
inventario, amplía el contexto territorial permitido. Puede responder a
densidad de candidatos, profundidad de navegación, disponibilidad territorial,
diversidad y contexto autorizado. Los seguidos pueden ingresar fuera de la
banda inicial y la proximidad pierde peso gradualmente: no corta candidatos de
forma abrupta.

La ubicación precisa es efímera y se utiliza bajo el contrato de
`19_LOCATION_LEGAL_GATE.md`. No se persiste en el cursor, snapshot frontend ni
cache PWA. El backend es owner de proximidad, expansión y ranking territorial.
El frontend sólo conserva contexto territorial coarse cuando corresponda. Una
ciudad declarada o inferida del perfil nunca se presenta como ubicación actual.

La geolocalización no bloquea el arranque. Con cache o snapshot válido, el
frontend lo muestra inmediatamente. Sin cache, el backend genera un Feed
provisional con territorio declarado o conocido y, en último término,
recencia, diversidad, popularidad moderada, espacios nuevos y subexpuestos.
Cuando el contexto mejora, el backend prepara otro snapshot completo.

## Snapshots, actualización contextual y estabilidad

Un snapshot fija composición y orden durante una sesión de Feed. Su cursor es
opaco, pertenece al backend e identifica continuidad dentro del mismo snapshot;
no expone coordenadas, scores internos ni señales privadas, y no permite
mezclar páginas de snapshots distintos.

La llegada de GPS, nuevos scores o un cambio contextual no reordena páginas que
el usuario ya está leyendo. Un contexto nuevo produce otro snapshot y un
refresh explícito puede adoptarlo. Las mutaciones sociales actualizan el estado
de cards sin recomponer automáticamente el orden; sólo una pérdida real de
elegibilidad puede retirar contenido inmediatamente.

El aviso manual `Actualizar`, o equivalente, sólo corresponde al arranque,
reentrada o cambio importante de contexto cuando:

- ya existe contenido válido visible;
- se prepara en background un snapshot mejor; y
- el snapshot nuevo está completamente listo.

No se muestra mientras el snapshot se genera. Al activarlo, el frontend adopta
coherentemente el snapshot nuevo, vuelve al inicio y descarta la continuidad
anterior sin mezclar páginas.

Este aviso no participa en el scroll normal. Mientras se consume la página o
grupo N, TanStack puede preparar N+1 desde el cursor actual. Al alcanzarla, se
continúa automáticamente, sin botón, reload, pantalla vacía ni reordenamiento
brusco, y puede comenzar el prefetch de N+2.

## Cache, PWA y background

TanStack Query es owner del cache remoto de sesión. El backend conserva
snapshots, ranking, contexto y memoria de exposición. Las APIs privadas siguen
`network-only`; JWT y respuestas privadas no ingresan a Cache Storage; Workbox
no es cache funcional del Feed privado.

No se autoriza persistencia funcional en IndexedDB sin una decisión futura
explícita que defina aislamiento por usuario, minimización, TTL, logout y
privacidad. Prefetch y revalidación son optimizaciones oportunistas: el diseño
no depende de ejecución sostenida con la aplicación cerrada, GPS continuo ni
Background Sync móvil.

Durante ETAPA 122, TanStack podrá conservar páginas, cursor opaco, snapshot id,
timestamp y estado de próxima página dentro de la sesión. ETAPA 119 debe decidir
si existe una necesidad real de último snapshot persistente y, antes de
autorizarla, coordinar con ETAPA 122 seguridad, privacidad, TTL, minimización,
aislamiento por identidad y limpieza. Esta posibilidad no autoriza IndexedDB.

Cuando el runtime lo permita pueden aprovecharse revalidación al recuperar
foco o conectividad y preparación de un snapshot ante cambio contextual. Son
optimizaciones, no garantías de ejecución en background.

## Estados de contenido y memoria de exposición

Los estados son distintos y no intercambiables:

```text
descargado -> cacheado -> incluido en snapshot -> renderizado -> expuesto -> consumido
```

Prefetchear, cachear o incluir una entidad en un snapshot no registra
exposición. Sólo una exposición real, determinada mediante un contrato de
visibilidad suficiente, alimenta la memoria temporal.

ETAPA 119 define privacidad, control y memoria conceptual con `usuario_id`,
`resource_type`, `resource_id`, `first_exposed_at`, `last_exposed_at`,
`exposure_count` y `last_feed_session`, o equivalentes. La
ventana conceptual es móvil, de aproximadamente tres a cuatro días; aplica una
penalización creciente con decay temporal y permite reingreso posterior. Nunca
constituye exclusión permanente.

La primera exposición no se penaliza. Las repeticiones aumentan la penalización
y señales fuertes pueden amortiguarla, sin convertirla en exclusión. El
frontend observa visibilidad suficiente dentro del viewport; el umbral y tiempo
mínimos se definen en ETAPA 119. El backend persiste y aplica la política sin
depender de Background Sync para afirmar que una exposición fue guardada.

## Cold start de usuario

Sin seguidos, likes, guardados o embedding, Candidate Generation usa según
disponibilidad territorio, recencia, diversidad, popularidad moderada, espacios
nuevos, contenido subexpuesto, exploración de rubros y expansión territorial.
La falta de señales personales no se interpreta como falta de interés.

## Cold start de plataforma

El modelo debe funcionar con pocos usuarios, espacios, seguidos o
interacciones. Ante inventario escaso puede relajar caps, ampliar territorio y
ponderar recencia, diversidad, popularidad normalizada, novedad y
underexposure. No depende de embeddings maduros ni de grandes volúmenes.

También puede reducir progresivamente la penalización por repetición cuando no
existen sustitutos y favorecer recencia sin eliminar contenido válido anterior.
La degradación debe ser determinista, comprensible y usar el mismo pipeline que
la operación a mayor escala.

## Diversidad, fairness y anti-repetición

El reranking final controla repetición de espacio y rubro, diversidad de
fuentes, cuotas de exploración y oportunidad mínima para candidatos nuevos o
subexpuestos. Es consciente del boost Premium, de modo que la ventaja comercial
no pueda reintroducir concentración después de aplicar límites sanitarios.

ETAPA 122 debe definir máximos acotados por espacio, separación mínima entre
publicaciones del mismo espacio, evitación de rubros consecutivos cuando haya
alternativas, límites de concentración por fuente, deduplicación por recurso,
popularidad normalizada y cuotas de exploración. Los límites se degradan
progresivamente cuando falte inventario para completar una página.

## Espacios nuevos y gratuitos

Un espacio nuevo o gratuito no queda enterrado por carecer de pago o señales
históricas. Novedad temporal, underexposure y exploration quota crean una
oportunidad medible, sujeta a elegibilidad, calidad mínima, límites de
frecuencia y diversidad territorial y por rubro. No garantizan una posición.

## Premium y Advertising

Se mantienen cuatro conceptos separados:

- entitlement Premium: capacidad comercial válida, owner ETAPA 106;
- señal Premium de ranking: boost acotado consumido por ETAPA 122;
- promoción paga: producto comercial explícito sujeto a su política;
- Advertising: composición comercial separada del ranking orgánico.

Premium aporta una ventaja real de exposición o posición, pero no cambia
elegibilidad, no garantiza posiciones, no rompe diversity/fairness, no crea
monopolios, no elimina oportunidades de espacios gratuitos, no anula
proximidad o relevancia y nunca evita moderación. El reranker final intenta
conservar su valor comercial dentro de esos límites sanitarios.

Advertising se compone después del ranking orgánico mediante slots elegibles y
pertinentes, frequency caps y rotulado visible `Patrocinado`. ETAPA 106 conserva
campañas, creatividades, entitlements y política comercial; ETAPA 122 sólo
consume contratos aprobados.

## Fuentes extensibles y Clasificados

Candidate Generation debe aceptar envelopes tipados y trazables sin borrar el
ownership de cada dominio. Fuentes futuras previstas:

- `SpacePostCandidate`;
- `SpaceStoryCandidate`;
- `ClassifiedCandidate`;
- `ClassifiedStoryCandidate`;
- `AdvertisingCandidate`.

Esta extensión no implementa Clasificados, no fusiona Publicaciones y
Clasificados en una única entidad ni crea un ranking universal. Elegibilidad,
lifecycle, índice, ranking y promoción permanecen bajo el dominio
correspondiente;
`AdvertisingCandidate` sólo alimenta el compositor comercial posterior y nunca
el pool o scoring orgánico. Advertising conserva su compositor separado.

## Historias

Historias requiere ranking propio, no una copia exacta del Feed. Puede combinar
pendientes/no vistas, seguimiento, cercanía, afinidad, recencia, exposición,
diversidad, descubrimiento y expansión territorial. Las vistas reducen
prioridad sin crear exclusión permanente.

La composición presenta una burbuja por espacio y evita monopolios. Una
historia inválida o sin multimedia disponible no es candidata reproducible.
Publicidad o promoción no simulan una historia orgánica.

Las futuras historias de Clasificados ingresan como fuente tipada y mantienen
su lifecycle. Advertising permanece identificado y separado. ETAPA 122 es
owner del ranking y continuidad de Historias; ETAPA 119, de memoria y privacidad.

## Escalabilidad y brecha actual

El Feed actual carga el universo elegible mediante `query.all()`. Ese mecanismo
puntúa todo el universo, ordena completamente en memoria, no pagina y no
constituye el diseño futuro. ETAPA 122 debe reemplazarlo por:

```text
sources limitados
-> consultas indexadas
-> candidate pools acotados
-> bulk hydration
-> scoring de candidatos
-> snapshot/cursor
-> infinite pagination y prefetch
```

El arranque rápido no se resuelve cacheando indefinidamente una consulta global
costosa. Paginación por cursor, estabilidad de snapshot y deduplicación entre
páginas forman un único contrato.

La implementación permanece en el monolito modular. No se crea un microservicio
de Feed, Ranking o Candidate Engine sin evidencia futura suficiente conforme a
`00_GOVERNANCE.md` y `01_ENGINEERING.md`.

## Owners y gates de implementación

| Concepto | Owner | Etapa |
| --- | --- | --- |
| Preferencias, privacidad, historial y memoria temporal de exposición | Contexto y recomendaciones | ETAPA 119 |
| Candidate Generation, ubicación, ranking, diversity/fairness, snapshots, cursor, infinite Feed y ranking de Historias | Feed/Candidate Engine/Ranking backend | ETAPA 122 |
| Premium, catálogo, políticas, entitlements, promociones y Advertising | Plataforma Comercial | ETAPA 106 |
| Cache remoto de sesión y prefetch oportunista | TanStack Query frontend | ETAPA 122 consume el contrato PWA vigente |
| Evaluación de último snapshot persistente, minimización, TTL y aislamiento | Contexto/privacidad coordinado con Feed | ETAPAS 119 y 122; no autorizado actualmente |
| Clasificados y su lifecycle/ranking | Dominio Clasificados | Sus etapas existentes; integración futura mediante envelopes |

La implementación exige contratos de elegibilidad, estabilidad y no duplicación
entre páginas; medición de exposición real; privacidad; observabilidad de
señales y boosts; caps de diversidad; degradación por bajo inventario; y pruebas
de cursor, cambio territorial, cache-first y separación orgánico/comercial.

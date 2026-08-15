# Plataforma Instalable y PWA Enterprise

Estado del documento: Documento Tecnico Oficial de FeedGo v1.0.
Version: 1.0.
Categoria: Documento Tecnico.
Nivel de autoridad: Tecnico especializado para arquitectura y experiencia PWA.
Documento dueno: `docs/18_PWA_ENTERPRISE.md`.
Responsable funcional: Plataforma PWA y experiencia instalada.
Documentos relacionados: `00_GOVERNANCE.md`, `01_ENGINEERING.md`,
`02_PRODUCT.md`, `04_CURRENT_STAGE.md`, `05_SEARCH_ROADMAP.md`,
`07_DECISIONS.md`, `08_ENGINEERING_PRINCIPLES.md`,
`15_LEGAL_AND_OPERATIONAL.md`, `17_OBSERVABILITY_AND_OPERATIONS.md`.
Cuando debe consultarse: antes de modificar manifiesto, service worker,
instalacion, cache PWA, experiencia standalone, comportamiento offline,
actualizaciones PWA, compatibilidad movil instalada o gates de beta y
lanzamiento.

## Estado

Alcance funcional aprobado. Sprints 96.1 y 96.2 cerrados tecnicamente a nivel
de repositorio; sus gates diferidos permanecen obligatorios. Sprint 96.3 es el
siguiente sprint y todavia no fue iniciado.

ETAPA 96 esta en curso. ETAPA 95 ya fue cerrada por 95.7-C; este documento
gobierna la etapa oficial vigente.

## Principio de producto

FeedGo es una aplicacion multiplataforma cuyo primer canal oficial de
distribucion sera una Progressive Web App (PWA).

La aplicacion web no constituye un producto diferente ni una version temporal
previa a aplicaciones moviles futuras.

## Objetivo

Convertir FeedGo en una PWA completa, segura, actualizable, resiliente y
verificable, apta como primer canal oficial de distribucion multiplataforma y
preparada para pruebas masivas, beta publica y lanzamiento controlado.

La experiencia instalada debe comportarse como una aplicacion y no solamente
como una pagina web agregada a la pantalla de inicio.

## Alcance obligatorio

- identidad FeedGo consistente en manifiesto, titulos, iconos y modo instalado;
- manifiesto valido con identidad, alcance, URL inicial y visualizacion;
- iconos adecuados para Android, variantes adaptables e iOS;
- HTTPS de extremo a extremo y configuracion segura de API;
- fallback de servidor para rutas profundas;
- service worker funcional, versionado, actualizable y recuperable;
- app shell precacheada y apertura offline controlada;
- limpieza segura de caches antiguas;
- politica de cache explicita por categoria de recurso y dato;
- proteccion de datos autenticados, personales y sensibles;
- aislamiento o eliminacion de datos al cerrar sesion o cambiar de usuario;
- prohibicion de presentar como exitosa una mutacion no persistida;
- navegacion standalone, carga y reapertura coherentes;
- safe areas, teclado virtual, viewport, overlays, scroll y foco correctos;
- compatibilidad verificable en Android e iOS/iPadOS;
- pruebas automatizadas, rollback, runbooks y gate final PWA.

## Controles objetivos de experiencia instalada

La experiencia instalada sera aceptable solo cuando:

- abra en modo standalone cuando la plataforma lo permita;
- use exclusivamente identidad FeedGo;
- cargue rutas iniciales y profundas sin depender de controles del navegador;
- no presente pantallas en blanco como respuesta controlada;
- abra el app shell sin red despues de una instalacion valida;
- informe que funciones requieren conexion y recupere el flujo al reconectar;
- no confirme como guardadas operaciones que no fueron persistidas;
- no oculte acciones criticas bajo barras, notch, safe areas o teclado virtual;
- no produzca scroll horizontal involuntario en los viewports soportados;
- mantenga areas tactiles y navegacion por teclado accesibles;
- bloquee fondo, scroll e interaccion cuando exista una capa activa;
- gestione foco y lo restaure al cerrar overlays;
- actualice entre versiones sin dejar caches incompatibles;
- permita recuperacion y rollback sin exigir borrado manual de datos;
- aisle datos entre usuarios y sesiones;
- solicite geolocalizacion en contexto, con finalidad clara y alternativa
  manual.

## Division aprobada

### Sprint 96.1 - Identidad instalada e instalacion segura

Objetivo: establecer una identidad FeedGo correcta y una base instalable
compatible con el despliegue productivo.

Alcance:

- manifiesto, identidad, colores e iconos;
- URL inicial, alcance, modo standalone y metadatos moviles;
- requisitos HTTPS, API segura y rutas profundas;
- matriz minima de plataformas y navegadores;
- definicion formal del alcance offline.

Criterios de cierre:

- identidad instalada exclusivamente FeedGo;
- manifiesto, activos e iconos validados automaticamente;
- instalacion base comprobada en la matriz minima;
- contratos de despliegue seguro y alcance offline aprobados;
- build, lint y validaciones especificas aprobados.

#### Contrato de Sprint 96.1-A - identidad instalada

Estado: implementado a nivel de repositorio; pendiente de validacion fisica y
productiva donde se indica.

Identidad canonica instalada:

- `name`: `FeedGo`;
- `short_name`: `FeedGo`;
- `id`: `/`;
- `start_url`: `/`;
- `scope`: `/`;
- `display`: `standalone`;
- `background_color`: `#030712`;
- `theme_color`: `#111827` como fallback estatico; el runtime de tema conserva
  el contrato dinamico aprobado en `21_THEME_CONTRACT.md`;
- `orientation`: omitida deliberadamente. FeedGo no bloquea una orientacion
  porque debe funcionar en movil, tablet y desktop y no existe una necesidad
  de producto documentada para restringirla.

El identificador `/` es estable y relativo al origen. No inventa dominio ni
proveedor y mantiene la identidad de la aplicacion independiente del ambiente.
`start_url` y `scope` incluyen todas las rutas publicas, protegidas y profundas
existentes bajo el origen de FeedGo.

Set de iconos aprobado:

- favicon PNG `48x48`;
- Apple touch icon PNG `180x180`;
- icono instalable PNG `192x192`, proposito `any`;
- icono instalable PNG `512x512`, proposito `any`;
- icono adaptable PNG `512x512`, proposito `maskable`.

Todos derivan de `frontend/public/logo_Feedgo.png`. La variante maskable no se
declara solo por metadata: conserva la identidad original completa, reducida y
centrada sobre el canvas opaco `#030712`, con su caja completa dentro del
circulo seguro de diametro 80%.

Matriz minima de plataformas para Sprint 96.1:

| Plataforma | Canal minimo | Validacion requerida |
| --- | --- | --- |
| Android | Chrome estable | manifest, instalacion, icono any/maskable, nombre, lanzamiento standalone |
| iOS | Safari y Home Screen | Apple touch icon, nombre, alta, apertura y reinstalacion |
| iPadOS | Safari y Home Screen | icono, nombre, apertura y orientaciones soportadas |
| Windows | Chrome y Edge estables | instalacion, icono, nombre y ventana standalone |
| Navegador sin instalacion PWA | web normal | degradacion progresiva sin bloquear funciones existentes |

Los emuladores y validadores automaticos son evidencia complementaria. El
cierre de compatibilidad requiere dispositivo fisico Android e iOS/iPadOS en
96.3.

Contrato de HTTPS, API y mixed content:

- frontend productivo y API productiva deben servirse exclusivamente mediante
  HTTPS valido;
- ninguna pagina HTTPS puede depender de API, uploads, media, fuentes, mapas,
  geocoding o assets activos por HTTP;
- las variables de build productivas deben exigir una URL API HTTPS o una ruta
  relativa segura definida por infraestructura;
- los fallbacks HTTP locales existentes son exclusivos de desarrollo y no son
  configuracion productiva;
- CORS productivo debe usar una allowlist explicita de origenes FeedGo HTTPS;
  no se permite `*` con credenciales ni una regex abierta como contrato
  productivo;
- dominio, hosting, certificados, reverse proxy y proveedor no se fijan en esta
  etapa. ETAPA 99 debe materializar este contrato sin reinterpretarlo.

Contrato de rutas profundas:

- el servidor o plataforma de hosting debe devolver el `index.html` de la SPA
  para toda navegacion GET/HEAD perteneciente a `scope` que no sea un archivo
  estatico ni una ruta de API;
- los assets inexistentes y las rutas API no deben reescribirse a HTML;
- `/comercios/:id`, `/publicaciones/:id` y todas las rutas reales del router
  deben admitir acceso directo y refresh;
- el fallback futuro del service worker no reemplaza el fallback del servidor
  en la primera visita;
- ETAPA 99 materializara la configuracion productiva; ETAPA 96 debe conservar
  el contrato y validarlo en un entorno representativo antes de cerrar.

Matriz inicial offline y cache para Sprint 96.2:

| Categoria | Owner / politica aprobada |
| --- | --- |
| App shell | PWA/service worker futuro; precache versionada |
| HTML y navegacion | PWA/service worker futuro; estrategia explicita con fallback controlado |
| JS/CSS versionados | PWA/service worker futuro; assets de build versionados |
| Bootstrap de tema | PWA/service worker futuro; asset obligatorio del app shell |
| Manifest, iconos y assets publicos aprobados | PWA/service worker futuro |
| Datos remotos de negocio durante la sesion | TanStack Query; conserva ownership actual |
| API publica | `network-only` inicial |
| API autenticada y respuestas privadas/JWT | `network-only`; prohibido Cache Storage |
| Mutaciones | `network-only`; sin cola, Background Sync ni exito no persistido |
| Uploads y media privada | `network-only` inicial |
| Mapas, tiles y geocoding | `network-only` inicial |

Sprint 96.1-A no implementa ninguna estrategia de runtime, no modifica el
service worker y no habilita funcionamiento offline.

#### Gate de Sprint 96.1-B - instalacion segura

Estado: cerrado tecnicamente a nivel de repositorio. La instalacion y el
despliegue reales conservan gates diferidos obligatorios que requieren
dispositivos fisicos o la infraestructura productiva de ETAPA 99.

Evidencia y limites del repositorio:

- `AppRouter` usa `BrowserRouter` y declara `/`, las rutas legales, Auth, Feed,
  Ranking, seguidos, Explorar, Perfil y las rutas dinamicas
  `/comercios/:id` y `/publicaciones/:id`. El hosting debe aplicar el contrato
  de fallback anterior a toda ruta frontend valida, sin reescribir API ni
  archivos estaticos inexistentes;
- una primera visita online y el refresh directo dependen del fallback del
  servidor. Una aplicacion instalada inicia en `start_url="/"`. No se declara
  apertura offline en Sprint 96.1;
- el frontend admite configurar la API mediante `VITE_API_URL`; los fallbacks
  `http://127.0.0.1:8000` y equivalentes son exclusivamente locales. ETAPA 99
  debe impedir un build productivo con fallback HTTP y materializar una URL
  HTTPS o una ruta relativa segura;
- el CORS actual cubre desarrollo local. ETAPA 99 debe reemplazar o extender
  esa configuracion para produccion mediante una allowlist explicita de los
  origenes HTTPS reales, sin inventarlos en esta etapa;
- las claves de geocoding, JWT signing, base de datos y cualquier otro secreto
  permanecen en configuracion backend. Ningun secreto productivo puede
  publicarse como variable `VITE_*`, asset o bundle frontend;
- el service worker productivo y la geolocalizacion solo pueden operar en
  contexto seguro. La excepcion de navegador para desarrollo local no es un
  contrato productivo;
- Cache Storage futuro no puede contener JWT, respuestas autenticadas, datos
  privados ni media privada. Logout, expiracion y cambio de usuario no pueden
  dejar contenido privado recuperable desde cache PWA para otra sesion;
- la promocion de instalacion queda a cargo de Chrome, Edge y Safari/Home
  Screen. Sprint 96.1 no agrega boton, banner, modal ni tutorial propio.

Matriz de cierre de Sprint 96.1:

| Criterio | Estado | Evidencia | Owner futuro |
| --- | --- | --- | --- |
| Identidad instalada exclusivamente FeedGo | CUMPLIDO | manifest, metadata HTML e iconos contractuales | 96.3 valida superficies fisicas |
| Manifest, assets e iconos validos | CUMPLIDO | test contractual, dimensiones PNG y build | 96.3 valida representacion por plataforma |
| `id`, `start_url`, `scope`, standalone y orientacion | CUMPLIDO | manifest y contrato 96.1-A | 96.3 valida lanzamiento instalado |
| Matriz minima de instalacion | CUMPLIDO A NIVEL REPOSITORIO / PENDIENTE DE ENTORNO | canales y resultados esperados definidos | 96.3 ejecuta Android, iOS/iPadOS y Windows |
| Primera visita y rutas profundas | CUMPLIDO A NIVEL REPOSITORIO / PENDIENTE DE ENTORNO | rutas auditadas y fallback GET/HEAD definido | ETAPA 99 lo materializa; 96.3 lo valida |
| Frontend y API HTTPS, sin mixed content | CUMPLIDO A NIVEL REPOSITORIO / PENDIENTE DE ENTORNO | API inyectable y contrato productivo definido | ETAPA 99 configura y valida origenes reales |
| CORS productivo explicito | CUMPLIDO A NIVEL REPOSITORIO / PENDIENTE DE ENTORNO | contrato allowlist definido; configuracion actual solo local | ETAPA 99 materializa la allowlist real |
| Limites de secretos, sesion y cache privada | CUMPLIDO | contrato de seguridad y matriz offline/cache | 96.2 implementa; 96.3 valida aislamiento |
| Alcance offline formal | CUMPLIDO | matriz separa app shell, TanStack Query y network-only | 96.2 implementa runtime |
| Runtime offline | PENDIENTE | fuera de alcance deliberado de 96.1 | 96.2 |
| Build, lint y tests especificos | CUMPLIDO | gate tecnico ejecutado al cerrar 96.1-B | sin owner pendiente |

Gates diferidos de validacion:

- instalacion, iconos, nombre, standalone, apertura, reinstalacion y
  orientaciones en la matriz fisica minima: Sprint 96.3;
- dominio y certificados HTTPS reales, API segura, ausencia efectiva de mixed
  content, CORS allowlist y fallback SPA del hosting: ETAPA 99;
- refresh directo de todas las rutas validas en el entorno desplegado: ETAPA
  99, con comprobacion integral en 96.3;
- geolocalizacion bajo HTTPS y permisos reales de plataforma: 96.3 y ETAPA 99.

Estos gates son evidencia futura obligatoria y no autorizan declarar lista la
PWA completa, comenzar beta ni lanzamiento. No constituyen una deficiencia
resoluble dentro del repositorio sin dispositivos, dominio o infraestructura
real.

### Sprint 96.2 - Runtime PWA, offline, seguridad y actualizacion

Objetivo: implementar una ejecucion resiliente, actualizable y segura.

Alcance:

- service worker, app shell y precache versionada;
- instalacion, activacion y limpieza de caches;
- fallback offline y recuperacion de conectividad;
- politicas de cache, privacidad, sesiones y cambio de usuario;
- degradacion controlada de API y dependencias externas;
- actualizacion entre versiones y recuperacion ante incompatibilidades.

Criterios de cierre:

- apertura offline controlada del app shell;
- matriz de cache aprobada y verificada;
- ausencia de filtracion de datos entre sesiones;
- ninguna mutacion fallida presentada como exitosa;
- actualizacion desde la version anterior comprobada;
- caches antiguas eliminadas de forma segura;
- recuperacion ante actualizacion incompatible verificada;
- pruebas automatizadas del runtime PWA aprobadas.

#### Implementacion 96.2-B - build, precache y firewall

Estado: completado y aprobado tecnicamente como parte del Sprint 96.2 cerrado.

Frontera arquitectonica permanente: **el Service Worker y la infraestructura
PWA son infraestructura tecnica de cliente y nunca una capa de negocio**. Solo
pueden decidir inventario estatico del app shell, transporte network-only,
fallback tecnico de navegacion, conectividad, lifecycle, actualizacion y
recuperacion del runtime. No pueden decidir validez de sesion, permisos,
privacidad de negocio, disponibilidad, exito de operaciones, datos a mostrar,
Search, Discovery, Candidate Engine, Ranking, IA ni ninguna decision derivada.

El flujo obligatorio permanece `Frontend -> Services -> Backend Routes ->
Backend Services -> Models/DB`. Backend conserva reglas, autorizaciones,
validaciones, decisiones y persistencia; TanStack Query conserva el ownership
del cache remoto de sesion. El runtime PWA no persiste datos de negocio, no
infiere estados funcionales y no crea una fuente de verdad paralela. Clasificar
metodos, origenes, headers sensibles, navegaciones frontend y assets de build
es exclusivamente una politica tecnica de plataforma.

El source unico del worker reside en `frontend/src/pwa/service-worker.js` y el
build produce `/service-worker.js` mediante `vite-plugin-pwa` con estrategia
`injectManifest`. El plugin no genera manifest ni registra automaticamente el
worker: conserva `frontend/public/manifest.json` y el owner de registro
existente. El build inyecta nombres hashed y falla si no puede generar el
worker; no existe un inventario manual posterior sobre `dist`.

Dependencias directas del build/runtime del worker: `vite-plugin-pwa@1.3.0`,
`workbox-core@7.4.1`, `workbox-precaching@7.4.1` y
`workbox-routing@7.4.1`. No se usa GenerateSW, Background Sync, cache de
runtime de API ni registro automatico del plugin.

El precache se limita a `index.html`, bundles JS/CSS generados, bootstrap y
tokens de tema, manifest, iconos instalables y logo FeedGo aprobados. Excluye
el propio worker, source maps, `vite.svg`, `icon-180.png` legacy y cualquier
asset publico no declarado. Las navegaciones frontend validas same-origin son
network-first y solo ante una excepcion real de red usan el `index.html`
precacheado; respuestas HTTP 404, 401, 403 u otros errores validos no se
convierten en shell.

El firewall clasifica como network-only todo metodo distinto de GET/HEAD, API
publica o autenticada, origen o path sensible, request con `Authorization`,
origen externo y recurso no incluido explicitamente en el precache. Por tanto,
Cache Storage contiene plataforma y nunca respuestas API, JWT, uploads, media
privada, mapas o geocoding. TanStack Query conserva sin cambios el ownership
de datos remotos durante la sesion.

96.2-B no implemento `skipWaiting`, `clients.claim`, worker waiting,
actualizacion controlada, cleanup entre versiones, UX offline ni recuperacion
avanzada. Esos contratos fueron implementados posteriormente por 96.2-C y
96.2-D.

#### Implementacion 96.2-C - registro, lifecycle y actualizacion controlada

Estado: completado y aprobado tecnicamente como parte del Sprint 96.2 cerrado.

`frontend/src/pwa/registerServiceWorker.js` es el owner tecnico unico del
registro `/service-worker.js`; `main.jsx` solo lo invoca. El runtime publica
exclusivamente los estados `unsupported`, `registering`, `registered`,
`installing`, `active`, `update-available`, `activating` y `error`. No contiene
usuario, sesion ni datos remotos y no constituye estado funcional global.

El owner detecta un worker `waiting` existente, `updatefound`, cambios del
worker `installing` y `controllerchange`. Una version instalada permanece
waiting por defecto: no existe `skipWaiting()` en `install` ni
`clients.claim()` en `activate`. Cerrar las paginas controladas permite la
activacion natural y la proxima apertura usa la version activa sin recarga
forzada.

La activacion inmediata requiere el mensaje tecnico `ACTIVATE_VERSION` con un
identificador tecnico sin datos privados. El worker consulta clientes window
same-origin, incluyendo no controlados. Con mas de uno responde
`ACTIVATION_BLOCKED_MULTITAB`, no activa ni recarga; con cero o uno responde
`ACTIVATION_ACCEPTED` despues de ejecutar `skipWaiting()` exclusivamente desde
ese handler. Si la solicitud tecnica falla responde `ACTIVATION_FAILED` y la
pagina publica estado `error`. Solo la pagina solicitante espera el cambio real
de controller y hace como maximo una recarga. La clave de `sessionStorage`
`feedgo:pwa:last-activated-version` es un guard tecnico; no almacena version de
sesion, usuario, token ni negocio y su fallo conserva un guard en memoria.

Durante `activate`, el cleanup solo puede borrar caches cuyo nombre comience
con `feedgo-precache-` y nunca el precache vigente. No borra otros caches,
IndexedDB, localStorage funcional, preferencias, Auth ni TanStack Query. El
firewall, precache restrictivo y navegacion network-first de 96.2-B permanecen
sin cambios funcionales.

96.2-C no agrega UI de update ni experiencia offline general. El contrato
tecnico puede observarse y solicitar activacion desde una integracion futura,
pero ninguna pantalla lo consume todavia. La arquitectura por capas permanece
preservada: PWA decide lifecycle de cliente y nunca validez de sesion, permisos,
datos, mutaciones o reglas de negocio.

#### Implementacion 96.2-D - offline, reconexion y recuperacion

Estado: completado y aprobado tecnicamente. Sprint 96.2 queda cerrado y Sprint
96.3 es el siguiente sprint; todavia no fue iniciado.

"FeedGo abre offline" significa solamente que una visita previa permitio
precachear `index.html`, JS, CSS, tema e identidad instalada, y que ese shell
puede abrir y representar rutas frontend. La primera visita sin red no inventa
un shell ni una pagina paralela. Datos, login, mutaciones, uploads, mapas y toda
operacion que requiera backend permanecen indisponibles y nunca se encolan ni
se presentan como confirmados.

`frontend/src/pwa/connectivityRuntime.js` es el owner tecnico de conectividad.
Sus estados son `offline`, `online-unverified`, `backend-reachable` y
`backend-unreachable`. `navigator.onLine === true` produce como maximo
`online-unverified`: nunca demuestra backend saludable, sesion valida ni
permisos. La senal global reutiliza `Alert` dentro de `MainLayout`, no bloquea
contenido disponible y solo aparece ante browser offline o fallo real de
transporte al backend.

El worker mantiene la API network-only y hace passthrough sin cache para GET,
HEAD, POST, PUT, PATCH y DELETE. Un rechazo de `fetch` por transporte emite
`BACKEND_UNREACHABLE`; cualquier `Response` HTTP emite `BACKEND_REACHABLE` y se
devuelve intacta. Por tanto 401, 403, 404, 409, 422 y 5xx nunca se convierten en
offline ni quedan ocultos. Los mensajes no incluyen URL, metodo, headers,
token, response, usuario ni payload. La notificacion es best-effort: si una
ventana desaparece o `postMessage` falla, nunca altera la respuesta HTTP ni el
error de transporte original.

Cuando vuelve el evento `online`, el estado pasa a `online-unverified` y la
senal offline desaparece. No hay reload, invalidacion, refetch ni listener de
Query adicional: TanStack Query conserva su comportamiento de reconexion y su
contenido en memoria. Una respuesta backend posterior confirma solo alcance
tecnico y elimina la senal de backend inaccesible.

No se agrega un estado funcional de sesion no verificada ni se modifica Auth.
Si existe un token local durante una indisponibilidad, la PWA solo representa
la indisponibilidad tecnica; no afirma ni niega validez de sesion. Mutaciones y
optimistic updates conservan sus owners actuales y deben recibir confirmacion o
error desde backend; no existen Background Sync, queues ni persistencia PWA de
operaciones.

La reparacion es explicita y no agresiva. `repairServiceWorker()` puede
desregistrar solamente workers same-origin cuyo script sea
`/service-worker.js`, borrar solamente caches `feedgo-precache-*` y volver a
registrar mediante el owner unico. No fuerza reload y nunca accede a caches
ajenos, localStorage funcional, `sessionStorage` funcional, preferencias,
tokens, IndexedDB, geolocalizacion, Auth, TanStack Query ni datos de negocio.
Assets faltantes intentan red y una navegacion offline sin shell falla de forma
segura; la reparacion queda disponible para corrupcion real, no se ejecuta
automaticamente para ocultar errores.

La frontera `Frontend -> Services -> Backend Routes -> Backend Services ->
Models/DB` permanece preservada. `src/pwa/` no importa features, services de
dominio, Auth ni QueryClient y no decide sesion, permisos, datos o resultados.
Firewall, precache y lifecycle de 96.2-B/96.2-C permanecen vigentes.

Tests unitarios y build verifican contratos, inventario, transporte, multitab,
anti-loop, cleanup, reconexion y reparacion. La ejecucion real en Service Worker
browser, instalacion, primera/segunda visita, DevTools offline, multitab real y
matriz Android/iOS/desktop son gates obligatorios diferidos a Sprint 96.3; no
justifican incorporar Playwright o Cypress dentro de 96.2-D.

Sprint 96.2 queda cerrado con build reproducible mediante `injectManifest`, app
shell y precache restrictivo, firewall network-only, lifecycle y actualizacion
controlados, proteccion multitab, offline y reconexion tecnicos, recuperacion
acotada, separacion PWA/TanStack Query y prohibicion de negocio en PWA.

Gates obligatorios diferidos a Sprint 96.3, no validados todavia en entorno
real:

- primera visita offline y visita offline con shell previamente instalado;
- navegacion y deep links offline;
- backend inaccesible con navegador online y reconexion real;
- worker waiting, actualizacion real y comportamiento multitab real;
- activacion natural y activacion explicita;
- proteccion real contra loops de reload;
- recuperacion ante worker o cache corrupto y ante asset faltante;
- Android Chrome, iPhone Safari, iPadOS Safari, Windows Chrome y Windows Edge;
- modo standalone, instalacion, desinstalacion y reinstalacion;
- iconos reales, variante maskable real y orientacion;
- geolocalizacion desde la experiencia instalada.

Gates de infraestructura productiva que continúan perteneciendo a ETAPA 99 y
no se consideran validados por el cierre de Sprint 96.2:

- dominio y HTTPS real;
- API productiva HTTPS y CORS productivo por allowlist;
- ausencia real de mixed content;
- fallback SPA del hosting;
- deep links y refresh directo desplegados.

### Sprint 96.3 - Experiencia instalada, compatibilidad y gate final

Objetivo: demostrar que FeedGo puede operar como aplicacion instalada en
Android e iOS y avanzar hacia operacion, pruebas masivas, beta y lanzamiento.

Alcance:

- navegacion standalone, carga y reapertura;
- safe areas, teclado, viewports, tactil, accesibilidad y overlays;
- instalacion y compatibilidad Android e iOS/iPadOS;
- rutas profundas, actualizacion, recuperacion y rollback;
- pruebas automatizadas integrales, senales operativas, runbooks y gate final.

Criterios de cierre:

- controles objetivos de experiencia instalada aprobados;
- matriz minima Android/iOS completa;
- rutas iniciales y profundas verificadas;
- apertura offline, reconexion y reapertura verificadas;
- actualizacion y rollback operativos;
- pruebas automatizadas, build y lint aprobados;
- runbooks aprobados;
- ausencia de bloqueantes criticos o altos;
- gate PWA habilitado expresamente.

## Bloqueantes de beta y lanzamiento

No podran comenzar la beta publica ni el lanzamiento oficial si ETAPA 96
permanece abierta, si existe cualquier bloqueante critico o alto, o si no estan
aprobados identidad, manifiesto, iconos, HTTPS, API productiva, rutas profundas,
service worker, actualizacion, recuperacion, apertura offline controlada,
aislamiento de sesiones, experiencia movil instalada, matriz Android/iOS,
pruebas automatizadas, rollback y runbooks.

## Dependencias

- ETAPA 95 debe cerrar identidad visual, temas, responsive, accesibilidad,
  navegacion, overlays, estados de interfaz, mapa y geolocalizacion.
- ETAPA 97 - Administracion Operativa Minima recibira senales, procedimientos
  de actualizacion, recuperacion, rollback y runbooks PWA.
- ETAPA 98 - Correccion y Pulido Visual del Frontend ejecutara la pasada final
  de calidad visible despues de PWA y operacion minima.
- ETAPA 99 - Infraestructura y Lanzamiento Controlado materializara HTTPS,
  configuracion productiva, fallback de rutas, despliegue y rollback sobre la
  PWA ya cerrada.

## Fuera de alcance obligatorio

- Capacitor y publicacion en Google Play o App Store;
- Web Push y Background Sync;
- mutaciones offline y colas de sincronizacion;
- mapas offline y funcionamiento offline completo;
- integraciones nativas;
- reescritura del frontend o rediseño general del sistema visual;
- reglas de negocio en frontend.

## Criterio final de aprobacion

ETAPA 96 quedara aprobada solo cuando los tres sprints esten cerrados, todos
los bloqueantes criticos y altos esten resueltos, la experiencia instalada
supere los controles objetivos, las sesiones y caches permanezcan aisladas,
actualizacion y rollback sean verificables, las pruebas y runbooks esten
aprobados y el gate PWA autorice continuar hacia operacion, infraestructura,
pruebas masivas, beta y lanzamiento.

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

ETAPA 96 cerrada tecnica y documentalmente. Sprints 96.1, 96.2 y 96.3 quedan
completados; el runtime fue validado contractualmente y mediante browser real
en Google Chrome y Microsoft Edge sobre Windows. Los gates de despliegue y
contexto productivo permanecen obligatorios para la futura auditoria de lanzamiento.

La reproduccion de determinados videos de Historias en iPhone/Safari/PWA queda
como defecto conocido diferido, no resuelto ni validado, bajo ETAPA 124 -
Compatibilidad Multimedia iOS/Safari/PWA. Esta excepcion acotada no reabre la
infraestructura PWA general ni habilita beta o lanzamiento sin los gates de
la futura auditoria de lanzamiento.

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
- `feedgo.com.ar` esta reservado como dominio canonico. Su reserva no implica
  DNS, hosting, certificados, reverse proxy ni frontend/API productivos. ETAPA
  99 debe materializar esas capacidades sin reinterpretar este contrato.

Contrato de rutas profundas:

- el servidor o plataforma de hosting debe devolver el `index.html` de la SPA
  para toda navegacion GET/HEAD perteneciente a `scope` que no sea un archivo
  estatico ni una ruta de API;
- los assets inexistentes y las rutas API no deben reescribirse a HTML;
- `/comercios/:id`, `/publicaciones/:id` y todas las rutas reales del router
  deben admitir acceso directo y refresh;
- el fallback futuro del service worker no reemplaza el fallback del servidor
  en la primera visita;
- la futura auditoria de lanzamiento materializara la configuracion productiva; ETAPA 96 debe conservar
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
dispositivos fisicos o la infraestructura productiva de la futura auditoria de lanzamiento.

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
  `http://127.0.0.1:8000` y equivalentes son exclusivamente locales. La futura auditoria de lanzamiento
  debe impedir un build productivo con fallback HTTP y materializar una URL
  HTTPS o una ruta relativa segura;
- el CORS actual cubre desarrollo local. La futura auditoria de lanzamiento debe reemplazar o extender
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
| Primera visita y rutas profundas | CUMPLIDO A NIVEL REPOSITORIO / PENDIENTE DE ENTORNO | rutas auditadas y fallback GET/HEAD definido | la futura auditoria de lanzamiento lo materializa; 96.3 lo valida |
| Frontend y API HTTPS, sin mixed content | CUMPLIDO A NIVEL REPOSITORIO / PENDIENTE DE ENTORNO | API inyectable y contrato productivo definido | la futura auditoria de lanzamiento configura y valida origenes reales |
| CORS productivo explicito | CUMPLIDO A NIVEL REPOSITORIO / PENDIENTE DE ENTORNO | contrato allowlist definido; configuracion actual solo local | la futura auditoria de lanzamiento materializa la allowlist real |
| Limites de secretos, sesion y cache privada | CUMPLIDO | contrato de seguridad y matriz offline/cache | 96.2 implementa; 96.3 valida aislamiento |
| Alcance offline formal | CUMPLIDO | matriz separa app shell, TanStack Query y network-only | 96.2 implementa runtime |
| Runtime offline | PENDIENTE | fuera de alcance deliberado de 96.1 | 96.2 |
| Build, lint y tests especificos | CUMPLIDO | gate tecnico ejecutado al cerrar 96.1-B | sin owner pendiente |

Gates diferidos de validacion:

- instalacion, iconos, nombre, standalone, apertura, reinstalacion y
  orientaciones en la matriz fisica minima: Sprint 96.3;
- dominio y certificados HTTPS reales, API segura, ausencia efectiva de mixed
  content, CORS allowlist y fallback SPA del hosting: futura auditoria de lanzamiento;
- refresh directo de todas las rutas validas en el entorno desplegado: ETAPA
  99, con comprobacion integral en 96.3;
- geolocalizacion bajo HTTPS y permisos reales de plataforma: 96.3 y futura auditoria de lanzamiento.

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

Gates de infraestructura productiva que continúan perteneciendo a la futura auditoria de lanzamiento y
no se consideran validados por el cierre de Sprint 96.2:

- delegacion/configuracion DNS de `feedgo.com.ar` y HTTPS real;
- API productiva HTTPS y CORS productivo por allowlist;
- ausencia real de mixed content;
- fallback SPA del hosting;
- deep links y refresh directo desplegados.

#### Implementacion 96.3-B - harness browser y controlabilidad

Estado: implementacion tecnica aprobada y cerrada con Sprint 96.3.

El harness usa `@playwright/test` como unico framework E2E y ejecuta targets
separados para Chromium administrado por Playwright, Google Chrome instalado y
Microsoft Edge instalado. Cada test recibe un BrowserContext efimero; no usa
perfiles personales, `userDataDir` ni contextos persistentes.

El modo Vite `pwa-e2e` habilita un bridge tecnico minimo que delega en el owner
real `serviceWorkerRuntime`. El bridge solo expone version tecnica, estado,
check de update, activacion explicita y reparacion. No contiene `skipWaiting`,
unregister, borrado de caches, Auth, token, QueryClient ni logica de negocio.
Una build normal define el modo como falso y debe eliminar el import y la API
global del bundle final.

Los fixtures N y N+1 se generan desde el mismo source con
`FEEDGO_PWA_TEST_VERSION`; la unica diferencia es metadata tecnica del bridge,
que modifica hashes y el inventario inyectado sin cambiar textos, pantallas ni
negocio. Un servidor local controlado puede alternar ambas versiones en el
mismo origen y simular de forma aislada worker invalido, registro fallido,
asset faltante, precache incompleto y update fallido. Los directorios de
fixtures, resultados, trazas y reportes quedan ignorados por Git.

Runbook inicial de validacion local:

1. instalar dependencias bloqueadas con `npm ci`;
2. instalar el Chromium compatible con `npx playwright install chromium`;
3. ejecutar `npm run test:e2e`, que genera N/N+1, inicia el servidor local,
   crea contextos limpios y lo apaga al finalizar;
4. usar `npx playwright test --project=chromium`, `--project=chrome` o
   `--project=edge` para repetir un target sobre fixtures ya generados;
5. inspeccionar solo artefactos ignorados en `test-results/` y
   `playwright-report/`; nunca reutilizar un perfil personal.

Para waiting y activacion: iniciar N, esperar worker activo y pagina
controlada, alternar el servidor a N+1, pedir `checkForUpdate()` mediante el
bridge y comprobar waiting antes de invocar `requestActivation()`. Multitab
requiere dos paginas del mismo contexto y debe conservar ambas abiertas ante
el intento. La recarga se mide desde eventos de navegacion del browser y el
guard tecnico existente, sin contadores agregados a produccion.

Para recovery: crear la falla solo dentro del servidor/contexto de fixture e
invocar `repair()` mediante el bridge. Deben sobrevivir caches ajenos y storage
funcional. El rollback PWA local invierte el fixture N+1 -> N y repite waiting
y activacion del owner; el rollback de despliegue productivo permanece en
la futura auditoria de lanzamiento.

Las safe areas no se corrigen preventivamente. Su validacion final sobre el
origen seguro desplegado permanece en la futura matriz de lanzamiento y
cualquier defecto reproducible requerira un bloque acotado aprobado.

El runbook local queda aprobado para diagnostico de update, recovery y rollback
PWA. El rollback del despliegue productivo pertenece a la futura auditoria de lanzamiento.

#### Validacion 96.3-C - Windows Chrome y Edge

Estado: validacion browser completada, aprobada y cerrada. Se ejecuto el build
Vite real de fixtures `pwa-e2e` con Service
Worker generado por `injectManifest`, en perfiles efimeros e independientes de
Google Chrome 151.0.7922.138 y Microsoft Edge 151.0.4129.86 sobre Windows.

Ambos navegadores validaron de forma independiente: primera visita limpia y
fallo seguro de primera visita offline; registro, control y precache FeedGo;
apertura y navegacion del shell previamente instalado sin red; mutaciones
network-only sin exito ficticio, queue ni Background Sync; distincion entre
navegador offline, fallo de transporte con navegador online y respuestas HTTP
401, 403, 404, 422 y 500; reconexion sin reload; update N -> N+1 con worker
waiting; activacion explicita por el owner real con una unica recarga;
activacion natural sin guard ni reload forzado; bloqueo multitab y posterior
activacion natural; update fallido conservando N; y repair acotado.

Cache Storage contuvo exclusivamente el namespace `feedgo-precache-*` y los
assets tecnicos aprobados por el inventario. No aparecieron endpoints API,
Authorization, JWT, payloads privados ni respuestas de negocio. El repair
elimino una cache FeedGo corrupta y conservo una cache ajena, localStorage
funcional de fixture e IndexedDB ajeno. Esto demuestra aislamiento tecnico; no
constituye persistencia offline ni validacion funcional de Auth.

La automatizacion no sustituye la integracion con el sistema operativo. La
matriz instalada que requiere un origen productivo seguro permanece como gate
de la futura auditoria de lanzamiento. La compatibilidad especifica de video en
iOS/Safari/PWA pertenece exclusivamente a ETAPA 124.

#### Decision 96.3-D - contexto geografico automatico y lectura anonima

El permiso de geolocalizacion pertenece al navegador/dispositivo. FeedGo no
persiste una autorizacion paralela. Al entrar en una capacidad territorial,
`granted` permite adquirir automaticamente y `prompt` habilita una unica
solicitud nativa idempotente; `denied` no se insiste. La ciudad declarada en el
perfil puede actuar como `profile_fallback`, nunca como ubicacion fisica actual:
no contiene coordenadas, no habilita distancia exacta ni expansion radial.

Anonimos pueden usar Explorar en modo lectura. Con permiso concedido usan el
territorio resuelto por backend; con denegacion seleccionan ciudad manual. Las
mutaciones siguen protegidas por frontend como UX y por backend como autoridad.
El detalle publico de un espacio puede mostrarse a un anonimo durante cinco
segundos desde su disponibilidad efectiva y luego deriva al flujo oficial de
registro; una accion protegida deriva inmediatamente. PWA y Service Worker no
participan en permiso, Auth, territorio ni este timer.

La validacion fisica en iPhone/Safari detecto reproduccion sostenida de videos
de publicaciones fuera de contexto visible. La correccion acotada pertenece al
owner frontend de media: las publicaciones reproducen con al menos 60 % de
visibilidad, se pausan fuera del viewport o con el documento oculto y comparten
exclusion de reproduccion activa. El detalle conserva reproduccion intencional
mientras la pagina esta visible. Historias, backend Range/206, Service Worker,
precache y firewall permanecen intactos. La eficacia sobre consumo real sigue
pendiente de revalidacion fisica en iPhone/Safari dentro de ETAPA 124.

La misma validacion fisica detecto rafagas `206` al recorrer videos de
Historias. Los rangos backend permanecen validos y `/uploads` sigue
`network-only`; la correccion queda acotada al owner de Historias: un unico
inicio explicito del video activo, pausa al cambiar/cerrar/desmontar u ocultar
el documento, reanudacion solo del medio que continua activo, cancelacion de
avances por error obsoletos y precarga exclusiva de imagenes. Se preservan el
avance de 4500 ms, las historias duplicadas intencionales y los contratos de
vistas. Las historias activas 51 y 52 referencian archivos fisicos faltantes y
quedan registradas como deuda de integridad sin reparacion de DB. La eficacia
real del lifecycle permanece pendiente de revalidacion en ETAPA 124.

La primera revalidacion fisica mostro que Safari, con `preload="metadata"`, no
siempre alcanza `loadeddata` antes de que se solicite reproduccion. Esperar ese
evento para el primer `play()` produjo un bloqueo circular. El hotfix mantiene
owner explicito y usa `loadedmetadata` para solicitar una sola reproduccion del
video activo; `loadeddata` no vuelve a iniciarla. Un rechazo real de `play()`
usa la salida segura existente y no deja el viewer detenido indefinidamente.
Pausa, background, cleanup, avance de 4500 ms, backend y PWA permanecen sin
cambios. La revalidacion fisica demostro que determinados videos continuan sin
iniciar; por eso el resultado no se declara resuelto y se difiere a ETAPA 124.

#### Defecto conocido diferido - video en Historias / iOS-Safari-PWA

Estado: DIFERIDO. No resuelto. No validado.

Las Historias de imagen continuan funcionando y la infraestructura PWA general
puede cerrarse. Determinados archivos de video solicitados correctamente con
respuestas `206 Partial Content` no inician dentro de `HistoriasViewer` en
iPhone/Safari/PWA. No existe causa raiz confirmada suficiente para otro cambio
seguro dentro de ETAPA 96.

La evidencia reproducible queda preservada en
`frontend/.pwa-fixtures/story-video-case-b.html`. El fixture es diagnostico,
queda fuera de la navegacion y de la build normal y no constituye una solucion
productiva. ETAPA 124 debe retomar Caso B, comparar Safari normal y standalone,
inspeccionar lifecycle, eventos, contenedor, MIME, codecs y Range cuando
corresponda y validar fisicamente iPhone/iPad sin repetir hotfixes por hipotesis.

### Sprint 96.3 - Experiencia instalada, compatibilidad y gate final

Estado: cerrado. Auditoria, harness browser, validacion Windows, evidencia
fisica disponible y gate final completados. La matriz que depende de HTTPS y
despliegue real se conserva para la futura auditoria de lanzamiento; el defecto multimedia acotado se
conserva en ETAPA 124.

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

## Gates diferidos despues del cierre

ETAPA 96 cerrada no equivale a produccion habilitada. La futura auditoria de lanzamiento debe materializar
y validar DNS, HTTPS, hosting, frontend y API productivos, CORS, ausencia de
mixed content, fallback SPA, deep links, refresh directo, rollback de despliegue
y matriz instalada sobre el origen real. `feedgo.com.ar` esta reservado, pero
esa reserva no demuestra ninguno de esos gates.

Separadamente, ETAPA 124 debe resolver y validar el defecto conocido de video
en Historias sobre iOS/Safari/PWA. Este defecto no bloquea el cierre de la
infraestructura PWA, pero debe evaluarse antes de declarar compatible ese
subdominio multimedia en las plataformas afectadas.

## Dependencias

- ETAPA 95 debe cerrar identidad visual, temas, responsive, accesibilidad,
  navegacion, overlays, estados de interfaz, mapa y geolocalizacion.
- ETAPA 97 - Administracion Operativa Minima recibira senales, procedimientos
  de actualizacion, recuperacion, rollback y runbooks PWA.
- ETAPA 98 - Correccion y Pulido Visual del Frontend ejecutara la pasada final
  de calidad visible despues de PWA y operacion minima.
- la futura auditoria de lanzamiento materializara HTTPS,
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

ETAPA 96 queda aprobada con sus tres sprints cerrados, arquitectura por capas,
sesiones y caches aisladas, API network-only, lifecycle/update/recovery
verificables, suites y build aprobados y gates futuros identificados sin
presentarlos como validados. El cierre autoriza continuar con ETAPA 97; no
autoriza por si mismo produccion, beta ni lanzamiento. No existe actualmente
una etapa numerada de lanzamiento; una futura auditoria humana debera definir
infraestructura y gates. Tampoco declara resuelto el defecto multimedia
diferido a ETAPA 124.

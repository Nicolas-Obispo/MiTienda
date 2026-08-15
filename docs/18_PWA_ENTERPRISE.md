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

Alcance funcional aprobado. Implementacion no iniciada.

ETAPA 96 permanece pendiente y no iniciada. ETAPA 95 ya fue cerrada por
95.7-C; este documento gobierna la siguiente etapa oficial sin adelantar su
implementacion.

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

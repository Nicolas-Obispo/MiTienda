# CHANGELOG

Historial ejecutivo de cambios de FeedGo!.

Este archivo registra los hitos principales del proyecto desde el cierre de la migración Enterprise.

Para detalle histórico extenso previo, ver:

- HISTORY.md
- NUEVOHISTORY.md

---

## ETAPA 71 — Cierre Definitivo de Migración Enterprise

**Commit:** `0b5de97`  
**Estado:** Cerrada

### Agregado

- Nuevo logo visual de FeedGo!: `frontend/public/logo_Feedgo.png`.

### Cambiado

- Branding principal actualizado de `MiPlaza` a `FeedGo!`.
- Login, Registro, Home, Feed y Layout principal actualizados para usar el logo FeedGo!.
- DELETE de publicación en `PublicacionDetallePage.jsx` migrado a la capa HTTP centralizada mediante `httpDelete()`.

### Eliminado

- `frontend/src/App.css`, archivo legacy sin uso.
- `backend/app/utils/__init__.py`, archivo huérfano sin uso.
- Variable muerta `API_BASE_URL` en `ProfilePage.jsx`.

### Validado

- Build frontend de producción OK.
- Arquitectura backend validada sobre `app/core` y `app/modules`.
- Arquitectura frontend validada sobre `src/core`, `src/shared` y `src/features`.
- Sin referencia legacy al DELETE hardcodeado `http://127.0.0.1:8000/publicaciones`.

### Pendiente no bloqueante

- Historias móvil: backend, upload, persistencia, `/historias/bar` e imágenes funcionan correctamente, pero el Feed móvil no renderiza historias. Queda para investigación futura.

---

## ETAPA 72 — Product Evolution Enterprise

**Estado:** Cerrada

**Último punto estable:** `ca9e8b6`

### Objetivo

Retomar evolución funcional de FeedGo! sobre la arquitectura Enterprise ya consolidada.

### Foco previsto

- Products.
- Rubros.
- Secciones.
- Mejoras UX.
- Historias móvil.
- Nuevas capacidades de producto.

### Resultado

ETAPA 72 queda cerrada como etapa histórica de evolución funcional, UX y performance incremental sobre la arquitectura Enterprise ya consolidada.

### Alcance consolidado

- Evolución funcional del producto.
- Mejoras UX mobile y de navegación.
- Historias permanentes temporales.
- Perfil, guardados y sincronización social.
- Performance frontend incremental.
- Cache selectiva y reducción de requests redundantes.

### Estado arquitectónico

- La arquitectura Enterprise sigue cerrada.
- No hay migración activa.
- Backend continúa siendo fuente de verdad.
- Frontend continúa organizado por `core`, `shared` y `features`.

## ETAPA 72.4 — Geolocalización MVP + UX de Espacios

**Commit:** `ffe882d`
**Estado:** Cerrada

### Agregado

* Componente reutilizable `LocationPicker`.
* Integración de Leaflet y React-Leaflet para selección visual de ubicación.
* Soporte de coordenadas geográficas (`latitud`, `longitud`) en espacios.
* Búsqueda de direcciones mediante Nominatim (OpenStreetMap).
* Selección manual de ubicación mediante movimiento de pin en mapa.
* Botón "Cómo llegar" basado en coordenadas reales.
* Botón de edición rápida desde el perfil del espacio.
* Botón de navegación "Volver" en perfil de espacio.

### Cambiado

* Formulario de creación y edición de espacios actualizado para soportar geolocalización.
* Al guardar cambios de un espacio se cierra el formulario automáticamente y se navega al perfil del espacio actualizado.
* Mejora visual del bloque de carga de portada.
* Mensajería y ayudas UX para selección de imagen de portada.
* Actualización automática de resultados en Explorar al activar o desactivar espacios.

### Backend

* Modelo `Comercio` preparado para persistir coordenadas geográficas.
* Schemas de espacios actualizados para exponer `latitud` y `longitud`.

### Validado

* Build frontend OK.
* Build backend OK (`python -m compileall app`).
* Creación de espacios con coordenadas.
* Edición de espacios con coordenadas.
* Persistencia correcta de ubicación.
* Navegación Google Maps mediante coordenadas.
* Refresco correcto de espacios activos/inactivos.

### Próxima etapa

* ETAPA 72.5 — Explorar por cercanía.
* Ordenamiento por distancia.
* Descubrimiento geolocalizado.
* Preparación para operación multiciudad.
## ETAPA 72.5 — Explorar por Cercanía

### Objetivo

Incorporar geolocalización en la experiencia de descubrimiento manteniendo el backend como fuente de verdad para el cálculo y ordenamiento de distancias.

### Backend

* Se agregan parámetros `lat`, `lng` y `radio_km` a la exploración de espacios.
* Se implementa cálculo de distancia geográfica mediante fórmula Haversine.
* Se incorpora atributo dinámico `distancia_km` en respuestas de comercios.
* Se habilita filtrado por radio de búsqueda.
* El cálculo de distancia permanece exclusivamente en backend respetando la arquitectura por capas.

### Frontend

* Explorar obtiene ubicación del dispositivo mediante Geolocation API.
* Explorar envía coordenadas al backend.
* Se muestra distancia estimada entre usuario y espacio.
* Se corrige la carga inicial para evitar renderizar resultados antes de resolver ubicación.

### Espacios Seguidos

* Se incorpora soporte de distancia en `/ver-seguidos`.
* Se envían coordenadas del usuario al endpoint de espacios seguidos.
* Se muestra distancia cuando el espacio posee coordenadas registradas.

### Validaciones realizadas

* Build frontend OK.
* Compilación backend OK.
* Pruebas funcionales en Explorar OK.
* Pruebas funcionales en Seguidos OK.
* Compatibilidad validada con modos clásico, smart y smart_semantic.

### Deuda técnica registrada

* Revisar ranking clásico para preservar señales históricas (historias/publicaciones) junto con cercanía.
* Diseñar ranking local inteligente basado en cercanía + señales sociales.
* Auditar precisión de LocationPicker y búsqueda Nominatim.

### Próxima etapa

ETAPA 72.6 — Precisión Geográfica y UX de LocationPicker.

## ETAPA 72.6 — Precisión Geográfica y UX de LocationPicker

### Objetivo

Mejorar la experiencia de búsqueda de ubicaciones y reducir errores producidos por resultados ambiguos de Nominatim.

### Auditoría realizada

Se auditó `frontend/src/shared/components/LocationPicker.jsx`.

Hallazgos:

* La búsqueda utilizaba Nominatim con `limit=1`.
* El usuario no podía elegir entre múltiples coincidencias.
* Si Nominatim devolvía una ubicación imprecisa, FeedGo! la aceptaba automáticamente.
* El pin movible ya funcionaba correctamente.

### Implementación

Se realizaron mejoras únicamente sobre:

`frontend/src/shared/components/LocationPicker.jsx`

Cambios:

* Nominatim pasa de `limit=1` a `limit=5`.
* Se almacenan múltiples resultados de búsqueda.
* Se muestra una lista de coincidencias debajo del buscador.
* El usuario puede seleccionar la coincidencia correcta.
* Al seleccionar una ubicación:

  * se actualiza el texto,
  * se mueve el pin,
  * se recentra el mapa.
* Se mantiene el pin movible mediante click y drag.
* Se mantiene el contrato actual de `onChange({ latitud, longitud })`.

### Validación

* ESLint específico del componente: OK.
* Sin errores de JSX.
* Sin errores de imports.
* Sin cambios de arquitectura.
* Sin modificaciones en otros módulos.

### Commit

`8ab781b`

`feat(spaces): mejora precision de location picker (ETAPA 72.6)`

### Resultado

Se mejora significativamente la precisión percibida por el usuario al permitir seleccionar manualmente entre varias coincidencias devueltas por Nominatim, manteniendo la filosofía de FeedGo! donde la ubicación final siempre puede corregirse mediante el pin del mapa.

## ETAPA 72.7 — Corrección mobile iOS: historias, media y geolocalización

### Commit funcional

`093daa6`

`fix(mobile): corrige historias, media y geolocalizacion en iOS (ETAPA 72.7)`

### Objetivo

Corregir fallos reales detectados en iPhone/Safari relacionados con historias, carga de imágenes, URLs de media y geolocalización.

### Cambios principales

- Historias mobile:
  - `fetchHistoriasBarItems` migrado a `httpGet`.
  - `fetchHistoriasPorComercio` migrado a `httpGet`.
  - `marcarHistoriaVista` migrado a `httpPost`.
  - Se corrigió apertura de historias en iPhone.
  - Se corrigió marcado de vistas y pendientes.

- Media:
  - `/media/upload` ahora devuelve rutas relativas `/uploads/...`.
  - Se evita guardar URLs absolutas dependientes de `localhost`, `127.0.0.1` o IP LAN.
  - Se normalizan thumbnails de historias con URLs locales.
  - Se corrigieron portadas en Mi Perfil y Espacios Seguidos usando `getMediaUrlFromAny`.

- UX:
  - Explorar y Seguidos ya no bloquean la carga esperando geolocalización.
  - Si iPhone no entrega ubicación por HTTP LAN, se muestra “Ubicación no disponible”.
  - PerfilComercio ya no se rompe completo si falla la carga de historias.

### Hallazgos técnicos

- El helper propio `requestJson` de historias presentó incompatibilidades en Safari/iOS.
- Los helpers core `httpGet` y `httpPost` funcionaron correctamente.
- URLs absolutas locales en `portada_url`, `thumbnailUrl` o `media_url` provocaban fallos en móvil.
- En iPhone, `navigator.geolocation` puede no entregar ubicación usando `http://192.168.x.x:5173`.

### Pendientes futuros

- Auditar `requestJson` de historias y decidir si se corrige o se elimina.
- Evaluar HTTPS local o túnel HTTPS para probar geolocalización real en iPhone.
- Revisar deuda de URLs históricas ya guardadas en DB.
- Seguir monitoreando bugs mobile que puedan compartir la misma causa raíz.
Actualizar CHANGELOG.md.

Registrar commits recientes:

71aa81d feat(auth): agrega aviso por inactividad de sesion
aaa1c22 feat(ux): optimiza experiencia mobile y perfil
3e8e895 feat(profile): agrega edicion basica de perfil

Contexto:
ETAPA 72.9

Resumen:
- aviso por inactividad de sesión a los 15 minutos
- modal con cerrar sesión / continuar
- mejoras UX mobile y perfil
- edición básica de perfil con provincia y ciudad
- nuevo PATCH /usuarios/me
- httpPatch frontend
- ProfilePage con modo editar perfil

NO tocar código.
Solo CHANGELOG.md.

## ETAPA 72.9 — Perfil de Usuario, Sesión y Organización de Guardados

### Commit 71aa81d

**feat(auth): agrega aviso por inactividad de sesion**

#### Cambios

* Se incorpora `SessionInactivityGuard`.
* Detección de inactividad luego de 15 minutos.
* Modal global con:

  * Continuar sesión.
  * Cerrar sesión.
* Integración con `AuthContext.logout()`.
* Soporte para eventos:

  * click
  * keydown
  * scroll
  * touchstart
  * pointerdown
* Compatibilidad con `visibilitychange` para Safari/iPhone.

#### Validación

* Build frontend OK.

---

### Commit aaa1c22

**feat(ux): optimiza experiencia mobile y perfil**

#### Cambios

* Optimización de grillas mobile.
* Ajustes de spacing y padding.
* Mejora visual de Mi Perfil.
* Ajustes responsive en:

  * Explorar
  * Ranking
  * PerfilComercio
* Corrección de visualización de portadas mediante `getMediaUrlFromAny()`.

#### Validación

* Build frontend OK.

---

### Commit 3e8e895

**feat(profile): agrega edicion basica de perfil**

#### Backend

* Nuevo schema `UsuarioPerfilUpdate`.
* Nuevo endpoint:

  * `PATCH /usuarios/me`
* Edición controlada de:

  * provincia
  * ciudad

#### Frontend

* Nuevo `httpPatch`.
* Nuevo service de actualización de perfil.
* Incorporación de modo edición en Mi Perfil.
* Actualización automática de datos visibles.

#### Validación

* Compile backend OK.
* Build frontend OK.

---

### Commit 42ea2bb

**feat(profile): mejora perfil y organiza guardados**

#### Perfil

* Reorganización completa del flujo de edición.
* Foto de perfil ampliada en modo edición.
* Correo visible junto a la foto.
* Botón "Cambiar foto" integrado dentro de Editar Perfil.
* Aviso visual:

  * ✔ Perfil actualizado.
  * Auto cierre a los 3 segundos.

#### Preferencias

* Incorporación de `color_fondo` en usuario.
* Persistencia en backend.
* Configuración disponible desde Editar Perfil.
* Sin aplicación visual global por el momento.

#### Guardados

* Eliminación de "Publicaciones guardadas" de Mi Perfil.
* Traslado de guardados a Seguidos.

#### Seguidos

* Nuevo selector:

  * Espacios seguidos.
  * Publicaciones guardadas.

#### Publicaciones

* Cambio de texto:

  * "Ver perfil" → "Ver espacio".
* Se mantiene navegación a:

  * `/comercios/:id`

#### Arquitectura

* Se mantiene la estructura Enterprise por capas:

  * Frontend
  * Services
  * Routes
  * Services Backend
  * DB

#### Validación

* Auditoría estructural completa aprobada.
* Build frontend OK.
* Compile backend OK.
* Working tree clean.

## ETAPA 72.10 — Historias permanentes (temporal)

### Commit 28fae51

**feat(stories): mantiene historias visibles temporalmente**

#### Decisión de producto

Durante la etapa temprana de adopción de FeedGo!, las historias permanecerán visibles indefinidamente para mantener actividad visible en la plataforma.

#### Cambios

* Se elimina temporalmente el filtro de expiración de historias.
* Las historias activas continúan apareciendo en:

  * Feed
  * Barra de historias
  * Perfil del espacio
  * Viewer de historias
* Se conserva `expira_en` en:

  * Base de datos
  * Modelos
  * Schemas
  * Flujo de creación

#### Sin cambios

* Likes de historias.
* Vistas de historias.
* Contadores.
* Frontend.
* Contratos de API.

#### Nota importante

Esta es una medida temporal de crecimiento temprano.

Cuando exista mayor volumen de usuarios y publicaciones se evaluará restaurar el comportamiento original de historias efímeras de 24 horas.

# CHANGELOG — ETAPA 72.11

## Performance Frontend Incremental

### Estado

ETAPA cerrada.

Objetivo: mejorar rendimiento percibido, reutilización de cache y reducción de requests innecesarios sin modificar arquitectura Enterprise, sin bajar calidad multimedia y sin alterar UX.

---

## 72.11A — Auditoría Performance

### Hallazgos iniciales

* Guardadas se cargaban manualmente en múltiples pantallas.
* Mutations sociales cancelaban toda la cache de TanStack Query.
* PerfilComercio utilizaba servicios directos para likes y guardados.
* Varias imágenes y videos no utilizaban optimizaciones modernas de carga.
* Historias repetían requests al mismo comercio dentro de una misma sesión.
* Existían cargas innecesarias y trabajo redundante en frontend.

---

## 72.11B — Guardadas + TanStack Query

### Commit

47a783e — perf(posts): cachea publicaciones guardadas con TanStack

### Cambios

* Se agregó query key dedicada:

  * queryKeys.posts.guardadas()

* Se creó:

  * usePublicacionesGuardadas()

* VerSeguidos migró a TanStack Query.

* Las publicaciones guardadas:

  * ya no cargan al ingresar a la pantalla.
  * cargan únicamente cuando el usuario abre la pestaña "Publicaciones guardadas".

### Beneficios

* Menor carga inicial.
* Menos requests innecesarios.
* Cache compartida para guardadas.

---

## 72.11C-1 — Cache Social Selectiva

### Commit

cce93cd — perf(social): acota cache e invalidacion de interacciones

### Cambios

* Eliminación de cancelQueries() global.
* Eliminación de snapshots globales.
* Implementación de snapshots selectivos.
* Implementación de rollback selectivo.
* Invalidación selectiva de queries relacionadas con publicaciones.
* Actualización optimista de cache para guardadas.

### Beneficios

* Menor trabajo interno de TanStack.
* Menos recargas innecesarias.
* Mayor coherencia entre pantallas.

---

## 72.11C-2 — PerfilComercio Sincronizado

### Commit

114313d — perf(spaces): sincroniza interacciones en perfil comercio

### Cambios

* PerfilComercio deja de utilizar:

  * toggleLike()
  * toggleGuardado()

* Pasa a utilizar:

  * useToggleLikePublicacionMutation()
  * useToggleGuardadoPublicacionMutation()

* Se mantiene respuesta instantánea mediante optimistic update local.

* Se agrega rollback local en caso de error.

### Beneficios

* Feed, Ranking, Detalle y PerfilComercio comparten el mismo flujo social.
* Mejor sincronización global.

---

## 72.11D-1 — Media Loading Seguro

### Commit

4db53dd — perf(media): optimiza carga de imagenes y videos

### Cambios

* Se agregó:

  * loading="lazy"
  * decoding="async"
  * preload="metadata"

* Aplicado en:

  * PublicacionCard
  * ExplorarPage
  * HistoriasBar
  * HistoriasViewer
  * PerfilComercioPage

### Restricciones respetadas

* No se modificó calidad multimedia.
* No se modificó autoplay.
* No se modificó UX.
* No se modificó timer de historias.

### Beneficios

* Menor presión inicial de red.
* Menor bloqueo del render principal.

---

## 72.11E-1 — Cache Local Historias Feed

### Commit

e55b5fc — perf(stories): cachea historias por comercio en feed

### Cambios

* Implementada cache local por comercio:

  * historiasPorComercioRef

* Se reutilizan historias ya cargadas en la misma sesión.

* Aplicado a:

  * apertura de historias
  * siguiente comercio
  * comercio anterior

* No se cachean listas vacías para evitar ocultar historias recién creadas.

### Beneficios

* Menos requests repetidos.
* Apertura más rápida de historias previamente vistas.

---

# Resultado Global

### Mejoras obtenidas

* Menos requests redundantes.
* Menos invalidaciones globales.
* Menor trabajo interno de TanStack Query.
* Mejor reutilización de cache.
* Mejor sincronización de likes y guardados.
* Menor carga temprana de multimedia.
* Menos requests repetidos de historias.

### Reglas Enterprise respetadas

* Sin refactor masivo.
* Sin cambios de arquitectura.
* Backend continúa siendo fuente de verdad.
* Sin degradar calidad multimedia.
* Sin cambios visibles de UX.
* Cambios acotados y auditados.

---

# Deudas Técnicas Registradas

## PERF-BE-01

N+1 en:

/historias/bar

Backend obtiene comercios y luego consulta historias por cada comercio.

---

## PERF-BE-02

N+1 en publicaciones guardadas.

Frontend debe completar publicaciones mediante requests adicionales cuando el endpoint devuelve información incompleta.

---

## PERF-FE-01

Ranking continúa realizando fetch auxiliar de:

* Feed
* Guardadas

para completar estados sociales.

---

## PERF-FE-02

PerfilComercio continúa mayormente fuera de TanStack Query.

---

## PERF-FE-03

Historias todavía no poseen cache global TanStack.

---

# Cierre

La ETAPA 72.11 queda oficialmente cerrada como:

PERFORMANCE FRONTEND INCREMENTAL

No representa el cierre definitivo de performance del producto completo, pero sí el cierre exitoso de la auditoría e implementación incremental de optimizaciones frontend seguras realizadas durante la ETAPA 72.

---

## ETAPA 73 — Evolución Funcional y Crecimiento del Producto

**Estado:** Activa

**Punto de partida:** `ca9e8b6`

### Contexto

ETAPA 73 inicia oficialmente después del cierre histórico de ETAPA 72.

La arquitectura Enterprise permanece cerrada y no hay migración activa. El trabajo actual continúa sobre la base ya consolidada.

### Foco

- Evolución funcional del producto.
- Mejoras UX incrementales.
- Performance incremental.
- Crecimiento del producto.
- Consolidación de flujos existentes.
- Nuevas capacidades sin refactor masivo.

### Reglas de etapa

- No reabrir migración Enterprise.
- No introducir refactors masivos sin necesidad.
- Mantener backend como fuente de verdad.
- Priorizar cambios acotados, auditables y compatibles con la arquitectura actual.

## ETAPA 73.1 — Historias, Retención y Evolución de Producto

### 73.1.1 — Optimización de refresco de barra de historias
**Commit:** `1c1129b`

- Se evita refrescar `/historias/bar` al cerrar el viewer cuando no hubo nuevas vistas registradas.
- Se reduce tráfico innecesario entre frontend y backend.
- Sin cambios visuales.
- Sin cambios de arquitectura.
- Sin cambios de comportamiento funcional.

### 73.1.2 — Optimización backend de /historias/bar
**Commit:** `d0eef47`

- Se elimina el principal N+1 detectado en la carga de la barra de historias.
- Se reemplaza la carga por comercio por consultas agregadas en lote.
- Se mantienen:
  - response shape
  - lógica de pendientes
  - lógica de vistas
  - lógica de likes
  - orden actual de la barra
- Mejora la escalabilidad y reduce significativamente la cantidad de consultas SQL.
- Sin cambios en frontend.
- Sin cambios en endpoints.
- Sin cambios visuales.

## ETAPA 73.3 – 73.4 | UX Cache-First + Hidratación Instantánea

### Objetivo

Mejorar la percepción de velocidad de la aplicación eliminando recargas visuales innecesarias, aprovechando TanStack Query como fuente de cache y realizando reconciliación de datos en segundo plano.

### Principio adoptado

Mostrar cache inmediatamente y reconciliar en segundo plano.

Este patrón pasa a considerarse una regla de UX para futuras pantallas del sistema.

---

### PERF-73.3.1 — Feed Cache-First

Commit: `fcda877`

* Eliminado comportamiento que ocultaba contenido visible durante refetch.
* El skeleton ahora solo aparece cuando no existen publicaciones renderizables.
* Se evita vaciar el feed ante errores temporales.
* Feed hidrata contenido desde cache antes de completar reconciliaciones secundarias.

Resultado:

* Al volver al Feed, las publicaciones aparecen instantáneamente.

---

### PERF-73.3.2 — Historias Cache-First

Commit: `72d0e8c`

* Creado hook `useHistoriasBar`.
* Incorporado cache TanStack para `/historias/bar`.
* Eliminada carga manual inicial de historias en Feed.
* Refetch de historias al cerrar viewer cuando existen vistas nuevas.

Resultado:

* La barra de historias reaparece instantáneamente al volver al Feed.

---

### PERF-73.3.3 — Ranking Cache-First

Commit: `357eabb`

* Ranking hidrata contenido desde cache antes de completar reconciliación de likes y guardados.
* Skeleton limitado a carga inicial real.
* Conservación de contenido visible durante refetch.

Resultado:

* Ranking vuelve a mostrarse inmediatamente al regresar a la pantalla.

---

### FEAT-73.4.1 — Hooks de Cache para Perfil de Comercio

Commit: `b0a06cd`

Se incorporan nuevos hooks:

* `useComercioDetalle`
* `usePublicacionesComercio`
* `useHistoriasComercio`

Basados en TanStack Query y reutilizando servicios existentes.

Resultado:

* Infraestructura preparada para cache-first en PerfilComercio.

---

### PERF-73.4.2 — Perfil de Comercio Cache-First

Commit: `29a5c4e`

* PerfilComercio deja de depender de una carga global bloqueante.
* Comercio, publicaciones e historias se hidratan desde cache.
* Métricas, analytics y seguimiento pasan a segundo plano.
* Se mantienen optimistic updates existentes.

Resultado:

* El perfil reaparece instantáneamente al volver a visitarlo.

---

### FIX-73.4.3 — Upload de Imagen en Publicaciones

Commit: `0af8bdc`

* Corregido envío de token en upload de imágenes desde PerfilComercio.
* `/media/upload` vuelve a recibir Authorization correctamente.

Resultado:

* Creación de publicaciones con imagen restaurada.

---

### FEAT-73.4.4 — Feed Prioriza Recencia

Commit: `be7d7ef`

Ajustada fórmula de ranking del Feed:

* Mayor peso para publicaciones recientes.
* Interacciones limitadas mediante caps.
* Afinidad IA mantenida.
* Ranking permanece sin modificaciones.

Resultado:

* Feed más dinámico y actualizado.
* Ranking continúa representando popularidad e interacción.

---

### PERF-73.4.5 — Estabilización de Seguimiento Visible

Commit: `ec396a1`

* Cache local de estado de seguimiento por comercio.
* Conservación visual de seguidores y estado siguiendo.
* Reconciliación posterior con backend.

Resultado:

* Eliminado el pestañeo visual del botón seguir/siguiendo y del contador de seguidores.

---

### Regla de Arquitectura UX Incorporada

Para futuras pantallas:

1. Mostrar cache inmediatamente.
2. Reconciliar datos en segundo plano.
3. Evitar loaders que oculten contenido ya disponible.
4. Evitar requests manuales duplicados.
5. Utilizar TanStack Query como fuente principal de cache.
6. Mantener backend como fuente de verdad.
7. Preservar optimistic updates cuando existan.

Pantallas ya adaptadas:

* Feed
* Historias Bar
* Ranking
* PerfilComercio

---

# ETAPA 74 — Cache-First Restante

## Objetivo

Completar la estrategia Cache-First en las pantallas que todavía conservaban fetches manuales, loaders bloqueantes o estados remotos fuera de TanStack Query.

## Cambios realizados

### ETAPA 74.1

Commit: f14ff31

- Se crea useMisComercios().
- Se agrega queryKeys.spaces.mis().
- ProfilePage migra GET /comercios/mis a TanStack Query.
- Invalidaciones cache-first para crear, editar, desactivar y reactivar espacios.
- Skeleton solo en carga inicial real.

### ETAPA 74.2

Commit: 0ea88ba

- Se crea useMisEspaciosSeguidos().
- Se agrega queryKeys.spaces.seguidos().
- VerSeguidosPage migra espacios seguidos a TanStack Query.
- Eliminado fetch manual principal.
- Lista visible durante refetch.

### ETAPA 74.3

Commit: 32b4e17

- RankingPage deja de usar fetch manual de guardadas.
- Se reutiliza cache de usePublicacionesGuardadas().
- Menos requests duplicados.

### ETAPA 74.4

Commit: c261a81

- PublicacionDetallePage evita loading bloqueante.
- Se introduce publicacionVisible.
- Skeleton solo cuando no existe información visible.
- Mejora experiencia al navegar desde listas.

### ETAPA 74.5

Commit: 12e2a0e

- FeedPage deja de usar fetch manual de guardadas.
- Se reutiliza cache de usePublicacionesGuardadas().
- Menos requests duplicados.
- Mantiene optimistic updates existentes.

## Auditoría Arquitectónica

Resultado:

- Arquitectura Enterprise validada.
- Backend continúa siendo fuente de verdad.
- Frontend mantiene responsabilidades de UX, cache y presentación.
- Sin hallazgos críticos.
- Sin migraciones de lógica de negocio al frontend.

## Estado final

ETAPA 74 cerrada.

Principios consolidados:

- Cache visible primero.
- Refetch en background.
- Skeletons solo en primera carga real.
- Menos fetches manuales.
- Menos estados duplicados.
- TanStack Query como estrategia principal de cache.

---

## ETAPA 77.2 — Discovery conectado al buscador predictivo

- Discovery conectado al buscador predictivo.
- Nuevo service taxonomy_search_services.py.
- Cache interno lazy para TaxonomyNode.
- Buscador prioriza texto nombre, Discovery fuerte, texto/Discovery débil y embeddings.
- Fallback de embeddings para evitar 500 si local provider falla.
- Frontend no modificado.
- Schemas no modificados.
- Validado endpoint /buscar/sugerencias con ropa, remera, indumentaria.

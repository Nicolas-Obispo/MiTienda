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

**Estado:** Próxima

### Objetivo

Retomar evolución funcional de FeedGo! sobre la arquitectura Enterprise ya consolidada.

### Foco previsto

- Products.
- Rubros.
- Secciones.
- Mejoras UX.
- Historias móvil.
- Nuevas capacidades de producto.

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

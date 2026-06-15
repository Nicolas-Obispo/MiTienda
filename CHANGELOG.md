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

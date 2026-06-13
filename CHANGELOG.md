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


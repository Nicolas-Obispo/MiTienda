/**
 * socialOptimisticUtils.js
 *
 * ETAPA 67 — SOCIAL ENTERPRISE
 *
 * Responsabilidad:
 * - Centralizar optimistic updates sociales.
 * - Evitar duplicación entre Feed, Ranking,
 *   PerfilComercio, Profile y Detalle.
 * - Mantener lógica reusable y rollback-friendly.
 */

/**
 * safeCounter
 *
 * Evita contadores negativos.
 */
function safeCounter(value, delta) {
  return Math.max(0, (value || 0) + delta);
}

/**
 * optimisticToggleLike
 *
 * Aplica actualización optimistic de like
 * sobre una colección de publicaciones.
 */
export function optimisticToggleLike(publicaciones, publicacionId) {
  return publicaciones.map((publicacion) => {
    if (publicacion.id !== publicacionId) {
      return publicacion;
    }

    const nextLiked = !Boolean(publicacion.liked_by_me);
    const delta = nextLiked ? 1 : -1;

    return {
      ...publicacion,
      liked_by_me: nextLiked,
      likes_count: safeCounter(publicacion.likes_count, delta),
      interacciones_count: safeCounter(
        publicacion.interacciones_count,
        delta
      ),
    };
  });
}

/**
 * optimisticToggleGuardado
 *
 * Aplica actualización optimistic de guardado
 * sobre una colección de publicaciones.
 */
export function optimisticToggleGuardado(
  publicaciones,
  publicacionId
) {
  return publicaciones.map((publicacion) => {
    if (publicacion.id !== publicacionId) {
      return publicacion;
    }

    const nextSaved = !Boolean(publicacion.guardada_by_me);
    const delta = nextSaved ? 1 : -1;

    return {
      ...publicacion,
      guardada_by_me: nextSaved,
      guardados_count: safeCounter(publicacion.guardados_count, delta),
      interacciones_count: safeCounter(
        publicacion.interacciones_count,
        delta
      ),
    };
  });
}

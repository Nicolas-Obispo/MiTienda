// Utilidades compartidas para actualizar publicaciones en la cache de TanStack Query.
// Objetivo: que Feed, Ranking y Detalle puedan sincronizar likes/guardados
// sin duplicar lógica local en cada pantalla.

function esPublicacionPorId(item, publicacionId) {
  return Number(item?.id) === Number(publicacionId);
}

function actualizarPublicacionEnLista(lista, publicacionId, updater) {
  if (!Array.isArray(lista)) return lista;

  return lista.map((item) => {
    if (!esPublicacionPorId(item, publicacionId)) return item;

    return updater(item);
  });
}

function actualizarPublicacionEnData(data, publicacionId, updater) {
  if (!data) return data;

  // Caso: detalle directo de una publicación
  if (esPublicacionPorId(data, publicacionId)) {
    return updater(data);
  }

  // Caso: array directo de publicaciones
  if (Array.isArray(data)) {
    return actualizarPublicacionEnLista(data, publicacionId, updater);
  }

  // Caso: respuesta paginada o agrupada
  return {
    ...data,
    publicaciones: actualizarPublicacionEnLista(
      data.publicaciones,
      publicacionId,
      updater
    ),
    items: actualizarPublicacionEnLista(data.items, publicacionId, updater),
    results: actualizarPublicacionEnLista(data.results, publicacionId, updater),
    data: actualizarPublicacionEnLista(data.data, publicacionId, updater),
  };
}

export function actualizarPublicacionEnCache(queryClient, publicacionId, updater) {
  queryClient.setQueriesData(
    {
      predicate: (query) => {
        const keyText = JSON.stringify(query.queryKey || []);

        return (
          keyText.includes("feed") ||
          keyText.includes("ranking") ||
          keyText.includes("posts") ||
          keyText.includes("publicaciones")
        );
      },
    },
    (oldData) => actualizarPublicacionEnData(oldData, publicacionId, updater)
  );
}

export function aplicarLikeOptimistaEnCache(queryClient, publicacionId) {
  actualizarPublicacionEnCache(queryClient, publicacionId, (publicacion) => {
    const likedActual = Boolean(publicacion?.liked_by_me);
    const proximoLiked = !likedActual;
    const delta = proximoLiked ? 1 : -1;

    return {
      ...publicacion,
      liked_by_me: proximoLiked,
      likes_count: Math.max(0, (publicacion?.likes_count || 0) + delta),
      interacciones_count: Math.max(
        0,
        (publicacion?.interacciones_count || 0) + delta
      ),
    };
  });
}

export function aplicarGuardadoOptimistaEnCache(queryClient, publicacionId) {
  actualizarPublicacionEnCache(queryClient, publicacionId, (publicacion) => {
    const guardadaActual = Boolean(publicacion?.guardada_by_me);
    const proximaGuardada = !guardadaActual;
    const delta = proximaGuardada ? 1 : -1;

    return {
      ...publicacion,
      guardada_by_me: proximaGuardada,
      guardados_count: Math.max(0, (publicacion?.guardados_count || 0) + delta),
      interacciones_count: Math.max(
        0,
        (publicacion?.interacciones_count || 0) + delta
      ),
    };
  });
}

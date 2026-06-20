// Utilidades compartidas para actualizar publicaciones en la cache de TanStack Query.
// Objetivo: que Feed, Ranking y Detalle puedan sincronizar likes/guardados
// sin duplicar lógica local en cada pantalla.

function esPublicacionPorId(item, publicacionId) {
  return Number(item?.id) === Number(publicacionId);
}

function esQueryKeyDePublicaciones(queryKey) {
  const keyText = JSON.stringify(queryKey || []);

  return (
    keyText.includes("feed") ||
    keyText.includes("ranking") ||
    keyText.includes("posts") ||
    keyText.includes("publicaciones")
  );
}

function esQueryKeyPostsGuardadas(queryKey) {
  return (
    Array.isArray(queryKey) &&
    queryKey[0] === "posts" &&
    queryKey[1] === "guardadas"
  );
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

function quitarPublicacionDeLista(lista, publicacionId) {
  if (!Array.isArray(lista)) return lista;

  return lista.filter((item) => !esPublicacionPorId(item, publicacionId));
}

function quitarPublicacionDeData(data, publicacionId) {
  if (!data) return data;

  if (esPublicacionPorId(data, publicacionId)) {
    return null;
  }

  if (Array.isArray(data)) {
    return quitarPublicacionDeLista(data, publicacionId);
  }

  return {
    ...data,
    publicaciones: quitarPublicacionDeLista(data.publicaciones, publicacionId),
    items: quitarPublicacionDeLista(data.items, publicacionId),
    results: quitarPublicacionDeLista(data.results, publicacionId),
    data: quitarPublicacionDeLista(data.data, publicacionId),
  };
}

function obtenerPublicacionDeLista(lista, publicacionId) {
  if (!Array.isArray(lista)) return null;

  return lista.find((item) => esPublicacionPorId(item, publicacionId)) || null;
}

function obtenerPublicacionDeData(data, publicacionId) {
  if (!data) return null;

  if (esPublicacionPorId(data, publicacionId)) {
    return data;
  }

  if (Array.isArray(data)) {
    return obtenerPublicacionDeLista(data, publicacionId);
  }

  return (
    obtenerPublicacionDeLista(data.publicaciones, publicacionId) ||
    obtenerPublicacionDeLista(data.items, publicacionId) ||
    obtenerPublicacionDeLista(data.results, publicacionId) ||
    obtenerPublicacionDeLista(data.data, publicacionId)
  );
}

function insertarPublicacionEnLista(lista, publicacion) {
  if (!Array.isArray(lista)) return lista;

  if (lista.some((item) => esPublicacionPorId(item, publicacion.id))) {
    return lista;
  }

  return [{ ...publicacion, guardada_by_me: true }, ...lista];
}

function insertarPublicacionEnData(data, publicacion) {
  if (!data || !publicacion?.id) return data;

  if (Array.isArray(data)) {
    return insertarPublicacionEnLista(data, publicacion);
  }

  return {
    ...data,
    publicaciones: insertarPublicacionEnLista(data.publicaciones, publicacion),
    items: insertarPublicacionEnLista(data.items, publicacion),
    results: insertarPublicacionEnLista(data.results, publicacion),
    data: insertarPublicacionEnLista(data.data, publicacion),
  };
}

export function publicacionesQueryPredicate(query) {
  return esQueryKeyDePublicaciones(query.queryKey);
}

export function publicacionesQueryFilters() {
  return {
    predicate: publicacionesQueryPredicate,
  };
}

export function snapshotPublicacionesCache(queryClient) {
  return queryClient
    .getQueryCache()
    .findAll(publicacionesQueryFilters())
    .map((query) => ({
      queryKey: query.queryKey,
      data: queryClient.getQueryData(query.queryKey),
    }));
}

export function restaurarSnapshotCache(queryClient, snapshotCache) {
  if (!Array.isArray(snapshotCache)) return;

  snapshotCache.forEach((snapshot) => {
    queryClient.setQueryData(snapshot.queryKey, snapshot.data);
  });
}

export function invalidarPublicacionesQueries(queryClient) {
  return queryClient.invalidateQueries(publicacionesQueryFilters());
}

export function obtenerPublicacionEnCache(queryClient, publicacionId) {
  const queries = queryClient.getQueryCache().findAll(publicacionesQueryFilters());

  for (const query of queries) {
    const publicacion = obtenerPublicacionDeData(
      queryClient.getQueryData(query.queryKey),
      publicacionId
    );

    if (publicacion) return publicacion;
  }

  return null;
}

export function actualizarPublicacionEnCache(queryClient, publicacionId, updater) {
  queryClient.setQueriesData(
    publicacionesQueryFilters(),
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

export function actualizarGuardadasOptimistaEnCache({
  queryClient,
  publicacionId,
  estabaGuardada,
}) {
  if (estabaGuardada) {
    queryClient.setQueriesData(
      {
        predicate: (query) => esQueryKeyPostsGuardadas(query.queryKey),
      },
      (oldData) => quitarPublicacionDeData(oldData, publicacionId)
    );

    return;
  }

  const publicacion = obtenerPublicacionEnCache(queryClient, publicacionId);

  if (!publicacion) return;

  queryClient.setQueriesData(
    {
      predicate: (query) => esQueryKeyPostsGuardadas(query.queryKey),
    },
    (oldData) => insertarPublicacionEnData(oldData, publicacion)
  );
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

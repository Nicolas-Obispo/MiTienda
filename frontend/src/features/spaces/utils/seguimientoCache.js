import { queryKeys } from "../../../core/constants/queryKeys.js";

function normalizarEstadoSeguimiento(data) {
  if (typeof data?.siguiendo !== "boolean") return undefined;
  return {
    ...data,
    siguiendo: data.siguiendo,
    seguidores_count:
      typeof data.seguidores_count === "number" ? data.seguidores_count : null,
  };
}

function actualizarListaSeguidos(data, { comercio, siguiendo }) {
  if (!Array.isArray(data)) return data;
  const comercioId = Number(comercio?.id);
  if (!comercioId) return data;
  if (!siguiendo) {
    return data.filter((item) => Number(item?.id) !== comercioId);
  }
  if (data.some((item) => Number(item?.id) === comercioId)) return data;
  return [comercio, ...data];
}

export function snapshotSeguimientoCaches(queryClient, comercioId) {
  return {
    status: queryClient.getQueryData(queryKeys.spaces.followingStatus(comercioId)),
    seguidos: queryClient
      .getQueryCache()
      .findAll({ queryKey: queryKeys.spaces.seguidosRoot() })
      .map((query) => ({
        queryKey: query.queryKey,
        data: queryClient.getQueryData(query.queryKey),
      })),
  };
}

export function restaurarSeguimientoCaches(queryClient, comercioId, snapshot) {
  queryClient.setQueryData(
    queryKeys.spaces.followingStatus(comercioId),
    snapshot?.status
  );
  for (const entry of snapshot?.seguidos || []) {
    queryClient.setQueryData(entry.queryKey, entry.data);
  }
}

export function aplicarSeguimientoEnCache({
  queryClient,
  comercioId,
  comercio,
  estado,
}) {
  const estadoNormalizado = normalizarEstadoSeguimiento(estado);
  if (!estadoNormalizado) return;
  queryClient.setQueryData(
    queryKeys.spaces.followingStatus(comercioId),
    estadoNormalizado
  );
  queryClient.setQueriesData(
    { queryKey: queryKeys.spaces.seguidosRoot() },
    (data) =>
      actualizarListaSeguidos(data, {
        comercio,
        siguiendo: estadoNormalizado.siguiendo,
      })
  );
}

export function crearEstadoSeguimientoOptimista(estadoActual) {
  if (typeof estadoActual?.siguiendo !== "boolean") return undefined;
  const siguiendo = !estadoActual.siguiendo;
  const seguidoresCount = estadoActual.seguidores_count;
  return {
    ...estadoActual,
    siguiendo,
    seguidores_count:
      typeof seguidoresCount === "number"
        ? Math.max(0, seguidoresCount + (siguiendo ? 1 : -1))
        : null,
  };
}

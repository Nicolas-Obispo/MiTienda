import { useQuery } from "@tanstack/react-query";

import { httpGet } from "@core";
import { queryKeys } from "@core/constants/queryKeys";
import { retryExceptNotFound } from "@core/query/retryPolicies";

/*
|--------------------------------------------------------------------------
| usePublicacionDetalle
|--------------------------------------------------------------------------
|
| Responsabilidad:
| - obtener detalle de una publicación
| - centralizar cache del detalle
| - permitir sincronización con Feed y Tendencias
|
*/

async function fetchPublicacionDetalle(publicacionId) {
  const token = localStorage.getItem("access_token");
  return httpGet(`/publicaciones/${publicacionId}`, token);
}

export function usePublicacionDetalle(publicacionId) {
  return useQuery({
    queryKey: queryKeys.posts.detalle(Number(publicacionId)),
    queryFn: () => fetchPublicacionDetalle(publicacionId),
    enabled: Boolean(publicacionId),
    staleTime: 1000 * 30,
    retry: retryExceptNotFound,
  });
}

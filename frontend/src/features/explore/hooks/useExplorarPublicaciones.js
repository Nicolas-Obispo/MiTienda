import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { fetchPublicacionesPublicas } from "@features/posts";

/*
|--------------------------------------------------------------------------
| useExplorarPublicaciones
|--------------------------------------------------------------------------
|
| Responsabilidad:
| - obtener publicaciones públicas para Explorar
| - reutilizar cache TanStack Query
| - mantener backend como fuente de verdad
|
*/

export function useExplorarPublicaciones({
  q = null,
  limit = 20,
  offset = 0,
}) {
  const query = String(q || "").trim() || null;

  return useQuery({
    queryKey: queryKeys.explore.posts({
      q: query,
      limit,
      offset,
    }),

    queryFn: () =>
      fetchPublicacionesPublicas({
        q: query,
        limit,
        offset,
      }),

    staleTime: 1000 * 30,
    retry: 1,
  });
}

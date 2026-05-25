import { useQuery } from "@tanstack/react-query";

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
  limit = 20,
  offset = 0,
}) {
  return useQuery({
    queryKey: [
      "explore",
      "posts",
      {
        limit,
        offset,
      },
    ],

    queryFn: () =>
      fetchPublicacionesPublicas({
        limit,
        offset,
      }),

    staleTime: 1000 * 30,
    retry: 1,
  });
}

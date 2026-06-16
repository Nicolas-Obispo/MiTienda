import { useInfiniteQuery } from "@tanstack/react-query";

import { listarComerciosActivos } from "@features/spaces";

/*
|--------------------------------------------------------------------------
| useExplorarEspacios
|--------------------------------------------------------------------------
|
| Responsabilidad:
| - obtener espacios para Explorar
| - reutilizar cache TanStack Query
| - manejar paginación incremental con useInfiniteQuery
| - mantener backend como fuente de verdad
|
*/

export function useExplorarEspacios({
  q = null,
  smart = false,
  lat = null,
  lng = null,
  radio_km = null,
  limit = 20,
}) {
  return useInfiniteQuery({
    queryKey: [
      "explore",
      "spaces",
      {
        q,
        smart,
        lat,
        lng,
        radio_km,
        limit,
      },
    ],

    initialPageParam: 0,

    queryFn: ({ pageParam = 0 }) =>
      listarComerciosActivos({
        q,
        smart,
        lat,
        lng,
        radio_km,
        limit,
        offset: pageParam,
      }),

    getNextPageParam: (lastPage, allPages) => {
      const ultimaPagina = Array.isArray(lastPage) ? lastPage : [];

      if (ultimaPagina.length < limit) {
        return undefined;
      }

      return allPages.length * limit;
    },

    staleTime: 1000 * 30,
    retry: 1,
  });
}

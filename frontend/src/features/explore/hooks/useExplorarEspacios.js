import { useInfiniteQuery } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
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

export function getExplorarEspaciosInfiniteQueryOptions({
  q = null,
  smart = false,
  smart_semantic = false,
  lat = null,
  lng = null,
  radio_km = null,
  limit = 20,
}) {
  const params = {
    q,
    smart,
    smart_semantic,
    lat,
    lng,
    radio_km,
    limit,
  };

  return {
    queryKey: queryKeys.explore.spaces(params),

    initialPageParam: 0,

    queryFn: ({ pageParam = 0 }) =>
      listarComerciosActivos({
        ...params,
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
  };
}

export function useExplorarEspacios({
  q = null,
  smart = false,
  smart_semantic = false,
  lat = null,
  lng = null,
  radio_km = null,
  limit = 20,
}) {
  return useInfiniteQuery({
    ...getExplorarEspaciosInfiniteQueryOptions({
      q,
      smart,
      smart_semantic,
      lat,
      lng,
      radio_km,
      limit,
    }),
    placeholderData: (previousData) => previousData,
    retry: 1,
  });
}

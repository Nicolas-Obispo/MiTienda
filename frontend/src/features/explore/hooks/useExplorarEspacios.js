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
  city_key = null,
  province_code = null,
  country_code = null,
  scope = "local",
  expansion_km = null,
  positionRevision = 0,
  limit = 20,
  enabled = true,
}) {
  const params = {
    q,
    smart,
    smart_semantic,
    lat,
    lng,
    radio_km,
    city_key,
    province_code,
    country_code,
    scope,
    expansion_km,
    positionRevision,
    limit,
  };

  return {
    queryKey: queryKeys.explore.spaces(params),

    initialPageParam: 0,

    queryFn: ({ pageParam = 0 }) =>
      listarComerciosActivos({
        ...params,
        positionRevision: undefined,
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
    enabled,
  };
}

export function useExplorarEspacios({
  q = null,
  smart = false,
  smart_semantic = false,
  lat = null,
  lng = null,
  radio_km = null,
  city_key = null,
  province_code = null,
  country_code = null,
  scope = "local",
  expansion_km = null,
  positionRevision = 0,
  limit = 20,
  enabled = true,
}) {
  return useInfiniteQuery({
    ...getExplorarEspaciosInfiniteQueryOptions({
      q,
      smart,
      smart_semantic,
      lat,
      lng,
      radio_km,
      city_key,
      province_code,
      country_code,
      scope,
      expansion_km,
      positionRevision,
      limit,
      enabled,
    }),
    retry: 1,
  });
}

import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { getBuscarSugerencias } from "@features/search/services/sugerencias_busqueda_service";

const SUGGESTIONS_STALE_TIME_MS = 1000 * 60 * 5;

export function useSearchSuggestions({
  q = null,
  limit = 5,
  enabled = true,
} = {}) {
  const query = String(q || "").trim();
  const limitNormalizado = Math.min(Math.max(Number(limit) || 5, 1), 10);
  const puedeBuscar = enabled === true && query.length >= 2;

  return useQuery({
    queryKey: queryKeys.search.suggestions({
      q: query || null,
      limit: limitNormalizado,
    }),
    queryFn: () =>
      getBuscarSugerencias({
        q: query,
        limit: limitNormalizado,
      }),
    enabled: puedeBuscar,
    staleTime: SUGGESTIONS_STALE_TIME_MS,
    placeholderData: (previousData) => previousData,
  });
}

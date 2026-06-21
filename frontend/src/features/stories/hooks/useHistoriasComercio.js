import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { fetchHistoriasPorComercio } from "@features/stories/services/historias_service";

function esComercioIdValido(comercioId) {
  return Boolean(comercioId) && !Number.isNaN(Number(comercioId));
}

export function useHistoriasComercio(comercioId) {
  const comercioIdNumber = Number(comercioId);

  return useQuery({
    queryKey: queryKeys.stories.bySpace(comercioIdNumber),
    queryFn: async () => {
      const data = await fetchHistoriasPorComercio(comercioIdNumber);

      return Array.isArray(data) ? data : data?.items || [];
    },
    enabled: esComercioIdValido(comercioId),
    staleTime: 1000 * 60,
    retry: 1,
  });
}

import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { getPublicacionesDeComercio } from "@features/spaces/services/comercios_service";

function esComercioIdValido(comercioId) {
  return Boolean(comercioId) && !Number.isNaN(Number(comercioId));
}

export function usePublicacionesComercio(comercioId) {
  const comercioIdNumber = Number(comercioId);

  return useQuery({
    queryKey: queryKeys.spaces.publicaciones(comercioIdNumber),
    queryFn: async () => {
      const data = await getPublicacionesDeComercio(comercioIdNumber);

      return Array.isArray(data) ? data : data?.items || [];
    },
    enabled: esComercioIdValido(comercioId),
    staleTime: 1000 * 60,
    retry: 1,
  });
}

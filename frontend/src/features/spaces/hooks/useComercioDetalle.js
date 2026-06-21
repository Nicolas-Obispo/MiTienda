import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { getComercioById } from "@features/spaces/services/comercios_service";

function esComercioIdValido(comercioId) {
  return Boolean(comercioId) && !Number.isNaN(Number(comercioId));
}

export function useComercioDetalle(comercioId) {
  const comercioIdNumber = Number(comercioId);

  return useQuery({
    queryKey: queryKeys.spaces.detalle(comercioIdNumber),
    queryFn: () => getComercioById(comercioIdNumber),
    enabled: esComercioIdValido(comercioId),
    staleTime: 1000 * 60,
    retry: 1,
  });
}

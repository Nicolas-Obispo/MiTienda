import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { listarEspecialidadesPorRubro } from "@features/spaces/services/rubros_service";

export function useRubroEspecialidades(rubroId) {
  const id = Number(rubroId);

  return useQuery({
    queryKey: queryKeys.spaces.rubroEspecialidades(id || null),
    queryFn: () => listarEspecialidadesPorRubro(id),
    enabled: Boolean(id),
    staleTime: 1000 * 60 * 10,
    gcTime: 1000 * 60 * 30,
    retry: 1,
    placeholderData: (previousData) => previousData,
  });
}

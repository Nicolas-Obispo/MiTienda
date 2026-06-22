import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { obtenerMisEspaciosSeguidos } from "@features/spaces/services/seguidores_service";

export function useMisEspaciosSeguidos({
  lat = null,
  lng = null,
  enabled = true,
} = {}) {
  return useQuery({
    queryKey: queryKeys.spaces.seguidos({ lat, lng }),
    queryFn: async () => {
      const data = await obtenerMisEspaciosSeguidos({ lat, lng });

      return Array.isArray(data) ? data : data?.items || [];
    },
    enabled,
    staleTime: 1000 * 60,
    gcTime: 1000 * 60 * 5,
    retry: 1,
    placeholderData: (previousData) => previousData,
  });
}

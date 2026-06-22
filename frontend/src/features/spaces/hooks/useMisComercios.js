import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { getMisComercios } from "@features/spaces/services/comercios_service";

export function useMisComercios({ enabled = true } = {}) {
  return useQuery({
    queryKey: queryKeys.spaces.mis(),
    queryFn: async () => {
      const data = await getMisComercios();

      return Array.isArray(data) ? data : data?.items || [];
    },
    enabled,
    staleTime: 1000 * 60,
    gcTime: 1000 * 60 * 5,
    retry: 1,
    placeholderData: (previousData) => previousData,
  });
}

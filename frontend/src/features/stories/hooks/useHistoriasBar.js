import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { fetchHistoriasBarItems } from "@features/stories/services/historias_service";

export function useHistoriasBar() {
  return useQuery({
    queryKey: queryKeys.stories.bar(),
    queryFn: async () => {
      const data = await fetchHistoriasBarItems();

      return Array.isArray(data) ? data : data?.items || [];
    },
    staleTime: 1000 * 30,
    retry: 1,
  });
}

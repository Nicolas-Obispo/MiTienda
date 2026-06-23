import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { listarRubros } from "@features/spaces/services/rubros_service";

export function useRubros() {
  return useQuery({
    queryKey: queryKeys.spaces.rubros(),
    queryFn: listarRubros,
    staleTime: 1000 * 60 * 10,
    gcTime: 1000 * 60 * 30,
    retry: 1,
    placeholderData: (previousData) => previousData,
  });
}

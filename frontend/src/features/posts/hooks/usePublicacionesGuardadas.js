import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { fetchPublicacionesGuardadas } from "@features/posts/services/feed_service";

export function usePublicacionesGuardadas({ enabled = true } = {}) {
  return useQuery({
    queryKey: queryKeys.posts.guardadas(),
    queryFn: fetchPublicacionesGuardadas,
    enabled,
    staleTime: 1000 * 30,
    retry: 1,
  });
}

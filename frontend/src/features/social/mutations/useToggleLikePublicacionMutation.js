import { useMutation, useQueryClient } from "@tanstack/react-query";

import { aplicarLikeOptimistaEnCache, toggleLike } from "@features/social";

/*
|--------------------------------------------------------------------------
| useToggleLikePublicacionMutation
|--------------------------------------------------------------------------
|
| Responsabilidad:
| - ejecutar like/unlike con useMutation
| - aplicar optimistic update en cache compartida
| - sincronizar Feed + Ranking + Detalle + futuras listas
| - hacer rollback global si backend falla
|
*/

export function useToggleLikePublicacionMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: toggleLike,

    onMutate: async (publicacionId) => {
      await queryClient.cancelQueries();

      const snapshotCache = queryClient.getQueryCache().findAll().map((query) => ({
        queryKey: query.queryKey,
        data: queryClient.getQueryData(query.queryKey),
      }));

      aplicarLikeOptimistaEnCache(queryClient, publicacionId);

      return {
        snapshotCache,
      };
    },

    onError: (_error, _publicacionId, context) => {
      if (!context?.snapshotCache) return;

      context.snapshotCache.forEach((snapshot) => {
        queryClient.setQueryData(snapshot.queryKey, snapshot.data);
      });
    },
  });
}
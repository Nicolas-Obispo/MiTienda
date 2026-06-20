import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  aplicarLikeOptimistaEnCache,
  invalidarPublicacionesQueries,
  publicacionesQueryFilters,
  restaurarSnapshotCache,
  snapshotPublicacionesCache,
  toggleLike,
} from "@features/social";

/*
|--------------------------------------------------------------------------
| useToggleLikePublicacionMutation
|--------------------------------------------------------------------------
|
| Responsabilidad:
| - ejecutar like/unlike con useMutation
| - aplicar optimistic update en cache compartida
| - sincronizar Feed + Ranking + Detalle + futuras listas
| - hacer rollback selectivo si backend falla
|
*/

export function useToggleLikePublicacionMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: toggleLike,

    onMutate: async (publicacionId) => {
      await queryClient.cancelQueries(publicacionesQueryFilters());

      const snapshotCache = snapshotPublicacionesCache(queryClient);

      aplicarLikeOptimistaEnCache(queryClient, publicacionId);

      return {
        snapshotCache,
      };
    },

    onError: (_error, _publicacionId, context) => {
      if (!context?.snapshotCache) return;

      restaurarSnapshotCache(queryClient, context.snapshotCache);
    },

    onSettled: () => {
      return invalidarPublicacionesQueries(queryClient);
    },
  });
}

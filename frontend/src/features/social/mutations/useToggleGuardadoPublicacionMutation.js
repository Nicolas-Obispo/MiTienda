import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  actualizarGuardadasOptimistaEnCache,
  aplicarGuardadoOptimistaEnCache,
  guardadoQueryFilters,
  invalidarGuardadoQueries,
  restaurarSnapshotCache,
  snapshotPublicacionesCache,
  toggleGuardado,
} from "@features/social";

/*
|--------------------------------------------------------------------------
| useToggleGuardadoPublicacionMutation
|--------------------------------------------------------------------------
|
| Responsabilidad:
| - ejecutar guardar/quitar guardado con useMutation
| - aplicar optimistic update en cache compartida
| - sincronizar Feed + Ranking + Detalle + futuras listas
| - hacer rollback selectivo si backend falla
|
*/

export function useToggleGuardadoPublicacionMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: toggleGuardado,

    onMutate: async ({ publicacionId, estabaGuardada }) => {
      const queryFilters = guardadoQueryFilters();
      await queryClient.cancelQueries(queryFilters);

      const snapshotCache = snapshotPublicacionesCache(
        queryClient,
        queryFilters
      );

      aplicarGuardadoOptimistaEnCache(queryClient, publicacionId);
      actualizarGuardadasOptimistaEnCache({
        queryClient,
        publicacionId,
        estabaGuardada,
      });

      return {
        snapshotCache,
      };
    },

    onError: (_error, _publicacionId, context) => {
      if (!context?.snapshotCache) return;

      restaurarSnapshotCache(queryClient, context.snapshotCache);
    },

    onSettled: () => {
      return invalidarGuardadoQueries(queryClient);
    },
  });
}

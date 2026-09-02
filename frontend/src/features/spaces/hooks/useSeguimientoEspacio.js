import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { toggleSeguimientoEspacio } from "@features/social";
import { obtenerEstadoSeguimiento } from "@features/spaces/services/seguidores_service";
import {
  aplicarSeguimientoEnCache,
  crearEstadoSeguimientoOptimista,
  restaurarSeguimientoCaches,
  snapshotSeguimientoCaches,
} from "@features/spaces/utils/seguimientoCache";

function comercioIdValido(comercioId) {
  return Boolean(comercioId) && !Number.isNaN(Number(comercioId));
}

export function useEstadoSeguimientoEspacio(comercioId, { enabled = true } = {}) {
  const id = Number(comercioId);
  return useQuery({
    queryKey: queryKeys.spaces.followingStatus(id),
    queryFn: ({ signal }) => obtenerEstadoSeguimiento(id, { signal }),
    enabled: enabled && comercioIdValido(id),
    staleTime: 1000 * 60,
    retry: 1,
  });
}

export function useToggleSeguimientoEspacioMutation({ comercioId, comercio }) {
  const queryClient = useQueryClient();
  const id = Number(comercioId);

  return useMutation({
    mutationFn: ({ siguiendoActual }) =>
      toggleSeguimientoEspacio({ comercioId: id, siguiendo: siguiendoActual }),
    onMutate: async ({ siguiendoActual }) => {
      if (typeof siguiendoActual !== "boolean") {
        throw new Error("El estado de seguimiento todavia no esta disponible.");
      }
      await Promise.all([
        queryClient.cancelQueries({
          queryKey: queryKeys.spaces.followingStatus(id),
          exact: true,
        }),
        queryClient.cancelQueries({ queryKey: queryKeys.spaces.seguidosRoot() }),
      ]);
      const snapshot = snapshotSeguimientoCaches(queryClient, id);
      aplicarSeguimientoEnCache({
        queryClient,
        comercioId: id,
        comercio,
        estado: crearEstadoSeguimientoOptimista(snapshot.status),
      });
      return { snapshot };
    },
    onSuccess: (estadoConfirmado) => {
      aplicarSeguimientoEnCache({
        queryClient,
        comercioId: id,
        comercio,
        estado: estadoConfirmado,
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.spaces.seguidosRoot(),
        refetchType: "none",
      });
    },
    onError: (_error, _variables, context) => {
      restaurarSeguimientoCaches(queryClient, id, context?.snapshot);
    },
  });
}

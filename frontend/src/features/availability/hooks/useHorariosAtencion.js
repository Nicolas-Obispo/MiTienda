import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import {
  obtenerHorariosAtencion,
  reemplazarHorariosAtencion,
} from "@features/availability/services/horarios_atencion_service";

export const horariosAtencionQueryKeys = {
  detalle: (comercioId) => ["availability", "horarios", Number(comercioId)],
};

function esComercioIdValido(comercioId) {
  return Boolean(comercioId) && !Number.isNaN(Number(comercioId));
}

function actualizarHorarioEnComercio(comercio, comercioId, estadoHorario) {
  if (!comercio || Number(comercio.id) !== Number(comercioId)) return comercio;

  return {
    ...comercio,
    horario_atencion: estadoHorario,
  };
}

function actualizarHorarioEnPaginaExplorar(pagina, comercioId, estadoHorario) {
  if (!Array.isArray(pagina)) return pagina;

  return pagina.map((comercio) =>
    actualizarHorarioEnComercio(comercio, comercioId, estadoHorario)
  );
}

export function useHorariosAtencion(comercioId, { enabled = true } = {}) {
  const comercioIdNumber = Number(comercioId);

  return useQuery({
    queryKey: horariosAtencionQueryKeys.detalle(comercioIdNumber),
    queryFn: () => obtenerHorariosAtencion(comercioIdNumber),
    enabled: enabled && esComercioIdValido(comercioId),
    staleTime: 1000 * 60,
    retry: 1,
    placeholderData: (previousData) => previousData,
  });
}

export function useReemplazarHorariosAtencionMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: reemplazarHorariosAtencion,
    onSuccess: (data, variables) => {
      const comercioId = Number(variables.comercioId);
      const estadoHorario = data?.estado_horario || null;

      queryClient.setQueryData(
        horariosAtencionQueryKeys.detalle(comercioId),
        data
      );

      if (estadoHorario) {
        queryClient.setQueryData(queryKeys.spaces.mis(), (actual) => {
          if (!Array.isArray(actual)) return actual;

          return actual.map((comercio) =>
            actualizarHorarioEnComercio(comercio, comercioId, estadoHorario)
          );
        });

        queryClient.setQueryData(
          queryKeys.spaces.detalle(comercioId),
          (actual) => actualizarHorarioEnComercio(actual, comercioId, estadoHorario)
        );

        queryClient.setQueriesData(
          { queryKey: ["explore", "spaces"] },
          (actual) => {
            if (!actual?.pages) {
              return actualizarHorarioEnPaginaExplorar(
                actual,
                comercioId,
                estadoHorario
              );
            }

            return {
              ...actual,
              pages: actual.pages.map((pagina) =>
                actualizarHorarioEnPaginaExplorar(
                  pagina,
                  comercioId,
                  estadoHorario
                )
              ),
            };
          }
        );
      }

      queryClient.invalidateQueries({ queryKey: queryKeys.spaces.mis() });
      queryClient.invalidateQueries({
        queryKey: queryKeys.spaces.detalle(comercioId),
      });
      queryClient.invalidateQueries({ queryKey: ["explore", "spaces"] });
    },
  });
}

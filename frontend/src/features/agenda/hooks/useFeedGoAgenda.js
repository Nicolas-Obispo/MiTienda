import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import {
  actualizarElementoAgenda,
  cambiarEstadoElementoAgenda,
  crearElementoAgenda,
  listarElementosAgendaGeneral,
  listarElementosAgenda,
  obtenerOCrearContextoAgenda,
} from "@features/agenda/services/feedgo_agenda_service";

function isComercioIdValido(comercioId) {
  return Boolean(comercioId) && !Number.isNaN(Number(comercioId));
}

function agendaElementosBaseKey(comercioId) {
  return ["agenda", "elementos", Number(comercioId)];
}

function agendaGeneralBaseKey() {
  return ["agenda", "general"];
}

export function useAgendaContexto(comercioId, { enabled = true } = {}) {
  const comercioIdNumber = Number(comercioId);

  return useQuery({
    queryKey: queryKeys.agenda.contexto(comercioIdNumber),
    queryFn: () => obtenerOCrearContextoAgenda(comercioIdNumber),
    enabled: enabled && isComercioIdValido(comercioId),
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 15,
    retry: 1,
    placeholderData: (previousData) => previousData,
  });
}

export function useAgendaElementos(
  comercioId,
  { inicio = null, fin = null, estado = null, tipo = null, enabled = true } = {}
) {
  const comercioIdNumber = Number(comercioId);

  return useQuery({
    queryKey: queryKeys.agenda.elementos({
      comercioId: comercioIdNumber,
      inicio,
      fin,
      estado,
      tipo,
    }),
    queryFn: () =>
      listarElementosAgenda({
        comercioId: comercioIdNumber,
        inicio,
        fin,
        estado,
        tipo,
      }),
    enabled: enabled && isComercioIdValido(comercioId),
    staleTime: 1000 * 30,
    gcTime: 1000 * 60 * 10,
    retry: 1,
    placeholderData: (previousData) => previousData,
  });
}

export function useAgendaGeneralElementos({
  inicio = null,
  fin = null,
  estado = null,
  tipo = null,
  comercioId = null,
  enabled = true,
} = {}) {
  return useQuery({
    queryKey: queryKeys.agenda.general({
      inicio,
      fin,
      estado,
      tipo,
      comercioId,
    }),
    queryFn: () =>
      listarElementosAgendaGeneral({
        inicio,
        fin,
        estado,
        tipo,
        comercioId,
      }),
    enabled,
    staleTime: 1000 * 30,
    gcTime: 1000 * 60 * 10,
    retry: 1,
    placeholderData: (previousData) => previousData,
  });
}

export function useCrearElementoAgendaMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: crearElementoAgenda,
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: agendaElementosBaseKey(variables.comercioId),
      });
      queryClient.invalidateQueries({
        queryKey: agendaGeneralBaseKey(),
      });
      return data;
    },
  });
}

export function useActualizarElementoAgendaMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: actualizarElementoAgenda,
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: agendaElementosBaseKey(variables.comercioId),
      });
      queryClient.invalidateQueries({
        queryKey: agendaGeneralBaseKey(),
      });
      return data;
    },
  });
}

export function useCambiarEstadoElementoAgendaMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: cambiarEstadoElementoAgenda,
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: agendaElementosBaseKey(variables.comercioId),
      });
      queryClient.invalidateQueries({
        queryKey: agendaGeneralBaseKey(),
      });
      return data;
    },
  });
}

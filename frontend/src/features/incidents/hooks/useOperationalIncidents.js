import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { useAuth } from "@features/auth";
import {
  actOnOperationalIncident, getOperationalIncident,
  getOperationalIncidentTimeline, listOperationalIncidents,
  openOperationalIncident,
} from "@features/incidents/services/incidentsService";

export function useOperationalIncidents(filters) {
  const { accessToken } = useAuth();
  return useInfiniteQuery({
    queryKey: queryKeys.incidents.list(filters),
    queryFn: ({ pageParam, signal }) => listOperationalIncidents({ filters, cursor: pageParam, token: accessToken, signal }),
    initialPageParam: null,
    getNextPageParam: (page) => page.next_cursor ?? undefined,
    enabled: Boolean(accessToken),
  });
}

export function useOperationalIncident(publicId) {
  const { accessToken } = useAuth();
  return useQuery({
    queryKey: queryKeys.incidents.detail(publicId),
    queryFn: ({ signal }) => getOperationalIncident({ publicId, token: accessToken, signal }),
    enabled: Boolean(accessToken && publicId),
  });
}

export function useOperationalIncidentTimeline(publicId) {
  const { accessToken } = useAuth();
  return useQuery({
    queryKey: queryKeys.incidents.timeline(publicId),
    queryFn: ({ signal }) => getOperationalIncidentTimeline({ publicId, token: accessToken, signal }),
    enabled: Boolean(accessToken && publicId),
  });
}

function useIncidentMutation(mutationFn) {
  const { accessToken } = useAuth();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables) => mutationFn({ ...variables, token: accessToken }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.incidents.all }),
  });
}

export function useOpenOperationalIncident() { return useIncidentMutation(openOperationalIncident); }
export function useActOnOperationalIncident() { return useIncidentMutation(actOnOperationalIncident); }

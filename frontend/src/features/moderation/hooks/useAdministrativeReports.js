import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { useAuth } from "@features/auth";
import {
  listarDenunciasAdministrativas,
  obtenerDenunciaAdministrativa,
  listarDecisionesModeracion,
  crearDecisionModeracion,
} from "@features/moderation/services/denuncias_service";

export function useAdministrativeReports(filters, { enabled = true } = {}) {
  const { accessToken } = useAuth();

  return useInfiniteQuery({
    queryKey: queryKeys.moderation.reports.list(filters),
    queryFn: ({ pageParam, signal }) =>
      listarDenunciasAdministrativas({
        filters,
        cursor: pageParam,
        token: accessToken,
        signal,
      }),
    initialPageParam: null,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    enabled: Boolean(enabled && accessToken),
    retry: 1,
  });
}


export function useModerationDecisions(reportId) {
  const { accessToken } = useAuth();
  return useQuery({
    queryKey: queryKeys.moderation.reports.decisions(reportId),
    queryFn: ({ signal }) => listarDecisionesModeracion({ reportId, token: accessToken, signal }),
    enabled: Boolean(accessToken && reportId),
  });
}


export function useCreateModerationDecision(reportId) {
  const { accessToken } = useAuth();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => crearDecisionModeracion({ reportId, payload, token: accessToken }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.moderation.all }),
        queryClient.invalidateQueries({ queryKey: queryKeys.feed.all }),
        queryClient.invalidateQueries({ queryKey: queryKeys.ranking.all }),
        queryClient.invalidateQueries({ queryKey: queryKeys.spaces.all }),
        queryClient.invalidateQueries({ queryKey: queryKeys.stories.all }),
      ]);
    },
  });
}

export function useAdministrativeReportDetail(
  reportId,
  { enabled = true } = {},
) {
  const { accessToken } = useAuth();

  return useQuery({
    queryKey: queryKeys.moderation.reports.detail(reportId),
    queryFn: ({ signal }) =>
      obtenerDenunciaAdministrativa({
        reportId,
        token: accessToken,
        signal,
      }),
    enabled: Boolean(enabled && accessToken && reportId),
    retry: 1,
  });
}

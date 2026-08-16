import { useMutation, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { eliminarHistoria } from "@features/stories/services/historias_service";

export function useEliminarHistoriaMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ historiaId }) => eliminarHistoria(historiaId),
    onSuccess: (_data, { historiaId, comercioId }) => {
      queryClient.setQueryData(
        queryKeys.stories.bySpace(Number(comercioId)),
        (historias) =>
          Array.isArray(historias)
            ? historias.filter((historia) => historia.id !== historiaId)
            : historias
      );

      queryClient.invalidateQueries({
        queryKey: queryKeys.stories.bar(),
      });
    },
  });
}

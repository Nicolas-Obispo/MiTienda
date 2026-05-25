import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { fetchRankingPublicaciones } from "@features/posts";

/*
|--------------------------------------------------------------------------
| useRankingPublicaciones
|--------------------------------------------------------------------------
|
| Responsabilidad:
| - obtener publicaciones del ranking
| - manejar cache automáticamente
| - preparar shared cache social
|
*/

export function useRankingPublicaciones() {
  return useQuery({
    queryKey: queryKeys.ranking.publicaciones(),
    queryFn: fetchRankingPublicaciones,
    staleTime: 1000 * 30,
    retry: 1,
  });
}

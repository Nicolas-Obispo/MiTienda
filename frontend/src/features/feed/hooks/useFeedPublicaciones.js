import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { fetchFeedPublicaciones } from "@features/posts/services/feed_service";

/*
|--------------------------------------------------------------------------
| useFeedPublicaciones
|--------------------------------------------------------------------------
|
| Responsabilidad:
| - obtener publicaciones del feed
| - manejar cache automáticamente
| - centralizar loading/error/refetch
| - preparar optimistic/realtime future
|
*/

export function useFeedPublicaciones() {
  return useQuery({
    queryKey: queryKeys.feed.publicaciones(),

    queryFn: fetchFeedPublicaciones,

    /*
    |--------------------------------------------------------------------------
    | UX enterprise
    |--------------------------------------------------------------------------
    */

    staleTime: 1000 * 30,

    /*
    |--------------------------------------------------------------------------
    | Reintentos suaves
    |--------------------------------------------------------------------------
    */

    retry: 1,
  });
}

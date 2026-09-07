import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { getMe } from "@features/auth/services/authService";

/**
 * Fuente unica en memoria para el contrato privado GET /usuarios/me.
 * El bearer sigue siendo opaco y pertenece a AuthContext; este hook no lo
 * persiste ni interpreta.
 */
export function useCurrentUser(accessToken) {
  return useQuery({
    queryKey: queryKeys.users.me(),
    queryFn: () => getMe(accessToken),
    enabled: Boolean(accessToken),
  });
}

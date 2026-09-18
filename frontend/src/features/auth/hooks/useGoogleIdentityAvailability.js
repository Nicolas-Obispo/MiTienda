import { useQuery } from "@tanstack/react-query";

import { getGoogleIdentityAvailability } from "@features/auth/services/authService";

/**
 * El backend es el único owner de disponibilidad. Un error queda como no
 * disponible para no bloquear el acceso con contraseña ni mostrar detalles
 * de configuración OAuth.
 */
export function useGoogleIdentityAvailability() {
  const query = useQuery({
    queryKey: ["identity", "google", "availability"],
    queryFn: ({ signal }) => getGoogleIdentityAvailability({ signal }),
    staleTime: 60_000,
    retry: false,
  });

  return {
    ...query,
    isAvailable: query.data?.google_identity_available === true,
  };
}

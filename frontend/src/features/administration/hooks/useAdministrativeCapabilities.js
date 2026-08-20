import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { useAuth } from "@features/auth";
import { fetchMyAdministrativeCapabilities } from "@features/administration/services/administrationService";

const EMPTY_CAPABILITIES = Object.freeze([]);

export function useAdministrativeCapabilities() {
  const { accessToken, estaAutenticado, usuario } = useAuth();

  const query = useQuery({
    queryKey: queryKeys.administration.capabilities(usuario?.id),
    queryFn: () => fetchMyAdministrativeCapabilities(accessToken),
    enabled: Boolean(estaAutenticado && accessToken && usuario?.id),
    staleTime: 0,
  });

  const capacidades = query.data?.capacidades ?? EMPTY_CAPABILITIES;

  return {
    ...query,
    esOperador: query.data?.es_operador === true,
    capacidades,
    tieneCapacidad: (capacidad) => capacidades.includes(capacidad),
  };
}

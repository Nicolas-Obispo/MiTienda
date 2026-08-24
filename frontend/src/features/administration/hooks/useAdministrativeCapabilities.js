import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { useAuth } from "@features/auth";
import { fetchMyAdministrativeCapabilities } from "@features/administration/services/administrationService";
import { ADMINISTRATIVE_CAPABILITIES_QUERY_RUNTIME_OPTIONS } from "@features/administration/hooks/administrativeCapabilitiesQueryOptions";

const EMPTY_CAPABILITIES = Object.freeze([]);

export function useAdministrativeCapabilities() {
  const { accessToken, estaAutenticado, usuario } = useAuth();

  const query = useQuery({
    ...ADMINISTRATIVE_CAPABILITIES_QUERY_RUNTIME_OPTIONS,
    queryKey: queryKeys.administration.capabilities(usuario?.id),
    queryFn: () => fetchMyAdministrativeCapabilities(accessToken),
    enabled: Boolean(estaAutenticado && accessToken && usuario?.id),
  });

  const capacidades = query.data?.capacidades ?? EMPTY_CAPABILITIES;

  return {
    ...query,
    esOperador: query.data?.es_operador === true,
    capacidades,
    tieneCapacidad: (capacidad) => capacidades.includes(capacidad),
  };
}

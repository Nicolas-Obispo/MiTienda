import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@core/constants/queryKeys";
import { useAuth } from "@features/auth";
import {
  getOperationalStatus,
  inspectOperationalResource,
} from "@features/operations/services/operationalStatusService";


export function useOperationalStatus() {
  const { accessToken } = useAuth();
  return useQuery({
    queryKey: queryKeys.operations.status(),
    queryFn: ({ signal }) => getOperationalStatus({ token: accessToken, signal }),
    enabled: Boolean(accessToken),
  });
}


export function useOperationalResourceIntegrity(resourceType, resourceId) {
  const { accessToken } = useAuth();
  return useQuery({
    queryKey: queryKeys.operations.resourceIntegrity(resourceType, resourceId),
    queryFn: ({ signal }) => inspectOperationalResource({ resourceType, resourceId, token: accessToken, signal }),
    enabled: Boolean(accessToken && resourceType && resourceId),
  });
}

import { useProtectedAction } from "@core/access/useProtectedAction";

/** Adapter compatible; el owner único vive en ProtectedActionProvider. */
export function useProtectedActionRedirect() {
  return useProtectedAction();
}

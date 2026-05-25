import { useQuery } from "@tanstack/react-query";

import { listarComerciosActivos } from "@features/spaces";

/*
|--------------------------------------------------------------------------
| useExplorarEspacios
|--------------------------------------------------------------------------
|
| Responsabilidad:
| - obtener espacios para Explorar
| - reutilizar cache TanStack Query
| - mantener backend como fuente de verdad
|
*/

export function useExplorarEspacios({
  q = null,
  smart = false,
  limit = 20,
  offset = 0,
}) {
  return useQuery({
    queryKey: [
      "explore",
      "spaces",
      {
        q,
        smart,
        limit,
        offset,
      },
    ],

    queryFn: () =>
      listarComerciosActivos({
        q,
        smart,
        limit,
        offset,
      }),

    staleTime: 1000 * 30,
    retry: 1,
  });
}

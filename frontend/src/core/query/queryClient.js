import { QueryClient } from "@tanstack/react-query";

/*
|--------------------------------------------------------------------------
| QueryClient global enterprise
|--------------------------------------------------------------------------
|
| Responsabilidades:
| - cache global
| - retries automáticos
| - stale management
| - refetch inteligente
| - base offline/realtime future-ready
|
*/

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30,
      gcTime: 1000 * 60 * 5,
      retry: 1,
      refetchOnWindowFocus: false,
    },

    mutations: {
      retry: 1,
    },
  },
});

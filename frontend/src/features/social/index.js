/**
 * Punto de entrada del feature social.
 *
 * ETAPA 67/68 — SOCIAL ENTERPRISE + SHARED CACHE
 *
 * Desde este archivo se exponen utilidades,
 * hooks, mutations y servicios sociales reutilizables.
 */

export * from "./utils/socialOptimisticUtils";
export * from "./utils/socialCacheUtils";

export * from "./hooks/useSocialInteractions";
export * from "./services/socialInteractionsService";

/*
|--------------------------------------------------------------------------
| Mutations enterprise
|--------------------------------------------------------------------------
*/

export * from "./mutations/useToggleLikePublicacionMutation";
export * from "./mutations/useToggleGuardadoPublicacionMutation";

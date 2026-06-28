// frontend/src/features/spaces/index.js

// Pages
export { default as PerfilComercioPage } from "@features/spaces/pages/PerfilComercioPage";

// Services
export * from "@features/spaces/services/comercios_service";
export * from "@features/spaces/services/rubros_service";
export * from "@features/spaces/services/seguidores_service";
export * from "@features/spaces/services/comercios_metricas_sociales_service";
export * from "@features/spaces/services/comercios_analytics_service";

// Hooks
export * from "@features/spaces/hooks/useComercioDetalle";
export * from "@features/spaces/hooks/usePublicacionesComercio";
export * from "@features/spaces/hooks/useMisComercios";
export * from "@features/spaces/hooks/useMisEspaciosSeguidos";
export * from "@features/spaces/hooks/useRubros";
export * from "@features/spaces/hooks/useRubroEspecialidades";

export { default as VerSeguidosPage } from '@features/spaces/pages/VerSeguidosPage';

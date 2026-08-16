// frontend/src/core/index.js

// Services
export * from "@core/services/http_service";

// Components
export { default as ActiveLayer } from "@core/components/ActiveLayer";
export { useAnonymousDetailGate } from "@core/access/useAnonymousDetailGate";
export { useProtectedActionRedirect } from "@core/access/useProtectedActionRedirect";

// Theme
export { ThemeProvider, useTheme } from "@core/theme";

export { default as AppRouter } from '@core/router/AppRouter';

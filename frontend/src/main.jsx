import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

import "./index.css";

import { AppRouter, ThemeProvider } from "@core";
import { AuthProvider } from "@features/auth";
import { GeographicContextProvider } from "@shared";
import { queryClient } from "./core/query/queryClient";
import { registerServiceWorker } from "./pwa/registerServiceWorker";
import GeographicIdentityCoordinator from "./core/bootstrap/GeographicIdentityCoordinator";

/*
|--------------------------------------------------------------------------
| Bootstrap principal de FeedGo!
|--------------------------------------------------------------------------
|
| Orden de providers:
| 1. QueryClientProvider
| 2. AuthProvider
| 3. AppRouter
|
*/

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <GeographicContextProvider>
            <GeographicIdentityCoordinator>
              <AppRouter />
            </GeographicIdentityCoordinator>
          </GeographicContextProvider>
        </AuthProvider>

        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </ThemeProvider>
  </React.StrictMode>
);

const serviceWorkerRuntime = registerServiceWorker();

if (__FEEDGO_PWA_E2E__) {
  void import("./pwa/e2eBridge").then(({ installPwaE2eBridge }) => {
    installPwaE2eBridge(serviceWorkerRuntime, __FEEDGO_PWA_TEST_VERSION__);
  });
}

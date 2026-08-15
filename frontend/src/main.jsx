import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

import "./index.css";

import { AppRouter, ThemeProvider } from "@core";
import { AuthProvider } from "@features/auth";
import { GeographicContextProvider } from "@shared";
import { queryClient } from "./core/query/queryClient";

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
            <AppRouter />
          </GeographicContextProvider>
        </AuthProvider>

        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </ThemeProvider>
  </React.StrictMode>
);

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/service-worker.js")
      .catch((err) => console.error("Error SW:", err));
  });
}

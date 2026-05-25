import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

import "./index.css";

import { AppRouter } from "@core";
import { AuthProvider } from "@features/auth";
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
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>

      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </React.StrictMode>
);

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/service-worker.js")
      .then(() => console.log("Service Worker registrado"))
      .catch((err) => console.error("Error SW:", err));
  });
}

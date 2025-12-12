import React from "react";
import ReactDOM from "react-dom/client";

// Contexto de autenticación (estado global)
import { AuthProvider } from "./context/AuthContext";

// Router principal de la aplicación
import AppRouter from "./router/AppRouter";

// Estilos globales
import "./index.css";

/**
 * Punto de entrada de la aplicación React.
 * La app completa queda envuelta por AuthProvider
 * para que cualquier componente pueda acceder al estado de auth.
 */
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  </React.StrictMode>
);

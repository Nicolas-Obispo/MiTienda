import React from "react";
import ReactDOM from "react-dom/client";

// Contexto de autenticación (estado global)
import { AuthProvider } from "./context/AuthContext";

// Router principal de la aplicación
import AppRouter from "./router/AppRouter";

// 🔥 IMPORT GLOBAL DE TAILWIND (OBLIGATORIO)
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  </React.StrictMode>
);

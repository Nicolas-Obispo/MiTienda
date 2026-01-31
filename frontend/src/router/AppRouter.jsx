// frontend/src/router/AppRouter.jsx

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

// Páginas
import Home from "../pages/Home";
import Login from "../pages/Login";
import FeedPage from "../pages/FeedPage";
import RankingPage from "../pages/RankingPage";
import ProfilePage from "../pages/ProfilePage";
import PerfilComercioPage from "../pages/PerfilComercioPage";

// Layout
import MainLayout from "../layouts/MainLayout";

// Auth
import { useAuth } from "../context/useAuth";

/**
 * getStoredToken
 * Lee un token directamente desde storage para evitar el "rebote"
 * en pestañas nuevas (antes de que el AuthContext se hidrate).
 */
function getStoredToken() {
  const keys = [
    "token",
    "accessToken",
    "access_token",
    "authToken",
    "AUTH_TOKEN",
    "mitienda_token",
    "mplaza_token",
  ];

  // localStorage
  try {
    for (const k of keys) {
      const v = window?.localStorage?.getItem(k);
      if (v && v !== "null" && v !== "undefined") return v;
    }
  } catch (_) {}

  // sessionStorage (por si tu implementación lo usa)
  try {
    for (const k of keys) {
      const v = window?.sessionStorage?.getItem(k);
      if (v && v !== "null" && v !== "undefined") return v;
    }
  } catch (_) {}

  return null;
}

/**
 * getIsAuthenticated
 * Unifica el criterio:
 * - Si el contexto ya sabe (estaAutenticado boolean), usamos eso.
 * - Si NO está listo todavía, usamos token desde el contexto.
 * - Si el contexto todavía no cargó nada, usamos token desde storage.
 */
function getIsAuthenticated(auth) {
  if (typeof auth?.estaAutenticado === "boolean") return auth.estaAutenticado;

  const tokenFromContext = auth?.token ?? auth?.accessToken ?? auth?.access_token;
  if (tokenFromContext) return true;

  const tokenFromStorage = getStoredToken();
  return Boolean(tokenFromStorage);
}

/**
 * ProtectedRoute
 */
function ProtectedRoute({ children }) {
  const auth = useAuth();
  const isAuthenticated = getIsAuthenticated(auth);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

/**
 * PublicOnlyRoute
 */
function PublicOnlyRoute({ children }) {
  const auth = useAuth();
  const isAuthenticated = getIsAuthenticated(auth);

  if (isAuthenticated) {
    return <Navigate to="/feed" replace />;
  }

  return children;
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Home />} />

          <Route
            path="/login"
            element={
              <PublicOnlyRoute>
                <Login />
              </PublicOnlyRoute>
            }
          />

          <Route
            path="/feed"
            element={
              <ProtectedRoute>
                <FeedPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/ranking"
            element={
              <ProtectedRoute>
                <RankingPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/perfil"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/comercios/:id"
            element={
              <ProtectedRoute>
                <PerfilComercioPage />
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

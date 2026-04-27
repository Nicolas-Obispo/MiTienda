// frontend/src/router/AppRouter.jsx

import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";

// Páginas
import Home from "../pages/Home";
import Login from "../pages/Login";
import Registro from "../pages/Registro";
import FeedPage from "../pages/FeedPage";
import RankingPage from "../pages/RankingPage";
import ProfilePage from "../pages/ProfilePage";
import PerfilComercioPage from "../pages/PerfilComercioPage";
import ExplorarPage from "../pages/ExplorarPage";
import PublicacionDetallePage from "../pages/PublicacionDetallePage";

// Layout
import MainLayout from "../layouts/MainLayout";

// Auth
import { useAuth } from "../context/useAuth";

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

  try {
    for (const k of keys) {
      const v = window?.localStorage?.getItem(k);
      if (v && v !== "null" && v !== "undefined") return v;
    }
  } catch (_) {}

  try {
    for (const k of keys) {
      const v = window?.sessionStorage?.getItem(k);
      if (v && v !== "null" && v !== "undefined") return v;
    }
  } catch (_) {}

  return null;
}

function getIsAuthenticated(auth) {
  if (typeof auth?.estaAutenticado === "boolean") return auth.estaAutenticado;

  const tokenFromContext = auth?.token ?? auth?.accessToken ?? auth?.access_token;
  if (tokenFromContext) return true;

  const tokenFromStorage = getStoredToken();
  return Boolean(tokenFromStorage);
}

function ProtectedRoute({ children }) {
  const auth = useAuth();
  const isAuthenticated = getIsAuthenticated(auth);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function PublicOnlyRoute({ children }) {
  const auth = useAuth();
  const isAuthenticated = getIsAuthenticated(auth);

  if (isAuthenticated) {
    return <Navigate to="/feed" replace />;
  }

  return children;
}

/**
 * GuestExploreRoute
 * -----------------
 * Permite explorar sin sesión, pero después de 5 minutos
 * redirige al usuario a login/registro.
 */
function GuestExploreRoute({ children }) {
  const auth = useAuth();
  const navigate = useNavigate();
  const isAuthenticated = getIsAuthenticated(auth);

  useEffect(() => {
    if (isAuthenticated) return;

    const timer = setTimeout(() => {
      navigate("/login", {
        replace: true,
        state: {
          message:
            "Para seguir explorando y guardar publicaciones, iniciá sesión o registrate.",
        },
      });
    }, 5 * 60 * 1000);

    return () => clearTimeout(timer);
  }, [isAuthenticated, navigate]);

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
            path="/registro"
            element={
              <PublicOnlyRoute>
                <Registro />
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
            path="/explorar"
            element={
              <GuestExploreRoute>
                <ExplorarPage />
              </GuestExploreRoute>
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
              <GuestExploreRoute>
                <PerfilComercioPage />
              </GuestExploreRoute>
            }
          />

          <Route
            path="/publicaciones/:id"
            element={
              <GuestExploreRoute>
                <PublicacionDetallePage />
              </GuestExploreRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
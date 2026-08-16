// frontend/src/router/AppRouter.jsx

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

// Páginas
import { Home } from "@features/home";
import { Login } from "@features/auth";
import { Registro } from "@features/auth";
import { FeedPage } from "@features/feed";
import { RankingPage } from "@features/posts";
import { ProfilePage } from "@features/auth";
import { PerfilComercioPage } from "@features/spaces";
import { ExplorarPage } from "@features/explore";
import { PublicacionDetallePage } from "@features/posts";
import { VerSeguidosPage } from "@features/spaces";
import { PrivacyPolicyPage, TermsPage } from "@features/legal";

// Layout
import { MainLayout } from "@shared";

// Auth
import { useAuth } from "@features/auth";

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
  } catch {
    // Storage access can be blocked by browser privacy settings.
  }

  try {
    for (const k of keys) {
      const v = window?.sessionStorage?.getItem(k);
      if (v && v !== "null" && v !== "undefined") return v;
    }
  } catch {
    // Storage access can be blocked by browser privacy settings.
  }

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
 * Permite descubrir contenido público sin sesión. Las mutaciones protegidas
 * conservan sus guards y el detalle de espacio aplica su gate específico.
 */
function GuestExploreRoute({ children }) {
  return children;
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/terminos-y-condiciones" element={<TermsPage />} />
          <Route path="/politica-de-privacidad" element={<PrivacyPolicyPage />} />

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
            path="/ver-seguidos"
            element={
              <ProtectedRoute>
                <VerSeguidosPage />
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

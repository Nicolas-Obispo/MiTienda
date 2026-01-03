// frontend/src/router/AppRouter.jsx

// React Router: componentes necesarios para manejar rutas
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

// Importamos las páginas
import Home from "../pages/Home";
import Login from "../pages/Login";
// Feed (ETAPA 32)
import FeedPage from "../pages/FeedPage";
// Ranking (ETAPA 34)
import RankingPage from "../pages/RankingPage";

// Importamos el layout principal
import MainLayout from "../layouts/MainLayout";

// Auth
import { useAuth } from "../context/useAuth";

/**
 * ProtectedRoute
 * Bloquea rutas si no hay sesión.
 */
function ProtectedRoute({ children }) {
  const auth = useAuth();

  // Soporta distintas implementaciones posibles sin romper:
  // - isAuthenticated (ideal)
  // - token / accessToken / access_token
  const isAuthenticated =
    auth?.isAuthenticated ??
    Boolean(auth?.token ?? auth?.accessToken ?? auth?.access_token);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

/**
 * PublicOnlyRoute
 * Si el usuario ya está logueado, evita entrar a /login.
 */
function PublicOnlyRoute({ children }) {
  const auth = useAuth();

  const isAuthenticated =
    auth?.isAuthenticated ??
    Boolean(auth?.token ?? auth?.accessToken ?? auth?.access_token);

  if (isAuthenticated) {
    return <Navigate to="/feed" replace />;
  }

  return children;
}

/**
 * AppRouter
 * Define todas las rutas de la aplicación.
 */
export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Rutas con layout principal */}
        <Route element={<MainLayout />}>
          <Route path="/" element={<Home />} />

          {/* Login público (si hay sesión, redirige a /feed) */}
          <Route
            path="/login"
            element={
              <PublicOnlyRoute>
                <Login />
              </PublicOnlyRoute>
            }
          />

          {/* Feed protegido (ETAPA 37) */}
          <Route
            path="/feed"
            element={
              <ProtectedRoute>
                <FeedPage />
              </ProtectedRoute>
            }
          />

          {/* Ranking protegido (ETAPA 37) */}
          <Route
            path="/ranking"
            element={
              <ProtectedRoute>
                <RankingPage />
              </ProtectedRoute>
            }
          />

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

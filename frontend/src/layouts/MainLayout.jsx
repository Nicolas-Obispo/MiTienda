import { Outlet, Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";

/**
 * MainLayout
 * -----------
 * Layout principal (UI + navegación).
 *
 * ETAPA 41 – Opción A:
 * - Navegación coherente tipo app
 * - Sin sesión: Inicio | Login
 * - Con sesión: Inicio | Feed | Ranking | Perfil | Cerrar sesión
 */
export default function MainLayout() {
  const { estaAutenticado, logout } = useAuth();
  const navigate = useNavigate();

  async function manejarLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Barra superior */}
      <header className="sticky top-0 z-20 border-b border-gray-800 bg-gray-950/80 backdrop-blur">
        <div className="mx-auto max-w-3xl px-4 py-3 flex items-center justify-between">
          {/* Navegación */}
          <nav className="flex items-center gap-4">
            <Link to="/" className="font-semibold hover:underline">
              Inicio
            </Link>

            {estaAutenticado && (
              <>
                <Link
                  to="/feed"
                  className="text-gray-300 hover:text-white hover:underline"
                >
                  Feed
                </Link>

                <Link
                  to="/ranking"
                  className="text-gray-300 hover:text-white hover:underline"
                >
                  Ranking
                </Link>

                <Link
                  to="/perfil"
                  className="text-gray-300 hover:text-white hover:underline"
                >
                  Perfil
                </Link>
              </>
            )}

            {!estaAutenticado && (
              <Link
                to="/login"
                className="text-gray-300 hover:text-white hover:underline"
              >
                Login
              </Link>
            )}
          </nav>

          {/* Estado sesión */}
          <div className="flex items-center gap-3">
            <span
              className={[
                "rounded-full px-3 py-1 text-xs font-semibold border",
                estaAutenticado
                  ? "bg-green-950/40 text-green-300 border-green-800"
                  : "bg-gray-900 text-gray-300 border-gray-800",
              ].join(" ")}
            >
              {estaAutenticado ? "Sesión activa" : "No autenticado"}
            </span>

            {estaAutenticado && (
              <button
                onClick={manejarLogout}
                className="rounded-xl border border-gray-700 bg-gray-900 px-3 py-1.5 text-sm font-semibold hover:bg-gray-800"
              >
                Cerrar sesión
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Contenido */}
      <main className="mx-auto max-w-3xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}

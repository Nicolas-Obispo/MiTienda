import { Outlet, Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";

/**
 * MainLayout
 * -----------
 * Layout principal (UI + navegación).
 *
 * - Sin sesión: Inicio | Login
 * - Con sesión: Inicio | Feed | Ranking | Explorar | Perfil | Cerrar sesión
 * - ✅ Muestra quién está logueado:
 *    - email (si existe)
 *    - sino ID (si existe)
 *    - sino "Activa"
 */
export default function MainLayout() {
  const { estaAutenticado, logout, usuario } = useAuth();
  const navigate = useNavigate();

  function getEtiquetaSesion() {
    if (!estaAutenticado) return "No autenticado";

    // 1) Identificador ideal
    const email =
      usuario?.email ||
      usuario?.correo ||
      usuario?.mail ||
      usuario?.sub || // si el backend lo mete así
      null;

    if (typeof email === "string" && email.trim()) {
      return `Sesión: ${email.trim()}`;
    }

    // 2) Fallback útil (al menos sabés con qué usuario estás)
    const id =
      usuario?.id ?? usuario?.user_id ?? usuario?.usuario_id ?? usuario?.uid ?? null;

    if (id !== null && id !== undefined) {
      return `Sesión: ID: ${id}`;
    }

    // 3) Último fallback
    return "Sesión: Activa";
  }

  async function manejarLogout() {
    await logout();
    navigate("/login");
  }

  const etiquetaSesion = getEtiquetaSesion();

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

                {/* ETAPA 48 — Explorar */}
                <Link
                  to="/explorar"
                  className="text-gray-300 hover:text-white hover:underline"
                >
                  Explorar
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
                "rounded-full px-3 py-1 text-xs font-semibold border max-w-[260px] truncate",
                estaAutenticado
                  ? "bg-green-950/40 text-green-300 border-green-800"
                  : "bg-gray-900 text-gray-300 border-gray-800",
              ].join(" ")}
              title={etiquetaSesion}
            >
              {etiquetaSesion}
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
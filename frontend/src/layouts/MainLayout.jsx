import {
  Outlet,
  Link,
  useNavigate,
  useLocation,
} from "react-router-dom";
import { useAuth } from "../context/useAuth";

export default function MainLayout() {
  const { estaAutenticado, logout, usuario } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  function getEtiquetaSesion() {
    if (!estaAutenticado) return "Visitante";

    const email =
      usuario?.email ||
      usuario?.correo ||
      usuario?.mail ||
      usuario?.sub ||
      null;

    if (typeof email === "string" && email.trim()) {
      return `Sesión: ${email.trim()}`;
    }

    return "Sesión activa";
  }

  async function manejarLogout() {
    await logout();
    navigate("/login");
  }

  /*
  ====================================================
  CONTROL DE ANCHO POR PÁGINA
  - Feed y Perfil ya manejan su layout interno
  - El resto usa contenedor centrado
  ====================================================
  */
  const paginasConLayoutPropio = ["/feed", "/perfil"];

  const usaLayoutPropio = paginasConLayoutPropio.some((path) =>
    location.pathname.startsWith(path)
  );

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* HEADER */}
      <header className="sticky top-0 z-30 border-b border-gray-800 bg-gray-950/90 backdrop-blur">
        <div className="mx-auto flex w-full max-w-3xl items-center justify-between px-4 py-3">
          {/* NAV */}
          <nav className="flex items-center gap-4">
            <Link
              to="/"
              className="text-base font-black tracking-tight text-white"
            >
              MiPlaza
            </Link>

            {/* SIEMPRE visible */}
            <Link
              to="/explorar"
              className="text-sm font-semibold text-gray-300 hover:text-white"
            >
              Explorar
            </Link>

            {/* SOLO con sesión */}
            {estaAutenticado && (
              <>
                <Link
                  to="/feed"
                  className="text-sm text-gray-300 hover:text-white"
                >
                  Feed
                </Link>

                <Link
                  to="/ranking"
                  className="text-sm text-gray-300 hover:text-white"
                >
                  Ranking
                </Link>

                <Link
                  to="/perfil"
                  className="text-sm text-gray-300 hover:text-white"
                >
                  Perfil
                </Link>
              </>
            )}
          </nav>

          {/* SESIÓN */}
          <div className="flex items-center gap-3">
            <span
              className={[
                "hidden rounded-full border px-3 py-1 text-xs font-semibold sm:inline-flex",
                estaAutenticado
                  ? "border-green-800 bg-green-950/40 text-green-300"
                  : "border-gray-800 bg-gray-900 text-gray-300",
              ].join(" ")}
            >
              {getEtiquetaSesion()}
            </span>

            {estaAutenticado ? (
              <button
                onClick={manejarLogout}
                className="rounded-xl border border-gray-700 bg-gray-900 px-3 py-1.5 text-sm font-semibold hover:bg-gray-800"
              >
                Cerrar sesión
              </button>
            ) : (
              <Link
                to="/login"
                className="rounded-xl bg-white px-4 py-2 text-sm font-bold text-gray-950 hover:opacity-90"
              >
                Ingresar
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* CONTENIDO */}
      <main
        className={
          usaLayoutPropio
            ? ""
            : "mx-auto w-full max-w-3xl px-4 py-6"
        }
      >
        <Outlet />
      </main>
    </div>
  );
}
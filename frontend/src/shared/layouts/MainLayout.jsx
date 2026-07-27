import {
  Outlet,
  Link,
  useLocation,
} from "react-router-dom";
import { useAuth } from "@features/auth";
import SessionInactivityGuard from "@features/auth/components/SessionInactivityGuard";

export default function MainLayout() {
  const { estaAutenticado } = useAuth();
  const location = useLocation();

  const paginasConLayoutPropio = ["/feed", "/perfil"];

  const usaLayoutPropio = paginasConLayoutPropio.some((path) =>
    location.pathname.startsWith(path)
  );

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <SessionInactivityGuard />

      {/* HEADER */}
      <header className="sticky top-0 z-30 border-b border-gray-800 bg-gray-950/90 backdrop-blur">
        <div className="mx-auto flex w-full max-w-3xl items-center justify-between gap-2 px-3 py-2 sm:gap-0 sm:px-4 sm:py-3">
          {/* LOGO */}
          <Link
            to="/"
            className="interactive-bubble interactive-bubble--flush shrink-0 items-center"
          >
            <div className="h-9 w-9 overflow-hidden rounded-full border border-gray-700 bg-gray-900 sm:h-12 sm:w-12">
              <img
                src="/logo_Feedgo.png"
                alt="MiPlaza"
                className="h-full w-full object-contain p-1"
              />
            </div>
          </Link>

          {/* NAV */}
          <nav className="flex min-w-0 flex-1 items-center gap-2 overflow-x-auto sm:flex-none sm:gap-4 sm:overflow-visible">
            {/* FEED */}
            {estaAutenticado && (
              <Link
                to="/feed"
                className="interactive-bubble group shrink-0 text-xs sm:text-sm"
              >
                <span
                  className={
                    location.pathname.startsWith("/feed")
                      ? "text-purple-300"
                      : "text-gray-300 group-hover:text-white"
                  }
                >
                🌎Feed
                </span>
              </Link>
            )}

            {/* MI PERFIL */}
            <Link
              to={estaAutenticado ? "/perfil" : "/registro"}
              state={
                estaAutenticado
                  ? undefined
                  : {
                      message:
                        "Creá tu cuenta para tener tu perfil en MiPlaza, guardar publicaciones y mostrar lo que hacés.",
                    }
              }
              className="interactive-bubble group shrink-0 text-xs font-semibold sm:text-sm"
            >
              <span
                className={
                  location.pathname.startsWith("/perfil")
                    ? "text-purple-300"
                    : "text-gray-300 group-hover:text-white"
                }
              >
              Mi Perfil
              </span>
            </Link>

            {/* RANKING */}
            {estaAutenticado && (
              <Link
                to="/ranking"
                className="interactive-bubble group shrink-0 text-xs sm:text-sm"
              >
                <span
                  className={
                    location.pathname.startsWith("/ranking")
                      ? "text-purple-300"
                      : "text-gray-300 group-hover:text-white"
                  }
                >
                Tendencias
                </span>
              </Link>
            )}

            {/* VER SEGUIDOS - solo con sesión */}
            {estaAutenticado && (
              <Link
                to="/ver-seguidos"
                className="interactive-bubble group shrink-0 text-xs sm:text-sm"
              >
                <span
                  className={
                    location.pathname.startsWith("/ver-seguidos")
                      ? "text-purple-300"
                      : "text-gray-300 group-hover:text-white"
                  }
                >
                Seguidos
                </span>
              </Link>
            )}

            {/* EXPLORAR */}
            <Link
              to="/explorar"
              className="interactive-bubble group shrink-0 text-xs font-semibold sm:text-sm"
            >
              <span
                className={
                  location.pathname.startsWith("/explorar")
                    ? "text-purple-300"
                    : "text-gray-300 group-hover:text-white"
                }
              >
              🔎Explorar
              </span>
            </Link>
          </nav>

          {/* SESIÓN */}
          <div className="flex shrink-0 items-center gap-2 sm:gap-3">
            {!estaAutenticado && (
              <Link
                to="/login"
                className="rounded-lg bg-white px-1.5 py-1 text-[11px] font-bold text-gray-950 hover:opacity-90 sm:rounded-xl sm:px-2 sm:text-xs"
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

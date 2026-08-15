import {
  Outlet,
  Link,
  useLocation,
} from "react-router-dom";
import { useAuth } from "@features/auth";
import SessionInactivityGuard from "@features/auth/components/SessionInactivityGuard";
import ConnectivityNotice from "@shared/components/ConnectivityNotice";

export default function MainLayout() {
  const { estaAutenticado } = useAuth();
  const location = useLocation();

  const paginasConLayoutPropio = ["/feed", "/perfil"];

  const usaLayoutPropio = paginasConLayoutPropio.some((path) =>
    location.pathname.startsWith(path)
  );

  return (
    <div className="min-h-screen bg-canvas text-primary">
      <SessionInactivityGuard />

      {/* HEADER */}
      <header className="sticky top-0 z-30 border-b border-border bg-surface backdrop-blur">
        <div className="mx-auto flex w-full max-w-3xl items-center justify-between gap-2 px-3 py-2 sm:gap-0 sm:px-4 sm:py-3">
          {/* LOGO */}
          <Link
            to="/"
            className="interactive-bubble interactive-bubble--flush shrink-0 items-center"
          >
            <div className="h-9 w-9 overflow-hidden rounded-full border border-border bg-surface-subtle sm:h-12 sm:w-12">
              <img
                src="/logo_Feedgo.png"
                alt="FeedGo"
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
                      ? "text-selected-text"
                      : "text-secondary group-hover:text-primary"
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
                        "Creá tu cuenta FeedGo para guardar publicaciones y administrar espacios.",
                    }
              }
              className="interactive-bubble group shrink-0 text-xs font-semibold sm:text-sm"
            >
              <span
                className={
                  location.pathname.startsWith("/perfil")
                    ? "text-selected-text"
                    : "text-secondary group-hover:text-primary"
                }
              >
              Perfil administrador
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
                      ? "text-selected-text"
                      : "text-secondary group-hover:text-primary"
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
                      ? "text-selected-text"
                      : "text-secondary group-hover:text-primary"
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
                    ? "text-selected-text"
                    : "text-secondary group-hover:text-primary"
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
                className="interactive-bubble interactive-bubble--primary-action rounded-lg bg-interactive-primary px-1.5 py-1 text-[11px] font-bold text-interactive-on-primary hover:bg-interactive-primary-hover sm:rounded-xl sm:px-2 sm:text-xs"
              >
                Ingresar
              </Link>
            )}
          </div>
        </div>
      </header>

      <ConnectivityNotice />

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

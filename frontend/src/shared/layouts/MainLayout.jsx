import {
  Outlet,
  Link,
  useLocation,
} from "react-router-dom";
import { useAuth } from "@features/auth";
import SessionInactivityGuard from "@features/auth/components/SessionInactivityGuard";
import ConnectivityNotice from "@shared/components/ConnectivityNotice";
import InteractiveLiquidLayers from "@shared/components/InteractiveLiquidLayers";
import { AdministrativeNavigationLink } from "@features/administration";

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
        <div className="mx-auto flex w-full max-w-3xl flex-wrap items-center justify-between gap-2 px-3 py-2 sm:flex-nowrap sm:gap-0 sm:px-4 sm:py-3">
          {/* LOGO */}
          <Link
            to="/"
            className="interactive-bubble interactive-bubble--flush interactive-bubble--liquid shrink-0 items-center"
          >
            <div className="h-9 w-9 overflow-hidden rounded-full border border-border bg-surface-subtle sm:h-12 sm:w-12">
              <img
                src="/logo_Feedgo.png"
                alt="FeedGo"
                className="h-full w-full object-contain p-1"
              />
            </div>
            <InteractiveLiquidLayers />
          </Link>

          {/* NAV */}
          <nav className="flex min-w-0 flex-1 items-center gap-2 overflow-x-auto sm:flex-none sm:gap-4 sm:overflow-visible">
            {/* FEED */}
            {estaAutenticado && (
              <Link
                to="/feed"
                className="interactive-bubble interactive-bubble--liquid group shrink-0 text-xs sm:text-sm"
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
                <InteractiveLiquidLayers />
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
              className="interactive-bubble interactive-bubble--liquid group shrink-0 text-xs font-semibold sm:text-sm"
            >
              <span
                className={
                  location.pathname === "/login"
                    ? "text-secondary group-hover:text-secondary"
                    : location.pathname.startsWith("/perfil")
                    ? "text-selected-text"
                    : "text-secondary group-hover:text-primary"
                }
              >
              Perfil administrador
              </span>
              <InteractiveLiquidLayers />
            </Link>

            {/* RANKING */}
            {estaAutenticado && (
              <Link
                to="/ranking"
                className="interactive-bubble interactive-bubble--liquid group shrink-0 text-xs sm:text-sm"
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
                <InteractiveLiquidLayers />
              </Link>
            )}

            {/* VER SEGUIDOS - solo con sesión */}
            {estaAutenticado && (
              <Link
                to="/ver-seguidos"
                className="interactive-bubble interactive-bubble--liquid group shrink-0 text-xs sm:text-sm"
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
                <InteractiveLiquidLayers />
              </Link>
            )}

            {/* EXPLORAR */}
            <Link
              to="/explorar"
              className="interactive-bubble interactive-bubble--liquid group shrink-0 text-xs font-semibold sm:text-sm"
            >
              <span
                className={
                  location.pathname === "/login"
                    ? "text-secondary group-hover:text-secondary"
                    : location.pathname.startsWith("/explorar")
                    ? "text-selected-text"
                    : "text-secondary group-hover:text-primary"
                }
              >
              🔎Explorar
              </span>
              <InteractiveLiquidLayers />
            </Link>
          </nav>

          {/* SESIÓN */}
          <div className={estaAutenticado
            ? "order-3 flex min-w-0 w-full items-center justify-end border-t border-border-subtle pt-2 sm:order-none sm:w-auto sm:shrink-0 sm:border-0 sm:pt-0"
            : "flex shrink-0 items-center gap-2 sm:gap-3"}>
            {!estaAutenticado && (
              <Link
                to="/login"
                className={`interactive-bubble interactive-bubble--liquid shrink-0 ${
                  location.pathname === "/login"
                    ? "group text-xs font-semibold sm:text-sm"
                    : "interactive-bubble--primary-action rounded-lg bg-interactive-primary px-1.5 py-1 text-[11px] font-bold text-interactive-on-primary hover:bg-interactive-primary-hover sm:rounded-xl sm:px-2 sm:text-xs"
                }`}
              >
                {location.pathname === "/login" ? (
                  <span className="text-secondary group-hover:text-secondary">
                    Ingresar
                  </span>
                ) : (
                  "Ingresar"
                )}
                <InteractiveLiquidLayers />
              </Link>
            )}

            {estaAutenticado && <AdministrativeNavigationLink />}
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

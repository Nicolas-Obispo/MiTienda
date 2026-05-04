import {
  Outlet,
  Link,
  useNavigate,
  useLocation,
} from "react-router-dom";
import { useAuth } from "../context/useAuth";

export default function MainLayout() {
  const { estaAutenticado, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  async function manejarLogout() {
    await logout();
    navigate("/login");
  }

  const paginasConLayoutPropio = ["/feed", "/perfil"];

  const usaLayoutPropio = paginasConLayoutPropio.some((path) =>
    location.pathname.startsWith(path)
  );

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* HEADER */}
      <header className="sticky top-0 z-30 border-b border-gray-800 bg-gray-950/90 backdrop-blur">
        <div className="mx-auto flex w-full max-w-3xl items-center justify-between px-4 py-3">
          {/* LOGO */}
          <Link to="/" className="flex items-center">
            <div className="h-12 w-12 overflow-hidden rounded-full border border-gray-700 bg-gray-900">
              <img
                src="/logo_miplaza.png"
                alt="MiPlaza"
                className="h-full w-full object-contain p-1"
              />
            </div>
          </Link>

          {/* NAV */}
          <nav className="flex items-center gap-4">
            {/* FEED */}
            {estaAutenticado && (
              <Link
                to="/feed"
                className={`text-sm ${
                  location.pathname.startsWith("/feed")
                    ? "text-purple-300"
                    : "text-gray-300 hover:text-white"
                }`}
              >
                Feed
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
              className={`text-sm font-semibold ${
                location.pathname.startsWith("/perfil")
                  ? "text-purple-300"
                  : "text-gray-300 hover:text-white"
              }`}
            >
              Mi Perfil
            </Link>

            {/* RANKING */}
            {estaAutenticado && (
              <Link
                to="/ranking"
                className={`text-sm ${
                  location.pathname.startsWith("/ranking")
                    ? "text-purple-300"
                    : "text-gray-300 hover:text-white"
                }`}
              >
                Ranking
              </Link>
            )}

            {/* VER SEGUIDOS */}
            <Link
              to="/ver-seguidos"
              className={`text-sm ${
                location.pathname.startsWith("/ver-seguidos")
                  ? "text-purple-300"
                  : "text-gray-300 hover:text-white"
              }`}
            >
              Seguidos
            </Link>


            {/* EXPLORAR */}
            <Link
              to="/explorar"
              className={`text-sm font-semibold ${
                location.pathname.startsWith("/explorar")
                  ? "text-purple-300"
                  : "text-gray-300 hover:text-white"
              }`}
            >
              🔎Explorar
            </Link>
          </nav>

          {/* SESIÓN */}
          <div className="flex items-center gap-3">
            {estaAutenticado ? (
              <button
                onClick={manejarLogout}
                className="rounded-xl border border-gray-700 bg-gray-900 px-2 py-1 text-xs font-semibold hover:bg-gray-800"
              >
                Cerrar sesión
              </button>
            ) : (
              <Link
                to="/login"
                className="rounded-xl bg-white px-2 py-1 text-xs font-bold text-gray-950 hover:opacity-90"
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
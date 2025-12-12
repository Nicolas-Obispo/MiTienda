import { Outlet, Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/**
 * MainLayout
 * Layout principal de la aplicación.
 * Contiene:
 * - Barra superior con navegación básica
 * - Botón de Logout (si está autenticado)
 * - Área de contenido (Outlet)
 */
export default function MainLayout() {
  const { estaAutenticado, logout } = useAuth();
  const navigate = useNavigate();

  /**
   * Maneja el proceso de Logout:
   * 1. Llama al logout del AuthContext
   * 2. Redirige a /login
   */
  async function manejarLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <div>
      {/* Barra superior */}
      <header
        style={{
          padding: "10px",
          backgroundColor: "#f0f0f0",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        {/* Navegación izquierda */}
        <nav>
          <Link to="/">Inicio</Link>
        </nav>

        {/* Acción derecha (Logout si está logueado) */}
        <div>
          {estaAutenticado && (
            <button onClick={manejarLogout}>
              Cerrar sesión
            </button>
          )}
        </div>
      </header>

      {/* Contenido principal */}
      <main style={{ padding: "20px" }}>
        <Outlet />
      </main>
    </div>
  );
}

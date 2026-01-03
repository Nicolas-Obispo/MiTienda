import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginUsuario } from "../services/authService";
import { useAuth } from "../context/useAuth";


/**
 * Login.jsx
 * ----------------
 * UI + lógica de login.
 *
 * Responsabilidades:
 * - Capturar credenciales
 * - Llamar al backend (/usuarios/login)
 * - Guardar el token vía AuthContext.login(token)
 * - Redirigir al Feed si el login es exitoso
 *
 * Nota:
 * - El guardado real en localStorage lo debe hacer AuthContext (lo vemos en el próximo paso si falta).
 */
export default function Login() {
  // Estados del formulario
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // Estados UI
  const [errorMensaje, setErrorMensaje] = useState("");
  const [cargando, setCargando] = useState(false);

  // Auth global
  const { login } = useAuth();

  // Navegación
  const navigate = useNavigate();

  /**
   * manejarSubmitLogin
   * - Envía credenciales al backend
   * - Guarda token en AuthContext
   * - Navega a /feed
   */
  async function manejarSubmitLogin(event) {
    event.preventDefault();
    setErrorMensaje("");
    setCargando(true);

    try {
      const token = await loginUsuario({ email, password });

      // Guardamos token en el estado global (y localStorage si el contexto lo implementa)
      login(token);

      // Redirigimos al feed
      navigate("/feed");
    } catch (error) {
      setErrorMensaje(error.message || "Error al iniciar sesión.");
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-80px)] flex items-center justify-center">
      <div className="w-full max-w-md rounded-2xl border border-gray-800 bg-gray-950 p-6 shadow-sm">
        <div className="mb-5">
          <h2 className="text-2xl font-semibold">Iniciar sesión</h2>
          <p className="mt-1 text-sm text-gray-400">
            Accedé para ver tu feed personalizado.
          </p>
        </div>

        <form onSubmit={manejarSubmitLogin} className="space-y-4">
          {/* Email */}
          <div>
            <label className="block text-sm text-gray-300 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="tuemail@dominio.com"
              className="w-full rounded-xl border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-600"
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm text-gray-300 mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
              className="w-full rounded-xl border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-600"
            />
          </div>

          {/* Error */}
          {errorMensaje && (
            <div className="rounded-xl border border-red-900 bg-red-950/40 p-3">
              <p className="text-sm text-red-200 break-words">
                {errorMensaje}
              </p>
            </div>
          )}

          {/* Botón */}
          <button
            type="submit"
            disabled={cargando}
            className="w-full rounded-xl bg-purple-600 px-4 py-2 text-sm font-semibold hover:bg-purple-500 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {cargando ? "Ingresando..." : "Ingresar"}
          </button>
        </form>

        <p className="mt-4 text-xs text-gray-500">
          Tip: si venías con un token viejo, al loguearte de nuevo se reemplaza.
        </p>
      </div>
    </div>
  );
}

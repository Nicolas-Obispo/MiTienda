import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { registrarUsuario, loginUsuario } from "../services/authService";
import { useAuth } from "../context/useAuth";

/**
 * Registro.jsx
 * ----------------
 * Pantalla de registro de usuarios.
 *
 * Responsabilidades:
 * - Capturar email y password
 * - Validar confirmación de password en frontend
 * - Registrar usuario en backend
 * - Hacer login automático después del registro
 * - Redirigir al feed
 */
export default function Registro() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmarPassword, setConfirmarPassword] = useState("");
  const [mostrarPassword, setMostrarPassword] = useState(false);
  const [mostrarConfirmarPassword, setMostrarConfirmarPassword] = useState(false);

  const [errorMensaje, setErrorMensaje] = useState("");
  const [cargando, setCargando] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  async function manejarSubmitRegistro(event) {
    event.preventDefault();
    setErrorMensaje("");

    if (password !== confirmarPassword) {
      setErrorMensaje("Las contraseñas no coinciden.");
      return;
    }

    setCargando(true);

    try {
      // 1. Registramos el usuario en backend.
      await registrarUsuario({ email, password });

      // 2. Iniciamos sesión automáticamente.
      const token = await loginUsuario({ email, password });

      // 3. Guardamos token globalmente.
      login(token);

      // 4. Redirigimos al feed.
      navigate("/feed");
    } catch (error) {
      setErrorMensaje(error.message || "Error al registrar usuario.");
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-px)] flex flex-col items-center justify-center px-4">

      {/* LOGO ARRIBA */}
      <div className="mb-0 animate-logo">
        <div className="h-80 w-80 overflow-hidden rounded-full bg-gray-950 flex items-center justify-center">
          <img
            src="/logo_miplaza.png"
            alt="MiPlaza"
            className="h-full w-full object-contain p-4"
          />
        </div>
      </div>

     {/* FORMULARIO */}
      <div className="w-full max-w-md rounded-2xl border border-gray-800 bg-gray-950 p-6 shadow-sm">
        <div className="mb-5">
          <h2 className="text-2xl font-semibold">Crear cuenta</h2>
          <p className="mt-1 text-sm text-gray-400">
            Registrate para guardar publicaciones, dar like y personalizar tu experiencia.
          </p>
        </div>

        <form
          onSubmit={manejarSubmitRegistro}
          autoComplete="off"
          className="space-y-4"
        >
          {/* Email */}
          <div>
            <label className="block text-sm text-gray-300 mb-1">Email</label>
            <input
              type="email"
              autoComplete="new-email"
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
              Contraseña
            </label>

            <div className="relative">
              <input
                type={mostrarPassword ? "text" : "password"}
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                placeholder="Mínimo 6 caracteres"
                className="w-full rounded-xl border border-gray-700 bg-gray-900 px-3 py-2 pr-10 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-600"
              />

              <button
                type="button"
                onClick={() => setMostrarPassword(!mostrarPassword)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
              >
                {mostrarPassword ? "🙉" : "🙈"}
              </button>
            </div>
          </div>

          {/* Confirmar Password */}
          <div>
            <label className="block text-sm text-gray-300 mb-1">
              Confirmar contraseña
            </label>

            <div className="relative">
              <input
                type={mostrarConfirmarPassword ? "text" : "password"}
                autoComplete="new-password"
                value={confirmarPassword}
                onChange={(e) => setConfirmarPassword(e.target.value)}
                required
                minLength={6}
                placeholder="Repetí tu contraseña"
                className="w-full rounded-xl border border-gray-700 bg-gray-900 px-3 py-2 pr-10 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-600"
              />

              <button
                type="button"
                onClick={() =>
                  setMostrarConfirmarPassword(!mostrarConfirmarPassword)
                }
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
              >
                {mostrarConfirmarPassword ? "🙉" : "🙈"}
              </button>
            </div>
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
            {cargando ? "Creando cuenta..." : "Crear cuenta"}
          </button>
        </form>

        <p className="mt-4 text-sm text-gray-400">
          ¿Ya tenés cuenta?{" "}
          <Link
            to="/login"
            className="font-medium text-purple-400 hover:text-purple-300"
          >
            Iniciá sesión
          </Link>
        </p>
      </div>
    </div>
  );
}
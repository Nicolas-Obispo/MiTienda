import { useState } from "react";
import { useNavigate, Link, useLocation } from "react-router-dom";
import { loginUsuario, useAuth } from "@features/auth";
import { Alert, Button, FormControl, Input, Surface } from "@shared";



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
  const [mostrarPassword, setMostrarPassword] = useState(false);

  // Estados UI
  const [errorMensaje, setErrorMensaje] = useState("");
  const [cargando, setCargando] = useState(false);

  // Auth global
  const { login } = useAuth();

  // Navegación
  const navigate = useNavigate();
  const location = useLocation();
  const mensajeContextual = location.state?.message || "";

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
    <div className="flex min-h-screen flex-col items-center justify-center bg-canvas px-4 text-primary">

      {/* LOGO ARRIBA */}
      <div className="mb-0 animate-logo">
        <div className="flex h-80 w-80 items-center justify-center overflow-hidden rounded-full bg-canvas">
          <img
            src="/logo_Feedgo.png"
            alt="FeedGo"
            className="h-full w-full object-contain p-4"
          />
        </div>
      </div>

     {/* FORMULARIO */}
      <Surface variant="elevated" className="w-full max-w-md p-6">
        <div className="mb-5">
          <h2 className="text-2xl font-semibold">Iniciar sesión</h2>
          <p className="mt-1 text-sm text-secondary">
            Accedé para ver tu feed personalizado.
          </p>
          {mensajeContextual && (
            <Surface variant="subtle" className="mt-4 p-3 text-sm">
              {mensajeContextual}
            </Surface>
          )}
        </div>

        <form onSubmit={manejarSubmitLogin} className="space-y-4">
          {/* Email */}
          <FormControl label="Email" labelFor="login-email">
            <Input
              id="login-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="tuemail@dominio.com"
              className="text-sm"
            />
          </FormControl>

          {/* Password */}
          <FormControl label="Password" labelFor="login-password">
            <Input
              id="login-password"
              type={mostrarPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
              className="text-sm"
              trailingAction={
                <Button
                  type="button"
                  onClick={() => setMostrarPassword(!mostrarPassword)}
                  variant="ghost"
                  iconOnly
                  aria-label={
                    mostrarPassword ? "Ocultar contraseña" : "Mostrar contraseña"
                  }
                >
                  <span aria-hidden="true">
                    {mostrarPassword ? "🙉" : "🙈"}
                  </span>
                </Button>
              }
            />
          </FormControl>

          {/* Error */}
          {errorMensaje && (
            <Alert role="alert" variant="danger" className="break-words">
              {errorMensaje}
            </Alert>
          )}

          {/* Botón */}
          <Button
            type="submit"
            disabled={cargando}
            variant="primary"
            className="w-full px-4 py-2 text-sm"
          >
            {cargando ? "Ingresando..." : "Ingresar"}
          </Button>
        </form>

        <div className="mt-4 space-y-2">
          <p className="text-xs text-muted">
            Tip: si venías con un token viejo, al loguearte de nuevo se reemplaza.
          </p>

          <p className="text-sm text-secondary">
            ¿No tenés cuenta?{" "}
            <Link
              to="/registro"
              className="font-medium text-brand underline decoration-current underline-offset-2 hover:text-brand-strong focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
            >
              Crear cuenta
            </Link>
          </p>
        </div>
      </Surface>
    </div>
  );
}

import { useState } from "react";
import { useNavigate, Link, useLocation } from "react-router-dom";
import { loginUsuario, useAuth } from "@features/auth";
import { Alert, Button, FormControl, Input, PasswordInput, Surface } from "@shared";
import { getInternalReturnTo } from "@core/navigation/internalReturnTo";



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
  const location = useLocation();
  const mensajeContextual = location.state?.message || "";
  const returnTo = getInternalReturnTo(location.state?.returnTo, "/feed");

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
      navigate(returnTo, { replace: true });
    } catch (error) {
      setErrorMensaje(error.message || "Error al iniciar sesión.");
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="flex flex-col items-center justify-start bg-canvas px-4 text-primary">

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
          <FormControl label="Contraseña" labelFor="login-password">
            <PasswordInput
              id="login-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
              className="text-sm"
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
            variant="ghost"
            className="w-full px-4 py-2 text-sm text-secondary hover:border-brand hover:text-secondary"
          >
            {cargando ? "Ingresando..." : "Ingresar"}
          </Button>
          <Link
            to="/recuperar-password"
            className="block text-center text-sm font-medium text-brand underline decoration-current underline-offset-2"
          >
            ¿Olvidaste tu contraseña?
          </Link>
        </form>

        <div className="mt-4 space-y-2">
          <p className="text-sm text-secondary">
            ¿No tenés cuenta?{" "}
            <Link
              to="/registro"
              state={{ message: mensajeContextual, returnTo }}
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

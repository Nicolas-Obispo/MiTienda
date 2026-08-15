import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { registrarUsuario, loginUsuario, useAuth } from "@features/auth";
import { Alert, Button, FormControl, Input, Surface } from "@shared";


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
  const [aceptaTerminos, setAceptaTerminos] = useState(false);
  const [aceptaPrivacidad, setAceptaPrivacidad] = useState(false);
  const [mostrarPassword, setMostrarPassword] = useState(false);
  const [mostrarConfirmarPassword, setMostrarConfirmarPassword] =
    useState(false);

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

    if (!aceptaTerminos || !aceptaPrivacidad) {
      setErrorMensaje(
        "Debes aceptar Terminos y Condiciones y Politica de Privacidad."
      );
      return;
    }

    setCargando(true);

    try {
      // 1. Registramos el usuario en backend.
      await registrarUsuario({
        email,
        password,
        aceptaTerminos,
        aceptaPrivacidad,
      });

      // 2. Iniciamos sesión automáticamente.
      const token = await loginUsuario({ email, password });

      // 3. Guardamos token globalmente.
      login(token);

      // 4. Activamos onboarding.
      sessionStorage.setItem("show_miplaza_welcome", "true");

      // 5. Redirigimos al feed.
      navigate("/feed");
    } catch (error) {
      setErrorMensaje(error.message || "Error al registrar usuario.");
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
          <h2 className="text-2xl font-semibold">Crear cuenta</h2>

          <p className="mt-1 text-sm text-secondary">
            Registrate para guardar publicaciones, dar like y administrar uno o
            varios espacios.
          </p>
        </div>

        <form
          onSubmit={manejarSubmitRegistro}
          autoComplete="off"
          className="space-y-4"
        >
          {/* Email */}
          <FormControl label="Email" labelFor="registro-email">
            <Input
              id="registro-email"
              type="email"
              autoComplete="new-email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="tuemail@dominio.com"
              className="text-sm"
            />
          </FormControl>

          {/* Password */}
          <FormControl labelFor="registro-password" label="Contraseña">
            <Input
              id="registro-password"
              type={mostrarPassword ? "text" : "password"}
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              placeholder="Mínimo 6 caracteres"
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

          {/* Confirmar Password */}
          <FormControl
            labelFor="registro-confirmar-password"
            label="Confirmar contraseña"
          >
            <Input
              id="registro-confirmar-password"
              type={mostrarConfirmarPassword ? "text" : "password"}
              autoComplete="new-password"
              value={confirmarPassword}
              onChange={(e) => setConfirmarPassword(e.target.value)}
              required
              minLength={6}
              placeholder="Repetí tu contraseña"
              className="text-sm"
              trailingAction={
                <Button
                  type="button"
                  onClick={() =>
                    setMostrarConfirmarPassword(!mostrarConfirmarPassword)
                  }
                  variant="ghost"
                  iconOnly
                  aria-label={
                    mostrarConfirmarPassword
                      ? "Ocultar confirmación de contraseña"
                      : "Mostrar confirmación de contraseña"
                  }
                >
                  <span aria-hidden="true">
                    {mostrarConfirmarPassword ? "🙉" : "🙈"}
                  </span>
                </Button>
              }
            />
          </FormControl>

          {/* Aceptaciones obligatorias */}
          <div className="space-y-3 rounded-xl border border-border bg-surface-subtle p-3">
            <label className="flex items-start gap-3 text-sm text-secondary">
              <input
                type="checkbox"
                checked={aceptaTerminos}
                onChange={(e) => setAceptaTerminos(e.target.checked)}
                required
                className="mt-1 h-4 w-4 rounded border-border-strong bg-surface accent-brand focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
              />
              <span>
                Acepto los{" "}
                <Link
                  to="/terminos-y-condiciones"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-brand underline decoration-current underline-offset-2 hover:text-brand-strong focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
                >
                  Terminos y Condiciones
                </Link>
                .
              </span>
            </label>

            <label className="flex items-start gap-3 text-sm text-secondary">
              <input
                type="checkbox"
                checked={aceptaPrivacidad}
                onChange={(e) => setAceptaPrivacidad(e.target.checked)}
                required
                className="mt-1 h-4 w-4 rounded border-border-strong bg-surface accent-brand focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
              />
              <span>
                Acepto la{" "}
                <Link
                  to="/politica-de-privacidad"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-brand underline decoration-current underline-offset-2 hover:text-brand-strong focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
                >
                  Politica de Privacidad
                </Link>
                .
              </span>
            </label>
          </div>

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
            className="w-full px-4 py-2 text-sm font-bold"
          >
            {cargando ? "Creando cuenta..." : "Crear cuenta"}
          </Button>
        </form>

        <p className="mt-4 text-sm text-secondary">
          ¿Ya tenés cuenta?{" "}

          <Link
            to="/login"
            className="font-medium text-brand underline decoration-current underline-offset-2 hover:text-brand-strong focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
          >
            Iniciá sesión
          </Link>
        </p>
      </Surface>
    </div>
  );
}

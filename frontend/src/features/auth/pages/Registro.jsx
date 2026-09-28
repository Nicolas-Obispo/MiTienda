import { useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { getInternalReturnTo } from "@core/navigation/internalReturnTo";
import {
  registrarUsuario,
  startGoogleAuthorization,
  useGoogleIdentityAvailability,
} from "@features/auth";
import { Alert, Button, FormControl, Input, PasswordInput, Surface } from "@shared";
import {
  evaluarPasswordRegistro,
  passwordRegistroValida,
} from "@features/auth/services/registrationValidation";


/**
 * Registro.jsx
 * ----------------
 * Pantalla de registro de usuarios.
 *
 * Responsabilidades:
 * - Capturar email y password
 * - Validar confirmación de password en frontend
 * - Registrar usuario en backend
 * - Comunicar un resultado neutral sin revelar existencia de cuenta
 */
export default function Registro() {
  const location = useLocation();
  const mensajeContextual = location.state?.message || "";
  const returnTo = getInternalReturnTo(location.state?.returnTo, "/feed");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmarPassword, setConfirmarPassword] = useState("");
  const [aceptaTerminos, setAceptaTerminos] = useState(false);
  const [aceptaPrivacidad, setAceptaPrivacidad] = useState(false);
  const [passwordTocado, setPasswordTocado] = useState(false);
  const [confirmacionTocada, setConfirmacionTocada] = useState(false);
  const [emailTocado, setEmailTocado] = useState(false);
  const [emailFormatoValido, setEmailFormatoValido] = useState(true);
  const [errorMensaje, setErrorMensaje] = useState("");
  const [mensajeRegistro, setMensajeRegistro] = useState("");
  const [cargando, setCargando] = useState(false);
  const [cargandoGoogle, setCargandoGoogle] = useState(false);
  const emailRef = useRef(null);
  const googleAuthorizationInFlightRef = useRef(false);

  const { isAvailable: googleIdentityAvailable } = useGoogleIdentityAvailability();
  const requisitosPassword = evaluarPasswordRegistro(password);
  const passwordValida = passwordRegistroValida(password);

  async function manejarSubmitRegistro(event) {
    event.preventDefault();
    setErrorMensaje("");
    setEmailTocado(true);
    setPasswordTocado(true);
    setConfirmacionTocada(true);

    if (!passwordValida) {
      return;
    }

    if (password !== confirmarPassword) {
      return;
    }

    if (!emailRef.current?.checkValidity()) {
      setEmailFormatoValido(false);
      return;
    }

    if (!aceptaTerminos || !aceptaPrivacidad) {
      setErrorMensaje(
        "Debes aceptar Términos y Condiciones y Política de Privacidad."
      );
      return;
    }

    setCargando(true);

    try {
      await registrarUsuario({
        email,
        password,
        aceptaTerminos,
        aceptaPrivacidad,
      });
      setMensajeRegistro(
        "Si pudimos crear la cuenta, ya podés ingresar. Si ya existía, ingresá o recuperá el acceso."
      );
      setPassword("");
      setConfirmarPassword("");
    } catch (error) {
      setErrorMensaje(error.message || "Error al registrar usuario.");
    } finally {
      setCargando(false);
    }
  }

  async function manejarRegistroGoogle() {
    if (
      !googleIdentityAvailable ||
      !aceptaTerminos ||
      !aceptaPrivacidad ||
      cargando ||
      cargandoGoogle ||
      googleAuthorizationInFlightRef.current
    ) {
      return;
    }

    googleAuthorizationInFlightRef.current = true;
    setErrorMensaje("");
    setCargandoGoogle(true);
    try {
      const result = await startGoogleAuthorization({
        purpose: "signup",
        returnTo,
        aceptaTerminos: true,
        aceptaPrivacidad: true,
      });
      window.location.assign(result.authorization_url);
    } catch {
      googleAuthorizationInFlightRef.current = false;
      setErrorMensaje("No pudimos iniciar el registro con Google. Intentá nuevamente más tarde.");
      setCargandoGoogle(false);
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
          noValidate
          className="space-y-4"
        >
          {/* Email */}
          <FormControl label="Usuario" labelFor="registro-email">
            <Input
              id="registro-email"
              ref={emailRef}
              type="email"
              autoComplete="new-email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setEmailFormatoValido(e.target.validity.valid);
              }}
              onBlur={(e) => {
                setEmailTocado(true);
                setEmailFormatoValido(e.target.validity.valid);
              }}
              required
              invalid={emailTocado && !emailFormatoValido}
              aria-describedby="registro-email-feedback"
              placeholder="nombre@correo.com"
              className="text-sm"
            />
            <div id="registro-email-feedback" aria-live="polite">
              {emailTocado && email && !emailFormatoValido && (
                <p className="mt-2 text-sm text-danger-text" role="alert">
                  Ingresá un correo electrónico válido.
                </p>
              )}

            </div>
          </FormControl>

          {/* Password */}
          <FormControl
            labelFor="registro-password"
            label="Contraseña"
          >
            <PasswordInput
              id="registro-password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setPasswordTocado(true);
              }}
              onBlur={() => setPasswordTocado(true)}
              required
              invalid={passwordTocado && !passwordValida}
              aria-describedby="registro-password-requisitos"
              placeholder="Creá una contraseña segura"
              className="text-sm"
            />
            <div
              id="registro-password-requisitos"
              className="mt-2 space-y-1 text-xs text-secondary"
              aria-live="polite"
            >
              <p className="font-medium">La contraseña debe tener:</p>
              {[
                ["longitud", "Al menos 8 caracteres"],
                ["mayuscula", "Una mayúscula"],
                ["minuscula", "Una minúscula"],
                ["numero", "Un número"],
                ["sinEspacios", "Sin espacios"],
                ["limiteBcrypt", "Hasta 72 bytes UTF-8"],
              ].map(([requisito, texto]) => (
                <p
                  key={requisito}
                  className={
                    requisitosPassword[requisito]
                      ? "text-success-text"
                      : passwordTocado
                        ? "text-danger-text"
                        : undefined
                  }
                >
                  <span aria-hidden="true">
                    {requisitosPassword[requisito] ? "✓" : "○"}
                  </span>{" "}
                  {texto}
                </p>
              ))}
            </div>
          </FormControl>

          {/* Confirmar Password */}
          <FormControl
            labelFor="registro-confirmar-password"
            label="Confirmar contraseña"
            error={
              confirmacionTocada && confirmarPassword !== password
                ? "Las contraseñas no coinciden."
                : null
            }
            errorId="registro-confirmar-password-error"
          >
            <PasswordInput
              id="registro-confirmar-password"
              autoComplete="new-password"
              value={confirmarPassword}
              onChange={(e) => {
                setConfirmarPassword(e.target.value);
                setConfirmacionTocada(true);
              }}
              onBlur={() => setConfirmacionTocada(true)}
              required
              invalid={
                confirmacionTocada && confirmarPassword !== password
              }
              aria-describedby={
                confirmacionTocada && confirmarPassword !== password
                  ? "registro-confirmar-password-error"
                  : undefined
              }
              placeholder="Repetí tu contraseña"
              className="text-sm"
              showLabel="Mostrar confirmación de contraseña"
              hideLabel="Ocultar confirmación de contraseña"
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
                  Términos y Condiciones
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
                  Política de Privacidad
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
          {mensajeRegistro && (
            <Alert role="status" variant="success" className="break-words">
              {mensajeRegistro}
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
          {googleIdentityAvailable && (
            <Button
              type="button"
              disabled={cargando || cargandoGoogle || !aceptaTerminos || !aceptaPrivacidad}
              variant="ghost"
              className="w-full px-4 py-2 text-sm text-secondary hover:border-brand hover:text-secondary"
              onClick={manejarRegistroGoogle}
            >
              {cargandoGoogle ? "Redirigiendo a Google..." : "Continuar con Google"}
            </Button>
          )}
          {googleIdentityAvailable && (!aceptaTerminos || !aceptaPrivacidad) && (
            <p className="text-center text-sm text-secondary" role="status">
              Aceptá Términos y Condiciones y Política de Privacidad para continuar con Google.
            </p>
          )}
        </form>

        <p className="mt-4 text-sm text-secondary">
          ¿Ya tenés cuenta?{" "}

          <Link
            to="/login"
            state={{ message: mensajeContextual, returnTo }}
            className="font-medium text-brand underline decoration-current underline-offset-2 hover:text-brand-strong focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
          >
            Iniciá sesión
          </Link>
        </p>
      </Surface>
    </div>
  );
}

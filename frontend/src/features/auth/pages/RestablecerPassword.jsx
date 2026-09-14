import { useLayoutEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import {
  PASSWORD_RESET_INVALID,
  extraerTokenVerificacionDelFragmento,
  restablecerPassword,
} from "@features/auth";
import { Button, FormControl, PasswordInput, Surface } from "@shared";
import {
  evaluarPasswordRegistro,
  passwordRegistroValida,
} from "@features/auth/services/registrationValidation";

export default function RestablecerPassword() {
  const secretRef = useRef(null);
  const [newPassword, setNewPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [passwordTouched, setPasswordTouched] = useState(false);
  const [confirmationTouched, setConfirmationTouched] = useState(false);
  const [status, setStatus] = useState(() => {
    const fragment = window.location.hash.startsWith("#")
      ? window.location.hash.slice(1)
      : window.location.hash;
    return new URLSearchParams(fragment).has("token") ? "editing" : "invalid";
  });
  const requirements = evaluarPasswordRegistro(newPassword);
  const valid = passwordRegistroValida(newPassword);

  useLayoutEffect(() => {
    const extracted = extraerTokenVerificacionDelFragmento();
    if (extracted) secretRef.current = extracted;
  }, []);

  async function submit(event) {
    event.preventDefault();
    setPasswordTouched(true);
    setConfirmationTouched(true);
    if (!valid || newPassword !== confirmation || !secretRef.current) return;
    const secret = secretRef.current;
    secretRef.current = null;
    setStatus("processing");
    try {
      await restablecerPassword({ token: secret, newPassword });
      setNewPassword("");
      setConfirmation("");
      setStatus("success");
    } catch (error) {
      setStatus(error.code === PASSWORD_RESET_INVALID ? "invalid" : "technical_error");
    }
  }

  if (status === "success") return (
    <main className="flex min-h-screen items-center justify-center bg-canvas px-4 text-primary">
      <Surface variant="elevated" className="w-full max-w-md p-6 text-center">
        <p>Listo, tu contraseña fue actualizada.</p>
        <Link to="/login" className="mt-5 inline-block font-medium text-brand underline">Iniciar sesión</Link>
      </Surface>
    </main>
  );

  if (status === "invalid" || status === "technical_error") return (
    <main className="flex min-h-screen items-center justify-center bg-canvas px-4 text-primary">
      <Surface variant="elevated" className="w-full max-w-md p-6 text-center">
        <p>{status === "invalid"
          ? "Este enlace ya no es válido. Pedí uno nuevo para continuar."
          : "No pudimos completar esto ahora. Intentá nuevamente en un momento."}</p>
      </Surface>
    </main>
  );

  return (
    <main className="flex min-h-screen items-center justify-center bg-canvas px-4 text-primary">
      <Surface variant="elevated" className="w-full max-w-md p-6">
        <h1 className="text-2xl font-semibold">Crear una nueva contraseña</h1>
        <form onSubmit={submit} noValidate className="mt-5 space-y-4">
          <FormControl label="Nueva contraseña" labelFor="reset-password">
            <PasswordInput id="reset-password" value={newPassword}
              autoComplete="new-password"
              onChange={(event) => { setNewPassword(event.target.value); setPasswordTouched(true); }}
              onBlur={() => setPasswordTouched(true)} required />
            <div className="mt-2 space-y-1 text-xs text-secondary">
              <p>La contraseña debe tener:</p>
              {[["longitud", "Al menos 8 caracteres"], ["mayuscula", "Una mayúscula"],
                ["minuscula", "Una minúscula"], ["numero", "Un número"],
                ["sinEspacios", "Sin espacios"]].map(([key, label]) => (
                <p key={key} className={requirements[key] ? "text-success-text" : passwordTouched ? "text-danger-text" : undefined}>
                  <span aria-hidden="true">{requirements[key] ? "✓" : "○"}</span> {label}
                </p>
              ))}
            </div>
          </FormControl>
          <FormControl label="Confirmar contraseña" labelFor="reset-confirmation"
            error={confirmationTouched && confirmation !== newPassword ? "Las contraseñas no coinciden." : null}
            errorId="reset-confirmation-error">
            <PasswordInput id="reset-confirmation" value={confirmation}
              autoComplete="new-password"
              onChange={(event) => { setConfirmation(event.target.value); setConfirmationTouched(true); }}
              onBlur={() => setConfirmationTouched(true)}
              invalid={confirmationTouched && confirmation !== newPassword}
              aria-describedby={confirmationTouched && confirmation !== newPassword ? "reset-confirmation-error" : undefined}
              showLabel="Mostrar confirmación de contraseña"
              hideLabel="Ocultar confirmación de contraseña"
              required />
          </FormControl>
          <Button type="submit" disabled={status === "processing"} className="w-full">
            {status === "processing" ? "Actualizando..." : "Actualizar contraseña"}
          </Button>
        </form>
      </Surface>
    </main>
  );
}

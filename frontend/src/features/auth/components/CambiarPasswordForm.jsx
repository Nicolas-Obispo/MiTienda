import { useState } from "react";

import {
  CURRENT_PASSWORD_INCORRECT,
  CURRENT_PASSWORD_RATE_LIMITED,
  cambiarPasswordAutenticado,
  useAuth,
} from "@features/auth";
import { Button, FormControl, PasswordInput } from "@shared";
import {
  evaluarPasswordRegistro,
  passwordRegistroValida,
} from "@features/auth/services/registrationValidation";

export default function CambiarPasswordForm({ onCancel, onSuccess }) {
  const { accessToken } = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [passwordTouched, setPasswordTouched] = useState(false);
  const [confirmationTouched, setConfirmationTouched] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const requirements = evaluarPasswordRegistro(newPassword);
  const valid = passwordRegistroValida(newPassword);

  function cancel() {
    setCurrentPassword("");
    setNewPassword("");
    setConfirmation("");
    setPasswordTouched(false);
    setConfirmationTouched(false);
    setFeedback(null);
    onCancel?.();
  }

  async function submit(event) {
    event.preventDefault();
    setPasswordTouched(true);
    setConfirmationTouched(true);
    setFeedback(null);
    if (!valid || newPassword !== confirmation || !accessToken) return;
    setSubmitting(true);
    try {
      await cambiarPasswordAutenticado(accessToken, { currentPassword, newPassword });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmation("");
      setPasswordTouched(false);
      setConfirmationTouched(false);
      if (onSuccess) {
        onSuccess();
      } else {
        setFeedback({ kind: "success", text: "Listo, tu contraseña fue actualizada." });
      }
    } catch (error) {
      if (error.code === CURRENT_PASSWORD_INCORRECT) {
        setCurrentPassword("");
        setFeedback({ kind: "error", text: "La contraseña actual no es correcta." });
      } else if (error.code === CURRENT_PASSWORD_RATE_LIMITED) {
        setFeedback({ kind: "error", text: "Hiciste varios intentos. Esperá un momento para volver a probar." });
      } else {
        setFeedback({ kind: "error", text: "No pudimos completar esto ahora. Intentá nuevamente en un momento." });
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={submit} noValidate className="space-y-3">
        <FormControl label="Contraseña actual" labelFor="current-password"
          error={feedback?.kind === "error" ? feedback.text : null}>
          <PasswordInput id="current-password" autoComplete="current-password"
            value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} required />
        </FormControl>
        <FormControl label="Nueva contraseña" labelFor="new-profile-password">
          <PasswordInput id="new-profile-password" autoComplete="new-password"
            value={newPassword}
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
        <FormControl label="Confirmar nueva contraseña" labelFor="confirm-profile-password"
          error={confirmationTouched && confirmation !== newPassword ? "Las contraseñas no coinciden." : null}
          errorId="confirm-profile-password-error">
          <PasswordInput id="confirm-profile-password" autoComplete="new-password"
            value={confirmation}
            onChange={(event) => { setConfirmation(event.target.value); setConfirmationTouched(true); }}
            onBlur={() => setConfirmationTouched(true)}
            invalid={confirmationTouched && confirmation !== newPassword}
            aria-describedby={confirmationTouched && confirmation !== newPassword ? "confirm-profile-password-error" : undefined}
            showLabel="Mostrar confirmación de contraseña"
            hideLabel="Ocultar confirmación de contraseña"
            required />
        </FormControl>
        {feedback?.kind === "success" && (
          <p className="text-sm text-success-text" role="status">{feedback.text}</p>
        )}
        <div className="flex flex-wrap gap-2">
          <Button type="submit" disabled={submitting} variant="secondary" className="px-3 py-2 text-xs">
            {submitting ? "Actualizando..." : "Actualizar contraseña"}
          </Button>
          <Button type="button" onClick={cancel} disabled={submitting} variant="secondary" className="px-3 py-2 text-xs">
            Cancelar
          </Button>
        </div>
    </form>
  );
}

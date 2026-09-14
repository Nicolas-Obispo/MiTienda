import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const read = (path) => readFile(new URL(path, import.meta.url), "utf8");

test("Perfil integra el cambio en su superficie privada", async () => {
  const profile = await read("../src/features/auth/pages/ProfilePage.jsx");
  assert.match(profile, /CambiarPasswordForm/);
  assert.match(profile, />\s*Cambiar contraseña\s*</);
  assert.match(profile, /showPasswordForm/);
});

test("formulario contiene campos y checklist exactos", async () => {
  const source = await read("../src/features/auth/components/CambiarPasswordForm.jsx");
  for (const text of ["Contraseña actual", "Nueva contraseña", "Confirmar nueva contraseña",
    "Al menos 8 caracteres", "Una mayúscula", "Una minúscula", "Un número", "Sin espacios"])
    assert.match(source, new RegExp(text));
  assert.match(source, /passwordRegistroValida/);
  assert.match(source, /Las contraseñas no coinciden\./);
});

test("feedback FeedGo traduce incorrecta, bloqueo, éxito y error", async () => {
  const source = await read("../src/features/auth/components/CambiarPasswordForm.jsx");
  for (const text of [
    "La contraseña actual no es correcta.",
    "Hiciste varios intentos. Esperá un momento para volver a probar.",
    "Listo, tu contraseña fue actualizada.",
    "No pudimos completar esto ahora. Intentá nuevamente en un momento.",
  ]) assert.match(source, new RegExp(text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  assert.doesNotMatch(source, /HTTP \d|current_password_rate_limited|current_password_incorrect/);
});

test("servicio es único consumidor HTTP y formulario limpia secretos tras éxito", async () => {
  const [service, form] = await Promise.all([
    read("../src/features/auth/services/authService.js"),
    read("../src/features/auth/components/CambiarPasswordForm.jsx"),
  ]);
  assert.match(service, /httpPatch\(\s*"\/usuarios\/me\/password"/);
  assert.match(service, /current_password: currentPassword/);
  assert.match(service, /new_password: newPassword/);
  assert.match(form, /setCurrentPassword\(""\)/);
  assert.match(form, /setNewPassword\(""\)/);
  assert.match(form, /setConfirmation\(""\)/);
  assert.doesNotMatch(form, /localStorage|sessionStorage|indexedDB|queryClient|navigation|returnTo/i);
});

test("frontend no implementa hashing, rate limiting ni revocación", async () => {
  const source = await read("../src/features/auth/components/CambiarPasswordForm.jsx");
  assert.doesNotMatch(source, /bcrypt|hashPassword|attempt_count|blocked_until|FeedGoSession|revocar/i);
});

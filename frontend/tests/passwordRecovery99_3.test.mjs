import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const read = (path) => readFile(new URL(path, import.meta.url), "utf8");

test("Login ofrece una unica entrada humana a recuperacion", async () => {
  const source = await read("../src/features/auth/pages/Login.jsx");
  assert.match(source, /to="\/recuperar-password"/);
  assert.match(source, /¿Olvidaste tu contraseña\?/);
});

test("recuperacion usa Usuario y respuesta uniforme", async () => {
  const [page, service] = await Promise.all([
    read("../src/features/auth/pages/RecuperarPassword.jsx"),
    read("../src/features/auth/services/authService.js"),
  ]);
  assert.match(page, /label="Usuario"/);
  assert.match(page, /Ingresá el correo que usás en FeedGo\./);
  const message = /Si ese usuario está registrado, te vamos a enviar un enlace para crear una nueva contraseña\./;
  assert.match(page, message);
  assert.match(service, message);
  assert.match(service, /\/usuarios\/password\/recuperacion/);
  assert.doesNotMatch(page, /rate limit|provider|HTTP|404|429|cuenta existe/i);
});

test("reset elimina fragmento antes de cualquier submit y no persiste secreto", async () => {
  const page = await read("../src/features/auth/pages/RestablecerPassword.jsx");
  assert.ok(page.indexOf("extraerTokenVerificacionDelFragmento()") < page.indexOf("restablecerPassword({ token: secret"));
  assert.doesNotMatch(page, /localStorage|sessionStorage|indexedDB|queryClient|returnTo|navigate\([^)]*secret/i);
  assert.match(page, /secretRef\.current = null/);
});

test("reset reutiliza checklist exacto y valida coincidencia", async () => {
  const page = await read("../src/features/auth/pages/RestablecerPassword.jsx");
  for (const text of ["Al menos 8 caracteres", "Una mayúscula", "Una minúscula", "Un número", "Sin espacios"])
    assert.match(page, new RegExp(text));
  assert.match(page, /passwordRegistroValida/);
  assert.match(page, /Las contraseñas no coinciden\./);
});

test("reset traduce estados y éxito sólo ofrece Login", async () => {
  const page = await read("../src/features/auth/pages/RestablecerPassword.jsx");
  assert.match(page, /Este enlace ya no es válido\. Pedí uno nuevo para continuar\./);
  assert.match(page, /Listo, tu contraseña fue actualizada\./);
  assert.match(page, /No pudimos completar esto ahora\. Intentá nuevamente en un momento\./);
  const success = page.slice(page.indexOf('status === "success"'), page.indexOf('status === "invalid"'));
  assert.match(success, /Iniciar sesión/);
  assert.doesNotMatch(success, /loginUsuario|useAuth|access_token/);
  assert.doesNotMatch(page, /HTTP \d|password_reset_link_invalid/);
});

test("rutas PWA conservan navegación y APIs network-only", async () => {
  const [router, classifier] = await Promise.all([
    read("../src/core/router/AppRouter.jsx"),
    read("../src/pwa/requestClassifier.js"),
  ]);
  assert.match(router, /path="\/recuperar-password"/);
  assert.match(router, /path="\/restablecer-password"/);
  assert.match(classifier, /"\/recuperar-password"/);
  assert.match(classifier, /"\/restablecer-password"/);
  assert.match(classifier, /isApiRequest[\s\S]*REQUEST_HANDLING\.NETWORK_ONLY/);
});

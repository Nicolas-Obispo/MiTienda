import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const servicePath = new URL("../src/features/auth/services/authService.js", import.meta.url);
const pagePath = new URL("../src/features/auth/pages/VerificarEmail.jsx", import.meta.url);
const registrationPath = new URL("../src/features/auth/pages/Registro.jsx", import.meta.url);
const routerPath = new URL("../src/core/router/AppRouter.jsx", import.meta.url);
const classifierPath = new URL("../src/pwa/requestClassifier.js", import.meta.url);

test("services frontend encapsulan confirmacion y reenvio", async () => {
  const source = await readFile(servicePath, "utf8");
  assert.match(source, /\/usuarios\/email-verificacion\/confirmar/);
  assert.match(source, /\/usuarios\/me\/email-verificacion\/reenvio/);
  assert.match(source, /extraerTokenVerificacionDelFragmento/);
  assert.match(source, /historyObject\.replaceState/);
});

test("pantalla elimina fragmento antes de confirmar y nunca persiste token", async () => {
  const source = await readFile(pagePath, "utf8");
  const replaceIndex = source.indexOf("extraerTokenVerificacionDelFragmento()");
  const requestIndex = source.indexOf("confirmarEmail(secret)");
  assert.ok(replaceIndex >= 0 && requestIndex > replaceIndex);
  assert.doesNotMatch(source, /localStorage|sessionStorage|indexedDB|queryClient|navigate\([^)]*secret/i);
  assert.match(source, /pendingSecretRef\.current = null/);
  assert.match(source, /location\.hash, location\.key/);
  assert.match(source, /processedDigestsRef/);
  assert.match(source, /operationsByDigestRef/);
});

test("UX cubre estados humanos sin codigos tecnicos", async () => {
  const source = await readFile(pagePath, "utf8");
  for (const message of [
    "Te enviamos un enlace para verificar tu cuenta.",
    "No pudimos enviar el enlace ahora. Podés pedir otro en un momento.",
    "Podés pedir otro enlace en unos segundos.",
    "Listo, tu cuenta ya está verificada.",
    "Este enlace ya no es válido. Pedí uno nuevo para continuar.",
    "No pudimos completar esto ahora. Intentá nuevamente en un momento.",
  ]) assert.match(source, new RegExp(message.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  assert.doesNotMatch(source, /HTTP 4|HTTP 5|identity_email|email_verification_rate_limited/);
  assert.match(source, /estaAutenticado.*Enviar otro enlace/s);
  assert.match(source, /!estaAutenticado.*Iniciar sesión para pedir otro enlace/s);
});

test("registro conserva alta y navega al estado de verificacion", async () => {
  const source = await readFile(registrationPath, "utf8");
  assert.match(source, /const registro = await registrarUsuario/);
  assert.match(source, /postAuthDestination/);
  assert.match(source, /pathname: "\/verificar-email"/);
  assert.match(source, /registrationEmailStatus: registro\.email_verification_status/);
});

test("superficie estable usa usuarios me y ofrece reenvio mientras no esta verificado", async () => {
  const source = await readFile(pagePath, "utf8");
  assert.match(source, /usuario[\s\S]*email_verified_at/);
  assert.match(source, /isCargandoUsuario/);
  assert.match(source, /setStatus\("unverified"\)/);
  assert.match(source, /\["sent", "unverified", "delivery_failed", "cooldown", "invalid"\]/);
  assert.match(source, /showAuthenticatedResend[\s\S]*!emailVerificado/);
  assert.match(source, /result\.status === "already_verified" && me\?\.email_verified_at/);
});

test("ruta y PWA mantienen verificacion como navegacion y API network-only", async () => {
  const [router, classifier] = await Promise.all([
    readFile(routerPath, "utf8"),
    readFile(classifierPath, "utf8"),
  ]);
  assert.match(router, /path="\/verificar-email"/);
  assert.match(classifier, /"\/verificar-email"/);
  assert.match(classifier, /isApiRequest[\s\S]*REQUEST_HANDLING\.NETWORK_ONLY/);
});

test("verificacion exitosa refresca la verdad de usuarios me", async () => {
  const source = await readFile(pagePath, "utf8");
  assert.match(source, /await refrescarUsuario\(\)/);
  assert.doesNotMatch(source, /email_verified_at\s*[:=]\s*(true|new)/);
});

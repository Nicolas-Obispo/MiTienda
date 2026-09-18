import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  exchangeGoogleSessionOnce,
  getGoogleSessionHandle,
} from "../src/features/auth/services/googleSessionResult.js";
import {
  createRequestClassifier,
  REQUEST_HANDLING,
} from "../src/pwa/requestClassifier.js";

const root = new URL("../", import.meta.url);
const readText = (path) => readFile(new URL(path, root), "utf8");
const validHandle = "g".repeat(43);

test("resultado Google acepta un unico handle opaco y nunca otros parametros", () => {
  assert.equal(getGoogleSessionHandle(`?handle=${validHandle}`), validHandle);
  assert.equal(getGoogleSessionHandle(`?handle=${validHandle}&other=x`), null);
  assert.equal(getGoogleSessionHandle(`?handle=${validHandle}&handle=${validHandle}`), null);
  assert.equal(getGoogleSessionHandle("?handle=not-valid"), null);
});

test("un handle se canjea una sola vez aun si React repite el effect", async () => {
  let calls = 0;
  const exchange = async () => {
    calls += 1;
    return { status: "authenticated", token: "opaque-feedgo-jwt" };
  };
  const handle = "h".repeat(43);

  const [first, second] = await Promise.all([
    exchangeGoogleSessionOnce(handle, exchange),
    exchangeGoogleSessionOnce(handle, exchange),
  ]);

  assert.equal(calls, 1);
  assert.deepEqual(first, second);
});

test("el coalescing aísla handles y no reintenta automaticamente un fallo", async () => {
  let calls = 0;
  const failedHandle = "f".repeat(43);
  const otherHandle = "o".repeat(43);
  const failedExchange = async () => {
    calls += 1;
    throw new Error("network failure");
  };

  await assert.rejects(exchangeGoogleSessionOnce(failedHandle, failedExchange));
  await assert.rejects(exchangeGoogleSessionOnce(failedHandle, failedExchange));
  await exchangeGoogleSessionOnce(otherHandle, async () => {
    calls += 1;
    return { status: "action_required" };
  });

  assert.equal(calls, 2);
});

test("Login y Registro dependen exclusivamente de la disponibilidad backend", async () => {
  const [service, hook, login, registro] = await Promise.all([
    readText("src/features/auth/services/authService.js"),
    readText("src/features/auth/hooks/useGoogleIdentityAvailability.js"),
    readText("src/features/auth/pages/Login.jsx"),
    readText("src/features/auth/pages/Registro.jsx"),
  ]);

  assert.match(service, /\/usuarios\/google\/availability/);
  assert.match(service, /\/usuarios\/google\/authorization/);
  assert.match(service, /\/usuarios\/google\/session/);
  assert.match(hook, /google_identity_available === true/);
  assert.match(hook, /retry: false/);
  assert.match(login, /purpose: "login"/);
  assert.match(login, /aceptaTerminos: false/);
  assert.match(login, /aceptaPrivacidad: false/);
  assert.match(registro, /purpose: "signup"/);
  assert.match(registro, /aceptaTerminos: true/);
  assert.match(registro, /aceptaPrivacidad: true/);
  assert.match(registro, /disabled=\{cargando \|\| cargandoGoogle \|\| !aceptaTerminos \|\| !aceptaPrivacidad\}/);
  assert.match(login, /googleAuthorizationInFlightRef\.current/);
  assert.match(registro, /googleAuthorizationInFlightRef\.current/);
  assert.match(registro, /Aceptá Términos y Condiciones y Política de Privacidad para continuar con Google\./);
  assert.equal((login.match(/Continuar con Google/g) || []).length, 1);
  assert.equal((registro.match(/Continuar con Google/g) || []).length, 1);
});

test("resultado Google limpia URL, delega token en AuthContext y no persiste handles", async () => {
  const [result, router] = await Promise.all([
    readText("src/features/auth/pages/GoogleAuthResult.jsx"),
    readText("src/core/router/AppRouter.jsx"),
  ]);

  assert.match(result, /navigate\(location\.pathname, \{ replace: true \}\)/);
  assert.match(result, /exchangeGoogleSessionOnce\(handle, exchangeGoogleSession\)/);
  assert.match(result, /login\(result\.token\)/);
  assert.match(result, /getInternalReturnTo\(result\.return_to, "\/feed"\)/);
  assert.doesNotMatch(result, /localStorage|sessionStorage|indexedDB|queryClient|console\./i);
  assert.match(router, /path="\/auth\/google\/resultado" element=\{<GoogleAuthResult \/>\}/);
  assert.doesNotMatch(router, /PublicOnlyRoute>[\s\S]{0,120}GoogleAuthResult/);
});

test("resultado Google es navegacion SPA, mientras APIs y Authorization siguen network-only", () => {
  const classifier = createRequestClassifier({
    appOrigin: "https://feedgo.example",
    apiBaseUrl: "https://api.feedgo.example",
  });
  const request = (path, options = {}) => ({
    url: new URL(path, "https://feedgo.example").href,
    method: options.method || "GET",
    mode: options.mode || "cors",
    headers: new Headers(options.headers),
  });

  assert.equal(
    classifier(request("/auth/google/resultado", { mode: "navigate" })),
    REQUEST_HANDLING.NAVIGATION,
  );
  assert.equal(
    classifier(request("https://api.feedgo.example/usuarios/google/session", { method: "POST" })),
    REQUEST_HANDLING.NETWORK_ONLY,
  );
  assert.equal(
    classifier(request("/auth/google/resultado", { headers: { Authorization: "Bearer opaque" } })),
    REQUEST_HANDLING.NETWORK_ONLY,
  );
});

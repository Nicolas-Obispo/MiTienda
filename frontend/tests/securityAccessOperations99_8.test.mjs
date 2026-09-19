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
const validHandle = "r".repeat(43);

test("authService conserva contratos de operaciones sensibles y DELETE JSON", async () => {
  const [service, http] = await Promise.all([
    readText("src/features/auth/services/authService.js"),
    readText("src/core/services/http_service.js"),
  ]);

  assert.match(service, /\/usuarios\/me\/authentication-methods\/password/);
  assert.match(service, /\{ confirm: true, new_password: newPassword \}/);
  assert.match(service, /\/usuarios\/google\/link\/authorization/);
  assert.match(service, /\{ confirm_link: true, return_to: returnTo \}/);
  assert.match(service, /\/usuarios\/me\/authentication-methods\/google/);
  assert.match(service, /httpDelete\([\s\S]*\{ confirm: true \}/);
  assert.match(service, /\/usuarios\/me\/reauthentication\/password/);
  assert.match(service, /\/usuarios\/google\/reauth\/authorization/);
  assert.match(service, /\/usuarios\/google\/reauth\/session/);
  assert.match(http, /httpDelete\(path, bodyOrToken = null, tokenOrOptions = null, options = \{\}\)/);
  assert.match(http, /body: body \? JSON\.stringify\(body\) : null/);
  assert.match(http, /Compatibilidad: los callers existentes usan httpDelete\(path, token\)/);
});

test("reauth Google usa coalescing aislado del resultado login/signup", async () => {
  let normalCalls = 0;
  let reauthCalls = 0;
  const [normal, reauth] = await Promise.all([
    exchangeGoogleSessionOnce(validHandle, async () => {
      normalCalls += 1;
      return { status: "authenticated", token: "normal" };
    }),
    exchangeGoogleSessionOnce(validHandle, async () => {
      reauthCalls += 1;
      return { status: "authenticated", token: "reauth" };
    }, "reauthentication"),
  ]);

  assert.equal(normalCalls, 1);
  assert.equal(reauthCalls, 1);
  assert.equal(normal.token, "normal");
  assert.equal(reauth.token, "reauth");
});

test("reauth coalescea StrictMode por handle y no reintenta fallos", async () => {
  const strictHandle = "s".repeat(43);
  let calls = 0;
  const exchange = async () => {
    calls += 1;
    return { status: "authenticated", token: "rotated" };
  };

  await Promise.all([
    exchangeGoogleSessionOnce(strictHandle, exchange, "reauthentication"),
    exchangeGoogleSessionOnce(strictHandle, exchange, "reauthentication"),
  ]);
  assert.equal(calls, 1);

  const failedHandle = "x".repeat(43);
  await assert.rejects(exchangeGoogleSessionOnce(
    failedHandle,
    async () => { throw new Error("network failure"); },
    "reauthentication",
  ));
  await assert.rejects(exchangeGoogleSessionOnce(
    failedHandle,
    async () => { throw new Error("must not retry"); },
    "reauthentication",
  ));
});

test("resultado reauth limpia handle y canjea solo por endpoint reauth", async () => {
  const [result, normalResult, router] = await Promise.all([
    readText("src/features/auth/pages/GoogleReauthenticationResult.jsx"),
    readText("src/features/auth/pages/GoogleAuthResult.jsx"),
    readText("src/core/router/AppRouter.jsx"),
  ]);

  assert.match(result, /navigate\(location\.pathname, \{ replace: true \}\)/);
  assert.match(result, /exchangeGoogleReauthenticationSession/);
  assert.match(result, /"reauthentication"/);
  assert.match(result, /login\(result\.token\)/);
  assert.match(result, /getInternalReturnTo\(result\.return_to, "\/perfil\?security=access"\)/);
  assert.doesNotMatch(result, /exchangeGoogleSession\b/);
  assert.doesNotMatch(result, /localStorage|sessionStorage|indexedDB|queryClient|console\./i);
  assert.match(normalResult, /exchangeGoogleSessionOnce\(handle, exchangeGoogleSession\)/);
  assert.match(router, /path="\/auth\/google\/reauth-resultado" element=\{<GoogleReauthenticationResult \/>\}/);
  assert.equal(getGoogleSessionHandle(""), null);
});

test("ambas rutas resultado son SPA y sus APIs permanecen network-only", () => {
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

  assert.equal(getGoogleSessionHandle(`?handle=${validHandle}`), validHandle);
  assert.equal(
    classifier(request("/auth/google/reauth-resultado", { mode: "navigate" })),
    REQUEST_HANDLING.NAVIGATION,
  );
  assert.equal(
    classifier(request("https://api.feedgo.example/usuarios/google/reauth/session", { method: "POST" })),
    REQUEST_HANDLING.NETWORK_ONLY,
  );
  assert.equal(
    classifier(request("/auth/google/reauth-resultado", { headers: { Authorization: "Bearer opaque" } })),
    REQUEST_HANDLING.NETWORK_ONLY,
  );
});

test("Seguridad y acceso requiere confirmacion y reauth sin reintentos automaticos", async () => {
  const profile = await readText("src/features/auth/pages/ProfilePage.jsx");

  assert.match(profile, /recent_reauthentication_required/);
  assert.match(profile, /setShowReauthentication\(true\)/);
  assert.match(profile, /login\(result\.token\)/);
  assert.match(profile, /window\.location\.assign\(result\.authorization_url\)/);
  assert.match(profile, /returnTo: "\/perfil\?security=access"/);
  assert.match(profile, /searchParams\.get\("security"\) !== "access"/);
  assert.match(profile, /navigate\("\/perfil", \{ replace: true \}\)/);
  assert.match(profile, /setSecurityConfirmation\("link-google"\)/);
  assert.match(profile, /setSecurityConfirmation\("unlink-google"\)/);
  assert.match(profile, /unlinkGoogleIdentity\(accessToken\)/);
  assert.match(profile, /async function handleAddPassword[\s\S]*securityActionInFlightRef\.current/);
  assert.match(profile, /async function submitPasswordReauthentication[\s\S]*securityActionInFlightRef\.current/);
  assert.match(profile, /refrescarUsuario\(\)/);
  assert.doesNotMatch(profile, /localStorage|sessionStorage/);
});

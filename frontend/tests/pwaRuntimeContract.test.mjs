import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

import {
  PWA_FORBIDDEN_PRECACHE_URLS,
  PWA_PRECACHE_GLOB_IGNORES,
  PWA_PRECACHE_GLOB_PATTERNS,
  PWA_REQUIRED_PRECACHE_URLS,
} from "../src/pwa/precacheContract.js";
import {
  createRequestClassifier,
  REQUEST_HANDLING,
} from "../src/pwa/requestClassifier.js";

const frontendRoot = new URL("../", import.meta.url);
const APP_ORIGIN = "https://feedgo.example";
const API_ORIGIN = "https://api.feedgo.example";

function request(path, options = {}) {
  return {
    url: new URL(path, APP_ORIGIN).href,
    method: options.method || "GET",
    mode: options.mode || "cors",
    headers: new Headers(options.headers),
  };
}

const classify = createRequestClassifier({
  appOrigin: APP_ORIGIN,
  apiBaseUrl: API_ORIGIN,
  precacheEntries: [
    { url: "/index.html", revision: "shell" },
    { url: "/assets/app-a1b2.js", revision: null },
    { url: "/theme-bootstrap.js", revision: "theme" },
  ],
});

test("contrato de build limita el precache al shell aprobado", () => {
  assert.deepEqual(PWA_PRECACHE_GLOB_PATTERNS, [
    "index.html",
    "assets/**/*.js",
    "assets/**/*.css",
    "theme-tokens.css",
    "theme-bootstrap.css",
    "theme-bootstrap.js",
    "manifest.json",
    "favicon-48.png",
    "apple-touch-icon-180.png",
    "icon-192.png",
    "icon-512.png",
    "icon-maskable-512.png",
    "logo_Feedgo.png",
  ]);
  assert.deepEqual(PWA_PRECACHE_GLOB_IGNORES, [
    "service-worker.js",
    "vite.svg",
    "icon-180.png",
    "**/*.map",
  ]);
});

test("API publica, autenticada y recursos sensibles son network-only", () => {
  const cases = [
    request(`${API_ORIGIN}/rubros/`),
    request(`${API_ORIGIN}/usuarios/me`),
    request(`${API_ORIGIN}/feed/publicaciones`),
    request(`${API_ORIGIN}/ranking/publicaciones`),
    request(`${API_ORIGIN}/publicaciones/guardadas`),
    request(`${API_ORIGIN}/feedgo-agenda/mis/elementos`),
    request(`${API_ORIGIN}/analytics/comercios/1`),
    request(`${API_ORIGIN}/geocoding/buscar`),
    request(`${API_ORIGIN}/uploads/private/image.png`),
    request("/uploads/private/image.png"),
    request("/media/private/image.png"),
    request("/geocoding/buscar"),
    request("/feed", { headers: { Authorization: "Bearer private" } }),
  ];

  for (const candidate of cases) {
    assert.equal(classify(candidate), REQUEST_HANDLING.NETWORK_ONLY);
  }
});

test("todas las mutaciones permanecen network-only", () => {
  for (const method of ["POST", "PUT", "PATCH", "DELETE"]) {
    assert.equal(
      classify(request("/feed", { method })),
      REQUEST_HANDLING.NETWORK_ONLY,
    );
  }
});

test("mapas, fuentes y cualquier origen externo permanecen network-only", () => {
  for (const url of [
    "https://tile.openstreetmap.org/1/2/3.png",
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
    "https://fonts.googleapis.com/css2?family=Nunito",
    "https://fonts.gstatic.com/font.woff2",
  ]) {
    assert.equal(classify(request(url)), REQUEST_HANDLING.NETWORK_ONLY);
  }
});

test("solo rutas frontend validas usan navegacion controlada", () => {
  for (const path of [
    "/",
    "/feed",
    "/explorar",
    "/comercios/42",
    "/publicaciones/99",
  ]) {
    assert.equal(
      classify(request(path, { mode: "navigate" })),
      REQUEST_HANDLING.NAVIGATION,
    );
  }

  assert.equal(
    classify(request("/api/desconocida", { mode: "navigate" })),
    REQUEST_HANDLING.NETWORK_ONLY,
  );
  assert.equal(
    classify(request("/missing.js", { mode: "navigate" })),
    REQUEST_HANDLING.NETWORK_ONLY,
  );
});

test("solo assets presentes en el manifiesto inyectado usan precache", () => {
  assert.equal(classify(request("/assets/app-a1b2.js")), REQUEST_HANDLING.PRECACHE);
  assert.equal(classify(request("/theme-bootstrap.js")), REQUEST_HANDLING.PRECACHE);
  assert.equal(classify(request("/legacy.js")), REQUEST_HANDLING.NETWORK_ONLY);
  assert.equal(
    classify(
      request("/icon-192.png", {
        headers: { Authorization: "Bearer private" },
      }),
    ),
    REQUEST_HANDLING.NETWORK_ONLY,
  );
});

test("worker generado contiene el inventario permitido y ningun asset prohibido", async () => {
  const worker = await readFile(new URL("dist/service-worker.js", frontendRoot), "utf8");
  const generatedUrls = new Set(
    [...worker.matchAll(/["']?url["']?\s*:\s*["']([^"']+)["']/g)].map((match) => {
      const url = new URL(match[1], APP_ORIGIN);
      return url.pathname;
    }),
  );

  for (const requiredUrl of PWA_REQUIRED_PRECACHE_URLS) {
    assert.ok(generatedUrls.has(requiredUrl), `Falta ${requiredUrl} en el precache generado`);
  }

  assert.ok([...generatedUrls].some((url) => /^\/assets\/.*\.js$/.test(url)));
  assert.ok([...generatedUrls].some((url) => /^\/assets\/.*\.css$/.test(url)));

  for (const forbiddenUrl of PWA_FORBIDDEN_PRECACHE_URLS) {
    assert.equal(generatedUrls.has(forbiddenUrl), false);
  }

  for (const url of generatedUrls) {
    assert.doesNotMatch(
      url,
      /usuarios|feed\/publicaciones|ranking\/publicaciones|guardadas|agenda|analytics|geocoding|uploads/i,
    );
  }
});

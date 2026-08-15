import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import { test } from "node:test";

const root = new URL("../", import.meta.url);
const readText = (path) => readFile(new URL(path, root), "utf8");

async function readPngSize(path) {
  const png = await readFile(new URL(path, root));
  assert.equal(png.subarray(1, 4).toString("ascii"), "PNG");
  return [png.readUInt32BE(16), png.readUInt32BE(20)];
}

test("manifest declara exclusivamente la identidad instalada FeedGo", async () => {
  const manifest = JSON.parse(await readText("public/manifest.json"));

  assert.equal(manifest.name, "FeedGo");
  assert.equal(manifest.short_name, "FeedGo");
  assert.equal(manifest.id, "/");
  assert.equal(manifest.start_url, "/");
  assert.equal(manifest.scope, "/");
  assert.equal(manifest.display, "standalone");
  assert.equal(manifest.background_color, "#030712");
  assert.equal(manifest.theme_color, "#111827");
  assert.equal("orientation" in manifest, false);

  const serialized = JSON.stringify(manifest);
  assert.doesNotMatch(serialized, /MiPlaza|MiTienda|vite\.svg/i);
  assert.deepEqual(
    manifest.icons.map(({ src, sizes, type, purpose }) => ({ src, sizes, type, purpose })),
    [
      { src: "/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      {
        src: "/icon-maskable-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ]
  );
});

test("HTML usa metadata instalada FeedGo y conserva el bootstrap de tema", async () => {
  const html = await readText("index.html");

  assert.match(html, /<title>FeedGo<\/title>/);
  assert.match(html, /apple-mobile-web-app-title" content="FeedGo"/);
  assert.match(html, /apple-touch-icon" sizes="180x180" href="\/apple-touch-icon-180\.png"/);
  assert.match(html, /rel="icon" type="image\/png" sizes="48x48" href="\/favicon-48\.png"/);
  assert.match(html, /rel="manifest" href="\/manifest\.json"/);
  assert.doesNotMatch(html, /MiPlaza|MiTienda|vite\.svg/i);

  const tokensIndex = html.indexOf("/theme-tokens.css");
  const bootstrapCssIndex = html.indexOf("/theme-bootstrap.css");
  const bootstrapJsIndex = html.indexOf("/theme-bootstrap.js");
  const appIndex = html.indexOf("/src/main.jsx");
  assert.ok(tokensIndex > -1 && bootstrapCssIndex > tokensIndex);
  assert.ok(bootstrapJsIndex > bootstrapCssIndex && appIndex > bootstrapJsIndex);
});

test("96.1-A no modifica ni implementa runtime offline en el service worker", async () => {
  const worker = await readText("public/service-worker.js");

  assert.match(worker, /self\.addEventListener\("fetch"/);
  assert.doesNotMatch(worker, /caches\.|CacheStorage|skipWaiting|clients\.claim|workbox|precache/i);
});

test("assets instalables existen y tienen dimensiones reales contractuales", async () => {
  const assets = [
    ["public/favicon-48.png", 48],
    ["public/apple-touch-icon-180.png", 180],
    ["public/icon-192.png", 192],
    ["public/icon-512.png", 512],
    ["public/icon-maskable-512.png", 512],
  ];

  for (const [path, expectedSize] of assets) {
    await access(new URL(path, root));
    assert.deepEqual(await readPngSize(path), [expectedSize, expectedSize]);
  }
});

test("routing y despliegue seguro quedan gobernados sin implementar hosting", async () => {
  const router = await readText("src/core/router/AppRouter.jsx");
  const httpService = await readText("src/core/services/http_service.js");
  const contract = await readText("../docs/18_PWA_ENTERPRISE.md");

  assert.match(router, /<BrowserRouter>/);
  for (const route of [
    "/",
    "/terminos-y-condiciones",
    "/politica-de-privacidad",
    "/login",
    "/registro",
    "/feed",
    "/ranking",
    "/ver-seguidos",
    "/explorar",
    "/perfil",
    "/comercios/:id",
    "/publicaciones/:id",
  ]) {
    assert.match(router, new RegExp(`path=["']${route.replace("/", "\\/")}["']`));
  }

  assert.match(httpService, /import\.meta\.env\.VITE_API_URL/);
  assert.match(contract, /navegacion GET\/HEAD/);
  assert.match(contract, /assets inexistentes y las rutas API no deben reescribirse a HTML/);
  assert.match(contract, /allowlist explicita de los\s+origenes HTTPS reales/);
  assert.match(contract, /Ningun secreto productivo puede\s+publicarse como variable `VITE_\*`/);
  assert.match(contract, /Cache Storage futuro no puede contener JWT/);
  assert.match(contract, /No se declara\s+apertura offline en Sprint 96\.1/);
});

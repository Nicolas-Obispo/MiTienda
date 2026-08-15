import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const [explore, geographicControls, mainLayout, sessionGuard, scheduleBadge] =
  await Promise.all([
    readSource("../src/features/explore/pages/ExplorarPage.jsx"),
    readSource("../src/shared/components/GeographicContextControls.jsx"),
    readSource("../src/shared/layouts/MainLayout.jsx"),
    readSource("../src/features/auth/components/SessionInactivityGuard.jsx"),
    readSource("../src/features/availability/components/EstadoHorarioBadge.jsx"),
  ]);

const migratedSources = [explore, geographicControls, mainLayout, sessionGuard, scheduleBadge].join("\n");

test("Explorar y sus owners visuales consumen tokens y primitives", () => {
  for (const primitive of ["Alert", "Button", "Input", "Skeleton", "Surface"]) {
    assert.match(explore, new RegExp(`<${primitive}\\b`));
  }
  assert.match(geographicControls, /<Surface\b/);
  assert.match(geographicControls, /<FormControl\b/);
  assert.match(geographicControls, /<Input\b/);
  assert.match(mainLayout, /bg-canvas/);
  assert.match(mainLayout, /bg-surface/);
  assert.match(sessionGuard, /bg-overlay-backdrop/);
  assert.match(scheduleBadge, /bg-success-surface/);
  assert.match(scheduleBadge, /bg-danger-surface/);
});

test("la migracion no introduce tema manual ni colores fisicos evitables", () => {
  assert.doesNotMatch(migratedSources, /#[\da-f]{3,8}|\brgb\(|\brgba\(/i);
  assert.doesNotMatch(migratedSources, /(?:bg|text|border|from|via|to)-(?:gray|slate|zinc|neutral|stone|white|black|red|green|emerald|orange|amber|yellow|blue|purple|pink)-?\d*/);
  assert.doesNotMatch(migratedSources, /resolvedTheme|data-theme|dark:|matchMedia\(/);
});

test("botones migrados usan el owner compartido sin duplicar bubble", () => {
  assert.doesNotMatch(explore, /<button\b/);
  assert.doesNotMatch(geographicControls, /<button\b/);
  assert.doesNotMatch(`${explore}\n${geographicControls}`, /interactive-bubble/);
  assert.match(explore, /variant="secondary"/);
  assert.match(mainLayout, /<Link[\s\S]*to="\/login"/);
});

test("Search territorial, cache y paginacion conservan sus contratos", () => {
  assert.match(explore, /setTimeout\(\(\) => \{[\s\S]*\}, 300\)/);
  assert.match(explore, /useSearchSuggestions\(/);
  for (const parameter of ["city_key", "province_code", "country_code", "positionRevision", "scope", "expansion_km"]) {
    assert.match(explore, new RegExp(`${parameter}:`));
  }
  assert.match(explore, /getExplorarEspaciosInfiniteQueryOptions\(paramsBusqueda\)/);
  assert.match(explore, /requestDeviceLocation\(\{ needDistance: true \}\)/);
  assert.match(explore, /expansion_km: 50/);
  assert.match(explore, /expansion_km: 100/);
  assert.match(explore, /espaciosQuery\.fetchNextPage\(\)/);
  assert.doesNotMatch(explore, /navigator\.geolocation/);
});

test("resultados conservan datos, privacidad y navegacion existentes", () => {
  assert.match(explore, /navigate\(`\/comercios\/\$\{comercioId\}`\)/);
  assert.match(explore, /navigate\(`\/publicaciones\/\$\{publicacionId\}`\)/);
  assert.match(explore, /typeof c\.distancia_km === "number"/);
  assert.match(explore, /\{c\.ciudad \|\| "Ciudad"\}/);
  assert.doesNotMatch(explore, /c\.(?:latitud|longitud|direccion|maps_url)/);
  assert.doesNotMatch(explore, /haversine|calculateDistance|calcularDistancia/i);
});

test("estados y controles territoriales mantienen semantica accesible", () => {
  assert.match(explore, /<Alert role="alert" variant="danger">/);
  assert.match(explore, /<Skeleton\b/);
  assert.match(explore, /aria-pressed=\{modoExplorar === "espacios"\}/);
  assert.match(explore, /aria-pressed=\{modoExplorar === "publicaciones"\}/);
  assert.match(geographicControls, /<Alert[\s\S]*role="status"[\s\S]*variant="warning">/);
  assert.match(geographicControls, /requestDeviceLocation\(\{ needDistance: true,/);
  assert.match(geographicControls, /selectManualTerritory\(/);
});

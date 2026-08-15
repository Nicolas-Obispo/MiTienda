import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const [page, hook, service] = await Promise.all([
  readSource("../src/features/spaces/pages/VerSeguidosPage.jsx"),
  readSource("../src/features/spaces/hooks/useMisEspaciosSeguidos.js"),
  readSource("../src/features/spaces/services/seguidores_service.js"),
]);

test("Seguidos migra shell, tabs, cards y estados a owners semanticos", () => {
  assert.match(page, /bg-canvas text-primary/);
  assert.equal((page.match(/<Button\b/g) || []).length, 2);
  assert.match(page, /aria-pressed=\{vistaActiva === "espacios"\}/);
  assert.match(page, /aria-pressed=\{vistaActiva === "guardadas"\}/);
  assert.match(page, /<Surface[\s\S]*as=\{Link\}/);
  assert.equal((page.match(/<Alert variant="danger" role="alert"/g) || []).length, 2);
});

test("Seguidos reutiliza contexto geografico y conserva su contrato de consulta", () => {
  assert.match(page, /<GeographicContextControls \/>/);
  assert.match(page, /lat: queryContext\?\.lat \?\? null/);
  assert.match(page, /lng: queryContext\?\.lng \?\? null/);
  assert.match(page, /positionRevision: queryContext\?\.positionRevision \?\? 0/);
  assert.match(hook, /queryKeys\.spaces\.seguidos\(\{ positionRevision \}\)/);
  assert.match(hook, /staleTime: 1000 \* 60/);
  assert.match(hook, /placeholderData: \(previousData\) => previousData/);
  assert.match(service, /params\.set\("lat", String\(lat\)\)/);
  assert.match(service, /params\.set\("lng", String\(lng\)\)/);
});

test("Seguidos conserva ciudad publica y solo representa distancia recibida", () => {
  assert.match(page, /c\.ciudad &&/);
  assert.match(page, /typeof c\.distancia_km === "number"/);
  assert.match(page, /Math\.round\(c\.distancia_km \* 1000\)/);
  assert.match(page, /c\.distancia_km\.toFixed\(1\)/);
  assert.doesNotMatch(page, /c\.(?:direccion|latitud|longitud|maps_url)/);
  assert.doesNotMatch(page, /haversine|calcularDistancia|Ubicaci[oó]n no disponible/i);
});

test("acciones migradas conservan interactive-bubble mediante Button", () => {
  assert.match(page, /<Button[\s\S]*Espacios seguidos[\s\S]*<\/Button>/);
  assert.match(page, /<Button[\s\S]*Publicaciones guardadas[\s\S]*<\/Button>/);
  assert.doesNotMatch(page, /interactive-bubble/);
});

test("Seguidos no introduce colores fisicos ni logica manual de tema", () => {
  const shellWithoutMediaOverlay = page
    .replace(/bg-black\/40/g, "")
    .replace(/text-white/g, "");

  assert.doesNotMatch(shellWithoutMediaOverlay, /#[\da-f]{3,8}|\brgb\(|\brgba\(/i);
  assert.doesNotMatch(shellWithoutMediaOverlay, /(?:bg|text|border|ring|from|via|to)-(?:gray|slate|zinc|neutral|stone|white|black|red|green|emerald|orange|amber|yellow|blue|purple|pink)(?:\/|-\d|\b)/);
  assert.doesNotMatch(page, /resolvedTheme|data-theme|dark:|matchMedia\(|localStorage\./);
});

test("Cache-First no oculta datos existentes durante revalidacion", () => {
  assert.match(page, /cargando && espacios\.length === 0/);
  assert.match(page, /espaciosErrorMessage &&[\s\S]*espacios\.length === 0/);
  assert.match(page, /!fetchingEspacios/);
  assert.match(hook, /placeholderData: \(previousData\) => previousData/);
});

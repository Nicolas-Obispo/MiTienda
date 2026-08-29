import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const paths = {
  home: "../src/features/administration/pages/AdministrativeHomePage.jsx",
  guide: "../src/features/administration/pages/AdministrativeGuidePage.jsx",
  denied: "../src/features/administration/components/AdministrativeAccessDenied.jsx",
  reports: "../src/features/moderation/pages/AdministrativeReportsPage.jsx",
  incidents: "../src/features/incidents/pages/OperationalIncidentsPage.jsx",
  status: "../src/features/operations/pages/OperationalStatusPage.jsx",
};

const sources = Object.fromEntries(
  await Promise.all(
    Object.entries(paths).map(async ([name, path]) => [
      name,
      await readFile(new URL(path, import.meta.url), "utf8"),
    ])
  )
);

test("ocho owners de enlaces administrativos reciben una sola capa Liquid", () => {
  const expected = { home: 2, guide: 1, denied: 1, reports: 1, incidents: 1, status: 2 };

  for (const [name, count] of Object.entries(expected)) {
    assert.equal((sources[name].match(/interactive-bubble--liquid/g) || []).length, count);
    assert.equal((sources[name].match(/<InteractiveLiquidLayers \/>/g) || []).length, count);
  }
});

test("destinos, textos y capacidades permanecen", () => {
  assert.match(sources.home, /to=\{surface\.to\}>Abrir<InteractiveLiquidLayers \/>/);
  assert.match(sources.home, /to="\/administracion\/guia">Abrir guía práctica<InteractiveLiquidLayers \/>/);
  for (const source of [sources.guide, sources.denied, sources.reports, sources.incidents, sources.status]) {
    assert.match(source, /to="\/administracion">Volver a Administración<InteractiveLiquidLayers \/>/);
  }
  assert.match(sources.status, /integrity\.data\.issues\.length && capabilities\.tieneCapacidad\("operations\.incidents\.manage"\)/);
  assert.match(sources.status, /to="\/administracion\/incidentes">Abrir incidente mediante el flujo existente/);
  assert.match(sources.home, /SURFACES\.filter\(\(\{ capability \}\) => tieneCapacidad\(capability\)\)/);
});

test("geometría, responsive, tokens y links textuales no cambian", () => {
  assert.match(sources.home, /min-h-11 w-full items-center justify-center text-sm font-semibold text-interactive-primary sm:w-auto/);
  assert.match(sources.status, /min-h-11 w-full items-center justify-center text-link sm:w-auto/);
  for (const source of [sources.guide, sources.denied, sources.reports, sources.incidents, sources.status]) {
    assert.match(source, /min-h-11 items-center text-link underline underline-offset-2/);
  }
  assert.match(sources.reports, /className="text-link underline underline-offset-2"[\s\S]*to=\{detail\.data\.recurso_actual\.ruta_publica\}/);
  assert.doesNotMatch(sources.reports, /className="text-link underline underline-offset-2 interactive-bubble/);
});

test("Button conserva inyección propia sin capas manuales duplicadas", () => {
  for (const source of Object.values(sources)) {
    const buttonBlocks = source.match(/<Button\b[\s\S]*?<\/Button>/g) || [];
    for (const block of buttonBlocks) {
      assert.doesNotMatch(block, /InteractiveLiquidLayers|interactive-bubble--liquid/);
    }
  }
});

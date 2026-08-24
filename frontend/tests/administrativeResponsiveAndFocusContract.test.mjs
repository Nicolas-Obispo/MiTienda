import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

const read = (path) => fs.readFileSync(new URL(path, import.meta.url), "utf8");
const home = read("../src/features/administration/pages/AdministrativeHomePage.jsx");
const reports = read("../src/features/moderation/pages/AdministrativeReportsPage.jsx");
const incidents = read("../src/features/incidents/pages/OperationalIncidentsPage.jsx");
const status = read("../src/features/operations/pages/OperationalStatusPage.jsx");
const focus = read("../src/features/administration/hooks/useAdministrativeFocus.js");

test("portada y superficies contraen su layout sin crear overflow horizontal", () => {
  assert.match(home, /grid gap-4 sm:grid-cols-2 lg:grid-cols-3/);
  assert.match(home, /w-full items-center justify-center[\s\S]*sm:w-auto/);
  assert.match(reports, /grid min-w-0 gap-5 lg:grid-cols/);
  assert.match(reports, /<section className="min-w-0"[\s\S]*<aside className="min-w-0"/);
  assert.match(incidents, /lg:grid-cols-\[minmax\(0,1fr\)_minmax\(0,1fr\)\]/);
  assert.match(incidents, /break-all font-medium/);
  assert.match(status, /sm:grid-cols-\[minmax\(0,1fr\)_minmax\(0,1fr\)_auto\]/);
});

test("formularios y acciones son apilables y táctiles en móvil", () => {
  assert.match(reports, /min-h-11 w-full sm:w-auto/);
  assert.match(incidents, /flex flex-col gap-2 sm:flex-row sm:flex-wrap/);
  assert.match(incidents, /min-h-11 w-full sm:w-auto/);
  assert.match(status, /min-h-11 w-full[\s\S]*sm:w-auto/);
  assert.doesNotMatch([home, reports, incidents, status].join("\n"), /<div[^>]+onClick=/);
});

test("abrir y cerrar detalles mueve y restaura el foco", () => {
  assert.match(reports, /detailTitleRef\.current\?\.focus\(\)/);
  assert.match(reports, /detailTriggerRef\.current\?\.focus\(\)/);
  assert.match(reports, /ref=\{titleRef\} tabIndex=\{-1\}/);
  assert.match(incidents, /detailTitleRef\.current\?\.focus\(\)/);
  assert.match(incidents, /detailTriggerRef\.current\?\.focus\(\)/);
  assert.match(incidents, /ref=\{titleRef\} tabIndex=\{-1\}/);
});

test("errores administrativos reciben foco programático junto a su origen", () => {
  assert.match(focus, /if \(isError\) errorRef\.current\?\.focus\(\)/);
  assert.match(reports, /detailErrorRef[\s\S]*decisionErrorRef[\s\S]*listErrorRef/);
  assert.match(incidents, /lifecycleErrorRef[\s\S]*legalErrorRef[\s\S]*adjustmentErrorRef/);
  assert.match(status, /statusErrorRef[\s\S]*integrityErrorRef/);
  for (const page of [reports, incidents, status]) assert.match(page, /tabIndex=\{-1\}/);
});

test("la navegación Administración-superficie usa controles nativos", () => {
  for (const page of [reports, incidents, status]) assert.match(page, /<Link[\s\S]*to="\/administracion">Volver a Administración<\/Link>/);
  assert.match(home, /<Link[\s\S]*to=\{surface\.to\}>Abrir<\/Link>/);
  assert.doesNotMatch([home, reports, incidents, status].join("\n"), /role="button"|tabIndex=\{0\}/);
});

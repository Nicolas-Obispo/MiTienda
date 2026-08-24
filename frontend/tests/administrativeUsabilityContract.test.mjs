import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

const read = (path) => fs.readFileSync(new URL(path, import.meta.url), "utf8");
const labels = read("../src/features/administration/utils/administrativeLabels.js");
const reports = read("../src/features/moderation/pages/AdministrativeReportsPage.jsx");
const incidents = read("../src/features/incidents/pages/OperationalIncidentsPage.jsx");
const status = read("../src/features/operations/pages/OperationalStatusPage.jsx");
const router = read("../src/core/router/AppRouter.jsx");
const denied = read("../src/features/administration/components/AdministrativeAccessDenied.jsx");

test("un único módulo traduce códigos administrativos sin cambiar contratos", () => {
  assert.match(labels, /export function administrativeLabel/);
  for (const page of [reports, incidents, status]) assert.match(page, /administrativeLabel/);
  assert.doesNotMatch(reports, /\{report\.motivo\}|\{report\.recurso_tipo\}|\{decision\.accion\}|\{decision\.resultado\}/);
  assert.doesNotMatch(incidents, /\{item\.severity\}|\{item\.status\}|\{item\.event_type\}|\{detail\.data\.status\}/);
  assert.doesNotMatch(status, /<strong>\{component\.component\}|:\s*\{component\.status\}|·\s*\{alert\.rule_name\}|variant="warning">\{issue\.code\}|<strong>\{integrity\.data\.resource_type\}/);
});

test("incidentes separa mutaciones, estados y errores por formulario", () => {
  assert.equal((incidents.match(/useActOnOperationalIncident\(\)/g) ?? []).length, 3);
  assert.match(incidents, /lifecycleAction\.isError/);
  assert.match(incidents, /legalAction\.isError/);
  assert.match(incidents, /adjustmentAction\.isError/);
  assert.match(incidents, /Detalle del avance/);
  assert.match(incidents, /Fundamento de la evaluación legal/);
  assert.match(incidents, /Motivo del cambio/);
  assert.doesNotMatch(incidents, /Resumen seguro/);
});

test("las tres superficies vuelven a Administración y comparten el fallback", () => {
  for (const page of [reports, incidents, status]) assert.match(page, /to="\/administracion">Volver a Administración/);
  assert.equal((router.match(/fallback={<AdministrativeAccessDenied \/>}/g) ?? []).length, 3);
  assert.match(denied, /No tenés permiso para acceder a esta sección administrativa/);
});

test("fundamento y evidencia explican la minimización visible", () => {
  assert.match(reports, /Fundamento de la decisión/);
  assert.match(reports, /Referencia de evidencia/);
  assert.match(reports, /No incluyas URLs, rutas, payloads, secretos ni datos privados/);
  assert.match(incidents, /sin incluir secretos ni datos privados/);
});

import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

const service = fs.readFileSync(new URL("../src/features/operations/services/operationalStatusService.js", import.meta.url), "utf8");
const hooks = fs.readFileSync(new URL("../src/features/operations/hooks/useOperationalStatus.js", import.meta.url), "utf8");
const page = fs.readFileSync(new URL("../src/features/operations/pages/OperationalStatusPage.jsx", import.meta.url), "utf8");
const router = fs.readFileSync(new URL("../src/core/router/AppRouter.jsx", import.meta.url), "utf8");
const queryKeys = fs.readFileSync(new URL("../src/core/constants/queryKeys.js", import.meta.url), "utf8");

test("operational status uses the service layer without direct fetch", () => {
  assert.match(service, /\/administracion\/operaciones\/estado/);
  assert.match(service, /\/recursos\/.*\/integridad/);
  assert.doesNotMatch(page, /\bfetch\s*\(/);
});

test("route requires operations.status.read", () => {
  assert.match(router, /path="\/administracion\/operaciones\/estado"/);
  assert.match(router, /capability="operations\.status\.read"/);
});

test("TanStack Query owns both remote projections and propagates abort signals", () => {
  assert.match(queryKeys, /operations:[\s\S]*status:[\s\S]*resourceIntegrity:/);
  assert.match(hooks, /queryFn: \(\{ signal \}\)/);
  assert.match(hooks, /inspectOperationalResource\(\{ resourceType, resourceId, token: accessToken, signal \}\)/);
});

test("UI states local volatile and non-global semantics", () => {
  assert.match(page, /volátil del proceso actual/i);
  assert.match(page, /No constituye historial, estado global, garantía de vigencia ni objetivo de recuperación/i);
});

test("UI presents the dedicated worker through its sanitized state", () => {
  assert.match(page, /operational_email_worker\.status/);
  assert.match(page, /Worker de correo operativo/);
  assert.match(page, /estado local y volÃ¡til/i);
  assert.doesNotMatch(page, /pid|claimed_by|state_file|heartbeat/i);
});

test("UI is read-only and has no destructive operations", () => {
  assert.doesNotMatch(service, /httpPost|httpPut|httpDelete|httpPatch/);
  assert.doesNotMatch(page, /Ejecutar backup|Ejecutar restore|Eliminar asset|Reparar referencia/i);
  assert.doesNotMatch(page, /canvas|svg|chart|grafana|prometheus/i);
});

test("incident opening reuses the existing protected flow", () => {
  assert.match(page, /operations\.incidents\.manage/);
  assert.match(page, /to="\/administracion\/incidentes"/);
  assert.doesNotMatch(service, /incidentes/);
});

test("UI performs targeted resource inspection only", () => {
  assert.match(page, /Tipo de recurso/);
  assert.match(page, /ID/);
  assert.match(page, /no recorre el filesystem/i);
  assert.doesNotMatch(service, /scan|barrido|listar-assets/i);
});

test("UI does not request sensitive operational details", () => {
  assert.doesNotMatch(page, /backup_file|manifest_file|checksum|stack trace|sql|authorization|bearer|\.env/i);
  assert.doesNotMatch(page, /type="file"|https?:\/\//i);
});

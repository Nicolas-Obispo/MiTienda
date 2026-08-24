import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

const service = fs.readFileSync(new URL("../src/features/incidents/services/incidentsService.js", import.meta.url), "utf8");
const hooks = fs.readFileSync(new URL("../src/features/incidents/hooks/useOperationalIncidents.js", import.meta.url), "utf8");
const page = fs.readFileSync(new URL("../src/features/incidents/pages/OperationalIncidentsPage.jsx", import.meta.url), "utf8");
const router = fs.readFileSync(new URL("../src/core/router/AppRouter.jsx", import.meta.url), "utf8");
const queryKeys = fs.readFileSync(new URL("../src/core/constants/queryKeys.js", import.meta.url), "utf8");

test("incident feature consumes administrative service contracts without direct fetch", () => {
  assert.match(service, /\/administracion\/incidentes/);
  assert.match(service, /\/acciones/);
  assert.match(service, /\/eventos/);
  assert.doesNotMatch(service, /fetch\s*\(/);
});

test("route is protected by the approved backend capability contract", () => {
  assert.match(router, /path="\/administracion\/incidentes"/);
  assert.match(router, /capability="operations\.incidents\.manage"/);
  assert.match(router, /AdministrativeAccessGuard/);
});

test("remote incident ownership remains in one TanStack Query cache", () => {
  assert.match(queryKeys, /incidents:[\s\S]*list:[\s\S]*detail:[\s\S]*timeline:/);
  assert.match(hooks, /useInfiniteQuery/);
  assert.match(hooks, /invalidateQueries\(\{ queryKey: queryKeys\.incidents\.all/);
});

test("rapid reads can cancel stale list, detail and timeline requests", () => {
  assert.match(hooks, /pageParam, signal/);
  assert.match(hooks, /getOperationalIncident\(\{ publicId, token: accessToken, signal \}\)/);
  assert.match(hooks, /getOperationalIncidentTimeline\(\{ publicId, token: accessToken, signal \}\)/);
});

test("UI covers manual opening, lifecycle, legal assessment and residual risk", () => {
  assert.match(page, /Abrir incidente/);
  assert.match(page, /start_investigation/);
  assert.match(page, /record_legal_assessment/);
  assert.match(page, /residual_risk_level/);
  assert.match(page, /expected_version/);
  assert.match(page, /idempotency_key/);
});

test("UI is an incident register and does not build an operations dashboard", () => {
  assert.doesNotMatch(page, /health\/ready|LocalAlertSink|MetricsRecorder|grafana|prometheus/i);
  assert.doesNotMatch(page, /backup_database|restore_database|dashboard/i);
});

test("UI does not request raw evidence, files, URLs, secrets or payloads", () => {
  assert.doesNotMatch(page, /type="file"|Authorization|Bearer|\.env|evidence_reference|https?:\/\//i);
  assert.doesNotMatch(page, /label="(Archivo|URL|Secreto|Payload)/i);
});

test("concurrency conflict has explicit UX", () => {
  assert.match(page, /administrativeErrorMessage\(lifecycleAction\.error/);
  assert.match(page, /administrativeErrorMessage\(legalAction\.error/);
  assert.match(page, /administrativeErrorMessage\(adjustmentAction\.error/);
});

test("legal, lifecycle and adjustment summaries have independent runtime state", () => {
  assert.match(page, /\[lifecycleSummary, setLifecycleSummary\]/);
  assert.match(page, /\[legalSummary, setLegalSummary\]/);
  assert.match(page, /\[adjustmentSummary, setAdjustmentSummary\]/);
  assert.doesNotMatch(page, /\[summary, setSummary\]/);
  assert.match(page, /onSuccess:\s*\(\) => setLegalSummary\(""\)/);
});

test("same current severity keeps the adjustment submit disabled", () => {
  assert.match(page, /adjustment === "change_severity" && adjustmentValue === detail\.data\.severity/);
});

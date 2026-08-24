import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

const service = fs.readFileSync(
  new URL("../src/features/moderation/services/denuncias_service.js", import.meta.url),
  "utf8",
);
const hooks = fs.readFileSync(
  new URL("../src/features/moderation/hooks/useAdministrativeReports.js", import.meta.url),
  "utf8",
);
const page = fs.readFileSync(
  new URL("../src/features/moderation/pages/AdministrativeReportsPage.jsx", import.meta.url),
  "utf8",
);
const router = fs.readFileSync(
  new URL("../src/core/router/AppRouter.jsx", import.meta.url),
  "utf8",
);
const queryKeys = fs.readFileSync(
  new URL("../src/core/constants/queryKeys.js", import.meta.url),
  "utf8",
);
const httpService = fs.readFileSync(
  new URL("../src/core/services/http_service.js", import.meta.url),
  "utf8",
);

test("inbox consumes existing moderation routes without direct fetch", () => {
  assert.match(service, /\/moderacion\/denuncias\?\$\{query\}/);
  assert.match(service, /\/moderacion\/denuncias\/\$\{Number\(reportId\)\}/);
  assert.doesNotMatch(service, /fetch\s*\(/);
});

test("keyset pagination and filters belong to shared query contracts", () => {
  assert.match(hooks, /useInfiniteQuery/);
  assert.match(hooks, /initialPageParam: null/);
  assert.match(hooks, /lastPage\.next_cursor/);
  assert.match(queryKeys, /reports:[\s\S]*list: \(filters\)/);
  assert.match(service, /"estado"[\s\S]*"recurso_tipo"[\s\S]*"motivo"/);
});

test("rapid filter changes can cancel stale HTTP reads", () => {
  assert.match(hooks, /queryFn: \(\{ pageParam, signal \}\)/);
  assert.match(hooks, /token: accessToken,[\s\S]*signal/);
  assert.match(httpService, /signal: options\.signal/);
});

test("route requires the approved administrative capability", () => {
  assert.match(router, /path="\/administracion\/denuncias"/);
  assert.match(router, /capability="moderation\.reports\.read"/);
  assert.match(router, /AdministrativeAccessGuard/);
});

test("report contracts remain private and decisions use their dedicated mutation", () => {
  assert.doesNotMatch(page, /denunciante|reporter_usuario_id|email|modo_activo/);
  assert.match(hooks, /useCreateModerationDecision/);
  assert.match(page, /moderation\.decisions\.write/);
  assert.doesNotMatch(page, /sancionar|asignar|apelaci|automatiz/i);
});

test("decision controls send report and resource versions plus causal restoration", () => {
  assert.match(page, /expected_denuncia_version/);
  assert.match(page, /expected_resource_revision/);
  assert.match(page, /reverses_decision_id/);
  assert.match(page, /moderation_hidden_by_decision_id/);
  assert.match(page, /idempotency_key/);
  assert.match(page, /administrativeErrorMessage\(createDecision\.error/);
});

test("empty, filtered-empty, error and unavailable resource states are explicit", () => {
  assert.match(page, /Todavía no hay denuncias registradas/);
  assert.match(page, /No hay denuncias que coincidan con estos filtros/);
  assert.match(page, /No pudimos consultar las denuncias/);
  assert.match(page, /No disponible actualmente/);
});

test("frontend only links a route returned by backend", () => {
  assert.match(page, /to=\{detail\.data\.recurso_actual\.ruta_publica\}/);
  assert.doesNotMatch(page, /\/historias\/\$\{/);
});

import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

const page = fs.readFileSync(new URL("../src/features/administration/pages/AdministrativeHomePage.jsx", import.meta.url), "utf8");
const nav = fs.readFileSync(new URL("../src/features/administration/components/AdministrativeNavigationLink.jsx", import.meta.url), "utf8");
const router = fs.readFileSync(new URL("../src/core/router/AppRouter.jsx", import.meta.url), "utf8");
const layout = fs.readFileSync(new URL("../src/shared/layouts/MainLayout.jsx", import.meta.url), "utf8");

test("private administration home is routed behind authentication", () => {
  assert.match(router, /path="\/administracion"[\s\S]*?<ProtectedRoute>[\s\S]*?<AdministrativeHomePage/);
});

test("each administrative surface is capability-driven", () => {
  for (const capability of ["moderation.reports.read", "operations.incidents.manage", "operations.status.read"]) {
    assert.match(page, new RegExp(capability.replaceAll(".", "\\.")));
    assert.match(nav, new RegExp(capability.replaceAll(".", "\\.")));
  }
  assert.match(page, /SURFACES\.filter\(\(\{ capability \}\) => tieneCapacidad\(capability\)\)/);
  assert.doesNotMatch(page, /modo_activo|ownership|is_admin/);
});

test("global access is conditional and reuses the shared capability query", () => {
  assert.match(layout, /estaAutenticado && <AdministrativeNavigationLink/);
  assert.match(nav, /NAVIGABLE_CAPABILITIES\.some\(tieneCapacidad\)/);
  assert.match(nav, /useAdministrativeCapabilities/);
});

test("administrative access occupies its own mobile row without changing desktop placement", () => {
  assert.match(layout, /flex-wrap items-center[\s\S]*sm:flex-nowrap/);
  assert.match(layout, /order-3 flex min-w-0 w-full[\s\S]*sm:order-none sm:w-auto sm:shrink-0/);
  assert.match(nav, /min-h-11 min-w-0 w-full justify-center whitespace-normal break-words[\s\S]*sm:w-auto sm:shrink-0/);
});

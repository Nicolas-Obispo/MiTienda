import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

const guide = fs.readFileSync(new URL("../src/features/administration/pages/AdministrativeGuidePage.jsx", import.meta.url), "utf8");
const home = fs.readFileSync(new URL("../src/features/administration/pages/AdministrativeHomePage.jsx", import.meta.url), "utf8");
const router = fs.readFileSync(new URL("../src/core/router/AppRouter.jsx", import.meta.url), "utf8");

test("la guía es privada y exige una identidad con capacidades administrativas", () => {
  assert.match(router, /path="\/administracion\/guia"[\s\S]*?<ProtectedRoute>[\s\S]*?<AdministrativeGuidePage/);
  assert.match(guide, /useAdministrativeCapabilities/);
  assert.match(guide, /capacidades\.length === 0/);
  assert.match(guide, /<AdministrativeAccessDenied \/>/);
  assert.match(home, /available\.length > 0[\s\S]*to="\/administracion\/guia"/);
});

test("la guía cubre el circuito administrativo aprobado en español claro", () => {
  for (const text of [
    "Acceso y capacidades", "Portada administrativa", "Consulta de denuncias",
    "Decisiones, fundamento y evidencia", "Ocultamiento y restauración causal",
    "Gestión de incidentes", "Límites de Estado Operativo",
    "Canal operativo por correo", "Errores y recuperación",
  ]) assert.match(guide, new RegExp(text));
});

test("la advertencia de minimización es visible y no incluye evidencia de pruebas", () => {
  assert.match(guide, /Nunca ingreses secretos, contraseñas, datos privados, URLs internas, rutas de archivos ni payloads/);
  assert.doesNotMatch(guide, /INC-[A-Z0-9]+|usuario\s+32|Publicación\s+9|Historia\s+37|fixture/i);
});

test("la guía conserva navegación táctil y responsive", () => {
  assert.match(guide, /to="\/administracion">Volver a Administración/);
  assert.match(guide, /grid gap-4 md:grid-cols-2/);
  assert.match(guide, /min-h-11/);
});

import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

const service = fs.readFileSync(
  new URL("../src/features/administration/services/administrationService.js", import.meta.url),
  "utf8",
);
const hook = fs.readFileSync(
  new URL("../src/features/administration/hooks/useAdministrativeCapabilities.js", import.meta.url),
  "utf8",
);
const guard = fs.readFileSync(
  new URL("../src/features/administration/components/AdministrativeAccessGuard.jsx", import.meta.url),
  "utf8",
);
const authContext = fs.readFileSync(
  new URL("../src/features/auth/context/AuthContext.jsx", import.meta.url),
  "utf8",
);
const queryKeys = fs.readFileSync(
  new URL("../src/core/constants/queryKeys.js", import.meta.url),
  "utf8",
);

test("administrative service consumes the backend contract through shared HTTP", () => {
  assert.match(service, /httpGet\("\/administracion\/me\/capacidades", tokenJWT\)/);
  assert.doesNotMatch(service, /fetch\s*\(/);
});

test("administrative query is scoped to the authenticated identity", () => {
  assert.match(hook, /queryKeys\.administration\.capabilities\(usuario\?\.id\)/);
  assert.match(hook, /estaAutenticado && accessToken && usuario\?\.id/);
  assert.match(queryKeys, /capabilities:\s*\(usuarioId\)/);
});

test("frontend guard consumes capabilities without inferring modo_activo", () => {
  assert.match(guard, /tieneCapacidad\(capability\)/);
  assert.doesNotMatch(guard, /modo_activo|publicador|is_admin/);
  assert.doesNotMatch(hook, /modo_activo|publicador|is_admin/);
});

test("anonymous and unauthorized states render fallback", () => {
  assert.match(guard, /if \(!estaAutenticado\) return fallback/);
  assert.match(guard, /isError \|\| !tieneCapacidad\(capability\)/);
});

test("session cleanup also clears administrative query data", () => {
  assert.match(authContext, /queryClient\.clear\(\)/);
});

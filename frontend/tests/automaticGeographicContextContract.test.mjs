import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { createManualContext, geographicQueryContext } from "../src/shared/location/geographicContextState.js";

const frontendRoot = new URL("../", import.meta.url);

test("el contexto automatico consulta permiso, es single-flight y conserva el fallback preciso", async () => {
  const [provider, state] = await Promise.all([
    readFile(new URL("src/shared/location/GeographicContext.jsx", frontendRoot), "utf8"),
    readFile(new URL("src/shared/location/geographicContextState.js", frontendRoot), "utf8"),
  ]);
  assert.match(provider, /navigator\.permissions\.query\(\{ name: "geolocation" \}\)/);
  assert.match(provider, /if \(activeRequestRef\.current\) return activeRequestRef\.current/);
  assert.match(provider, /if \(permission === "denied"\) return applyProfileFallback\(\)/);
  assert.match(state, /if \(error\?\.code !== 3\) throw error/);
  assert.match(state, /return read\(PRECISE_POSITION_OPTIONS\)/);
});

test("Explorar y Seguidos inicializan el owner geografico sin duplicar su algoritmo", async () => {
  const [explore, followed] = await Promise.all([
    readFile(new URL("src/features/explore/pages/ExplorarPage.jsx", frontendRoot), "utf8"),
    readFile(new URL("src/features/spaces/pages/VerSeguidosPage.jsx", frontendRoot), "utf8"),
  ]);
  for (const source of [explore, followed]) {
    assert.match(source, /void ensureAutomaticContext\(\)/);
    assert.doesNotMatch(source, /navigator\.geolocation|permissions\.query/);
  }
});

test("profile_fallback y contexto manual nunca se presentan al backend como GPS", () => {
  for (const source of ["profile_fallback", "manual"]) {
    const context = createManualContext({ city: "Rafaela", province: "Santa Fe", source });
    const query = geographicQueryContext(context);
    assert.equal(context.source, source);
    assert.equal(query.lat, null);
    assert.equal(query.lng, null);
    assert.equal(query.city_key, "Rafaela");
  }
});

test("las pantallas no representan distancia sin coordenadas reales", async () => {
  const [explore, followed] = await Promise.all([
    readFile(new URL("src/features/explore/pages/ExplorarPage.jsx", frontendRoot), "utf8"),
    readFile(new URL("src/features/spaces/pages/VerSeguidosPage.jsx", frontendRoot), "utf8"),
  ]);
  for (const source of [explore, followed]) {
    assert.match(source, /queryContext\?\.lat !== null && typeof c\.distancia_km === "number"/);
  }
});

test("la composicion reconcilia identidad sin acoplar Shared con Auth", async () => {
  const [coordinator, provider] = await Promise.all([
    readFile(new URL("src/core/bootstrap/GeographicIdentityCoordinator.jsx", frontendRoot), "utf8"),
    readFile(new URL("src/shared/location/GeographicContext.jsx", frontendRoot), "utf8"),
  ]);
  assert.match(coordinator, /useAuth/);
  assert.match(coordinator, /reconcileIdentity/);
  assert.match(coordinator, /user:\$\{usuario\.id\}/);
  assert.match(provider, /setIdentityRevision\(\(current\) => current \+ 1\)/);
  assert.match(provider, /browserPermission, identityRevision, requestDeviceLocation/);
  assert.doesNotMatch(provider, /@features\/auth|useAuth/);
});

test("cambios de permiso eliminan solo coordenadas efimeras del dispositivo", async () => {
  const provider = await readFile(new URL("src/shared/location/GeographicContext.jsx", frontendRoot), "utf8");
  assert.match(provider, /status\.addEventListener\?\.\("change", handleChange\)/);
  assert.match(provider, /status\.state === "denied" && contextRef\.current\.source === "device"/);
  assert.match(provider, /automaticAttemptRef\.current = null/);
  assert.doesNotMatch(provider, /localStorage|sessionStorage|IndexedDB/);
});

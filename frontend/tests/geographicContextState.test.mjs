import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { queryKeys } from "../src/core/constants/queryKeys.js";
import {
  acceptDevicePosition,
  acquirePosition,
  createManualContext,
  DISTANCE_MAX_AGE_MS,
  FAST_POSITION_OPTIONS,
  geographicQueryContext,
  geolocationErrorState,
  isDistanceFresh,
  isSignificantDisplacement,
  isTerritoryFresh,
  PRECISE_POSITION_OPTIONS,
  TERRITORY_MAX_AGE_MS,
} from "../src/shared/location/geographicContextState.js";

const territory = {
  city_key: "rafaela",
  province_code: "AR-S",
  country_code: "AR",
  city: "Rafaela",
  province: "Santa Fe",
  country: "Argentina",
};

function reading(overrides = {}) {
  return { lat: -31.25, lng: -61.49, accuracy: 20, capturedAt: 1000, ...overrides };
}

test("las lecturas rápida y precisa usan la política aprobada", () => {
  assert.deepEqual(FAST_POSITION_OPTIONS, { maximumAge: 60000, timeout: 3000, enableHighAccuracy: false });
  assert.deepEqual(PRECISE_POSITION_OPTIONS, { maximumAge: 0, timeout: 8000, enableHighAccuracy: true });
});

test("lectura rápida se refina solo cuando la precisión lo requiere", async () => {
  const calls = [];
  const result = await acquirePosition(async (options) => {
    calls.push(options);
    return calls.length === 1 ? reading({ accuracy: 250 }) : reading({ accuracy: 30 });
  });
  assert.equal(result.accuracy, 30);
  assert.deepEqual(calls, [FAST_POSITION_OPTIONS, PRECISE_POSITION_OPTIONS]);
});

test("lectura rapida suficiente realiza un unico intento", async () => {
  const calls = [];
  const result = await acquirePosition(async (options) => {
    calls.push(options);
    return reading({ accuracy: 30 });
  });
  assert.equal(result.accuracy, 30);
  assert.deepEqual(calls, [FAST_POSITION_OPTIONS]);
});

test("timeout rapido usa una unica lectura precisa como fallback", async () => {
  const calls = [];
  const result = await acquirePosition(async (options) => {
    calls.push(options);
    if (calls.length === 1) throw Object.assign(new Error("timeout rapido"), { code: 3 });
    return reading({ accuracy: 25 });
  });
  assert.equal(result.accuracy, 25);
  assert.deepEqual(calls, [FAST_POSITION_OPTIONS, PRECISE_POSITION_OPTIONS]);
});

test("dos timeouts preservan el error preciso final sin mas intentos", async () => {
  const calls = [];
  const preciseTimeout = Object.assign(new Error("timeout preciso"), { code: 3 });
  await assert.rejects(
    acquirePosition(async (options) => {
      calls.push(options);
      if (calls.length === 1) throw Object.assign(new Error("timeout rapido"), { code: 3 });
      throw preciseTimeout;
    }),
    (error) => error === preciseTimeout
  );
  assert.deepEqual(calls, [FAST_POSITION_OPTIONS, PRECISE_POSITION_OPTIONS]);
});

test("fallback preciso preserva un error final distinto de timeout", async () => {
  const calls = [];
  const unavailable = Object.assign(new Error("no disponible"), { code: 2 });
  await assert.rejects(
    acquirePosition(async (options) => {
      calls.push(options);
      if (calls.length === 1) throw Object.assign(new Error("timeout rapido"), { code: 3 });
      throw unavailable;
    }),
    (error) => error === unavailable
  );
  assert.deepEqual(calls, [FAST_POSITION_OPTIONS, PRECISE_POSITION_OPTIONS]);
});

test("permiso denegado no ejecuta fallback preciso", async () => {
  const calls = [];
  const denied = Object.assign(new Error("permiso denegado"), { code: 1 });
  await assert.rejects(
    acquirePosition(async (options) => {
      calls.push(options);
      throw denied;
    }),
    (error) => error === denied
  );
  assert.deepEqual(calls, [FAST_POSITION_OPTIONS]);
});

test("error rapido distinto de timeout se preserva sin fallback", async () => {
  const calls = [];
  const unavailable = Object.assign(new Error("no disponible"), { code: 2 });
  await assert.rejects(
    acquirePosition(async (options) => {
      calls.push(options);
      throw unavailable;
    }),
    (error) => error === unavailable
  );
  assert.deepEqual(calls, [FAST_POSITION_OPTIONS]);
});

test("fallo de refinamiento conserva lectura territorial útil", async () => {
  let calls = 0;
  const result = await acquirePosition(async () => {
    calls += 1;
    if (calls === 1) return reading({ accuracy: 500 });
    throw Object.assign(new Error("timeout"), { code: 3 });
  });
  assert.equal(result.accuracy, 500);
  assert.equal(isDistanceFresh(result, result.capturedAt), false);
});

test("permiso rechazado y API ausente conservan estados recuperables", () => {
  assert.equal(geolocationErrorState({ code: 1 }), "denied");
  assert.equal(geolocationErrorState({ code: "unavailable" }), "unavailable");
  assert.equal(geolocationErrorState({ code: 3 }), "error");
});

test("frescura territorial y de distancia son independientes", () => {
  const context = acceptDevicePosition(null, reading({ accuracy: 500 }), territory, { now: 1000 });
  assert.equal(isTerritoryFresh(context, 1000 + TERRITORY_MAX_AGE_MS), true);
  assert.equal(isDistanceFresh(context, 1000), false);
  const precise = acceptDevicePosition(null, reading(), territory, { now: 1000 });
  assert.equal(isDistanceFresh(precise, 1000 + DISTANCE_MAX_AGE_MS), true);
  assert.equal(isDistanceFresh(precise, 1001 + DISTANCE_MAX_AGE_MS), false);
});

test("ruido GPS no incrementa revisión y desplazamiento significativo sí", () => {
  const initial = acceptDevicePosition(null, reading(), territory, { now: 1000 });
  const noise = acceptDevicePosition(initial, reading({ lat: -31.25005, capturedAt: 2000 }), territory, { now: 2000 });
  const moved = acceptDevicePosition(noise, reading({ lat: -31.252, capturedAt: 3000 }), territory, { now: 3000 });
  assert.equal(isSignificantDisplacement(initial, noise), false);
  assert.equal(noise.positionRevision, initial.positionRevision);
  assert.equal(moved.positionRevision, initial.positionRevision + 1);
});

test("cambio de ciudad y refresco obsoleto incrementan revisión", () => {
  const initial = acceptDevicePosition(null, reading(), territory, { now: 1000 });
  const sunchales = { ...territory, city_key: "sunchales", city: "Sunchales" };
  const changed = acceptDevicePosition(initial, reading({ capturedAt: 2000 }), sunchales, { now: 2000 });
  const refreshed = acceptDevicePosition(changed, reading({ capturedAt: 70000 }), sunchales, { now: 70000 });
  assert.equal(changed.positionRevision, initial.positionRevision + 1);
  assert.equal(refreshed.positionRevision, changed.positionRevision + 1);
});

test("fallback manual y de perfil nunca se presentan como GPS", () => {
  const manual = createManualContext({ city: "Rafaela", province: "Santa Fe" });
  const profile = createManualContext({ city: "Sunchales", province: "Santa Fe", source: "profile_fallback" });
  assert.equal(manual.source, "manual");
  assert.equal(profile.source, "profile_fallback");
  assert.equal(geographicQueryContext(manual).lat, null);
});

test("query key ignora coordenadas crudas y cambia con positionRevision", () => {
  const base = {
    q: "plomero",
    city_key: "rafaela",
    province_code: "AR-S",
    country_code: "AR",
    scope: "local",
    positionRevision: 2,
  };
  const first = queryKeys.explore.spaces({ ...base, lat: -31.25, lng: -61.49 });
  const noise = queryKeys.explore.spaces({ ...base, lat: -31.25001, lng: -61.49001 });
  const revised = queryKeys.explore.spaces({ ...base, positionRevision: 3 });
  assert.deepEqual(first, noise);
  assert.notDeepEqual(first, revised);
});

test("prefetch y consulta principal comparten el mismo builder", async () => {
  const source = await readFile(new URL("../src/features/explore/pages/ExplorarPage.jsx", import.meta.url), "utf8");
  assert.match(source, /getExplorarEspaciosInfiniteQueryOptions\(paramsBusqueda\)/);
  assert.doesNotMatch(source, /navigator\.geolocation/);
});

test("Seguidos inicia contexto automatico mediante el owner sin usar APIs del navegador directamente", async () => {
  const source = await readFile(new URL("../src/features/spaces/pages/VerSeguidosPage.jsx", import.meta.url), "utf8");
  assert.match(source, /useGeographicContext/);
  assert.match(source, /ensureAutomaticContext/);
  assert.doesNotMatch(source, /navigator\.geolocation/);
});

test("resolverTerritorio se ejecuta solo despues de adquirir coordenadas validas", async () => {
  const source = await readFile(
    new URL("../src/shared/location/GeographicContext.jsx", import.meta.url),
    "utf8"
  );
  const acquisition = source.indexOf("await acquirePosition(readPosition, { needDistance })");
  const territoryResolution = source.indexOf("await resolverTerritorio({ latitud: reading.lat, longitud: reading.lng })");

  assert.notEqual(acquisition, -1);
  assert.notEqual(territoryResolution, -1);
  assert.ok(acquisition < territoryResolution);
});

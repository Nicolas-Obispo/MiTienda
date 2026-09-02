import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const profile = await readFile(
  new URL(
    "../src/features/spaces/pages/PerfilComercioPage.jsx",
    import.meta.url
  ),
  "utf8"
);

const privateMetricsLoader = profile.match(
  /async function loadDatosSecundarios[\s\S]*?\n  }\n\n  async function refreshHistorias/
)?.[0] || "";

const followingHook = await readFile(
  new URL(
    "../src/features/spaces/hooks/useSeguimientoEspacio.js",
    import.meta.url
  ),
  "utf8"
);

const privateMetricsEffect = profile.match(
  /useEffect\(\(\) => \{\n    let isCurrent = true;[\s\S]*?isEstadisticasOpen,\n  \]\);/
)?.[0] || "";

const privateMetricsGateSource = profile.match(
  /function puedeCargarMetricasPrivadas\([\s\S]*?\n}\n\nexport default/
)?.[0] || "";
const executablePrivateMetricsGateSource = privateMetricsGateSource.replace(
  /\n\nexport default$/,
  ""
);
const puedeCargarMetricasPrivadas = Function(
  `${executablePrivateMetricsGateSource}; return puedeCargarMetricasPrivadas;`
)();

function contarRequestsPrivados(overrides = {}) {
  const puedeCargar = puedeCargarMetricasPrivadas({
    comercioId: 5,
    estaAutenticado: true,
    comercioResuelto: true,
    esPropietario: true,
    isEstadisticasOpen: true,
    ...overrides,
  });

  return puedeCargar ? 3 : 0;
}

test("metricas privadas requieren ownership resuelto y modal abierto", () => {
  assert.equal(contarRequestsPrivados({ esPropietario: false }), 0);
  assert.equal(contarRequestsPrivados({ isEstadisticasOpen: false }), 0);
  assert.equal(contarRequestsPrivados({ comercioResuelto: false }), 0);
  assert.equal(contarRequestsPrivados({ estaAutenticado: false }), 0);
  assert.equal(contarRequestsPrivados({ comercioId: Number.NaN }), 0);
  assert.equal(contarRequestsPrivados(), 3);
  assert.match(profile, /comercioResuelto: comercioQuery\.isSuccess/);
  assert.match(profile, /esPropietario: comercioQuery\.data\?\.es_propietario/);
  assert.match(
    privateMetricsEffect,
    /if \(!puedeCargar\)[\s\S]*void loadDatosSecundarios/
  );
});

test("solo el loader privado contiene los tres requests de metricas", () => {
  assert.equal(
    (privateMetricsLoader.match(/obtenerMetricasSocialesEspacio\(comercioId\)/g) || []).length,
    1
  );
  assert.equal(
    (privateMetricsLoader.match(/obtenerComparacionMetricasSocialesEspacio\(comercioId\)/g) || []).length,
    1
  );
  assert.equal(
    (privateMetricsLoader.match(/obtenerAnalyticsEspacio\(comercioId\)/g) || []).length,
    1
  );
  assert.match(privateMetricsLoader, /Promise\.all\(/);
  assert.doesNotMatch(profile, /useMisComercios|queryKeys\.analytics|useQuery\(/);
});

test("comercio ajeno o estadisticas cerradas limpian datos privados", () => {
  const clearBranch = privateMetricsEffect.match(
    /if \(!puedeCargar\) \{[\s\S]*?return \(\) =>/
  )?.[0] || "";

  assert.match(clearBranch, /setMetricasSociales\(null\)/);
  assert.match(clearBranch, /setComparacionMetricas\(null\)/);
  assert.match(clearBranch, /setAnalyticsEspacio\(null\)/);
  assert.match(privateMetricsLoader, /if \(!isCurrent\(\)\) return/);
});

test("el 403 no participa del descubrimiento de ownership", () => {
  assert.doesNotMatch(profile, /status\s*===?\s*403|error\?\.status\s*===?\s*403/);
  assert.match(privateMetricsGateSource, /esPropietario === true/);
});

test("seguimiento conserva su carga separada de las metricas privadas", () => {
  assert.match(profile, /useEstadoSeguimientoEspacio\(comercioId/);
  assert.match(followingHook, /obtenerEstadoSeguimiento\(id, \{ signal \}\)/);
  assert.match(followingHook, /enabled: enabled && comercioIdValido\(id\)/);
  assert.doesNotMatch(privateMetricsLoader, /obtenerEstadoSeguimiento/);
});

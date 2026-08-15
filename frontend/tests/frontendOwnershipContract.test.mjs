import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

test("features consumen autenticacion mediante el hook publico", async () => {
  const [authIndex, createStory] = await Promise.all([
    readSource("../src/features/auth/index.js"),
    readSource("../src/features/stories/components/CrearHistoriaModal.jsx"),
  ]);

  assert.doesNotMatch(authIndex, /export \{ AuthContext \}/);
  assert.match(createStory, /import \{ useAuth \} from "@features\/auth"/);
  assert.match(createStory, /const \{ accessToken \} = useAuth\(\)/);
  assert.doesNotMatch(createStory, /useContext\(AuthContext\)|AuthContextCore/);
});

test("tema, geografia y overlays conservan un unico owner", async () => {
  const [themeRuntime, geographicProvider, geocodingService, activeLayer] =
    await Promise.all([
      readSource("../src/core/theme/themeRuntime.js"),
      readSource("../src/shared/location/GeographicContext.jsx"),
      readSource("../src/shared/services/geocoding_service.js"),
      readSource("../src/core/components/ActiveLayer.jsx"),
    ]);

  assert.match(themeRuntime, /__FEEDGO_THEME_BOOTSTRAP__/);
  assert.match(geographicProvider, /resolverTerritorio/);
  assert.match(geocodingService, /\/geocoding\/(?:forward|reverse|territory)/);
  assert.doesNotMatch(geocodingService, /geoapify|nominatim/i);
  assert.match(activeLayer, /createPortal/);
  assert.match(activeLayer, /lockBodyScroll/);
});

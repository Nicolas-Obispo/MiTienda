import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const [selector, themeProvider, themeBootstrap, helper] = await Promise.all([
  readFile(new URL("../src/features/auth/components/AppearanceSelector.jsx", import.meta.url), "utf8"),
  readFile(new URL("../src/core/theme/ThemeProvider.jsx", import.meta.url), "utf8"),
  readFile(new URL("../public/theme-bootstrap.js", import.meta.url), "utf8"),
  readFile(new URL("../src/shared/components/InteractiveLiquidLayers.jsx", import.meta.url), "utf8"),
]);

test("selector conserva las tres opciones y radios nativos", () => {
  for (const [value, label] of [
    ["dark", "Fondo oscuro"],
    ["light", "Fondo claro"],
    ["system", "Usar configuración del sistema"],
  ]) {
    assert.match(selector, new RegExp(`value: "${value}"[\\s\\S]*label: "${label}"`));
  }
  assert.match(selector, /APPEARANCE_OPTIONS\.map\(\(option\) =>/);
  assert.match(selector, /<label[\s\S]*<input[\s\S]*type="radio"/);
  assert.match(selector, /name="theme-preference"/);
  assert.match(selector, /value=\{option\.value\}/);
});

test("cada label generado recibe una única capa Liquid", () => {
  assert.equal((selector.match(/interactive-bubble--liquid/g) || []).length, 1);
  assert.equal((selector.match(/<InteractiveLiquidLayers \/>/g) || []).length, 1);
  assert.match(selector, /interactive-bubble--liquid interactive-bubble--secondary[\s\S]*<input[\s\S]*<InteractiveLiquidLayers \/>[\s\S]*<\/label>/);
  assert.match(helper, /aria-hidden="true"/);
  assert.doesNotMatch(helper, /on[A-Z][A-Za-z]*=|pointer-events-auto/);
});

test("checked, cambio, foco y selección visual permanecen", () => {
  assert.match(selector, /const isSelected = preference === option\.value/);
  assert.match(selector, /checked=\{isSelected\}/);
  assert.match(selector, /onChange=\{\(\) => setPreference\(option\.value\)\}/);
  assert.match(selector, /focus-within:outline[\s\S]*focus-within:outline-focus-ring/);
  assert.match(selector, /border-border-strong bg-surface text-primary shadow-elevation/);
  assert.match(selector, /border-border bg-surface-subtle text-primary hover:bg-surface/);
  assert.match(selector, /accent-brand/);
});

test("persistencia y resolución light dark system permanecen en su owner", () => {
  assert.match(selector, /const \{ preference, setPreference \} = useTheme\(\)/);
  assert.doesNotMatch(selector, /localStorage|matchMedia|data-theme|resolvedTheme/);
  assert.match(themeProvider, /themeBridge\.setPreference\(nextPreference\)/);
  assert.match(themeProvider, /preference: snapshot\.preference/);
  assert.match(themeProvider, /resolvedTheme: snapshot\.resolvedTheme/);
  assert.match(themeBootstrap, /localStorage/);
  assert.match(themeBootstrap, /matchMedia/);
  assert.match(themeBootstrap, /data-theme/);
});

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const selectorSource = await readFile(
  new URL(
    "../src/features/auth/components/AppearanceSelector.jsx",
    import.meta.url
  ),
  "utf8"
);
const profileSource = await readFile(
  new URL("../src/features/auth/pages/ProfilePage.jsx", import.meta.url),
  "utf8"
);

const editStart = profileSource.indexOf("{showPerfilForm && (");
const editEnd = profileSource.indexOf(
  "{!showPerfilForm && showActivarEspacioInfo",
  editStart
);
const editSurface = profileSource.slice(editStart, editEnd);

test("Editar perfil mantiene ocultas inicialmente las preferencias aprobadas", () => {
  assert.match(selectorSource, /value: "dark"/);
  assert.match(selectorSource, /label: "Fondo oscuro"/);
  assert.match(selectorSource, /value: "light"/);
  assert.match(selectorSource, /label: "Fondo claro"/);
  assert.match(selectorSource, /value: "system"/);
  assert.match(selectorSource, /label: "Usar configuración del sistema"/);
  assert.match(profileSource, /const \[showAppearanceOptions, setShowAppearanceOptions\] = useState\(false\)/);
  assert.match(profileSource, />\s*Color de fondo\s*<\/Button>/);
  assert.match(profileSource, /aria-expanded=\{showAppearanceOptions\}/);
  assert.match(profileSource, /aria-controls="perfil-apariencia-options"/);
  assert.match(profileSource, /\{showAppearanceOptions && \([\s\S]*<AppearanceSelector \/>/);
});

test("selector consume solo preference y setPreference del owner", () => {
  assert.match(
    selectorSource,
    /const \{ preference, setPreference \} = useTheme\(\)/
  );
  assert.match(selectorSource, /checked=\{isSelected\}/);
  assert.match(selectorSource, /onChange=\{\(\) => setPreference\(option.value\)\}/);
  assert.doesNotMatch(
    selectorSource,
    /localStorage|matchMedia|resolvedTheme|data-theme|bootstrap|bridge|theme-color/
  );
});

test("radios nativos preservan teclado, foco y estado seleccionado", () => {
  assert.match(selectorSource, /<fieldset/);
  assert.match(selectorSource, /<legend/);
  assert.match(selectorSource, /type="radio"/);
  assert.match(selectorSource, /name="theme-preference"/);
  assert.match(selectorSource, /focus-within:outline-focus-ring/);
  assert.match(selectorSource, /border-border-strong bg-surface text-primary shadow-elevation/);
  assert.doesNotMatch(selectorSource, /selected-(?:border|surface|text)|purple|violet|lila/i);
  assert.match(selectorSource, /interactive-bubble interactive-bubble--secondary/);
});

test("Editar perfil adopta primitives sin mover estado de formulario", () => {
  for (const primitive of [
    "AppearanceSelector",
    "Surface",
    "Button",
    "FormControl",
    "Input",
    "Alert",
  ]) {
    assert.match(editSurface, new RegExp(`<${primitive}\\b`));
  }

  assert.match(editSurface, /onSubmit=\{handlePerfilSubmit\}/);
  assert.match(editSurface, /onChange=\{handlePerfilFormChange\}/);
  assert.match(editSurface, /onClick=\{cancelarEdicionPerfil\}/);
});

test("acciones migradas componen Button e interactive-bubble una sola vez", () => {
  assert.doesNotMatch(editSurface, /<button\b/);
  assert.match(editSurface, /variant="secondary"/);
  assert.doesNotMatch(editSurface, /type="submit"[\s\S]{0,120}variant="primary"/);
  assert.match(editSurface, /type="submit"[\s\S]{0,120}variant="secondary"/);

  const buttonUses = editSurface.match(/<Button\b/g) || [];
  assert.ok(buttonUses.length >= 3);
  assert.doesNotMatch(editSurface, /interactive-bubble/);
});

test("superficie migrada no introduce colores fisicos ni logica manual de tema", () => {
  assert.doesNotMatch(editSurface, /#[\da-f]{3,8}|\brgb\(|\brgba\(/i);
  assert.doesNotMatch(
    editSurface,
    /(?:bg|text|border)-(?:gray|white|black|red|green|orange|amber|yellow|purple)-?\d*/
  );
  assert.doesNotMatch(
    editSurface,
    /resolvedTheme|data-theme|dark:|matchMedia|localStorage/
  );
});

test("selector existe solo en Editar perfil", () => {
  assert.equal((profileSource.match(/<AppearanceSelector \/>/g) || []).length, 1);
});

test("tema no forma parte del payload persistido del perfil", () => {
  assert.match(
    profileSource,
    /const payload = \{\s*provincia: perfilForm\.provincia\.trim\(\),\s*ciudad: perfilForm\.ciudad\.trim\(\),\s*\}/
  );
  assert.doesNotMatch(
    profileSource.slice(
      profileSource.indexOf("async function handlePerfilSubmit"),
      profileSource.indexOf("async function uploadMedia")
    ),
    /preference|resolvedTheme|setPreference/
  );
  assert.doesNotMatch(profileSource, /Color del perfil|perfilForm\.color_fondo|showColorFondoOptions/);
});

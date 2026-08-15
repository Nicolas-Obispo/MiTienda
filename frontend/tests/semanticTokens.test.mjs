import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

const physicalSource = await readFile(
  new URL("../public/theme-tokens.css", import.meta.url),
  "utf8"
);
const aliasesSource = await readFile(
  new URL("../src/core/theme/tokens.css", import.meta.url),
  "utf8"
);
const globalCss = await readFile(
  new URL("../src/index.css", import.meta.url),
  "utf8"
);
const bootstrapCss = await readFile(
  new URL("../public/theme-bootstrap.css", import.meta.url),
  "utf8"
);
const bootstrapJs = await readFile(
  new URL("../public/theme-bootstrap.js", import.meta.url),
  "utf8"
);
const interactionButton = await readFile(
  new URL("../src/shared/components/InteraccionButton.jsx", import.meta.url),
  "utf8"
);

function declarationsFor(selectorPattern) {
  const match = physicalSource.match(
    new RegExp(`${selectorPattern}\\s*\\{([\\s\\S]*?)\\}`)
  );
  assert.ok(match, `No se encontro el selector ${selectorPattern}`);
  return new Map(
    [...match[1].matchAll(/(--fg-[\w-]+)\s*:\s*([^;]+);/g)].map(
      ([, name, value]) => [name, value.trim()]
    )
  );
}

function rgb(hex) {
  const value = hex.replace("#", "");
  return [0, 2, 4].map((offset) => Number.parseInt(value.slice(offset, offset + 2), 16));
}

function luminance(hex) {
  const channels = rgb(hex).map((channel) => {
    const normalized = channel / 255;
    return normalized <= 0.04045
      ? normalized / 12.92
      : ((normalized + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function contrast(first, second) {
  const values = [luminance(first), luminance(second)].sort((a, b) => b - a);
  return (values[0] + 0.05) / (values[1] + 0.05);
}

const dark = declarationsFor(":root,\\s*html\\[data-theme=\"dark\"\\]");
const light = declarationsFor("html\\[data-theme=\"light\"\\]");

test("dark y light implementan el mismo contrato semantico", () => {
  assert.equal(dark.size, 38);
  assert.deepEqual([...dark.keys()].sort(), [...light.keys()].sort());
});

test("aliases Tailwind v4 cubren todos los tokens sin valores fisicos", () => {
  assert.match(aliasesSource, /@theme inline/);
  for (const token of dark.keys()) {
    assert.match(aliasesSource, new RegExp(`var\\(${token}\\)`));
  }
  assert.doesNotMatch(aliasesSource, /#[\da-f]{3,8}|\brgb\(|\brgba\(/i);
  assert.match(globalCss, /@import "\.\/core\/theme\/tokens\.css"/);
});

test("aliases de texto generan la API publica documentada", () => {
  assert.match(aliasesSource, /--color-primary:\s*var\(--fg-color-text-primary\)/);
  assert.match(aliasesSource, /--color-secondary:\s*var\(--fg-color-text-secondary\)/);
  assert.match(aliasesSource, /--color-muted:\s*var\(--fg-color-text-muted\)/);
  assert.match(aliasesSource, /--color-inverse:\s*var\(--fg-color-text-inverse\)/);
  assert.doesNotMatch(aliasesSource, /--color-text-(?:primary|secondary|muted|inverse):/);
});

test("no existe configuracion Tailwind paralela", async () => {
  await assert.rejects(access(new URL("../tailwind.config.js", import.meta.url)));
  await assert.rejects(access(new URL("../tailwind.config.cjs", import.meta.url)));
  assert.doesNotMatch(aliasesSource, /dark:/);
});

test("pares aprobados alcanzan contraste WCAG en ambos temas", () => {
  const textPairs = [
    ["text-primary", "canvas"],
    ["text-primary", "surface"],
    ["text-secondary", "canvas"],
    ["text-secondary", "surface"],
    ["interactive-on-primary", "interactive-primary"],
    ["success-text", "success-surface"],
    ["warning-text", "warning-surface"],
    ["danger-text", "danger-surface"],
    ["selected-text", "selected-surface"],
  ];

  for (const [themeName, tokens] of [["dark", dark], ["light", light]]) {
    for (const [foreground, background] of textPairs) {
      const ratio = contrast(
        tokens.get(`--fg-color-${foreground}`),
        tokens.get(`--fg-color-${background}`)
      );
      assert.ok(ratio >= 4.5, `${themeName}: ${foreground}/${background} = ${ratio}`);
    }

    for (const background of ["canvas", "surface", "surface-subtle"]) {
      const ratio = contrast(
        tokens.get("--fg-color-focus-ring"),
        tokens.get(`--fg-color-${background}`)
      );
      assert.ok(ratio >= 3, `${themeName}: focus-ring/${background} = ${ratio}`);
    }
  }
});

test("canvas es fuente unica para anti-flash y theme-color", () => {
  assert.match(bootstrapCss, /background:\s*var\(--fg-color-canvas\)/);
  assert.match(bootstrapJs, /getPropertyValue\("--fg-color-canvas"\)/);
  assert.doesNotMatch(bootstrapJs, /#[\da-f]{3,8}/i);
});

test("interactive-bubble consume roles y conserva su contrato de interaccion", () => {
  assert.match(globalCss, /\.interactive-bubble\s*\{/);
  assert.match(globalCss, /--bubble-text:\s*var\(--fg-color-text-secondary\)/);
  assert.match(globalCss, /--bubble-focus:\s*var\(--fg-color-focus-ring\)/);
  assert.match(globalCss, /\.interactive-bubble--danger/);
  assert.match(globalCss, /\.interactive-bubble--warning/);
  assert.match(globalCss, /@keyframes likePop/);
  assert.match(globalCss, /@keyframes saveBounce/);
  assert.match(globalCss, /mask-composite:\s*exclude/);
  assert.match(globalCss, /prefers-reduced-motion:\s*reduce/);
  assert.doesNotMatch(interactionButton, /--bubble-|rgba?\(/);
  assert.match(interactionButton, /interactive-bubble--danger/);
  assert.match(interactionButton, /interactive-bubble--warning/);
  assert.match(interactionButton, /setTimeout[\s\S]*300/);
});

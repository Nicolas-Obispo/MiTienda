import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";

const sourceRoot = new URL("../src/", import.meta.url);
const readSource = (relativePath) =>
  readFile(new URL(relativePath, import.meta.url), "utf8");

async function readJsxSources(directoryUrl = sourceRoot) {
  const entries = await readdir(directoryUrl, { withFileTypes: true });
  const sources = [];

  for (const entry of entries) {
    const entryUrl = new URL(`${entry.name}${entry.isDirectory() ? "/" : ""}`, directoryUrl);
    if (entry.isDirectory()) {
      sources.push(...(await readJsxSources(entryUrl)));
    } else if (entry.name.endsWith(".jsx")) {
      sources.push({
        file: path.relative(sourceRoot.pathname, entryUrl.pathname),
        source: await readFile(entryUrl, "utf8"),
      });
    }
  }

  return sources;
}

const [button, helper, interactionButton, styles, jsxSources] =
  await Promise.all([
    readSource("../src/shared/components/primitives/Button.jsx"),
    readSource("../src/shared/components/InteractiveLiquidLayers.jsx"),
    readSource("../src/shared/components/InteraccionButton.jsx"),
    readSource("../src/index.css"),
    readJsxSources(),
  ]);

test("Liquid es el unico owner productivo de la superficie", () => {
  assert.match(styles, /Productive liquid surface shared by interactive controls/);
  assert.match(styles, /\.interactive-bubble--liquid \{\s*--liquid-upper-reflection:/);
  assert.match(styles, /\.interactive-bubble--liquid::before \{/);
  assert.match(styles, /\.interactive-bubble--liquid::after \{/);
  assert.match(styles, /-webkit-backdrop-filter: blur\(5px\) saturate\(1\.18\) contrast\(1\.06\)/);
  assert.match(styles, /backdrop-filter: blur\(5px\) saturate\(1\.18\) contrast\(1\.06\)/);
  assert.match(styles, /@supports not \(\(backdrop-filter: blur\(1px\)\)/);
  assert.doesNotMatch(styles, /water-lens|prototype|!important/);
});

test("el reflejo superior es claro en dark y conserva el owner light", () => {
  assert.match(styles, /\.interactive-bubble--liquid \{\s*--liquid-upper-reflection: var\(--fg-color-surface-elevated\);/);
  assert.match(styles, /html\[data-theme="dark"\] \.interactive-bubble--liquid \{\s*--liquid-upper-reflection: color-mix\(\s*in srgb,\s*var\(--fg-color-text-primary\) 58%,\s*transparent\s*\);/);
  assert.equal(
    (styles.match(/color-mix\(in srgb, var\(--liquid-upper-reflection\) (?:72|76)%, transparent\)/g) || []).length,
    2
  );
  assert.doesNotMatch(styles, /--liquid-upper-reflection:\s*(?:#|rgb|rgba|var\(--fg-color-(?:border|canvas|surface-subtle))/);
});

test("InteractiveLiquidLayers es exclusivamente decorativo", () => {
  assert.match(helper, /export default function InteractiveLiquidLayers\(\)/);
  assert.match(helper, /<span[\s\S]*aria-hidden="true"[\s\S]*className="interactive-bubble__rainbow-border"[\s\S]*\/>/);
  assert.doesNotMatch(helper, /on[A-Z][A-Za-z]*=|useState|useEffect|useReducer|useRef|children|props|\.\.\./);
  assert.match(styles, /\.interactive-bubble > span \{\s*position: relative;\s*z-index: 1;/);
  assert.match(styles, /\.interactive-bubble::before,\s*\.interactive-bubble > \.interactive-bubble__rainbow-border \{[\s\S]*z-index: -1;/);
});

test("el borde multicolor, fallback y reduced motion permanecen centralizados", () => {
  assert.equal((styles.match(/conic-gradient\(/g) || []).length, 1);
  assert.match(styles, /\.interactive-bubble > \.interactive-bubble__rainbow-border/);
  assert.match(styles, /@supports not \(\(mask-composite: exclude\)/);
  assert.match(styles, /@supports not \(\(backdrop-filter: blur\(1px\)/);
  assert.match(styles, /prefers-reduced-motion:[\s\S]*\.interactive-bubble--liquid::before,[\s\S]*\.interactive-bubble--liquid::after/);
});

test("Button e InteraccionButton inyectan exactamente una capa Liquid", () => {
  for (const owner of [button, interactionButton]) {
    assert.equal((owner.match(/interactive-bubble--liquid/g) || []).length, 1);
    assert.equal((owner.match(/<InteractiveLiquidLayers \/>/g) || []).length, 1);
  }
  assert.match(button, /interactive-bubble interactive-bubble--liquid/);
  assert.match(interactionButton, /interactive-bubble--liquid/);
});

test("todo control manual con interactive-bubble declara Liquid", () => {
  const automaticOwners = new Set([
    "shared/components/InteraccionButton.jsx",
    "shared/components/primitives/Button.jsx",
  ]);

  for (const { file, source } of jsxSources) {
    if (automaticOwners.has(file.replaceAll("\\", "/"))) continue;

    for (const line of source.split(/\r?\n/)) {
      if (/interactive-bubble(?:\s|["'`])/.test(line)) {
        assert.match(line, /interactive-bubble--liquid/, `${file}: ${line.trim()}`);
      }
    }
  }
});

test("cada consumidor manual tiene una sola capa y Button no recibe helpers manuales", () => {
  for (const { file, source } of jsxSources) {
    if (!source.includes("InteractiveLiquidLayers")) continue;
    if (file.endsWith("InteractiveLiquidLayers.jsx")) continue;

    const liquidCount = (source.match(/interactive-bubble--liquid/g) || []).length;
    const layerCount = (source.match(/<InteractiveLiquidLayers \/>/g) || []).length;
    assert.equal(layerCount, liquidCount, file);
    assert.doesNotMatch(
      source,
      /<Button\b(?:(?!<\/Button>)[\s\S])*<InteractiveLiquidLayers \/>(?:(?!<\/Button>)[\s\S])*<\/Button>/,
      file
    );
  }
});

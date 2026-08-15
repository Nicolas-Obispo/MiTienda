import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const primitiveUrls = {
  alert: new URL("../src/shared/components/primitives/Alert.jsx", import.meta.url),
  button: new URL("../src/shared/components/primitives/Button.jsx", import.meta.url),
  controls: new URL(
    "../src/shared/components/primitives/FormControls.jsx",
    import.meta.url
  ),
  skeleton: new URL(
    "../src/shared/components/primitives/Skeleton.jsx",
    import.meta.url
  ),
  surface: new URL(
    "../src/shared/components/primitives/Surface.jsx",
    import.meta.url
  ),
};

const sources = Object.fromEntries(
  await Promise.all(
    Object.entries(primitiveUrls).map(async ([name, url]) => [
      name,
      await readFile(url, "utf8"),
    ])
  )
);
const combined = Object.values(sources).join("\n");
const globalCss = await readFile(new URL("../src/index.css", import.meta.url), "utf8");
const interactionButton = await readFile(
  new URL("../src/shared/components/InteraccionButton.jsx", import.meta.url),
  "utf8"
);
const primitivesIndex = await readFile(
  new URL("../src/shared/components/primitives/index.js", import.meta.url),
  "utf8"
);
const sharedIndex = await readFile(
  new URL("../src/shared/index.js", import.meta.url),
  "utf8"
);

test("Button cubre variantes justificadas sobre una unica interactive-bubble", () => {
  for (const variant of [
    "primary",
    "secondary",
    "danger",
    "success",
    "warning",
    "ghost",
  ]) {
    assert.match(sources.button, new RegExp(`${variant}:`));
  }

  assert.match(sources.button, /"interactive-bubble[^"]*font-semibold"/);
  assert.equal((combined.match(/\.interactive-bubble\s*\{/g) || []).length, 0);
  assert.equal((globalCss.match(/\.interactive-bubble\s*\{/g) || []).length, 1);
});

test("interactive-bubble queda en components y no anula utilities semanticas", () => {
  assert.match(sources.button, /bg-interactive-primary text-interactive-on-primary/);
  assert.match(sources.button, /bg-surface-subtle text-primary/);
  assert.match(sources.button, /bg-danger-surface text-danger-text/);
  assert.match(sources.button, /bg-success-surface text-success-text/);
  assert.match(sources.button, /bg-warning-surface text-warning-text/);
  assert.match(globalCss, /@layer components\s*\{\s*\.interactive-bubble\s*\{/);
});

test("Button conserva semantica, props, eventos nativos y disabled accesible", () => {
  assert.match(sources.button, /type = "button"/);
  assert.match(sources.button, /\.\.\.props/);
  assert.match(sources.button, /disabled=\{disabled\}/);
  assert.match(sources.button, /aria-disabled=\{disabled \|\| undefined\}/);
  assert.doesNotMatch(sources.button, /preventDefault|stopPropagation|onClick\s*=/);
});

test("Button iconOnly exige un nombre accesible sin imponer su contenido", () => {
  assert.match(sources.button, /iconOnly && !ariaLabel && !ariaLabelledBy/);
  assert.match(sources.button, /requiere aria-label o aria-labelledby/);
  assert.match(sources.button, /aria-label=\{ariaLabel\}/);
  assert.match(sources.button, /aria-labelledby=\{ariaLabelledBy\}/);
});

test("InteraccionButton conserva su owner funcional y animaciones", () => {
  assert.match(interactionButton, /interactive-bubble/);
  assert.match(interactionButton, /animate-like/);
  assert.match(interactionButton, /animate-save/);
  assert.match(interactionButton, /setTimeout[\s\S]*300/);
  assert.match(globalCss, /@keyframes likePop/);
  assert.match(globalCss, /@keyframes saveBounce/);
  assert.match(
    globalCss,
    /\.interactive-bubble:disabled[\s\S]*--fg-color-disabled-text/
  );
});

test("Surface centraliza solo superficie y preserva semantica componible", () => {
  for (const variant of ["base", "subtle", "elevated"]) {
    assert.match(sources.surface, new RegExp(`${variant}:`));
  }
  assert.match(sources.surface, /as: Component = "div"/);
  assert.match(sources.surface, /\.\.\.props/);
  assert.match(sources.surface, /min-w-0 rounded-2xl border/);
  assert.doesNotMatch(sources.surface, /onClick|useEffect|useState/);
});

test("controles comparten apariencia sin apropiarse de validacion", () => {
  assert.match(sources.controls, /export const Input/);
  assert.match(sources.controls, /export const Select/);
  assert.match(sources.controls, /export const Textarea/);
  assert.match(sources.controls, /export function FormControl/);
  assert.match(sources.controls, /aria-invalid=\{invalid \|\| undefined\}/);
  assert.match(sources.controls, /htmlFor=\{labelFor\}/);
  assert.match(sources.controls, /id=\{errorId\}/);
  assert.match(sources.controls, /id=\{helpId\}/);
  assert.match(sources.controls, /min-w-0 w-full rounded-xl border/);
  assert.doesNotMatch(sources.controls, /useState|useEffect|onChange\s*=/);
});

test("Input integra una accion trailing sin apropiarse de su logica", () => {
  assert.match(sources.controls, /trailingAction = null/);
  assert.match(sources.controls, /trailingAction && "pr-12"/);
  assert.match(sources.controls, /absolute inset-y-0 right-1 flex items-center/);
  assert.match(sources.controls, /\[&>\.interactive-bubble\]:!h-8/);
  assert.match(sources.controls, /\{trailingAction\}/);
  assert.doesNotMatch(sources.controls, /password|showPassword|mostrarPassword/);
});

test("Alert limita variantes a evidencia funcional y no fuerza live region", () => {
  assert.match(sources.alert, /success:/);
  assert.match(sources.alert, /warning:/);
  assert.match(sources.alert, /danger:/);
  assert.doesNotMatch(sources.alert, /info:/);
  assert.doesNotMatch(sources.alert, /role="alert"|aria-live/);
  assert.match(sources.alert, /\.\.\.props/);
});

test("Skeleton no impone layout y respeta reduced motion", () => {
  assert.match(sources.skeleton, /bg-skeleton-base/);
  assert.match(sources.skeleton, /motion-reduce:animate-none/);
  assert.match(sources.skeleton, /"aria-hidden": "true"/);
  assert.doesNotMatch(sources.skeleton, /w-|h-|rounded-/);
});

test("primitives consumen semantica sin tema manual ni colores fisicos", () => {
  assert.doesNotMatch(combined, /#[\da-f]{3,8}|\brgb\(|\brgba\(/i);
  assert.doesNotMatch(
    combined,
    /(?:bg|text|border)-(?:gray|white|black|red|green|orange|amber|yellow|purple)-?\d*/
  );
  assert.doesNotMatch(combined, /resolvedTheme|data-theme|dark:|matchMedia|localStorage/);
});

test("ModalSurface no duplica el ownership vigente de ActiveLayer", async () => {
  const activeLayer = await readFile(
    new URL("../src/core/components/ActiveLayer.jsx", import.meta.url),
    "utf8"
  );

  assert.doesNotMatch(primitivesIndex, /Modal/);
  assert.match(activeLayer, /createPortal/);
  assert.match(activeLayer, /role="dialog"/);
  assert.match(activeLayer, /lockBodyScroll/);
});

test("API publica expone solo primitives aprobadas y oculta helpers internos", () => {
  for (const publicName of [
    "Alert",
    "Button",
    "FormControl",
    "Input",
    "Select",
    "Textarea",
    "Skeleton",
    "Surface",
  ]) {
    assert.match(primitivesIndex, new RegExp(`\\b${publicName}\\b`));
  }

  assert.doesNotMatch(primitivesIndex, /classNames|VARIANT_CLASSES/);
  assert.match(sharedIndex, /export \* from "@shared\/components\/primitives"/);
});

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const [interactionButton, publicationCard, socialIcons, button, themeTokens] = await Promise.all([
  readFile(
    new URL("../src/shared/components/InteraccionButton.jsx", import.meta.url),
    "utf8"
  ),
  readFile(
    new URL("../src/features/posts/components/PublicacionCard.jsx", import.meta.url),
    "utf8"
  ),
  readFile(
    new URL("../src/shared/constants/socialIcons.js", import.meta.url),
    "utf8"
  ),
  readFile(
    new URL("../src/shared/components/primitives/Button.jsx", import.meta.url),
    "utf8"
  ),
  readFile(new URL("../public/theme-tokens.css", import.meta.url), "utf8"),
]);

test("activos y métricas consumen los mismos símbolos compartidos", () => {
  assert.match(socialIcons, /like: "❤️"/);
  assert.match(socialIcons, /guardado: "⭐"/);
  assert.match(interactionButton, /activeIcon: SOCIAL_ICONS\.like/);
  assert.match(interactionButton, /activeIcon: SOCIAL_ICONS\.guardado/);
  assert.match(publicationCard, /icon=\{SOCIAL_ICONS\.like\}/);
  assert.match(publicationCard, /icon=\{SOCIAL_ICONS\.guardado\}/);
  assert.doesNotMatch(`${interactionButton}\n${publicationCard}`, /"❤️"|"⭐"/);
});

test("inactivos usan Lucide outline y activos no construyen otro SVG", () => {
  assert.match(interactionButton, /Icon: Heart/);
  assert.match(interactionButton, /Icon: Star/);
  assert.match(
    interactionButton,
    /active \? \([\s\S]*\{cfg\.activeIcon\}[\s\S]*\) : \([\s\S]*<Icon/
  );
  assert.match(interactionButton, /<Icon[\s\S]*fill-none stroke-current/);
  assert.doesNotMatch(interactionButton, /fill-current|activeColor/);
});

test("labels e iconos inactivos usan texto principal adaptativo", () => {
  assert.match(
    interactionButton,
    /<span className="text-primary">\{label\}<\/span>/
  );
  assert.match(interactionButton, /fill-none stroke-current[\s\S]*text-primary/);
  assert.doesNotMatch(interactionButton, /text-interactive-on-primary/);
  assert.match(themeTokens, /:root,[\s\S]*--fg-color-text-primary: #f9fafb;/);
  assert.match(themeTokens, /html\[data-theme="light"\][\s\S]*--fg-color-text-primary: #111827;/);
  assert.match(button, /bg-interactive-primary text-interactive-on-primary/);
  assert.match(interactionButton, /onClick=\{handleClick\}/);
  assert.match(interactionButton, /disabled=\{disabled\}/);
  assert.match(interactionButton, /aria-label=\{iconOnly \? accessibleLabel : undefined\}/);
  assert.match(interactionButton, /aria-hidden="true"/);
  assert.match(interactionButton, /interactive-bubble--liquid/);
  assert.match(interactionButton, /<InteractiveLiquidLayers \/>/);
});

test("métricas conservan contenido y layout sin superficie encapsulada", () => {
  const metricOwner = publicationCard.match(
    /function MetricBadge[\s\S]*?^}/m
  )?.[0];

  assert.ok(metricOwner);
  assert.match(metricOwner, /inline-flex items-center px-3 py-1 text-xs text-primary/);
  assert.match(metricOwner, /aria-hidden="true">\{icon\}/);
  assert.match(metricOwner, /\{label\}/);
  assert.match(metricOwner, /\{value \?\? 0\}/);
  assert.doesNotMatch(
    metricOwner,
    /border|bg-|shadow|rounded|interactive-bubble|InteractiveLiquidLayers/
  );

  assert.match(
    publicationCard,
    /<footer className="mt-4 flex flex-wrap items-center gap-2">[\s\S]*label="Likes"[\s\S]*label="Guardados"[\s\S]*label="Interacciones"/
  );
});

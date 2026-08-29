import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const [card, detail, profile] = await Promise.all([
  readFile(new URL("../src/features/posts/components/PublicacionCard.jsx", import.meta.url), "utf8"),
  readFile(new URL("../src/features/posts/pages/PublicacionDetallePage.jsx", import.meta.url), "utf8"),
  readFile(new URL("../src/features/spaces/pages/PerfilComercioPage.jsx", import.meta.url), "utf8"),
]);

test("cinco enlaces navegables reciben exactamente una capa Liquid", () => {
  assert.equal((card.match(/interactive-bubble--liquid/g) || []).length, 1);
  assert.equal((card.match(/<InteractiveLiquidLayers \/>/g) || []).length, 1);
  assert.equal((detail.match(/interactive-bubble--liquid/g) || []).length, 1);
  assert.equal((detail.match(/<InteractiveLiquidLayers \/>/g) || []).length, 1);
  assert.equal((profile.match(/interactive-bubble--liquid/g) || []).length, 3);
  assert.equal((profile.match(/<InteractiveLiquidLayers \/>/g) || []).length, 3);
});

test("links internos conservan nodos, destinos, textos y clases", () => {
  assert.match(card, /comercioId \? \([\s\S]*<Link[\s\S]*to=\{`\/comercios\/\$\{comercioId\}`\}[\s\S]*interactive-bubble--secondary text-xs[\s\S]*Ver espacio/);
  assert.match(detail, /comercioId && \([\s\S]*<Link[\s\S]*to=\{`\/comercios\/\$\{comercioId\}`\}[\s\S]*interactive-bubble--secondary shrink-0 text-xs font-semibold[\s\S]*Ver perfil/);
});

test("contactos externos conservan URL, sanitización y seguridad", () => {
  assert.match(profile, /href=\{`https:\/\/wa\.me\/\$\{String\(comercio\.whatsapp\)\.replace\(\/\\D\/g, ""\)\}\?text=Hola%2C%20te%20encontré%20en%20FeedGo%20y%20quiero%20consultarte`\}/);
  assert.match(profile, /href=\{`https:\/\/instagram\.com\/\$\{String\(comercio\.instagram\)\.replace\("@", ""\)\}`\}/);
  assert.match(profile, /`https:\/\/www\.google\.com\/maps\?q=\$\{comercio\.latitud\},\$\{comercio\.longitud\}`[\s\S]*: comercio\.maps_url/);
  assert.equal((profile.match(/target="_blank"/g) || []).length, 3);
  assert.equal((profile.match(/rel="noreferrer"/g) || []).length, 3);
  for (const text of ["WhatsApp", "Instagram", "Cómo llegar"]) assert.match(profile, new RegExp(text));
  assert.match(profile, /MessageCircle size=\{14\} aria-hidden="true"/);
  assert.match(profile, /Camera size=\{14\} aria-hidden="true"/);
  assert.match(profile, /MapPin size=\{14\} aria-hidden="true"/);
});

test("Button, InteraccionButton, métricas y enlaces textuales no duplican capas", () => {
  for (const source of [card, detail, profile]) {
    for (const block of source.match(/<(?:Button|InteraccionButton)\b[\s\S]*?(?:\/>|<\/(?:Button|InteraccionButton)>)/g) || []) {
      assert.doesNotMatch(block, /InteractiveLiquidLayers|interactive-bubble--liquid/);
    }
  }
  const metricOwner = card.match(/function MetricBadge[\s\S]*?^}/m)?.[0] || "";
  assert.match(metricOwner, /inline-flex items-center px-3 py-1/);
  assert.doesNotMatch(metricOwner, /interactive-bubble|InteractiveLiquidLayers/);
  assert.match(card, /className="rounded-sm text-\[11px\] text-interactive-primary underline/);
  assert.match(card, /className="rounded-sm text-primary focus-visible:outline/);
});

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const card = await readFile(
  new URL(
    "../src/features/posts/components/PublicacionCard.jsx",
    import.meta.url
  ),
  "utf8"
);

test("la variante normal muestra identidad del espacio antes del titulo", () => {
  assert.match(card, /pub\?\.comercio_portada_url/);
  assert.match(card, /src=\{pub\.comercio_portada_url\}/);
  assert.match(card, /loading="lazy"[\s\S]*className="h-full w-full object-cover"/);
  assert.match(card, /getInicialesComercio\(nombreComercio\)/);
  assert.match(card, /min-w-0 truncate text-sm font-medium text-secondary/);
  assert.match(card, /ml-auto flex min-w-0 shrink-0[\s\S]*Ver espacio/);
  assert.match(
    card,
    /<\/div>\s*<h2 className="truncate text-lg font-semibold sm:text-xl">/
  );
});

test("avatar y nombre no agregan enlaces ni reutilizan la multimedia", () => {
  const normalHeader = card.match(
    /<header className="space-y-2 p-4">[\s\S]*?<\/header>/
  )?.[0] || "";

  assert.equal((normalHeader.match(/<Link\b/g) || []).length, 2);
  assert.match(normalHeader, /to=\{`\/comercios\/\$\{comercioId\}`\}/);
  assert.match(normalHeader, /to=\{`\/publicaciones\/\$\{pub\.id\}`\}/);
  assert.doesNotMatch(normalHeader, /getMediaUrlFromAny|getMediaUrl\(pub\)/);
});

test("la variante compacta no consume la identidad nueva", () => {
  const compactBranch = card.match(
    /if \(compact\) \{[\s\S]*?\n  return \(\n    <article className=/
  )?.[0] || "";

  assert.doesNotMatch(compactBranch, /comercio_portada_url|getInicialesComercio/);
  assert.match(card, /wholeCardLinkEnabled = compactWholeCardLink && !compactActions/);
});

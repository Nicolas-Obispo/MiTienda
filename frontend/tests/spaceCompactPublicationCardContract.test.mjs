import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const [card, profile, ranking] = await Promise.all([
  readFile(new URL("../src/features/posts/components/PublicacionCard.jsx", import.meta.url), "utf8"),
  readFile(new URL("../src/features/spaces/pages/PerfilComercioPage.jsx", import.meta.url), "utf8"),
  readFile(new URL("../src/features/posts/pages/RankingPage.jsx", import.meta.url), "utf8"),
]);

test("Perfil activa un unico Link semantico para toda la card compacta", () => {
  assert.match(profile, /<PublicacionCard[\s\S]*compact[\s\S]*compactWholeCardLink/);
  assert.match(card, /wholeCardLinkEnabled = compactWholeCardLink && !compactActions/);
  assert.match(card, /<Link[\s\S]*to=\{`\/publicaciones\/\$\{pub\.id\}`\}[\s\S]*aria-label=\{`Ver publicación: \$\{accessiblePublicationName\}`\}/);
  assert.doesNotMatch(profile, /compactActions/);
});

test("el acceso redundante se omite sin alterar las metricas", () => {
  assert.match(card, /!wholeCardLinkEnabled \? \([\s\S]*Ver publicación[\s\S]*\) : null/);
  assert.match(card, /❤️ \{pub\?\.likes_count \?\? 0\}/);
  assert.match(card, /⭐ \{pub\?\.guardados_count \?\? 0\}/);
  assert.match(card, /wholeCardLinkEnabled[\s\S]*"flex items-center px-3 py-2"/);
});

test("hover y foco animan sin layout shift y respetan reduced motion", () => {
  assert.match(card, /transition-\[border-color,box-shadow\] duration-200 ease-out/);
  assert.match(card, /hover:border-border-strong hover:shadow-\[inset_0_0_0_1px_var\(--fg-color-border-strong\)\]/);
  assert.match(card, /focus-visible:outline-focus-ring focus-visible:shadow-\[inset_0_0_0_1px_var\(--fg-color-border-strong\)\]/);
  assert.match(card, /group-hover:scale-\[1\.015\] group-focus-visible:scale-\[1\.015\]/);
  assert.match(card, /motion-reduce:transform-none motion-reduce:transition-none/);
  assert.doesNotMatch(card, /compactWholeCardLink[\s\S]*translate-[xy]/);
});

test("Ranking reutiliza el Link semantico y la animacion del owner compact", () => {
  const loadingGrid = ranking.slice(
    ranking.indexOf("{/* Estado: Loading */}"),
    ranking.indexOf("{/* Estado: Error */}")
  );
  const publicationsGrid = ranking.slice(
    ranking.indexOf("{/* Estado: OK */}"),
    ranking.indexOf("</main>")
  );

  for (const grid of [loadingGrid, publicationsGrid]) {
    for (const className of ["grid-cols-3", "sm:grid-cols-3", "md:grid-cols-4", "gap-0", "[&>*]:w-full"]) {
      assert.match(grid, new RegExp(className.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
    }
    assert.doesNotMatch(grid, /grid-cols-2|md:grid-cols-3|gap-2|sm:gap-3/);
  }
  assert.equal((loadingGrid.match(/<Skeleton\b/g) || []).length, 4);
  assert.match(ranking, /<PublicacionCard[\s\S]*compact[\s\S]*compactWholeCardLink/);
  assert.match(card, /!wholeCardLinkEnabled \? \([\s\S]*Ver publicación[\s\S]*\) : null/);
  assert.match(card, /group-hover:scale-\[1\.015\] group-focus-visible:scale-\[1\.015\]/);
  assert.match(card, /motion-reduce:transform-none motion-reduce:transition-none/);
});

test("Seguir conserva estado y handler con geometria compacta", () => {
  assert.match(profile, /variant=\{siguiendoVisible \? "secondary" : "primary"\}/);
  assert.match(profile, /onClick=\{handleToggleFollow\}/);
  assert.match(profile, /className="min-h-6 rounded-xl px-\[5\.6px\] py-\[2\.8px\] text-\[8\.4px\] leading-\[11\.2px\] active:\[transform:none\]"/);
  assert.match(profile, /seguimientoDesconocido[\s\S]*"Comprobando\.\.\."[\s\S]*siguiendoVisible[\s\S]*"Siguiendo"[\s\S]*"\+Seguir"/);
});

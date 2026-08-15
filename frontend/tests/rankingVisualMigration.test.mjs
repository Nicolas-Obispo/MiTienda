import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const [ranking, rankingHook, card] = await Promise.all([
  readSource("../src/features/posts/pages/RankingPage.jsx"),
  readSource("../src/features/posts/hooks/useRankingPublicaciones.js"),
  readSource("../src/features/posts/components/PublicacionCard.jsx"),
]);

test("Ranking migra shell y estados mediante primitives semanticas", () => {
  assert.match(ranking, /bg-canvas text-primary/);
  assert.match(ranking, /text-secondary/);
  assert.match(ranking, /<Skeleton\b/);
  assert.match(ranking, /<Alert variant="danger" role="alert"/);
  assert.match(ranking, /<Surface variant="subtle"/);
});

test("Ranking reutiliza PublicacionCard sin crear una card paralela", () => {
  assert.match(ranking, /import \{ PublicacionCard \} from "@features\/posts"/);
  assert.match(ranking, /<PublicacionCard[\s\S]*rankIndex=\{idx\}/);
  assert.match(ranking, /headerRightBadgeText="Ranking"/);
  assert.match(ranking, /compact/);
  assert.match(card, /<InteraccionButton/);
  assert.doesNotMatch(ranking, /<InteraccionButton/);
});

test("Ranking no introduce colores fisicos ni logica manual de tema", () => {
  assert.doesNotMatch(ranking, /#[\da-f]{3,8}|\brgb\(|\brgba\(/i);
  assert.doesNotMatch(ranking, /(?:bg|text|border|ring|from|via|to)-(?:gray|slate|zinc|neutral|stone|white|black|red|green|emerald|orange|amber|yellow|blue|purple|pink)(?:\/|-\d|\b)/);
  assert.doesNotMatch(ranking, /resolvedTheme|data-theme|dark:|matchMedia\(|localStorage\./);
});

test("la pantalla no inventa tabs, filtros ni botones inexistentes", () => {
  assert.doesNotMatch(ranking, /<button\b|<Button\b/);
  assert.doesNotMatch(ranking, /role="tab"|setFiltro|setTab|setRango/);
});

test("query key, endpoint owner y Cache-First permanecen", () => {
  assert.match(rankingHook, /queryKey: queryKeys\.ranking\.publicaciones\(\)/);
  assert.match(rankingHook, /queryFn: fetchRankingPublicaciones/);
  assert.match(rankingHook, /staleTime: 1000 \* 30/);
  assert.match(ranking, /rankingItems\.length > 0 && publicaciones\.length === 0/);
  assert.match(ranking, /setPublicaciones\(rankingItems\)/);
  assert.match(ranking, /mantenerVisible: hidratoDesdeCache \|\| publicaciones\.length > 0/);
  assert.match(ranking, /isLoading && publicaciones\.length === 0/);
});

test("orden y merge del Ranking no se recalculan ni reordenan", () => {
  assert.match(ranking, /const merged = rankingItems\.map\(\(p\) =>/);
  assert.match(ranking, /feedById\.get\(p\.id\)/);
  assert.match(ranking, /guardada_by_me: guardadasSet\.has\(p\.id\)/);
  assert.match(ranking, /publicaciones\.map\(\(p, idx\) =>/);
  assert.doesNotMatch(ranking, /publicaciones\.sort|rankingItems\.sort|score\s*[+*=]/);
});

test("likes y guardados conservan locks, optimistic update y rollback", () => {
  assert.match(ranking, /isLikeLocked\(pubId\)/);
  assert.match(ranking, /isSaveLocked\(pubId\)/);
  assert.match(ranking, /optimisticToggleLike\(prev, pubId\)/);
  assert.match(ranking, /optimisticToggleGuardado\(prev, pubId\)/);
  assert.match(ranking, /toggleLikeMutation\.mutateAsync\(pubId\)/);
  assert.match(ranking, /toggleGuardadoMutation\.mutateAsync\(/);
  assert.equal((ranking.match(/setPublicaciones\(snapshot\)/g) || []).length, 2);
});

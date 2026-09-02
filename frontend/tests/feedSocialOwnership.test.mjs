import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const feed = await readFile(
  new URL("../src/features/feed/pages/FeedPage.jsx", import.meta.url),
  "utf8"
);

test("TanStack es el único owner de publicaciones renderizadas por Feed", () => {
  assert.match(feed, /data: feedData = \[\][\s\S]*useFeedPublicaciones\(\)/);
  assert.match(feed, /const publicaciones = useMemo\(\(\) => \{/);
  assert.doesNotMatch(feed, /useState\(\[\]\).*publicaciones|\[publicaciones, setPublicaciones\]/);
  assert.doesNotMatch(feed, /setPublicaciones\(/);
  assert.doesNotMatch(feed, /useEffect\([\s\S]{0,800}setPublicaciones/);
});

test("like y guardado delegan optimistic update y rollback a los hooks compartidos", () => {
  assert.match(feed, /useToggleLikePublicacionMutation\(\)/);
  assert.match(feed, /useToggleGuardadoPublicacionMutation\(\)/);
  assert.match(feed, /toggleLikeMutation\.mutateAsync\(pubId\)/);
  assert.match(feed, /toggleGuardadoMutation\.mutateAsync\(/);
  assert.doesNotMatch(feed, /optimisticToggleLike|optimisticToggleGuardado/);
});

test("derivación conserva merge por id, orden, keys y altura natural", () => {
  assert.match(feed, /feedItems\.map\(\(publicacion\) => \(\{/);
  assert.match(feed, /guardadasSet\.has\(publicacion\.id\)/);
  assert.doesNotMatch(feed, /\.sort\(/);
  assert.match(feed, /publicaciones\.map\(\(p\) => \([\s\S]*key=\{p\.id\}/);
  assert.match(feed, /pub=\{p\}/);
  assert.doesNotMatch(feed, /min-h-\[72vh\]/);
  assert.match(feed, /scroll-mt-24[\s\S]*rounded-3xl[\s\S]*overflow-hidden[\s\S]*<PublicacionCard/);
});

test("Cache First y errores conservan los estados existentes", () => {
  assert.match(feed, /const isLoading = isFeedLoading && publicaciones\.length === 0/);
  assert.match(feed, /isLoading && publicaciones\.length === 0/);
  assert.match(feed, /errorMessage && publicaciones\.length === 0/);
  assert.match(feed, /noticeMessage && publicaciones\.length > 0/);
  assert.match(feed, /role="status" aria-live="polite"/);
});

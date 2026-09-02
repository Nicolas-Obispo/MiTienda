import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const [feed, ranking, profile] = await Promise.all([
  readSource("../src/features/feed/pages/FeedPage.jsx"),
  readSource("../src/features/posts/pages/RankingPage.jsx"),
  readSource("../src/features/spaces/pages/PerfilComercioPage.jsx"),
]);

const surfaces = { feed, ranking, profile };

test("errores sociales usan avisos no bloqueantes y mensajes seguros", () => {
  for (const source of Object.values(surfaces)) {
    assert.match(source, /const \[noticeMessage, setNoticeMessage\] = useState\(""\)/);
    assert.match(source, /No se pudo actualizar Me gusta\. Intentá nuevamente\./);
    assert.match(source, /No se pudo actualizar el guardado\. Intentá nuevamente\./);
    assert.doesNotMatch(source, /setNoticeMessage\(error(?:\?\.)?\.message/);
  }
});

test("avisos con datos son accesibles, descartables y no reemplazan contenido", () => {
  for (const source of Object.values(surfaces)) {
    assert.match(source, /<Alert variant="warning" role="status" aria-live="polite"/);
    assert.match(source, /onClick=\{\(\) => setNoticeMessage\(""\)\}/);
    assert.match(source, />\s*Cerrar\s*<\/Button>/);
  }

  assert.match(feed, /\{!isLoading && publicaciones\.length > 0 && \(/);
  assert.match(ranking, /\{publicaciones\.length > 0 && \(/);
  assert.match(profile, /\{!isInitialLoading && \(!errorMessage \|\| hayDatosVisibles\) && \(/);
});

test("refetch fallido conserva datos y carga inicial conserva error bloqueante", () => {
  assert.match(feed, /if \(feedQueryError\)[\s\S]*if \(publicaciones\.length > 0\)[\s\S]*Seguís viendo la última información disponible\.[\s\S]*else \{[\s\S]*setErrorMessage/);
  assert.match(ranking, /if \(publicaciones\.length > 0\)[\s\S]*Seguís viendo la última información disponible\.[\s\S]*else \{[\s\S]*setErrorMessage/);
  assert.match(profile, /if \(comercio \|\| publicaciones\.length > 0 \|\| historias\.length > 0\)[\s\S]*Seguís viendo la última información disponible\./);

  assert.match(feed, /errorMessage && publicaciones\.length === 0/);
  assert.match(ranking, /errorMessage && publicaciones\.length === 0/);
  assert.match(profile, /errorMessage && !hayDatosVisibles/);
});

test("keys, orden, geometria y handlers exitosos permanecen", () => {
  assert.match(feed, /publicaciones\.map\(\(p\) => \([\s\S]*key=\{p\.id\}/);
  assert.match(ranking, /publicaciones\.map\(\(p, idx\) => \([\s\S]*key=\{p\.id\}/);
  assert.match(profile, /publicaciones\.map\(\(p\) => \([\s\S]*key=\{p\.id\}/);

  assert.doesNotMatch(`${feed}\n${ranking}\n${profile}`, /publicaciones\.sort\(/);
  assert.match(feed, /toggleLikeMutation\.mutateAsync\(pubId\)/);
  assert.match(feed, /toggleGuardadoMutation\.mutateAsync\(/);
  assert.match(ranking, /toggleLikeMutation\.mutateAsync\(pubId\)/);
  assert.match(profile, /toggleGuardadoMutation\.mutateAsync\(/);
  assert.doesNotMatch(feed, /min-h-\[72vh\]/);
  assert.match(feed, /scroll-mt-24[\s\S]*rounded-3xl[\s\S]*overflow-hidden[\s\S]*<PublicacionCard/);
  assert.match(ranking, /grid-cols-3[\s\S]*sm:grid-cols-3[\s\S]*md:grid-cols-4/);
  assert.match(profile, /grid grid-cols-2 gap-0 sm:grid-cols-3 \[&>\*\]:w-full/);
});

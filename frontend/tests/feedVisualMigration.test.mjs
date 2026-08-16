import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const [feed, card, publicationVideo, storiesBar, storiesViewer, interactionButton, feedHook] =
  await Promise.all([
    readSource("../src/features/feed/pages/FeedPage.jsx"),
    readSource("../src/features/posts/components/PublicacionCard.jsx"),
    readSource("../src/shared/media/PublicationVideo.jsx"),
    readSource("../src/features/stories/components/HistoriasBar.jsx"),
    readSource("../src/features/stories/components/HistoriasViewer.jsx"),
    readSource("../src/shared/components/InteraccionButton.jsx"),
    readSource("../src/features/feed/hooks/useFeedPublicaciones.js"),
  ]);

test("Feed migra canvas, estados y cards mediante primitives", () => {
  for (const primitive of ["Alert", "Button", "Skeleton", "Surface"]) {
    assert.match(feed, new RegExp(`<${primitive}\\b`));
  }
  assert.match(feed, /bg-canvas text-primary/);
  assert.match(feed, /border-border bg-surface/);
  assert.match(card, /border-border bg-surface/);
  assert.match(card, /bg-surface-subtle/);
});

test("shell de Feed no contiene tema manual ni colores fisicos", () => {
  const shell = `${feed}\n${storiesBar}\n${interactionButton}`;
  assert.doesNotMatch(shell, /#[\da-f]{3,8}|\brgb\(|\brgba\(/i);
  assert.doesNotMatch(shell, /(?:bg|text|border|ring|from|via|to)-(?:gray|slate|zinc|neutral|stone|white|black|red|green|emerald|orange|amber|yellow|blue|purple|pink)(?:\/|-\d|\b)/);
  assert.doesNotMatch(shell, /resolvedTheme|data-theme|dark:|matchMedia\(|localStorage\./);
});

test("los colores fisicos restantes de PublicacionCard pertenecen al escenario multimedia", () => {
  assert.match(card, /relative aspect-square bg-black/);
  assert.match(card, /bg-gradient-to-t from-black\/80 via-black\/35 to-transparent/);
  assert.match(card, /text-white\/90/);

  const withoutMediaOverlay = card
    .replace(/bg-black/g, "")
    .replace(/border-black\/30/g, "")
    .replace(/bg-black\/60/g, "")
    .replace(/from-black\/80/g, "")
    .replace(/via-black\/35/g, "")
    .replace(/text-white(?:\/90)?/g, "");

  assert.doesNotMatch(withoutMediaOverlay, /(?:bg|text|border|from|via|to)-(?:gray|white|black|red|green|orange|amber|yellow|purple)(?:\/|-\d|\b)/);
});

test("InteraccionButton conserva owner, callbacks y animaciones", () => {
  assert.match(card, /<InteraccionButton[\s\S]*type="like"/);
  assert.match(card, /<InteraccionButton[\s\S]*type="guardar"/);
  assert.match(interactionButton, /onClick\?\.\(e\)/);
  assert.match(interactionButton, /setTimeout\([\s\S]*300/);
  assert.match(interactionButton, /animate-like/);
  assert.match(interactionButton, /animate-save/);
  assert.match(interactionButton, /interactive-bubble--danger/);
  assert.match(interactionButton, /interactive-bubble--warning/);
  assert.match(interactionButton, /aria-label=\{iconOnly \? accessibleLabel : undefined\}/);
  assert.doesNotMatch(interactionButton, /text-red-|text-yellow-|text-gray-|border-red-|border-yellow-|border-gray-/);
});

test("HistoriasBar usa Button compartido y conserva orden y apertura", () => {
  assert.match(storiesBar, /<Button\b/);
  assert.doesNotMatch(storiesBar, /<button\b/);
  assert.doesNotMatch(storiesBar, /interactive-bubble\s/);
  assert.match(storiesBar, /return bTienePend - aTienePend/);
  assert.match(storiesBar, /onClickComercio\(item\.comercioId\)/);
  assert.match(storiesBar, /getMediaUrlFromAny/);
});

test("Cache-First y carga no bloquean datos utilizables", () => {
  assert.match(feedHook, /queryKey: queryKeys\.feed\.publicaciones\(\)/);
  assert.match(feedHook, /queryFn: fetchFeedPublicaciones/);
  assert.match(feedHook, /staleTime: 1000 \* 30/);
  assert.match(feed, /feedItems\.length > 0 && publicaciones\.length === 0/);
  assert.match(feed, /isFeedLoading && publicaciones\.length === 0 && feedItems\.length === 0/);
  assert.match(feed, /isLoading && publicaciones\.length === 0/);
});

test("Feed conserva optimistic updates, guardados y contratos de historias", () => {
  assert.match(feed, /optimisticToggleLike\(prev, pubId\)/);
  assert.match(feed, /optimisticToggleGuardado\(prev, pubId\)/);
  assert.match(feed, /toggleLikeMutation\.mutateAsync\(pubId\)/);
  assert.match(feed, /toggleGuardadoMutation\.mutateAsync\(/);
  assert.match(feed, /fetchHistoriasPorComercio\(comercioId\)/);
  assert.match(feed, /marcarHistoriaVista\(historiaId\)/);
  assert.match(feed, /refetchHistoriasBar\(\)/);
  assert.match(feed, /navigate\(`\/comercios\/\$\{comercioId\}`\)/);
  assert.match(storiesViewer, /requestAnimationFrame/);
  assert.match(storiesViewer, /toggleLikeHistoria\(historiaActual\.id\)/);
});

test("reproduccion multimedia conserva atributos y delega lifecycle visible", () => {
  assert.match(card, /getMediaUrlFromAny/);
  assert.match(card, /<PublicationVideo/);
  for (const attribute of ["muted", "loop", "playsInline", "preload={preload}"]) {
    assert.match(publicationVideo, new RegExp(attribute.replace(/[{}]/g, "\\$&")));
  }
  assert.doesNotMatch(publicationVideo, /autoPlay/);
  assert.match(feed, /requestIdleCallback/);
  assert.match(feed, /img\.decoding = "async"/);
  assert.match(feed, /img\.loading = "eager"/);
});

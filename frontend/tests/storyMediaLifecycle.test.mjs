import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  collectStoryImageUrls,
  isStoryImageUrl,
  isStoryVideoUrl,
  pauseStoryVideo,
  playStoryVideo,
} from "../src/features/stories/components/storyMediaLifecycle.js";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");
const [viewer, feed, storiesService, pwaWorker] = await Promise.all([
  readSource("../src/features/stories/components/HistoriasViewer.jsx"),
  readSource("../src/features/feed/pages/FeedPage.jsx"),
  readSource("../src/features/stories/services/historias_service.js"),
  readSource("../src/pwa/service-worker.js"),
]);

test("clasifica imagenes y videos de historias sin confundir query strings", () => {
  assert.equal(isStoryVideoUrl("/uploads/video.mov?version=1"), true);
  assert.equal(isStoryVideoUrl("/uploads/video.mp4#media"), true);
  assert.equal(isStoryImageUrl("/uploads/foto.jpg?version=1"), true);
  assert.equal(isStoryImageUrl("/uploads/video.mov"), false);
});

test("preload conserva solo imagenes y nunca entrega videos a Image", () => {
  const historias = [
    { media_url: "/uploads/a.mov" },
    { media_url: "/uploads/a.jpg" },
    { media_url: "/uploads/b.mp4" },
    { media_url: "/uploads/b.png" },
  ];
  const urls = collectStoryImageUrls(historias, (item) => item.media_url, 3);

  assert.deepEqual(urls, ["/uploads/a.jpg", "/uploads/b.png"]);
  assert.match(feed, /collectStoryImageUrls\(historias, getMediaUrlFromAny, max\)/);
});

test("play y pause operan sobre el unico video activo y toleran rechazo", async () => {
  let plays = 0;
  let pauses = 0;
  const video = {
    play() {
      plays += 1;
      return Promise.reject(new Error("autoplay blocked"));
    },
    pause() {
      pauses += 1;
    },
  };

  const started = await playStoryVideo(video, { hidden: false });
  pauseStoryVideo(video);

  assert.equal(plays, 1);
  assert.equal(pauses, 1);
  assert.equal(started, false);
  assert.equal(
    await playStoryVideo({ play: () => { throw new Error("blocked"); } }, { hidden: false }),
    false
  );
});

test("documento oculto nunca inicia reproduccion", () => {
  let plays = 0;
  playStoryVideo({ play: () => { plays += 1; } }, { hidden: true });
  assert.equal(plays, 0);
});

test("metadata inicia play sin esperar loadeddata y loadeddata no lo repite", () => {
  assert.match(viewer, /preload="metadata"/);
  assert.match(viewer, /onLoadedMetadata=\{\(event\) => \{/);
  assert.match(viewer, /onLoadedMetadata[\s\S]*playStoryVideo\(video, document\)/);
  assert.match(viewer, /onLoadedData=\{\(event\) => \{/);
  assert.match(viewer, /onLoadedData[\s\S]*setMediaLista\(true\)/);
  assert.doesNotMatch(viewer, /onLoadedData=[\s\S]{0,350}playStoryVideo/);
});

test("fallo real de play programa una unica salida segura", () => {
  assert.match(viewer, /playStoryVideo\(video, document\)\.then\(\(started\)/);
  assert.match(viewer, /if \(started\)[\s\S]*setMediaLista\(true\)/);
  assert.match(viewer, /setMediaLista\(false\)[\s\S]*programarAvancePorError\(\)/);
  assert.match(viewer, /const programarAvancePorError = useCallback/);
});

test("viewer conserva un medio activo y elimina autoplay indiscriminado", () => {
  assert.equal((viewer.match(/<video\b/g) || []).length, 1);
  assert.equal((viewer.match(/<img\b/g) || []).length, 1);
  assert.doesNotMatch(viewer, /\bautoPlay\b/);
  assert.match(viewer, /startedVideoRef\.current !== video/);
  assert.match(viewer, /onLoadedMetadata[\s\S]*video\.currentTime = 0/);
});

test("transiciones, cierre, desmontaje y background pausan explicitamente", () => {
  assert.match(viewer, /const pausarVideoActivo = useCallback/);
  assert.match(viewer, /document\.hidden[\s\S]*pauseStoryVideo\(video\)/);
  assert.match(viewer, /document\.addEventListener\("visibilitychange"/);
  assert.match(viewer, /document\.removeEventListener\("visibilitychange"/);
  assert.match(viewer, /cerrarViewer[\s\S]*pausarVideoActivo\(\)/);
  assert.match(viewer, /irSiguiente[\s\S]*pausarVideoActivo\(\)/);
  assert.match(viewer, /irAnterior[\s\S]*pausarVideoActivo\(\)/);
});

test("foreground solo reanuda el elemento activo ya iniciado", () => {
  assert.match(
    viewer,
    /video && mediaLista && startedVideoRef\.current === video[\s\S]*playStoryVideo\(video, document\)/
  );
});

test("avance queda bloqueado contra carrera entre RAF y onEnded", () => {
  assert.match(viewer, /if \(advanceLockedRef\.current\) return/);
  assert.match(viewer, /advanceLockedRef\.current = true/);
  assert.match(viewer, /onEnded=\{irSiguiente\}/);
  assert.match(viewer, /const DURACION_MS_DEFAULT = 4500/);
});

test("timeout de error tiene identidad, validacion y cleanup", () => {
  assert.match(viewer, /errorAdvanceTimeoutRef/);
  assert.match(viewer, /clearTimeout\(errorAdvanceTimeoutRef\.current\)/);
  assert.match(viewer, /runIdRef\.current === expectedRun/);
  assert.ok((viewer.match(/limpiarErrorAdvanceTimeout\(\)/g) || []).length >= 5);
});

test("backend de vistas y runtime PWA permanecen fuera del lifecycle", () => {
  assert.match(storiesService, /marcarHistoriaVista/);
  assert.doesNotMatch(viewer, /service-worker|CacheStorage|caches\./i);
  assert.match(pwaWorker, /createRequestClassifier/);
});

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  createPublicationVideoLifecycle,
  PUBLICATION_VIDEO_VISIBILITY_THRESHOLD,
} from "../src/shared/media/publicationVideoLifecycle.js";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

function createDocument() {
  const listeners = new Set();
  return {
    hidden: false,
    addEventListener(type, listener) {
      if (type === "visibilitychange") listeners.add(listener);
    },
    removeEventListener(type, listener) {
      if (type === "visibilitychange") listeners.delete(listener);
    },
    dispatchVisibility() {
      for (const listener of listeners) listener();
    },
    listenerCount() {
      return listeners.size;
    },
  };
}

function createVideo({ rejectPlay = false } = {}) {
  return {
    pauseCalls: 0,
    playCalls: 0,
    pause() { this.pauseCalls += 1; },
    play() {
      this.playCalls += 1;
      return rejectPlay ? Promise.reject(new Error("autoplay blocked")) : Promise.resolve();
    },
  };
}

function createObserverHarness() {
  const instances = [];
  class Observer {
    constructor(callback, options) {
      this.callback = callback;
      this.options = options;
      this.disconnected = false;
      instances.push(this);
    }
    observe(target) { this.target = target; }
    disconnect() { this.disconnected = true; }
    setVisibility(ratio) {
      this.callback([{ target: this.target, isIntersecting: ratio > 0, intersectionRatio: ratio }]);
    }
  }
  return { Observer, instances };
}

test("video visible reproduce, fuera del viewport pausa y al volver reanuda", () => {
  const documentObject = createDocument();
  const video = createVideo();
  const { Observer, instances } = createObserverHarness();
  const cleanup = createPublicationVideoLifecycle({ video, documentObject, IntersectionObserverClass: Observer });

  assert.equal(PUBLICATION_VIDEO_VISIBILITY_THRESHOLD, 0.6);
  assert.deepEqual(instances[0].options.threshold, [0.6]);
  instances[0].setVisibility(0.6);
  assert.equal(video.playCalls, 1);
  instances[0].setVisibility(0.59);
  assert.equal(video.pauseCalls, 1);
  instances[0].setVisibility(0.8);
  assert.equal(video.playCalls, 2);
  cleanup();
});

test("documento oculto pausa y solo reanuda si el video sigue visible", () => {
  const documentObject = createDocument();
  const video = createVideo();
  const { Observer, instances } = createObserverHarness();
  const cleanup = createPublicationVideoLifecycle({ video, documentObject, IntersectionObserverClass: Observer });

  instances[0].setVisibility(0.9);
  documentObject.hidden = true;
  documentObject.dispatchVisibility();
  assert.equal(video.pauseCalls, 1);
  instances[0].setVisibility(0.1);
  documentObject.hidden = false;
  documentObject.dispatchVisibility();
  assert.equal(video.playCalls, 1);
  cleanup();
});

test("videos de publicaciones se excluyen mutuamente", () => {
  const documentObject = createDocument();
  const first = createVideo();
  const second = createVideo();
  const firstHarness = createObserverHarness();
  const secondHarness = createObserverHarness();
  const cleanupFirst = createPublicationVideoLifecycle({ video: first, documentObject, IntersectionObserverClass: firstHarness.Observer });
  const cleanupSecond = createPublicationVideoLifecycle({ video: second, documentObject, IntersectionObserverClass: secondHarness.Observer });

  firstHarness.instances[0].setVisibility(0.9);
  secondHarness.instances[0].setVisibility(0.9);
  assert.equal(first.playCalls, 1);
  assert.equal(first.pauseCalls, 1);
  assert.equal(second.playCalls, 1);
  cleanupFirst();
  cleanupSecond();
});

test("cleanup y remount estilo StrictMode no acumulan observer ni listener", () => {
  const documentObject = createDocument();
  const video = createVideo();
  const { Observer, instances } = createObserverHarness();
  const firstCleanup = createPublicationVideoLifecycle({ video, documentObject, IntersectionObserverClass: Observer });
  firstCleanup();
  const secondCleanup = createPublicationVideoLifecycle({ video, documentObject, IntersectionObserverClass: Observer });

  assert.equal(instances[0].disconnected, true);
  assert.equal(documentObject.listenerCount(), 1);
  secondCleanup();
  assert.equal(instances[1].disconnected, true);
  assert.equal(documentObject.listenerCount(), 0);
});

test("rechazo de play se consume y fallback sin IntersectionObserver queda pausado", async () => {
  const documentObject = createDocument();
  const rejected = createVideo({ rejectPlay: true });
  const detailCleanup = createPublicationVideoLifecycle({ video: rejected, documentObject, observeViewport: false });
  await Promise.resolve();
  assert.equal(rejected.playCalls, 1);
  detailCleanup();

  const fallback = createVideo();
  const cleanup = createPublicationVideoLifecycle({ video: fallback, documentObject, IntersectionObserverClass: undefined });
  assert.equal(fallback.playCalls, 0);
  assert.equal(fallback.pauseCalls, 1);
  cleanup();
});

test("consumidores comparten PublicationVideo, imagenes e interacciones permanecen", async () => {
  const [component, card, explore, detail, stories] = await Promise.all([
    readSource("../src/shared/media/PublicationVideo.jsx"),
    readSource("../src/features/posts/components/PublicacionCard.jsx"),
    readSource("../src/features/explore/pages/ExplorarPage.jsx"),
    readSource("../src/features/posts/pages/PublicacionDetallePage.jsx"),
    readSource("../src/features/stories/components/HistoriasViewer.jsx"),
  ]);
  assert.match(component, /muted[\s\S]*loop[\s\S]*playsInline[\s\S]*controls=\{controls\}[\s\S]*preload=\{preload\}/);
  assert.match(card, /<PublicationVideo/);
  assert.match(explore, /<PublicationVideo/);
  assert.match(detail, /<PublicationVideo[\s\S]*detail/);
  assert.match(card, /<img[\s\S]*loading="lazy"/);
  assert.match(card, /<InteraccionButton[\s\S]*type="like"/);
  assert.match(card, /<InteraccionButton[\s\S]*type="guardar"/);
  assert.match(stories, /<video[\s\S]*onEnded=\{irSiguiente\}/);
  assert.doesNotMatch(stories, /\bautoPlay\b/);
  assert.match(stories, /playStoryVideo/);
  assert.doesNotMatch(stories, /PublicationVideo/);
});

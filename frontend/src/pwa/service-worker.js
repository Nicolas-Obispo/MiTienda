import { cacheNames, setCacheNameDetails } from "workbox-core";
import { matchPrecache, precache } from "workbox-precaching";
import { registerRoute } from "workbox-routing";

import { createRequestClassifier, REQUEST_HANDLING } from "./requestClassifier.js";
import { cleanupOldFeedGoPrecaches } from "./cacheCleanup.js";
import { isActivationMessage } from "./lifecycleContract.js";
import { handleActivationRequest } from "./workerLifecycle.js";

const PRECACHE_ENTRIES = self.__WB_MANIFEST;
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

setCacheNameDetails({
  prefix: "feedgo",
  precache: "precache",
  suffix: "v1",
});

const classifyRequest = createRequestClassifier({
  appOrigin: self.location.origin,
  apiBaseUrl: API_BASE_URL,
  precacheEntries: PRECACHE_ENTRIES,
});

registerRoute(
  ({ request }) => classifyRequest(request) === REQUEST_HANDLING.NAVIGATION,
  async ({ request }) => {
    try {
      return await fetch(request);
    } catch (networkError) {
      const shell = await matchPrecache("/index.html");
      if (shell) return shell;
      throw networkError;
    }
  },
);

registerRoute(
  ({ request }) => classifyRequest(request) === REQUEST_HANDLING.PRECACHE,
  async ({ request }) => (await matchPrecache(request)) || fetch(request),
);

precache(PRECACHE_ENTRIES);

self.addEventListener("message", (event) => {
  if (!isActivationMessage(event.data)) return;

  event.waitUntil(
    handleActivationRequest({
      data: event.data,
      responsePort: event.ports[0],
      clientsObject: self.clients,
      skipWaiting: () => self.skipWaiting(),
    }),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    cleanupOldFeedGoPrecaches({
      cacheStorage: caches,
      currentPrecacheName: cacheNames.precache,
    }),
  );
});

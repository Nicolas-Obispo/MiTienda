import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

import { createApiNetworkHandler } from "../src/pwa/apiNetworkHandler.js";
import {
  CONNECTIVITY_STATE,
  createConnectivityRuntime,
} from "../src/pwa/connectivityRuntime.js";
import { PWA_MESSAGE } from "../src/pwa/lifecycleContract.js";
import { repairPwaInfrastructure } from "../src/pwa/repairPwaRuntime.js";
import { queryClient } from "../src/core/query/queryClient.js";

const frontendRoot = new URL("../", import.meta.url);

class FakeEventTarget {
  constructor() {
    this.listeners = new Map();
  }

  addEventListener(type, listener) {
    const listeners = this.listeners.get(type) || [];
    listeners.push(listener);
    this.listeners.set(type, listeners);
  }

  emit(type, event = {}) {
    for (const listener of this.listeners.get(type) || []) listener(event);
  }
}

function createConnectivityHarness(onLine = true) {
  const windowObject = new FakeEventTarget();
  const serviceWorker = new FakeEventTarget();
  const navigatorObject = { onLine, serviceWorker };
  const runtime = createConnectivityRuntime({ navigatorObject, windowObject });
  runtime.start();
  return { runtime, navigatorObject, windowObject, serviceWorker };
}

test("online inicial es conectividad no verificada, nunca backend saludable", () => {
  const { runtime } = createConnectivityHarness(true);
  assert.equal(runtime.getSnapshot(), CONNECTIVITY_STATE.ONLINE_UNVERIFIED);
});

test("transiciones online y offline representan solo estado tecnico", () => {
  const harness = createConnectivityHarness(true);
  harness.navigatorObject.onLine = false;
  harness.windowObject.emit("offline");
  assert.equal(harness.runtime.getSnapshot(), CONNECTIVITY_STATE.OFFLINE);

  harness.navigatorObject.onLine = true;
  harness.windowObject.emit("online");
  assert.equal(harness.runtime.getSnapshot(), CONNECTIVITY_STATE.ONLINE_UNVERIFIED);
});

test("fallo de transporte se distingue de browser offline", () => {
  const harness = createConnectivityHarness(true);
  harness.serviceWorker.emit("message", {
    data: { type: PWA_MESSAGE.BACKEND_UNREACHABLE },
  });
  assert.equal(harness.runtime.getSnapshot(), CONNECTIVITY_STATE.BACKEND_UNREACHABLE);

  harness.navigatorObject.onLine = false;
  harness.serviceWorker.emit("message", {
    data: { type: PWA_MESSAGE.BACKEND_UNREACHABLE },
  });
  assert.equal(harness.runtime.getSnapshot(), CONNECTIVITY_STATE.OFFLINE);
});

test("401, 403, 404 y 5xx son respuestas backend, no offline", async () => {
  for (const status of [401, 403, 404, 500, 503]) {
    const notifications = [];
    const response = { ok: false, status };
    const handler = createApiNetworkHandler({
      fetchFunction: async () => response,
      notifyClients: async (message) => notifications.push(message),
    });

    assert.equal(await handler({ request: { method: "GET" } }), response);
    assert.deepEqual(notifications, [{ type: PWA_MESSAGE.BACKEND_REACHABLE }]);
  }
});

test("fallo al notificar conectividad no altera respuesta ni error original", async () => {
  const response = { ok: true, status: 200 };
  const successfulHandler = createApiNetworkHandler({
    fetchFunction: async () => response,
    notifyClients: async () => { throw new Error("client disappeared"); },
  });
  assert.equal(await successfulHandler({ request: { method: "GET" } }), response);

  const transportError = new TypeError("Failed to fetch");
  const failingHandler = createApiNetworkHandler({
    fetchFunction: async () => { throw transportError; },
    notifyClients: async () => { throw new Error("client disappeared"); },
  });
  await assert.rejects(
    failingHandler({ request: { method: "GET" } }),
    (error) => error === transportError,
  );
});

test("fallo de transporte en mutaciones se propaga sin exito ni cola", async () => {
  for (const method of ["POST", "PUT", "PATCH", "DELETE"]) {
    const transportError = new TypeError("Failed to fetch");
    const notifications = [];
    const handler = createApiNetworkHandler({
      fetchFunction: async () => { throw transportError; },
      notifyClients: async (message) => notifications.push(message),
    });

    await assert.rejects(handler({ request: { method } }), transportError);
    assert.deepEqual(notifications, [{ type: PWA_MESSAGE.BACKEND_UNREACHABLE }]);
  }
});

test("respuesta real posterior elimina indisponibilidad sin reload", () => {
  const harness = createConnectivityHarness(true);
  harness.serviceWorker.emit("message", {
    data: { type: PWA_MESSAGE.BACKEND_UNREACHABLE },
  });
  harness.serviceWorker.emit("message", {
    data: { type: PWA_MESSAGE.BACKEND_REACHABLE },
  });
  assert.equal(harness.runtime.getSnapshot(), CONNECTIVITY_STATE.BACKEND_REACHABLE);
});

test("cambio de conectividad no elimina contenido TanStack existente", () => {
  const queryKey = ["pwa-connectivity-contract"];
  const cachedData = { source: "existing-session-cache" };
  queryClient.setQueryData(queryKey, cachedData);

  const harness = createConnectivityHarness(true);
  harness.navigatorObject.onLine = false;
  harness.windowObject.emit("offline");
  harness.navigatorObject.onLine = true;
  harness.windowObject.emit("online");

  assert.equal(queryClient.getQueryData(queryKey), cachedData);
  queryClient.removeQueries({ queryKey, exact: true });
});

test("reparacion solo elimina worker y precaches FeedGo", async () => {
  const unregistered = [];
  const deleted = [];
  const functionalStorage = new Map([
    ["access_token", "untouched-token"],
    ["feedgo:theme-preference", "dark"],
  ]);
  const registration = (scriptURL, name) => ({
    active: { scriptURL },
    waiting: null,
    installing: null,
    unregister: async () => { unregistered.push(name); return true; },
  });

  const result = await repairPwaInfrastructure({
    serviceWorkerContainer: {
      getRegistrations: async () => [
        registration("https://feedgo.example/service-worker.js", "feedgo"),
        registration("https://feedgo.example/other-worker.js", "other"),
      ],
    },
    cacheStorage: {
      keys: async () => [
        "feedgo-precache-v0",
        "feedgo-precache-v1",
        "feedgo-runtime-v1",
        "other-app-cache",
      ],
      delete: async (cacheName) => { deleted.push(cacheName); return true; },
    },
    appOrigin: "https://feedgo.example",
  });

  assert.deepEqual(unregistered, ["feedgo"]);
  assert.deepEqual(deleted, ["feedgo-precache-v0", "feedgo-precache-v1"]);
  assert.deepEqual(result, {
    unregistered: ["/service-worker.js"],
    deletedCaches: ["feedgo-precache-v0", "feedgo-precache-v1"],
  });
  assert.equal(functionalStorage.get("access_token"), "untouched-token");
  assert.equal(functionalStorage.get("feedgo:theme-preference"), "dark");
});

test("PWA no importa negocio, Auth ni QueryClient y no implementa sync", async () => {
  const files = [
    "apiNetworkHandler.js",
    "cacheCleanup.js",
    "connectivityRuntime.js",
    "lifecycleContract.js",
    "precacheContract.js",
    "registerServiceWorker.js",
    "repairPwaRuntime.js",
    "requestClassifier.js",
    "service-worker.js",
    "useConnectivityState.js",
    "workerLifecycle.js",
  ];
  const sources = await Promise.all(files.map((file) =>
    readFile(new URL(`src/pwa/${file}`, frontendRoot), "utf8")));
  const source = sources.join("\n");

  assert.doesNotMatch(source, /@features|features\/|@services|services\/|AuthContext|QueryClient|useQuery/i);
  assert.doesNotMatch(source, /Background\s*Sync|SyncManager|indexedDB|persistQueryClient/i);
  assert.doesNotMatch(source, /access_token|Bearer|JWT|usuario|permissions?|premium/i);
});

test("señal global es discreta y no altera Auth ni navegación", async () => {
  const [notice, layout] = await Promise.all([
    readFile(new URL("src/shared/components/ConnectivityNotice.jsx", frontendRoot), "utf8"),
    readFile(new URL("src/shared/layouts/MainLayout.jsx", frontendRoot), "utf8"),
  ]);

  assert.match(notice, /role="status"/);
  assert.match(notice, /datos y acciones que requieren servidor/);
  assert.doesNotMatch(notice, /useAuth|token|sesión válida|login/i);
  assert.match(layout, /<ConnectivityNotice \/>/);
  assert.doesNotMatch(notice, /reload\(|refetch|invalidateQueries/);
});

test("worker conserva firewall, lifecycle y passthrough sin runtime cache", async () => {
  const worker = await readFile(new URL("src/pwa/service-worker.js", frontendRoot), "utf8");

  for (const method of ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"]) {
    assert.match(worker, new RegExp(`"${method}"`));
  }
  assert.match(worker, /createApiNetworkHandler/);
  assert.doesNotMatch(worker, /clients\.claim|BackgroundSync|registerSync|caches\.open/);
  assert.equal((worker.match(/self\.skipWaiting\(\)/g) || []).length, 1);
});

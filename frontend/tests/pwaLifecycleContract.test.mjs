import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

import {
  cleanupOldFeedGoPrecaches,
  FEEDGO_PRECACHE_PREFIX,
} from "../src/pwa/cacheCleanup.js";
import {
  PWA_MESSAGE,
  PWA_RELOAD_GUARD_KEY,
  PWA_RUNTIME_STATE,
} from "../src/pwa/lifecycleContract.js";
import { createServiceWorkerRuntime } from "../src/pwa/registerServiceWorker.js";
import { handleActivationRequest } from "../src/pwa/workerLifecycle.js";

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

  emit(type) {
    for (const listener of this.listeners.get(type) || []) listener();
  }
}

class FakeMessageChannel {
  constructor() {
    this.port1 = { onmessage: null };
    this.port2 = {
      postMessage: (data) => this.port1.onmessage?.({ data }),
    };
  }
}

function createStorage() {
  const values = new Map();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
  };
}

function createHarness({
  registration,
  registerError,
  supported = true,
  cacheStorageObject,
} = {}) {
  const serviceWorker = new FakeEventTarget();
  const registerCalls = [];
  serviceWorker.controller = registration?.controller ?? {};
  serviceWorker.register = async (url) => {
    registerCalls.push(url);
    if (registerError) throw registerError;
    return registration;
  };

  const windowObject = new FakeEventTarget();
  let reloads = 0;
  windowObject.location = {
    origin: "https://feedgo.example",
    reload: () => reloads += 1,
  };
  const loggerErrors = [];

  const runtime = createServiceWorkerRuntime({
    navigatorObject: supported ? { serviceWorker } : {},
    windowObject,
    documentObject: { readyState: "complete" },
    sessionStorageObject: createStorage(),
    MessageChannelConstructor: FakeMessageChannel,
    cacheStorageObject,
    activationIdFactory: () => "build-test-1",
    logger: { error: (...args) => loggerErrors.push(args) },
  });

  return {
    runtime,
    serviceWorker,
    registerCalls,
    loggerErrors,
    getReloads: () => reloads,
  };
}

const flush = () => new Promise((resolve) => setImmediate(resolve));

function createRegistration(overrides = {}) {
  return Object.assign(new FakeEventTarget(), {
    waiting: null,
    installing: null,
    active: null,
    ...overrides,
  });
}

test("registro tiene owner y URL unicos y browser sin soporte queda controlado", async () => {
  const unsupported = createHarness({ supported: false });
  unsupported.runtime.start();
  assert.equal(unsupported.runtime.getState(), PWA_RUNTIME_STATE.UNSUPPORTED);

  const registration = createRegistration({ active: {} });
  const supported = createHarness({ registration });
  supported.runtime.start();
  supported.runtime.start();
  await flush();

  assert.deepEqual(supported.registerCalls, ["/service-worker.js"]);
  assert.equal(supported.runtime.getState(), PWA_RUNTIME_STATE.ACTIVE);

  const [main, owner] = await Promise.all([
    readFile(new URL("src/main.jsx", frontendRoot), "utf8"),
    readFile(new URL("src/pwa/registerServiceWorker.js", frontendRoot), "utf8"),
  ]);
  assert.match(main, /registerServiceWorker\(\)/);
  assert.doesNotMatch(main, /serviceWorker\.register/);
  assert.equal((owner.match(/\.register\(PWA_SERVICE_WORKER_URL\)/g) || []).length, 1);
  assert.match(owner, /export function repairServiceWorker\(\)/);
});

test("fallo de registro publica error tecnico sin propagar datos", async () => {
  const failure = new Error("registration failed");
  const harness = createHarness({ registerError: failure });
  harness.runtime.start();
  await flush();

  assert.equal(harness.runtime.getState(), PWA_RUNTIME_STATE.ERROR);
  assert.deepEqual(harness.loggerErrors, [["Error SW:", failure]]);
});

test("waiting existente y updatefound se detectan sin activacion automatica", async () => {
  const waiting = { postMessage: () => assert.fail("no debe activarse solo") };
  const registration = createRegistration({ waiting });
  const harness = createHarness({ registration });
  harness.runtime.start();
  await flush();
  assert.equal(harness.runtime.getState(), PWA_RUNTIME_STATE.UPDATE_AVAILABLE);

  registration.waiting = null;
  const installing = new FakeEventTarget();
  installing.state = "installing";
  registration.installing = installing;
  registration.emit("updatefound");
  assert.equal(harness.runtime.getState(), PWA_RUNTIME_STATE.INSTALLING);

  registration.waiting = waiting;
  installing.state = "installed";
  installing.emit("statechange");
  assert.equal(harness.runtime.getState(), PWA_RUNTIME_STATE.UPDATE_AVAILABLE);
});

test("worker ya instalado se representa sin quedar atrapado en installing", async () => {
  const installing = new FakeEventTarget();
  installing.state = "installed";
  const registration = createRegistration({ installing });
  const harness = createHarness({ registration });
  harness.runtime.start();
  await flush();

  assert.equal(harness.runtime.getState(), PWA_RUNTIME_STATE.UPDATE_AVAILABLE);
});

test("checkForUpdate usa y refresca la registration del owner", async () => {
  let updateCalls = 0;
  const registration = createRegistration({
    active: {},
    update: async () => { updateCalls += 1; },
  });
  const harness = createHarness({ registration });
  harness.serviceWorker.getRegistration = async () => registration;
  harness.runtime.start();
  await flush();

  assert.equal(await harness.runtime.checkForUpdate(), true);
  assert.equal(updateCalls, 1);
});

test("una pestaña permite activacion explicita y recarga como maximo una vez", async () => {
  let sentMessage;
  const waiting = {
    postMessage(message, [responsePort]) {
      sentMessage = message;
      responsePort.postMessage({
        type: PWA_MESSAGE.ACTIVATION_ACCEPTED,
        activationId: message.activationId,
      });
    },
  };
  const harness = createHarness({ registration: createRegistration({ waiting }) });
  harness.runtime.start();
  await flush();

  assert.equal(await harness.runtime.requestActivation(), true);
  assert.equal(await harness.runtime.requestActivation(), false);
  assert.deepEqual(Object.keys(sentMessage).sort(), ["activationId", "type"]);
  assert.equal(sentMessage.type, PWA_MESSAGE.ACTIVATE_VERSION);
  assert.equal(harness.runtime.getState(), PWA_RUNTIME_STATE.ACTIVATING);

  harness.serviceWorker.emit("controllerchange");
  harness.serviceWorker.emit("controllerchange");
  assert.equal(harness.getReloads(), 1);
});

test("varias pestañas bloquean activacion inmediata", async () => {
  let skipWaitingCalls = 0;
  const responses = [];
  const activated = await handleActivationRequest({
    data: { type: PWA_MESSAGE.ACTIVATE_VERSION, activationId: "build-2" },
    responsePort: { postMessage: (message) => responses.push(message) },
    clientsObject: { matchAll: async () => [{ id: "a" }, { id: "b" }] },
    skipWaiting: async () => skipWaitingCalls += 1,
  });

  assert.equal(activated, false);
  assert.equal(skipWaitingCalls, 0);
  assert.deepEqual(responses, [{
    type: PWA_MESSAGE.ACTIVATION_BLOCKED_MULTITAB,
    activationId: "build-2",
  }]);
});

test("pagina conserva update disponible cuando worker informa multitab", async () => {
  const waiting = {
    postMessage(message, [responsePort]) {
      responsePort.postMessage({
        type: PWA_MESSAGE.ACTIVATION_BLOCKED_MULTITAB,
        activationId: message.activationId,
      });
    },
  };
  const harness = createHarness({ registration: createRegistration({ waiting }) });
  harness.runtime.start();
  await flush();

  assert.equal(await harness.runtime.requestActivation(), false);
  assert.equal(harness.runtime.getState(), PWA_RUNTIME_STATE.UPDATE_AVAILABLE);
  harness.serviceWorker.emit("controllerchange");
  assert.equal(harness.getReloads(), 0);
});

test("pagina representa fallo tecnico de activacion como error", async () => {
  const waiting = {
    postMessage(message, [responsePort]) {
      responsePort.postMessage({
        type: PWA_MESSAGE.ACTIVATION_FAILED,
        activationId: message.activationId,
      });
    },
  };
  const harness = createHarness({ registration: createRegistration({ waiting }) });
  harness.runtime.start();
  await flush();

  assert.equal(await harness.runtime.requestActivation(), false);
  assert.equal(harness.runtime.getState(), PWA_RUNTIME_STATE.ERROR);
});

test("un unico cliente activa solo por mensaje explicito", async () => {
  let skipWaitingCalls = 0;
  const responses = [];
  const clientsObject = { matchAll: async () => [{ id: "only" }] };

  assert.equal(await handleActivationRequest({
    data: { type: "UNKNOWN", token: "secret" },
    responsePort: { postMessage: (message) => responses.push(message) },
    clientsObject,
    skipWaiting: async () => skipWaitingCalls += 1,
  }), false);

  assert.equal(await handleActivationRequest({
    data: { type: PWA_MESSAGE.ACTIVATE_VERSION, activationId: "build-3" },
    responsePort: { postMessage: (message) => responses.push(message) },
    clientsObject,
    skipWaiting: async () => skipWaitingCalls += 1,
  }), true);

  assert.equal(skipWaitingCalls, 1);
  assert.deepEqual(responses, [{
    type: PWA_MESSAGE.ACTIVATION_ACCEPTED,
    activationId: "build-3",
  }]);
});

test("fallo tecnico de skipWaiting no se presenta como activacion aceptada", async () => {
  const responses = [];
  const activated = await handleActivationRequest({
    data: { type: PWA_MESSAGE.ACTIVATE_VERSION, activationId: "build-failed" },
    responsePort: { postMessage: (message) => responses.push(message) },
    clientsObject: { matchAll: async () => [{ id: "only" }] },
    skipWaiting: async () => { throw new Error("activation failed"); },
  });

  assert.equal(activated, false);
  assert.deepEqual(responses, [{
    type: PWA_MESSAGE.ACTIVATION_FAILED,
    activationId: "build-failed",
  }]);
});

test("activacion natural queda activa en la proxima apertura sin recarga forzada", async () => {
  const harness = createHarness({
    registration: createRegistration({ active: { state: "activated" } }),
  });
  harness.runtime.start();
  await flush();

  assert.equal(harness.runtime.getState(), PWA_RUNTIME_STATE.ACTIVE);
  harness.serviceWorker.emit("controllerchange");
  assert.equal(harness.getReloads(), 0);
});

test("guard de reload y cleanup solo almacenan o borran infraestructura tecnica", async () => {
  assert.equal(PWA_RELOAD_GUARD_KEY, "feedgo:pwa:last-activated-version");
  assert.equal(FEEDGO_PRECACHE_PREFIX, "feedgo-precache-");

  const deleted = [];
  const obsolete = await cleanupOldFeedGoPrecaches({
    cacheStorage: {
      keys: async () => [
        "feedgo-precache-v0",
        "feedgo-precache-v1",
        "feedgo-runtime-v1",
        "other-app-cache",
      ],
      delete: async (name) => deleted.push(name),
    },
    currentPrecacheName: "feedgo-precache-v1",
  });

  assert.deepEqual(obsolete, ["feedgo-precache-v0"]);
  assert.deepEqual(deleted, ["feedgo-precache-v0"]);
});

test("reparacion explicita reutiliza el owner unico sin recarga automatica", async () => {
  let unregisterCalls = 0;
  const deleted = [];
  const registration = createRegistration({
    active: { scriptURL: "https://feedgo.example/service-worker.js" },
    unregister: async () => { unregisterCalls += 1; return true; },
  });
  const harness = createHarness({
    registration,
    cacheStorageObject: {
      keys: async () => ["feedgo-precache-v1", "other-cache"],
      delete: async (name) => { deleted.push(name); return true; },
    },
  });
  harness.serviceWorker.getRegistrations = async () => [registration];
  harness.runtime.start();
  await flush();

  const result = await harness.runtime.repair();

  assert.equal(unregisterCalls, 1);
  assert.deepEqual(deleted, ["feedgo-precache-v1"]);
  assert.deepEqual(harness.registerCalls, ["/service-worker.js", "/service-worker.js"]);
  assert.deepEqual(result, {
    unregistered: ["/service-worker.js"],
    deletedCaches: ["feedgo-precache-v1"],
  });
  assert.equal(harness.getReloads(), 0);
});

test("worker no contiene lifecycle automatico ni mensajes privados", async () => {
  const [worker, contract] = await Promise.all([
    readFile(new URL("src/pwa/service-worker.js", frontendRoot), "utf8"),
    readFile(new URL("src/pwa/lifecycleContract.js", frontendRoot), "utf8"),
  ]);

  assert.doesNotMatch(worker, /clients\.claim/);
  assert.doesNotMatch(worker, /addEventListener\(["']install["']/);
  assert.equal((worker.match(/self\.skipWaiting\(\)/g) || []).length, 1);
  assert.doesNotMatch(`${worker}\n${contract}`, /JWT|Bearer|usuario|sessionId|payload/i);
});

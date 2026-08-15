import {
  PWA_MESSAGE,
  PWA_RELOAD_GUARD_KEY,
  PWA_RUNTIME_STATE,
  PWA_SERVICE_WORKER_URL,
} from "./lifecycleContract.js";
import { repairPwaInfrastructure } from "./repairPwaRuntime.js";

function createActivationId() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  return `update-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function createServiceWorkerRuntime({
  navigatorObject,
  windowObject,
  documentObject,
  sessionStorageObject,
  MessageChannelConstructor,
  cacheStorageObject,
  activationIdFactory = createActivationId,
  logger = console,
}) {
  let state = PWA_RUNTIME_STATE.REGISTERED;
  let registration = null;
  let started = false;
  let explicitActivationId = null;
  const subscribers = new Set();
  const observedWorkers = new WeakSet();

  const publish = (nextState) => {
    state = nextState;
    for (const subscriber of subscribers) subscriber(state);
  };

  const observeInstallingWorker = (worker) => {
    if (!worker || observedWorkers.has(worker)) return;
    observedWorkers.add(worker);
    publish(PWA_RUNTIME_STATE.INSTALLING);

    worker.addEventListener("statechange", () => {
      if (worker.state === "installed") {
        if (registration?.waiting || navigatorObject.serviceWorker.controller) {
          publish(PWA_RUNTIME_STATE.UPDATE_AVAILABLE);
        } else {
          publish(PWA_RUNTIME_STATE.REGISTERED);
        }
      } else if (worker.state === "activated" && !explicitActivationId) {
        publish(PWA_RUNTIME_STATE.ACTIVE);
      }
    });
  };

  const observeRegistration = (nextRegistration) => {
    registration = nextRegistration;

    if (registration.waiting) {
      publish(PWA_RUNTIME_STATE.UPDATE_AVAILABLE);
    } else if (registration.active) {
      publish(PWA_RUNTIME_STATE.ACTIVE);
    } else {
      publish(PWA_RUNTIME_STATE.REGISTERED);
    }

    registration.addEventListener("updatefound", () => {
      observeInstallingWorker(registration.installing);
    });

    if (registration.installing) observeInstallingWorker(registration.installing);
  };

  const register = async () => {
    publish(PWA_RUNTIME_STATE.REGISTERING);
    try {
      observeRegistration(
        await navigatorObject.serviceWorker.register(PWA_SERVICE_WORKER_URL),
      );
    } catch (error) {
      publish(PWA_RUNTIME_STATE.ERROR);
      logger.error("Error SW:", error);
    }
  };

  const handleControllerChange = () => {
    if (!explicitActivationId) return;

    const activationId = explicitActivationId;
    explicitActivationId = null;
    publish(PWA_RUNTIME_STATE.ACTIVE);

    try {
      if (sessionStorageObject?.getItem(PWA_RELOAD_GUARD_KEY) === activationId) return;
      sessionStorageObject?.setItem(PWA_RELOAD_GUARD_KEY, activationId);
    } catch {
      // El guard en memoria ya evita una segunda recarga en esta pagina.
    }
    windowObject.location.reload();
  };

  return {
    start() {
      if (started) return;
      started = true;

      if (!navigatorObject?.serviceWorker) {
        publish(PWA_RUNTIME_STATE.UNSUPPORTED);
        return;
      }

      navigatorObject.serviceWorker.addEventListener(
        "controllerchange",
        handleControllerChange,
      );

      if (documentObject?.readyState === "complete") {
        void register();
      } else {
        windowObject.addEventListener("load", register, { once: true });
      }
    },

    getState() {
      return state;
    },

    subscribe(subscriber) {
      subscribers.add(subscriber);
      subscriber(state);
      return () => subscribers.delete(subscriber);
    },

    requestActivation() {
      const waitingWorker = registration?.waiting;
      if (
        !waitingWorker ||
        !MessageChannelConstructor ||
        explicitActivationId
      ) {
        return Promise.resolve(false);
      }

      const activationId = activationIdFactory();
      const channel = new MessageChannelConstructor();
      explicitActivationId = activationId;

      return new Promise((resolve) => {
        channel.port1.onmessage = ({ data }) => {
          if (
            data?.type === PWA_MESSAGE.ACTIVATION_ACCEPTED &&
            data.activationId === activationId
          ) {
            publish(PWA_RUNTIME_STATE.ACTIVATING);
            resolve(true);
            return;
          }

          explicitActivationId = null;
          if (data?.type === PWA_MESSAGE.ACTIVATION_BLOCKED_MULTITAB) {
            publish(PWA_RUNTIME_STATE.UPDATE_AVAILABLE);
          } else if (data?.type === PWA_MESSAGE.ACTIVATION_FAILED) {
            publish(PWA_RUNTIME_STATE.ERROR);
          }
          resolve(false);
        };

        waitingWorker.postMessage(
          { type: PWA_MESSAGE.ACTIVATE_VERSION, activationId },
          [channel.port2],
        );
      });
    },

    async repair() {
      publish(PWA_RUNTIME_STATE.REGISTERING);
      try {
        const result = await repairPwaInfrastructure({
          serviceWorkerContainer: navigatorObject.serviceWorker,
          cacheStorage: cacheStorageObject,
          appOrigin: windowObject.location.origin,
        });
        registration = null;
        await register();
        return result;
      } catch (error) {
        publish(PWA_RUNTIME_STATE.ERROR);
        logger.error("Error reparando PWA:", error);
        throw error;
      }
    },
  };
}

export const serviceWorkerRuntime = createServiceWorkerRuntime({
  navigatorObject: globalThis.navigator,
  windowObject: globalThis.window,
  documentObject: globalThis.document,
  sessionStorageObject: globalThis.sessionStorage,
  MessageChannelConstructor: globalThis.MessageChannel,
  cacheStorageObject: globalThis.caches,
});

export function registerServiceWorker() {
  serviceWorkerRuntime.start();
  return serviceWorkerRuntime;
}

export function repairServiceWorker() {
  return serviceWorkerRuntime.repair();
}

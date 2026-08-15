import { PWA_MESSAGE } from "./lifecycleContract.js";

export const CONNECTIVITY_STATE = Object.freeze({
  OFFLINE: "offline",
  ONLINE_UNVERIFIED: "online-unverified",
  BACKEND_REACHABLE: "backend-reachable",
  BACKEND_UNREACHABLE: "backend-unreachable",
});

export function createConnectivityRuntime({ navigatorObject, windowObject }) {
  let state = navigatorObject?.onLine === false
    ? CONNECTIVITY_STATE.OFFLINE
    : CONNECTIVITY_STATE.ONLINE_UNVERIFIED;
  let started = false;
  const subscribers = new Set();

  const publish = (nextState) => {
    if (state === nextState) return;
    state = nextState;
    for (const subscriber of subscribers) subscriber();
  };

  const handleOnline = () => publish(CONNECTIVITY_STATE.ONLINE_UNVERIFIED);
  const handleOffline = () => publish(CONNECTIVITY_STATE.OFFLINE);
  const handleWorkerMessage = ({ data }) => {
    if (navigatorObject?.onLine === false) {
      publish(CONNECTIVITY_STATE.OFFLINE);
      return;
    }

    if (data?.type === PWA_MESSAGE.BACKEND_REACHABLE) {
      publish(CONNECTIVITY_STATE.BACKEND_REACHABLE);
    } else if (data?.type === PWA_MESSAGE.BACKEND_UNREACHABLE) {
      publish(CONNECTIVITY_STATE.BACKEND_UNREACHABLE);
    }
  };

  return {
    start() {
      if (started) return;
      started = true;
      windowObject?.addEventListener("online", handleOnline);
      windowObject?.addEventListener("offline", handleOffline);
      navigatorObject?.serviceWorker?.addEventListener("message", handleWorkerMessage);
    },

    getSnapshot() {
      return state;
    },

    subscribe(subscriber) {
      subscribers.add(subscriber);
      return () => subscribers.delete(subscriber);
    },
  };
}

export const connectivityRuntime = createConnectivityRuntime({
  navigatorObject: globalThis.navigator,
  windowObject: globalThis.window,
});

connectivityRuntime.start();

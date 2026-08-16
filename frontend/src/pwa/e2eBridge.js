const BRIDGE_NAME = "__FEEDGO_PWA_E2E__";

export function installPwaE2eBridge(serviceWorkerRuntime, buildVersion) {
  const bridge = Object.freeze({
    buildVersion,
    checkForUpdate: () => serviceWorkerRuntime.checkForUpdate(),
    getRuntimeState: () => serviceWorkerRuntime.getState(),
    requestActivation: () => serviceWorkerRuntime.requestActivation(),
    repair: () => serviceWorkerRuntime.repair(),
  });

  Object.defineProperty(globalThis, BRIDGE_NAME, {
    configurable: false,
    enumerable: false,
    writable: false,
    value: bridge,
  });
}

export const PWA_RUNTIME_STATE = Object.freeze({
  UNSUPPORTED: "unsupported",
  REGISTERING: "registering",
  REGISTERED: "registered",
  INSTALLING: "installing",
  ACTIVE: "active",
  UPDATE_AVAILABLE: "update-available",
  ACTIVATING: "activating",
  ERROR: "error",
});

export const PWA_MESSAGE = Object.freeze({
  ACTIVATE_VERSION: "ACTIVATE_VERSION",
  ACTIVATION_ACCEPTED: "ACTIVATION_ACCEPTED",
  ACTIVATION_BLOCKED_MULTITAB: "ACTIVATION_BLOCKED_MULTITAB",
  ACTIVATION_FAILED: "ACTIVATION_FAILED",
  BACKEND_REACHABLE: "BACKEND_REACHABLE",
  BACKEND_UNREACHABLE: "BACKEND_UNREACHABLE",
});

export const PWA_RELOAD_GUARD_KEY = "feedgo:pwa:last-activated-version";
export const PWA_SERVICE_WORKER_URL = "/service-worker.js";

export function isActivationMessage(data) {
  return (
    data?.type === PWA_MESSAGE.ACTIVATE_VERSION &&
    typeof data.activationId === "string" &&
    data.activationId.length > 0
  );
}

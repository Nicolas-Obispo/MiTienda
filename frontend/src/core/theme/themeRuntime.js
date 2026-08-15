const BRIDGE_KEY = "__FEEDGO_THEME_BOOTSTRAP__";
const FALLBACK_SNAPSHOT = Object.freeze({
  preference: "system",
  resolvedTheme: "dark",
});

let didReportMissingBridge = false;

const emergencyBridge = Object.freeze({
  getSnapshot: () => FALLBACK_SNAPSHOT,
  setPreference: () => false,
  subscribe: () => () => {},
});

export function getThemeBridge(globalObject = window) {
  const bridge = globalObject?.[BRIDGE_KEY];
  if (
    bridge &&
    typeof bridge.getSnapshot === "function" &&
    typeof bridge.setPreference === "function" &&
    typeof bridge.subscribe === "function"
  ) {
    return bridge;
  }

  if (!didReportMissingBridge) {
    didReportMissingBridge = true;
    console.error("Theme bootstrap unavailable; using the safe dark fallback.");
  }
  return emergencyBridge;
}

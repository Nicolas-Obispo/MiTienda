(function bootstrapFeedGoTheme(global) {
  "use strict";

  var BRIDGE_KEY = "__FEEDGO_THEME_BOOTSTRAP__";
  var STORAGE_KEY = "feedgo.theme.preference.v1";
  var SYSTEM_QUERY = "(prefers-color-scheme: dark)";
  var VALID_PREFERENCES = ["system", "light", "dark"];

  if (global[BRIDGE_KEY]) return;

  var subscribers = new Set();
  var mediaQueryList = null;
  var removeSystemListener = null;
  var snapshot = null;

  function validatePreference(value) {
    return VALID_PREFERENCES.indexOf(value) >= 0 ? value : null;
  }

  function getStorage() {
    try {
      return global.localStorage || null;
    } catch {
      return null;
    }
  }

  function readPreference() {
    var storage = getStorage();
    if (!storage) return "system";

    try {
      return validatePreference(storage.getItem(STORAGE_KEY)) || "system";
    } catch {
      return "system";
    }
  }

  function persistPreference(preference) {
    var storage = getStorage();
    if (!storage) return false;

    try {
      storage.setItem(STORAGE_KEY, preference);
      return true;
    } catch {
      return false;
    }
  }

  function getSystemTheme() {
    if (typeof global.matchMedia !== "function") return "dark";

    try {
      return global.matchMedia(SYSTEM_QUERY).matches ? "dark" : "light";
    } catch {
      return "dark";
    }
  }

  function resolveTheme(preference) {
    if (preference === "light" || preference === "dark") return preference;
    return getSystemTheme();
  }

  function getThemeColorMeta() {
    var document = global.document;
    if (!document) return null;

    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) return meta;

    if (!document.createElement || !document.head) return null;
    meta = document.createElement("meta");
    meta.setAttribute("name", "theme-color");
    document.head.appendChild(meta);
    return meta;
  }

  function applyTheme(resolvedTheme) {
    var acceptedTheme = resolvedTheme === "light" ? "light" : "dark";
    var document = global.document;

    if (document && document.documentElement) {
      document.documentElement.setAttribute("data-theme", acceptedTheme);
      document.documentElement.style.colorScheme = acceptedTheme;
    }

    var meta = getThemeColorMeta();
    if (meta && typeof global.getComputedStyle === "function") {
      try {
        var canvas = global
          .getComputedStyle(document.documentElement)
          .getPropertyValue("--fg-color-canvas")
          .trim();
        if (canvas) meta.setAttribute("content", canvas);
      } catch {
        // El fallback estatico del meta permanece vigente.
      }
    }

    return acceptedTheme;
  }

  function notify() {
    subscribers.forEach(function notifySubscriber(listener) {
      listener();
    });
  }

  function setSnapshot(preference, resolvedTheme, shouldNotify) {
    var nextSnapshot = Object.freeze({
      preference: preference,
      resolvedTheme: applyTheme(resolvedTheme),
    });
    var changed =
      !snapshot ||
      snapshot.preference !== nextSnapshot.preference ||
      snapshot.resolvedTheme !== nextSnapshot.resolvedTheme;

    snapshot = nextSnapshot;
    if (changed && shouldNotify) notify();
    return snapshot;
  }

  function detachSystemListener() {
    if (removeSystemListener) removeSystemListener();
    removeSystemListener = null;
    mediaQueryList = null;
  }

  function handleSystemChange(event) {
    if (!snapshot || snapshot.preference !== "system") return;
    setSnapshot("system", event && event.matches ? "dark" : "light", true);
  }

  function attachSystemListener() {
    detachSystemListener();
    if (!snapshot || snapshot.preference !== "system") return;
    if (typeof global.matchMedia !== "function") return;

    try {
      mediaQueryList = global.matchMedia(SYSTEM_QUERY);
      if (typeof mediaQueryList.addEventListener === "function") {
        mediaQueryList.addEventListener("change", handleSystemChange);
        removeSystemListener = function removeModernListener() {
          mediaQueryList.removeEventListener("change", handleSystemChange);
        };
      } else if (typeof mediaQueryList.addListener === "function") {
        mediaQueryList.addListener(handleSystemChange);
        removeSystemListener = function removeLegacyListener() {
          mediaQueryList.removeListener(handleSystemChange);
        };
      }
    } catch {
      detachSystemListener();
    }
  }

  function setPreference(value) {
    var preference = validatePreference(value);
    if (!preference) return false;

    persistPreference(preference);
    setSnapshot(preference, resolveTheme(preference), true);
    attachSystemListener();
    return true;
  }

  function subscribe(listener) {
    subscribers.add(listener);
    return function unsubscribe() {
      subscribers.delete(listener);
    };
  }

  function getSnapshot() {
    return snapshot;
  }

  function dispose() {
    detachSystemListener();
    subscribers.clear();
  }

  var preference = readPreference();
  setSnapshot(preference, resolveTheme(preference), false);

  global[BRIDGE_KEY] = Object.freeze({
    getSnapshot: getSnapshot,
    setPreference: setPreference,
    subscribe: subscribe,
    dispose: dispose,
  });

  attachSystemListener();
})(window);

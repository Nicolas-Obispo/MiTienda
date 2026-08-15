import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

import { getThemeBridge } from "../src/core/theme/themeRuntime.js";

const bootstrapSource = await readFile(
  new URL("../public/theme-bootstrap.js", import.meta.url),
  "utf8"
);

function createEnvironment({
  storedPreference = null,
  systemDark = false,
  matchMediaAvailable = true,
  readThrows = false,
  writeThrows = false,
} = {}) {
  const attributes = new Map();
  const metaAttributes = new Map([["name", "theme-color"], ["content", "#030712"]]);
  const storageValues = new Map();
  if (storedPreference !== null) {
    storageValues.set("feedgo.theme.preference.v1", storedPreference);
  }

  const mediaListeners = new Set();
  const mediaQueryList = {
    matches: systemDark,
    addEventListener(type, listener) {
      if (type === "change") mediaListeners.add(listener);
    },
    removeEventListener(type, listener) {
      if (type === "change") mediaListeners.delete(listener);
    },
    dispatch(matches) {
      this.matches = matches;
      for (const listener of [...mediaListeners]) listener({ matches });
    },
  };

  const meta = {
    setAttribute(name, value) {
      metaAttributes.set(name, value);
    },
    getAttribute(name) {
      return metaAttributes.get(name) ?? null;
    },
  };

  const document = {
    documentElement: {
      style: {},
      setAttribute(name, value) {
        attributes.set(name, value);
      },
      getAttribute(name) {
        return attributes.get(name) ?? null;
      },
    },
    querySelector(selector) {
      return selector === 'meta[name="theme-color"]' ? meta : null;
    },
    createElement() {
      return meta;
    },
    head: {
      appendChild() {},
    },
  };

  const localStorage = {
    getItem(key) {
      if (readThrows) throw new Error("storage read unavailable");
      return storageValues.get(key) ?? null;
    },
    setItem(key, value) {
      if (writeThrows) throw new Error("storage write unavailable");
      storageValues.set(key, value);
    },
  };

  const window = {
    document,
    localStorage,
    getComputedStyle(element) {
      return {
        getPropertyValue(property) {
          if (property !== "--fg-color-canvas") return "";
          return element.getAttribute("data-theme") === "light"
            ? "#f8fafc"
            : "#030712";
        },
      };
    },
  };
  if (matchMediaAvailable) {
    window.matchMedia = () => mediaQueryList;
  }

  vm.runInNewContext(bootstrapSource, { window, Set, Object });

  return {
    window,
    bridge: window.__FEEDGO_THEME_BOOTSTRAP__,
    document,
    meta,
    mediaListeners,
    mediaQueryList,
    storageValues,
  };
}

function assertApplied(environment, expectedTheme, expectedColor) {
  assert.equal(
    environment.document.documentElement.getAttribute("data-theme"),
    expectedTheme
  );
  assert.equal(environment.document.documentElement.style.colorScheme, expectedTheme);
  assert.equal(environment.meta.getAttribute("content"), expectedColor);
}

test("primera carga usa system y resuelve sistema claro", () => {
  const environment = createEnvironment({ systemDark: false });
  assert.deepEqual(
    { ...environment.bridge.getSnapshot() },
    { preference: "system", resolvedTheme: "light" }
  );
  assertApplied(environment, "light", "#f8fafc");
});

test("system oscuro se aplica antes del runtime", () => {
  const environment = createEnvironment({ systemDark: true });
  assert.equal(environment.bridge.getSnapshot().resolvedTheme, "dark");
  assertApplied(environment, "dark", "#030712");
});

test("sin matchMedia el fallback es dark", () => {
  const environment = createEnvironment({ matchMediaAvailable: false });
  assert.deepEqual(
    { ...environment.bridge.getSnapshot() },
    { preference: "system", resolvedTheme: "dark" }
  );
  assertApplied(environment, "dark", "#030712");
});

test("preferencias explicitas prevalecen sobre el sistema", () => {
  const light = createEnvironment({ storedPreference: "light", systemDark: true });
  const dark = createEnvironment({ storedPreference: "dark", systemDark: false });
  assert.equal(light.bridge.getSnapshot().resolvedTheme, "light");
  assert.equal(dark.bridge.getSnapshot().resolvedTheme, "dark");
  assert.equal(light.mediaListeners.size, 0);
  assert.equal(dark.mediaListeners.size, 0);
});

test("system reacciona en vivo con un unico listener", () => {
  const environment = createEnvironment({ systemDark: false });
  assert.equal(environment.mediaListeners.size, 1);

  environment.bridge.setPreference("system");
  assert.equal(environment.mediaListeners.size, 1);

  environment.mediaQueryList.dispatch(true);
  assert.equal(environment.bridge.getSnapshot().preference, "system");
  assert.equal(environment.bridge.getSnapshot().resolvedTheme, "dark");
  assertApplied(environment, "dark", "#030712");
});

test("light y dark ignoran cambios del sistema y limpian el listener", () => {
  const environment = createEnvironment({ systemDark: false });
  environment.bridge.setPreference("light");
  assert.equal(environment.mediaListeners.size, 0);

  environment.mediaQueryList.dispatch(true);
  assert.equal(environment.bridge.getSnapshot().resolvedTheme, "light");

  environment.bridge.setPreference("dark");
  environment.mediaQueryList.dispatch(false);
  assert.equal(environment.bridge.getSnapshot().resolvedTheme, "dark");
});

test("setPreference persiste solo la preferencia", () => {
  const environment = createEnvironment();
  assert.equal(environment.bridge.setPreference("dark"), true);
  assert.equal(
    environment.storageValues.get("feedgo.theme.preference.v1"),
    "dark"
  );
  assert.equal(environment.storageValues.has("resolvedTheme"), false);
});

test("preferencia invalida se trata como ausencia y no puede establecerse", () => {
  const environment = createEnvironment({
    storedPreference: "sepia",
    systemDark: false,
  });
  assert.equal(environment.bridge.getSnapshot().preference, "system");
  assert.equal(environment.bridge.setPreference("sepia"), false);
  assert.equal(environment.bridge.getSnapshot().preference, "system");
});

test("fallos de lectura y escritura de localStorage son recuperables", () => {
  const readFailure = createEnvironment({ readThrows: true, systemDark: true });
  assert.equal(readFailure.bridge.getSnapshot().preference, "system");
  assert.equal(readFailure.bridge.getSnapshot().resolvedTheme, "dark");

  const writeFailure = createEnvironment({ writeThrows: true, systemDark: false });
  assert.equal(writeFailure.bridge.setPreference("dark"), true);
  assert.deepEqual(
    { ...writeFailure.bridge.getSnapshot() },
    { preference: "dark", resolvedTheme: "dark" }
  );
});

test("suscripcion y cleanup no filtran notificaciones", () => {
  const environment = createEnvironment();
  let notifications = 0;
  const unsubscribe = environment.bridge.subscribe(() => {
    notifications += 1;
  });

  environment.bridge.setPreference("dark");
  assert.equal(notifications, 1);
  unsubscribe();
  environment.bridge.setPreference("light");
  assert.equal(notifications, 1);

  environment.bridge.dispose();
  assert.equal(environment.mediaListeners.size, 0);
});

test("runtime adopta exactamente el bridge creado por bootstrap", () => {
  const environment = createEnvironment({ storedPreference: "dark" });
  assert.equal(getThemeBridge(environment.window), environment.bridge);
});

test("bootstrap conserva una unica instancia canonica", () => {
  const environment = createEnvironment({ storedPreference: "dark" });
  const firstBridge = environment.bridge;
  vm.runInNewContext(bootstrapSource, {
    window: environment.window,
    Set,
    Object,
  });

  assert.equal(environment.window.__FEEDGO_THEME_BOOTSTRAP__, firstBridge);
  assert.equal(environment.mediaListeners.size, 0);
});

test("bootstrap carga en head antes del entrypoint React", async () => {
  const html = await readFile(new URL("../index.html", import.meta.url), "utf8");
  const bootstrapStylesIndex = html.indexOf(
    '<link rel="stylesheet" href="/theme-bootstrap.css" />'
  );
  const tokenStylesIndex = html.indexOf(
    '<link rel="stylesheet" href="/theme-tokens.css" />'
  );
  const bootstrapIndex = html.indexOf('<script src="/theme-bootstrap.js"></script>');
  const reactIndex = html.indexOf('<script type="module" src="/src/main.jsx"></script>');
  const headCloseIndex = html.indexOf("</head>");

  assert.ok(tokenStylesIndex > 0);
  assert.ok(tokenStylesIndex < bootstrapStylesIndex);
  assert.ok(bootstrapStylesIndex > 0);
  assert.ok(bootstrapStylesIndex < bootstrapIndex);
  assert.ok(bootstrapIndex > 0);
  assert.ok(bootstrapIndex < headCloseIndex);
  assert.ok(bootstrapIndex < reactIndex);
  assert.doesNotMatch(
    html.slice(bootstrapIndex, bootstrapIndex + 80),
    /async|defer|type="module"/
  );
  assert.doesNotMatch(html, /<style[\s>]/i);
});

test("assets anti-flash son locales y no dependen de backend", async () => {
  const stylesheet = await readFile(
    new URL("../public/theme-bootstrap.css", import.meta.url),
    "utf8"
  );

  assert.match(stylesheet, /html[\s\S]*body[\s\S]*#root/);
  assert.match(stylesheet, /var\(--fg-color-canvas\)/);
  assert.doesNotMatch(stylesheet, /#[\da-f]{3,8}/i);
  assert.doesNotMatch(bootstrapSource, /fetch\(|XMLHttpRequest|axios|https?:\/\//i);
  assert.doesNotMatch(bootstrapSource, /dark\s*:\s*\{|light\s*:\s*\{/);
  assert.match(bootstrapSource, /--fg-color-canvas/);
});

test("API publica React queda limitada al contrato aprobado", async () => {
  const provider = await readFile(
    new URL("../src/core/theme/ThemeProvider.jsx", import.meta.url),
    "utf8"
  );
  const publicIndex = await readFile(
    new URL("../src/core/theme/index.js", import.meta.url),
    "utf8"
  );

  assert.match(provider, /preference:/);
  assert.match(provider, /resolvedTheme:/);
  assert.match(provider, /setPreference/);
  assert.doesNotMatch(publicIndex, /themeRuntime|ThemeContextCore/);
  assert.doesNotMatch(provider, /localStorage|matchMedia|querySelector|documentElement/);
});

test("features y paginas no consumen bridge ni manipulan estado global de tema", async () => {
  const featuresRoot = new URL("../src/features/", import.meta.url);
  const paths = await readdir(featuresRoot, { recursive: true });
  const sourceFiles = paths.filter((path) => /\.(js|jsx)$/.test(path));
  const combined = (
    await Promise.all(
      sourceFiles.map((path) => readFile(new URL(path, featuresRoot), "utf8"))
    )
  ).join("\n");

  assert.doesNotMatch(
    combined,
    /__FEEDGO_THEME_BOOTSTRAP__|feedgo\.theme\.preference|data-theme|theme-color|matchMedia/
  );
});

test("cambio de tema no toca foco, overlays ni reduced motion", async () => {
  const globalCss = await readFile(new URL("../src/index.css", import.meta.url), "utf8");
  assert.match(globalCss, /prefers-reduced-motion/);
  assert.doesNotMatch(bootstrapSource, /activeElement|focus\(|blur\(|aria-modal/);
  assert.doesNotMatch(bootstrapSource, /prefers-reduced-motion/);
  assert.doesNotMatch(bootstrapSource, /body\.style|overflow\s*=|position\s*=/);
});

test("main monta un unico ThemeProvider", async () => {
  const main = await readFile(new URL("../src/main.jsx", import.meta.url), "utf8");
  assert.equal((main.match(/<ThemeProvider>/g) || []).length, 1);
  assert.equal((main.match(/<\/ThemeProvider>/g) || []).length, 1);
});

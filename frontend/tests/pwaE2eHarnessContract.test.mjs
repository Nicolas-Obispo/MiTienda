import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const frontendRoot = new URL("../", import.meta.url);

test("harness E2E queda condicionado al modo pwa-e2e", async () => {
  const [main, viteConfig, bridge] = await Promise.all([
    readFile(new URL("src/main.jsx", frontendRoot), "utf8"),
    readFile(new URL("vite.config.js", frontendRoot), "utf8"),
    readFile(new URL("src/pwa/e2eBridge.js", frontendRoot), "utf8"),
  ]);

  assert.match(viteConfig, /mode === 'pwa-e2e'/);
  assert.match(main, /if \(__FEEDGO_PWA_E2E__\)/);
  assert.match(main, /import\("\.\/pwa\/e2eBridge"\)/);
  assert.match(bridge, /serviceWorkerRuntime\.requestActivation\(\)/);
  assert.match(bridge, /serviceWorkerRuntime\.repair\(\)/);
  assert.doesNotMatch(bridge, /skipWaiting|caches\.delete|unregister\(/);
  assert.doesNotMatch(bridge, /token|Auth|QueryClient|@features|@services/i);
});

test("Playwright usa perfiles aislados y targets Chromium Chrome Edge", async () => {
  const [config, spec] = await Promise.all([
    readFile(new URL("playwright.config.js", frontendRoot), "utf8"),
    readFile(new URL("e2e/tests/pwa-harness.spec.js", frontendRoot), "utf8"),
  ]);

  assert.match(config, /name: "chromium"/);
  assert.match(config, /channel: "chrome"/);
  assert.match(config, /channel: "msedge"/);
  assert.match(config, /workers: 1/);
  assert.doesNotMatch(config, /userDataDir|launchPersistentContext/);
  assert.match(spec, /context\.cookies\(\)/);
  assert.match(spec, /context\.newPage\(\)/);
  assert.match(spec, /context\.setOffline\(true\)/);
});

test("fixtures de errores y versiones viven fuera del build normal", async () => {
  const [builder, server, gitignore] = await Promise.all([
    readFile(new URL("e2e/scripts/build-version-fixtures.mjs", frontendRoot), "utf8"),
    readFile(new URL("e2e/scripts/pwa-fixture-server.mjs", frontendRoot), "utf8"),
    readFile(new URL(".gitignore", frontendRoot), "utf8"),
  ]);

  assert.match(builder, /\["N", "version-n"\]/);
  assert.match(builder, /\["N\+1", "version-n-plus-one"\]/);
  for (const fault of [
    "api-unreachable",
    "worker-invalid",
    "registration-failed",
    "asset-missing",
    "precache-incomplete",
    "update-failed",
  ]) {
    assert.match(server, new RegExp(fault));
  }
  assert.match(gitignore, /\.pwa-fixtures\//);
  assert.match(gitignore, /test-results\//);
});

import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

const rootUrl = new URL("../", import.meta.url);
const readSource = (path) => readFile(new URL(path, rootUrl), "utf8");

const assertMissing = async (path) => {
  await assert.rejects(access(new URL(path, rootUrl)));
};

test("los assets starter y branding duplicados eliminados no reaparecen", async () => {
  await Promise.all([
    assertMissing("public/favicon.png"),
    assertMissing("public/logo_miplaza.png"),
    assertMissing("public/logo_miplaza2.png"),
    assertMissing("src/assets/react.svg"),
  ]);
});

test("service worker conserva solo logging operativo de error", async () => {
  const [main, serviceWorker] = await Promise.all([
    readSource("src/main.jsx"),
    readSource("public/service-worker.js"),
  ]);

  assert.match(main, /register\("\/service-worker\.js"\)/);
  assert.match(main, /console\.error\("Error SW:"/);
  assert.doesNotMatch(main, /Service Worker registrado/);
  assert.doesNotMatch(serviceWorker, /console\.(?:log|debug)/);
});

test("query keys internas no amplian accidentalmente la API publica", async () => {
  const availabilityHook = await readSource(
    "src/features/availability/hooks/useHorariosAtencion.js",
  );

  assert.match(availabilityHook, /const horariosAtencionQueryKeys =/);
  assert.doesNotMatch(availabilityHook, /export const horariosAtencionQueryKeys/);
});

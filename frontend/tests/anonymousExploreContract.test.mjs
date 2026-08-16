import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  ANONYMOUS_DETAIL_DELAY_MS,
  scheduleAnonymousDetailGate,
} from "../src/core/access/anonymousDetailGate.js";

const frontendRoot = new URL("../", import.meta.url);

test("el gate de detalle agenda exactamente cinco segundos y su cleanup cancela el timer", () => {
  const calls = [];
  const cleanup = scheduleAnonymousDetailGate({
    onExpire: () => calls.push("expired"),
    setTimer(callback, delay) {
      calls.push([callback, delay]);
      return 41;
    },
    clearTimer(id) {
      calls.push(["cleared", id]);
    },
  });
  assert.equal(ANONYMOUS_DETAIL_DELAY_MS, 5000);
  assert.equal(calls.length, 1);
  assert.equal(calls[0][1], 5000);
  cleanup();
  assert.deepEqual(calls[1], ["cleared", 41]);
});

test("el detalle de espacio usa el owner central solo cuando el comercio ya existe", async () => {
  const detail = await readFile(new URL("src/features/spaces/pages/PerfilComercioPage.jsx", frontendRoot), "utf8");
  assert.match(detail, /useAnonymousDetailGate/);
  assert.match(detail, /enabled: !estaAutenticado/);
  assert.match(detail, /ready: Boolean\(comercio\)/);
  assert.match(detail, /navigate\("\/registro"/);
  assert.match(detail, /requireAuthentication: usuarioDebeLoguearse/);
});

test("Explorar anonimo queda en lectura sin el redirect global historico", async () => {
  const router = await readFile(new URL("src/core/router/AppRouter.jsx", frontendRoot), "utf8");
  const guestRoute = router.slice(router.indexOf("function GuestExploreRoute"), router.indexOf("export default function AppRouter"));
  assert.match(guestRoute, /return children/);
  assert.doesNotMatch(guestRoute, /setTimeout|navigate\(|5 \* 60/);
});

test("las acciones protegidas reutilizan una redireccion central y no sustituyen al backend", async () => {
  const [guard, commerce, post] = await Promise.all([
    readFile(new URL("src/core/access/useProtectedActionRedirect.js", frontendRoot), "utf8"),
    readFile(new URL("src/features/spaces/pages/PerfilComercioPage.jsx", frontendRoot), "utf8"),
    readFile(new URL("src/features/posts/pages/PublicacionDetallePage.jsx", frontendRoot), "utf8"),
  ]);
  assert.match(guard, /if \(estaAutenticado\) return false/);
  assert.match(guard, /navigate\("\/registro"/);
  assert.match(commerce, /useProtectedActionRedirect/);
  assert.match(post, /useProtectedActionRedirect/);
  assert.doesNotMatch(guard, /fetch|httpPost|permission|ranking|Search|Discovery/);
});

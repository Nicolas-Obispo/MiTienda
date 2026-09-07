import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);
const readText = (path) => readFile(new URL(path, root), "utf8");

test("ProtectedActionProvider es el owner unico del Auth Wall", async () => {
  const [provider, adapter, router] = await Promise.all([
    readText("src/core/access/ProtectedActionProvider.jsx"),
    readText("src/core/access/useProtectedActionRedirect.js"),
    readText("src/core/router/AppRouter.jsx"),
  ]);

  assert.match(provider, /const requireAuthentication = useCallback/);
  assert.match(provider, /<ActiveLayer/);
  assert.match(provider, /inert=\{wall \? true : undefined\}/);
  assert.match(provider, /aria-hidden=\{wall \? "true" : undefined\}/);
  assert.match(provider, /goToAuth\("\/login"\)/);
  assert.match(provider, /goToAuth\("\/registro"\)/);
  assert.match(provider, /getInternalReturnTo/);
  assert.doesNotMatch(provider, /localStorage|sessionStorage|indexedDB|Cache Storage/i);
  assert.match(adapter, /return useProtectedAction\(\)/);
  assert.equal((router.match(/<ProtectedActionProvider>/g) || []).length, 1);
});

test("las interacciones no pasivas publicas pasan por el owner central", async () => {
  const [space, post, report] = await Promise.all([
    readText("src/features/spaces/pages/PerfilComercioPage.jsx"),
    readText("src/features/posts/pages/PublicacionDetallePage.jsx"),
    readText("src/features/moderation/components/PublicacionReportControl.jsx"),
  ]);

  for (const handler of [
    "handleToggleLike",
    "handleToggleFollow",
    "handleToggleSave",
    "handleOpenHistorias",
    "handleOpenDenunciaComercio",
  ]) {
    assert.match(
      space,
      new RegExp(`function ${handler}\\([^)]*\\) \\{[\\s\\S]{0,120}usuarioDebeLoguearse\\(\\)`)
    );
  }
  assert.equal((space.match(/if \(usuarioDebeLoguearse\(\)\) event\.preventDefault\(\)/g) || []).length, 3);
  assert.match(post, /handleToggleLike\(\)[\s\S]{0,100}usuarioDebeLoguearse\(\)/);
  assert.match(post, /handleToggleGuardar\(\)[\s\S]{0,100}usuarioDebeLoguearse\(\)/);
  assert.match(report, /if \(requireAuthentication\(\)\) return/);
});

test("navegacion, busqueda, filtros, paginacion y detalle siguen siendo pasivos", async () => {
  const explore = await readText("src/features/explore/pages/ExplorarPage.jsx");

  assert.match(explore, /cambiarModoExplorar/);
  assert.match(explore, /setSearchScope/);
  assert.match(explore, /fetchNextPage\(\)/);
  assert.match(explore, /irAPerfilComercio/);
  assert.match(explore, /irADetallePublicacion/);
  assert.doesNotMatch(explore, /useProtectedAction|requireAuthentication/);
});

test("el gate temporal comparte wall y no superpone redirecciones", async () => {
  const space = await readText("src/features/spaces/pages/PerfilComercioPage.jsx");

  assert.match(space, /onExpire: openAnonymousDetailGate/);
  assert.match(space, /openAnonymousDetailGate[\s\S]{0,180}usuarioDebeLoguearse/);
  assert.doesNotMatch(space, /navigate\("\/registro"/);
  assert.equal((space.match(/useAnonymousDetailGate\(/g) || []).length, 1);
});

test("Login y Registro preservan solamente el returnTo validado", async () => {
  const [provider, login, registration, internalReturnTo] = await Promise.all([
    readText("src/core/access/ProtectedActionProvider.jsx"),
    readText("src/features/auth/pages/Login.jsx"),
    readText("src/features/auth/pages/Registro.jsx"),
    readText("src/core/navigation/internalReturnTo.js"),
  ]);

  assert.match(provider, /location\.pathname.*location\.search/);
  assert.doesNotMatch(provider, /location\.hash/);
  assert.match(login, /navigate\(returnTo, \{ replace: true \}\)/);
  assert.match(login, /state=\{\{ message: mensajeContextual, returnTo \}\}/);
  assert.match(registration, /state=\{\{ message: mensajeContextual, returnTo \}\}/);
  assert.match(registration, /registrationEmailStatus:[\s\S]{0,100}returnTo/);
  assert.match(internalReturnTo, /url\.searchParams\.delete\(key\)/);
  assert.doesNotMatch(internalReturnTo, /url\.hash/);
});

test("ActiveLayer conserva foco, Escape y restauracion sin un segundo focus trap", async () => {
  const [provider, layer] = await Promise.all([
    readText("src/core/access/ProtectedActionProvider.jsx"),
    readText("src/core/components/ActiveLayer.jsx"),
  ]);

  assert.match(provider, /initialFocusRef=\{loginButtonRef\}/);
  assert.match(layer, /event\.key === "Escape"/);
  assert.match(layer, /event\.key !== "Tab"/);
  assert.match(layer, /previousFocus\.focus\(\)/);
  assert.doesNotMatch(provider, /createPortal|document\.body\.style|event\.key === "Tab"/);
});

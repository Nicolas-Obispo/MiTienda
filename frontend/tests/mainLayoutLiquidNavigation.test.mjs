import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const [layout, administrationLink, helper] = await Promise.all([
  readFile(new URL("../src/shared/layouts/MainLayout.jsx", import.meta.url), "utf8"),
  readFile(
    new URL("../src/features/administration/components/AdministrativeNavigationLink.jsx", import.meta.url),
    "utf8"
  ),
  readFile(
    new URL("../src/shared/components/InteractiveLiquidLayers.jsx", import.meta.url),
    "utf8"
  ),
]);

test("todos los controles de navegación global reciben una sola capa Liquid", () => {
  assert.equal((layout.match(/interactive-bubble--liquid/g) || []).length, 7);
  assert.equal((layout.match(/<InteractiveLiquidLayers \/>/g) || []).length, 7);
  assert.equal((administrationLink.match(/interactive-bubble--liquid/g) || []).length, 1);
  assert.equal((administrationLink.match(/<InteractiveLiquidLayers \/>/g) || []).length, 1);
});

test("nodos, destinos, textos, logo y condiciones permanecen", () => {
  for (const destination of ["/", "/feed", "/ranking", "/ver-seguidos", "/explorar", "/login"]) {
    assert.match(layout, new RegExp(`to="${destination.replace("/", "\\/")}"`));
  }
  assert.match(layout, /to=\{estaAutenticado \? "\/perfil" : "\/registro"\}/);
  for (const text of ["Feed", "Perfil administrador", "Tendencias", "Seguidos", "Explorar", "Ingresar"]) {
    assert.match(layout, new RegExp(text));
  }
  assert.match(layout, /src="\/logo_Feedgo\.png"/);
  assert.match(layout, /alt="FeedGo"/);
  assert.match(layout, /\{estaAutenticado && \(/);
  assert.match(layout, /\{!estaAutenticado && \(/);
  assert.match(layout, /estaAutenticado && <AdministrativeNavigationLink/);
  assert.match(administrationLink, /NAVIGABLE_CAPABILITIES\.some\(tieneCapacidad\)/);
  assert.match(administrationLink, /to="\/administracion"/);
  assert.match(administrationLink, /Administración/);
});

test("geometría, responsive y color semántico se conservan", () => {
  assert.match(layout, /interactive-bubble--flush[\s\S]*shrink-0 items-center/);
  assert.match(layout, /text-xs sm:text-sm/);
  assert.match(layout, /rounded-lg[\s\S]*px-1\.5 py-1[\s\S]*sm:rounded-xl sm:px-2 sm:text-xs/);
  assert.match(layout, /text-selected-text/);
  assert.match(layout, /text-secondary group-hover:text-primary/);
  assert.match(layout, /text-interactive-on-primary/);
  assert.match(administrationLink, /min-h-11 min-w-0 w-full[\s\S]*sm:w-auto sm:shrink-0 sm:text-sm/);
});

test("helper sigue siendo decorativo y no altera interacción", () => {
  assert.match(helper, /aria-hidden="true"/);
  assert.doesNotMatch(helper, /on[A-Z][A-Za-z]*=|useState|useEffect|useReducer|useRef/);
  assert.doesNotMatch(helper, /pointer-events-auto/);
});

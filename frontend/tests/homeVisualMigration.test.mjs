import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const [home, router, mainLayout, button] = await Promise.all([
  readSource("../src/features/home/pages/Home.jsx"),
  readSource("../src/core/router/AppRouter.jsx"),
  readSource("../src/shared/layouts/MainLayout.jsx"),
  readSource("../src/shared/components/primitives/Button.jsx"),
]);

test("Home real vive en slash y reutiliza MainLayout", () => {
  assert.match(router, /<Route element=\{<MainLayout \/>\}>/);
  assert.match(router, /<Route path="\/" element=\{<Home \/>\}/);
  assert.match(mainLayout, /<Outlet \/>/);
});

test("Home migra canvas, hero y cards mediante roles y Surface", () => {
  assert.match(home, /bg-canvas text-primary/);
  assert.match(home, /<Surface\s+as="section"\s+variant="elevated"/);
  assert.equal((home.match(/<Surface\b/g) || []).length, 4);
  assert.match(home, /from-brand\/15 via-surface to-canvas-subtle/);
  assert.match(home, /text-secondary/);
  assert.match(home, /text-muted/);
});

test("CTAs conservan Link, destinos y bubble compartida", () => {
  assert.equal((home.match(/<Link\b/g) || []).length, 3);
  assert.match(home, /to="\/explorar"/);
  assert.match(home, /to="\/feed"/);
  assert.match(home, /to="\/registro"/);
  assert.match(home, /interactive-bubble--primary-action/);
  assert.equal((home.match(/interactive-bubble--secondary/g) || []).length, 2);
  assert.doesNotMatch(home, /<Button\b/);
  assert.match(button, /interactive-bubble/);
  assert.match(button, /font-semibold/);
});

test("Home conserva bifurcacion de invitado y usuario autenticado", () => {
  assert.match(home, /const \{ estaAutenticado \} = useAuth\(\)/);
  assert.match(home, /\{estaAutenticado \? \(/);
  assert.match(home, /Ir a mi feed/);
  assert.match(home, /Crear cuenta gratis/);
  assert.doesNotMatch(home, /fetch\(|httpGet|useQuery|navigate\(/);
});

test("Home no introduce tema manual ni colores fisicos evitables", () => {
  assert.doesNotMatch(home, /#[\da-f]{3,8}|\brgb\(|\brgba\(/i);
  assert.doesNotMatch(
    home,
    /(?:bg|text|border|from|via|to)-(?:gray|slate|zinc|neutral|stone|white|black|red|green|emerald|orange|amber|yellow|blue|purple|pink)(?:\/|-\d|\b)/
  );
  assert.doesNotMatch(
    home,
    /resolvedTheme|data-theme|dark:|matchMedia\(|localStorage\./
  );
});

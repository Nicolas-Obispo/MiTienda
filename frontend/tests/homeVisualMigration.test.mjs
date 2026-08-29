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
  assert.equal((home.match(/<Surface\b/g) || []).length, 2);
  assert.match(home, /INFORMATION_BLOCKS\.map\(\(\{ title, description \}\) =>/);
  assert.match(home, /sm:grid-cols-2 lg:grid-cols-3/);
  assert.match(home, /from-brand\/15 via-surface to-canvas-subtle/);
  assert.match(home, /text-secondary/);
  assert.match(home, /text-muted/);
});

test("Home presenta los seis bloques informativos aprobados en orden", () => {
  const blocks = [
    ["Descubrí negocios y servicios", "Encontrá comercios, profesionales, oficios y servicios activos en tu zona desde un solo lugar."],
    ["Explorá sin registrarte", "Recorré perfiles, publicaciones y novedades de FeedGo sin necesidad de crear una cuenta."],
    ["Interactuá con la plataforma", "Creá tu cuenta para guardar publicaciones, dar like y personalizar tu experiencia."],
    ["Creá tu propio espacio", "Si tenés un negocio, ofrecés un servicio o ejercés una profesión, creá un espacio para mostrar quién sos, qué hacés y cómo contactarte."],
    ["Mostrá tu actividad", "Publicá contenido y novedades para mantener tu espacio actualizado y acercar tu propuesta a potenciales clientes."],
    ["Gestioná los espacios de tus clientes", "Si trabajás con publicidad, comunicación o redes, administrá desde un mismo perfil los espacios de tu cartera de clientes y mantené cada negocio organizado."],
  ];
  let previousIndex = -1;
  for (const [title, description] of blocks) {
    const titleIndex = home.indexOf(`title: "${title}"`);
    const descriptionIndex = home.indexOf(`"${description}"`, titleIndex);
    assert.ok(titleIndex > previousIndex);
    assert.ok(descriptionIndex > titleIndex);
    previousIndex = descriptionIndex;
  }
  assert.match(home, /Podés explorar sin cuenta\. Solo necesitás registrarte para interactuar[\s\S]*con la plataforma\./);
});

test("CTAs conservan Link, destinos y bubble compartida", () => {
  assert.equal((home.match(/<Link\b/g) || []).length, 3);
  assert.match(home, /to="\/explorar"/);
  assert.match(home, /to="\/feed"/);
  assert.match(home, /to="\/registro"/);
  assert.match(home, /interactive-bubble--primary-action/);
  assert.equal((home.match(/interactive-bubble--secondary/g) || []).length, 2);
  assert.equal((home.match(/interactive-bubble--liquid/g) || []).length, 3);
  assert.equal((home.match(/<InteractiveLiquidLayers \/>/g) || []).length, 3);
  assert.doesNotMatch(home, /<Button\b/);
  assert.match(button, /interactive-bubble/);
  assert.match(button, /font-semibold/);
});

test("los tres CTA conservan geometría, variantes y una capa Liquid", () => {
  assert.match(
    home,
    /to="\/explorar"[\s\S]*interactive-bubble--liquid interactive-bubble--primary-action[\s\S]*text-interactive-on-primary[\s\S]*Explorar sin registrarme[\s\S]*<InteractiveLiquidLayers \/>/
  );
  assert.match(
    home,
    /to="\/feed"[\s\S]*interactive-bubble--liquid interactive-bubble--secondary[\s\S]*text-primary[\s\S]*Ir a mi feed[\s\S]*<InteractiveLiquidLayers \/>/
  );
  assert.match(
    home,
    /to="\/registro"[\s\S]*interactive-bubble--liquid interactive-bubble--secondary[\s\S]*text-primary[\s\S]*Crear cuenta gratis[\s\S]*<InteractiveLiquidLayers \/>/
  );
  assert.equal(
    (home.match(/rounded-2xl[\s\S]{0,160}px-5 py-3 text-center text-sm font-bold/g) || []).length,
    3
  );
  assert.match(home, /mt-8 flex flex-col gap-3 sm:flex-row/);
});

test("Liquid de Home es decorativo y no altera los seis bloques", () => {
  assert.match(home, /import InteractiveLiquidLayers from "@shared\/components\/InteractiveLiquidLayers"/);
  assert.equal((home.match(/title: "/g) || []).length, 6);
  assert.match(home, /INFORMATION_BLOCKS\.map\(\(\{ title, description \}\) =>/);
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

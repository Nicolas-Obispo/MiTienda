import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const [profile, detailHook] = await Promise.all([
  readSource("../src/features/spaces/pages/PerfilComercioPage.jsx"),
  readSource("../src/features/spaces/hooks/useComercioDetalle.js"),
]);

test("perfil publico de espacio usa shell, estados y primitives semanticos", () => {
  assert.match(profile, /min-h-screen bg-canvas text-primary/);
  assert.match(profile, /<Surface as="section"/);
  assert.match(profile, /<Skeleton\b/);
  assert.match(profile, /<Alert className="p-5" variant="danger"/);
  assert.match(profile, /<ActiveLayer/);
  assert.match(profile, /<Input\b/);
  assert.match(profile, /<Textarea\b/);
});

test("acciones migradas reutilizan Button y una unica infraestructura bubble", () => {
  assert.ok((profile.match(/<Button\b/g) || []).length >= 10);
  assert.match(profile, /variant="primary"/);
  assert.match(profile, /variant="secondary"/);
  assert.match(profile, /variant="ghost"/);
  assert.doesNotMatch(profile, /<button\b/);
  assert.doesNotMatch(profile, /interactive-bubble::|\.interactive-bubble\s*\{/);
});

test("direccion y Como llegar se renderizan solo desde el contrato publico recibido", () => {
  assert.match(profile, /comercio\?\.direccion\s*\? `\$\{comercio\.direccion\}, \$\{comercio\.ciudad\}`/);
  assert.match(profile, /\(comercio\?\.latitud && comercio\?\.longitud\) \|\| comercio\?\.maps_url/);
  assert.match(profile, /comercio\.maps_url/);
  assert.doesNotMatch(profile, /mostrar_direccion_publicamente/);
  assert.doesNotMatch(profile, /Ubicaci[oÃ³]n no disponible/);
  assert.doesNotMatch(profile, /distancia_km\s*[+*/=-]|haversine/i);
});

test("owners de publicaciones, historias, horarios, agenda y moderacion se reutilizan", () => {
  assert.match(profile, /<PublicacionCard\b/);
  assert.match(profile, /<HistoriasViewer\b/);
  assert.match(profile, /<CrearHistoriaModal\b/);
  assert.match(profile, /<EstadoHorarioBadge\b/);
  assert.match(profile, /<AgendaPrivadaModal\b/);
  assert.match(profile, /<DenunciaModal\b/);
});

test("cache y comportamiento funcional del perfil conservan sus owners", () => {
  assert.match(profile, /useComercioDetalle\(comercioId\)/);
  assert.match(profile, /usePublicacionesComercio\(comercioId\)/);
  assert.match(profile, /useHistoriasComercio\(comercioId\)/);
  assert.match(profile, /optimisticToggleLike/);
  assert.match(profile, /optimisticToggleGuardado/);
  assert.match(detailHook, /queryKey: queryKeys\.spaces\.detalle\(comercioIdNumber\)/);
  assert.match(detailHook, /staleTime: 1000 \* 60/);
});

test("tema es declarativo y los unicos colores fisicos son marcas externas", () => {
  const withoutExternalBranding = profile
    .replace(/text-green-400 group-hover:text-green-300/g, "")
    .replace(/text-pink-400 group-hover:text-pink-300/g, "");

  assert.doesNotMatch(withoutExternalBranding, /#[\da-f]{3,8}|\brgb\(|\brgba\(/i);
  assert.doesNotMatch(
    withoutExternalBranding,
    /(?:bg|text|border|ring|from|via|to)-(?:gray|slate|zinc|neutral|stone|white|black|red|green|emerald|orange|amber|yellow|blue|purple|pink)(?:\/|-\d|\b)/
  );
  assert.doesNotMatch(
    profile,
    /resolvedTheme|data-theme|dark:|matchMedia\(|localStorage\.getItem\("feedgo\.theme/
  );
});

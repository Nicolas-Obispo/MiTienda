import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const [profile, detailHook, scheduleBadge] = await Promise.all([
  readSource("../src/features/spaces/pages/PerfilComercioPage.jsx"),
  readSource("../src/features/spaces/hooks/useComercioDetalle.js"),
  readSource("../src/features/availability/components/EstadoHorarioBadge.jsx"),
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

test("denuncia de espacio queda bajo Seguir y se oculta al propietario", () => {
  assert.match(
    profile,
    /!esComercioMio\(comercio\)[\s\S]*flex shrink-0 flex-col items-center gap-2[\s\S]*\+Seguir[\s\S]*aria-label="Denunciar espacio"[\s\S]*>\s*\.\.\.\s*<\/span>/
  );
  assert.equal((profile.match(/setIsDenunciaComercioOpen\(true\)/g) || []).length, 1);
  assert.match(profile, /recursoTipo=\{RECURSO_DENUNCIA_COMERCIO\}[\s\S]*recursoId=\{comercio\?\.id\}/);
});

test("identidad y acciones comparten una cabecera superior sin mover contactos ni horario", () => {
  assert.match(
    profile,
    /flex items-start justify-between gap-4[\s\S]*flex min-w-0 flex-1 items-start gap-4[\s\S]*aria-label=\{`Abrir historias de[\s\S]*<h1[\s\S]*!esComercioMio\(comercio\)[\s\S]*flex shrink-0 flex-col items-center gap-2/
  );
  assert.doesNotMatch(profile, /IZQUIERDA \(todo tu contenido actual\)|nombre, descripción/);
  assert.match(
    profile,
    /mt-4 flex w-full flex-wrap items-end gap-x-4 gap-y-2[\s\S]*WhatsApp[\s\S]*Instagram[\s\S]*Cómo llegar[\s\S]*<EstadoHorarioBadge[\s\S]*className="ml-auto justify-end"/
  );
});

test("direccion se renderiza una sola vez inmediatamente sobre el estado operativo", () => {
  assert.equal((profile.match(/comercio\?\.direccion\s*\? `\$\{comercio\.direccion\}, \$\{comercio\.ciudad\}`/g) || []).length, 1);
  assert.match(profile, /min-w-0 flex-1 text-left/);
  assert.match(profile, /ml-auto flex max-w-full flex-col items-end gap-1 text-right/);
  assert.match(profile, /flex max-w-full items-start justify-end gap-2 break-words text-xs text-secondary/);
  const addressPosition = profile.indexOf("{comercio?.ciudad && (", profile.indexOf("items-end gap-1 text-right"));
  const schedulePosition = profile.indexOf("<EstadoHorarioBadge", addressPosition);
  assert.ok(addressPosition > -1 && schedulePosition > addressPosition);
  assert.doesNotMatch(
    profile,
    /min-w-0 flex-1 text-left[\s\S]*comercio\?\.ciudad[\s\S]*ml-auto flex max-w-full flex-col items-end/
  );
  assert.match(scheduleBadge, /isInline[\s\S]*min-h-9 py-1 text-xs/);
});

test("metricas publicas se ocultan pero Estadisticas conserva datos y acceso", () => {
  assert.doesNotMatch(profile, /\{publicacionesCountVisible\} publicaciones|\{seguidoresCountLabel\}/);
  assert.doesNotMatch(profile, /PUBLICACIONES \*\/|SEGUIDORES \*\//);
  assert.match(profile, /obtenerMetricasSocialesEspacio\(comercioId\)/);
  assert.match(profile, /metricasSociales\?\.total_seguidores/);
  assert.match(profile, /onClick=\{\(\) => setIsEstadisticasOpen\(true\)\}[\s\S]*Estadísticas/);
});

test("contactos y acciones administrativas comparten el patron compacto", () => {
  assert.equal((profile.match(/interactive-bubble interactive-bubble--liquid group cursor-pointer rounded-xl px-2 py-1 text-xs font-semibold/g) || []).length, 3);
  assert.equal((profile.match(/className="group cursor-pointer rounded-xl px-2 py-1 text-xs"/g) || []).length, 3);
  assert.ok((profile.match(/inline-flex items-center gap-1/g) || []).length >= 6);
  assert.equal((profile.match(/(?:PlusCircle|BarChart3) size=\{14\}/g) || []).length, 3);
  for (const handler of ["setIsCrearHistoriaOpen", "setIsCrearPublicacionOpen", "setIsEstadisticasOpen"]) {
    assert.match(profile, new RegExp(`onClick=\\{\\(\\) => ${handler}\\(true\\)\\}`));
  }
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

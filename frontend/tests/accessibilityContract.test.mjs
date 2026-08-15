import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import test from "node:test";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const [activeLayer, profile, spaceProfile, viewer, createStory, inactivityGuard, feed, publicationCard, css, mainLayout] =
  await Promise.all([
    readSource("../src/core/components/ActiveLayer.jsx"),
    readSource("../src/features/auth/pages/ProfilePage.jsx"),
    readSource("../src/features/spaces/pages/PerfilComercioPage.jsx"),
    readSource("../src/features/stories/components/HistoriasViewer.jsx"),
    readSource("../src/features/stories/components/CrearHistoriaModal.jsx"),
    readSource("../src/features/auth/components/SessionInactivityGuard.jsx"),
    readSource("../src/features/feed/pages/FeedPage.jsx"),
    readSource("../src/features/posts/components/PublicacionCard.jsx"),
    readSource("../src/index.css"),
    readSource("../src/shared/layouts/MainLayout.jsx"),
  ]);

const srcRoot = new URL("../src/", import.meta.url);
const sourcePaths = (await readdir(srcRoot, { recursive: true }))
  .filter((path) => path.endsWith(".jsx") || path.endsWith(".js"));
const allRuntimeSources = (
  await Promise.all(
    sourcePaths.map(async (path) => [path, await readFile(new URL(path, srcRoot), "utf8")])
  )
);
const normalizedPaths = (entries) =>
  entries.map(([path]) => path.replaceAll("\\", "/"));

test("ActiveLayer conserva dialogo modal, trap, cierre y retorno de foco", () => {
  assert.match(activeLayer, /role="dialog"/);
  assert.match(activeLayer, /aria-modal="true"/);
  assert.match(activeLayer, /aria-labelledby=\{labelledBy\}/);
  assert.match(activeLayer, /aria-describedby=\{describedBy\}/);
  assert.match(activeLayer, /event\.key === "Escape"/);
  assert.match(activeLayer, /event\.key !== "Tab"/);
  assert.match(activeLayer, /previousFocusRef\.current/);
  assert.match(activeLayer, /previousFocus\.focus\(\)/);
  assert.match(activeLayer, /aria-label="Cerrar capa activa"[\s\S]*tabIndex=\{-1\}/);
  assert.match(activeLayer, /clearTimeout\(initialFocusTimerRef\.current\)/);
  assert.match(activeLayer, /previousFocus\?\.isConnected/);
  assert.match(activeLayer, /items-start justify-center overflow-y-auto overscroll-contain/);
  assert.match(activeLayer, /relative z-10 my-auto outline-none/);
});

test("ActiveLayer es el unico owner de portal y scroll lock", () => {
  const portalOwners = allRuntimeSources.filter(([, source]) => source.includes("createPortal"));
  const scrollLockOwners = allRuntimeSources.filter(([, source]) => source.includes("document.body.style"));
  const fullscreenOwners = allRuntimeSources.filter(([, source]) => source.includes("fixed inset-0"));

  assert.deepEqual(normalizedPaths(portalOwners), ["core/components/ActiveLayer.jsx"]);
  assert.deepEqual(normalizedPaths(scrollLockOwners), ["core/components/ActiveLayer.jsx"]);
  assert.deepEqual(
    normalizedPaths(fullscreenOwners).sort(),
    ["core/components/ActiveLayer.jsx", "features/stories/components/HistoriasViewer.jsx"]
  );
});

test("Crear Historia reutiliza ActiveLayer con nombre y descripcion", () => {
  assert.match(createStory, /<ActiveLayer/);
  assert.match(createStory, /labelledBy="crear-historia-title"/);
  assert.match(createStory, /describedBy="crear-historia-description"/);
  assert.match(createStory, /id="crear-historia-title"/);
  assert.match(createStory, /id="crear-historia-description"/);
});

test("guardia de inactividad delega modal, foco y Escape en ActiveLayer", () => {
  assert.match(inactivityGuard, /<ActiveLayer/);
  assert.match(inactivityGuard, /labelledBy="session-inactivity-title"/);
  assert.match(inactivityGuard, /initialFocusRef=\{continueButtonRef\}/);
  assert.match(inactivityGuard, /id="session-inactivity-title"/);
  assert.match(inactivityGuard, /ref=\{continueButtonRef\}/);
  assert.doesNotMatch(inactivityGuard, /<div className="fixed inset-0/);
});

test("bienvenida de Feed conserva estado y delega semantica modal", () => {
  assert.match(feed, /<ActiveLayer/);
  assert.match(feed, /labelledBy="feed-welcome-title"/);
  assert.match(feed, /describedBy="feed-welcome-description"/);
  assert.match(feed, /initialFocusRef=\{welcomeActionRef\}/);
  assert.match(feed, /closeOnBackdrop=\{false\}/);
  assert.match(feed, /closeOnEscape=\{false\}/);
});

test("capas de estadisticas y publicacion reutilizan ActiveLayer", () => {
  assert.equal((spaceProfile.match(/<ActiveLayer/g) || []).length, 2);
  assert.match(spaceProfile, /labelledBy="estadisticas-espacio-title"/);
  assert.match(spaceProfile, /describedBy="estadisticas-espacio-description"/);
  assert.match(spaceProfile, /labelledBy="crear-publicacion-title"/);
  assert.match(spaceProfile, /describedBy="crear-publicacion-description"/);
  assert.doesNotMatch(spaceProfile, /<div className="fixed inset-0/);
});

test("backdrops y contenido alto usan contratos compartidos", () => {
  const horarios = allRuntimeSources.find(([path]) =>
    path.endsWith("HorariosAtencionEditor.jsx")
  )[1];

  assert.match(horarios, /backdropClassName="bg-overlay-backdrop"/);
  assert.doesNotMatch(horarios, /backdropClassName="bg-overlay"/);
  for (const source of [createStory, feed, spaceProfile]) {
    assert.match(source, /max-h-\[calc\(100dvh-2rem\)\] overflow-y-auto/);
  }
});

test("PublicacionCard ofrece enlaces nativos al detalle sin reemplazar acciones", () => {
  assert.match(publicationCard, /to=\{`\/publicaciones\/\$\{pub\.id\}`\}/);
  assert.match(publicationCard, /Ver publicación/);
  assert.match(publicationCard, /<InteraccionButton/);
  assert.doesNotMatch(publicationCard, /role="link"|tabIndex=\{0\}/);
});

test("formulario de espacios asocia labels y usa control nativo para portada", () => {
  for (const id of [
    "espacio-nombre",
    "espacio-rubro",
    "espacio-especialidad",
    "espacio-provincia",
    "espacio-ciudad",
    "espacio-descripcion",
    "espacio-whatsapp",
    "espacio-instagram",
    "espacio-direccion",
  ]) {
    assert.match(profile, new RegExp(`htmlFor="${id}"`));
    assert.match(profile, new RegExp(`id="${id}"`));
  }
  assert.doesNotMatch(profile, /role="button"/);
  assert.match(profile, /<button[\s\S]*aria-label="Seleccionar portada del espacio"/);
  assert.match(profile, /disabled=\{isUploadingPortada\}/);
});

test("HistoriasViewer ofrece activacion nativa sin alterar su contrato fijo", () => {
  assert.match(viewer, /aria-label="Me gusta"/);
  assert.match(viewer, /aria-label="Cerrar historias"/);
  assert.match(viewer, /aria-label="Historia anterior"/);
  assert.match(viewer, /aria-label="Siguiente historia"/);
  assert.match(viewer, /motion-reduce:animate-none/);
  assert.doesNotMatch(viewer, /onMouseDown=/);
});

test("movimiento compartido respeta prefers-reduced-motion", () => {
  assert.match(
    css,
    /@media \(prefers-reduced-motion: reduce\)[\s\S]*\.animate-logo,[\s\S]*\.animate-like,[\s\S]*\.animate-save[\s\S]*animation: none/
  );
  assert.match(css, /@media \(prefers-reduced-motion: reduce\)[\s\S]*\.interactive-bubble:active[\s\S]*transform: none/);
});

test("navegacion principal conserva Link y nombre de producto correcto", () => {
  assert.match(mainLayout, /<Link[\s\S]*to="\/"/);
  assert.match(mainLayout, /alt="FeedGo"/);
  assert.match(mainLayout, /<nav\b/);
});

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const [viewer, viewerCss, createModal, storiesService] = await Promise.all([
  readSource("../src/features/stories/components/HistoriasViewer.jsx"),
  readSource("../src/features/stories/components/HistoriasViewer.css"),
  readSource("../src/features/stories/components/CrearHistoriaModal.jsx"),
  readSource("../src/features/stories/services/historias_service.js"),
]);

test("HistoriasViewer declara un contrato multimedia fijo y aislado", () => {
  assert.match(viewer, /className="historias-viewer-fixed fixed inset-0 z-50 bg-black"/);
  assert.match(viewer, /data-visual-contract="fixed-media"/);
  assert.match(viewer, /import "\.\/HistoriasViewer\.css"/);
  assert.match(viewerCss, /\.historias-viewer-fixed/);
  assert.match(viewerCss, /isolation: isolate/);
  assert.match(viewerCss, /color-scheme: dark/);
  assert.doesNotMatch(viewerCss, /var\(--fg-|data-theme|prefers-color-scheme/);
});

test("escenario, progreso, overlays y texto permanecen invariantes", () => {
  assert.match(viewer, /fixed inset-0 z-50 bg-black/);
  assert.match(viewer, /bg-white\/25 overflow-hidden/);
  assert.match(viewer, /className="h-full bg-white"/);
  assert.match(viewer, /text-sm font-semibold text-white truncate/);
  assert.match(viewer, /bg-white\/10[\s\S]*hover:bg-white\/20/);
  assert.match(viewer, /text-white\/70 text-sm/);
});

test("viewer no hereda runtime de tema, Button ni interactive-bubble", () => {
  assert.doesNotMatch(
    viewer,
    /useTheme|resolvedTheme|setPreference|data-theme=|matchMedia\(|localStorage|dark:/
  );
  assert.doesNotMatch(viewer, /<Button\b|interactive-bubble/);
  assert.match(viewer, /<button\b/);
});

test("cambio de tema no forma parte del estado ni reinicia el ciclo", () => {
  for (const state of [
    "indexActual",
    "progreso",
    "mediaLista",
    "cycleKey",
    "likedByMe",
    "isDenunciaOpen",
  ]) {
    assert.match(viewer, new RegExp(`\\[${state},`));
  }
  assert.doesNotMatch(viewer, /useEffect\([\s\S]{0,500}(?:theme|preference|appearance)/i);
});

test("navegacion, teclado, timer y reproduccion conservan contrato", () => {
  assert.match(viewer, /requestAnimationFrame\(tick\)/);
  assert.match(viewer, /cancelAnimationFrame/);
  assert.match(viewer, /elapsed \/ DURACION_MS_DEFAULT/);
  assert.match(viewer, /e\.key === "Escape"/);
  assert.match(viewer, /e\.key === "ArrowLeft"/);
  assert.match(viewer, /e\.key === "ArrowRight"/);
  assert.match(viewer, /autoPlay[\s\S]*muted[\s\S]*playsInline[\s\S]*preload="metadata"/);
  assert.match(viewer, /onEnded=\{irSiguiente\}/);
  assert.match(viewer, /className="h-full w-full object-contain"/);
});

test("controles conservan foco visible y activacion accesible", () => {
  assert.match(viewer, /aria-label="Cerrar historias"/);
  assert.match(viewer, /aria-label="Historia anterior"/);
  assert.match(viewer, /aria-label="Siguiente historia"/);
  assert.match(viewer, /aria-label="Quitar me gusta"/);
  assert.match(viewer, /aria-label="Me gusta"/);
  assert.match(viewer, /onClick=\{handleToggleLikeHistoria\}/);
  assert.match(viewer, /focus-visible:outline-white/);
});

test("like, heartFly y denuncia conservan sus owners funcionales", () => {
  assert.match(viewer, /@keyframes heartFly/);
  assert.match(viewer, /heartFly_900ms_ease-in-out_forwards/);
  assert.match(viewer, /toggleLikeHistoria\(historiaActual\.id\)/);
  assert.match(viewer, /<DenunciaModal/);
  assert.match(viewer, /RECURSO_DENUNCIA_HISTORIA/);
});

test("CrearHistoriaModal usa primitives y roles semanticos", () => {
  assert.match(createModal, /<ActiveLayer/);
  assert.match(createModal, /labelledBy="crear-historia-title"/);
  assert.match(createModal, /describedBy="crear-historia-description"/);
  assert.match(createModal, /<Surface variant="elevated"/);
  assert.ok((createModal.match(/<Input\b/g) || []).length >= 4);
  assert.match(createModal, /<Alert variant="danger" role="alert"/);
  assert.match(createModal, /<Button[\s\S]*variant="secondary"/);
  assert.match(createModal, /<Button[\s\S]*variant="primary"/);
  assert.doesNotMatch(createModal, /fixed inset-0 z-50|bg-overlay-backdrop/);
});

test("creacion conserva archivo, upload, payload, submit y cierre", () => {
  assert.match(createModal, /setSelectedFile\(file\)/);
  assert.match(createModal, /uploadImagen\(selectedFile, accessToken\)/);
  assert.match(createModal, /media_url: finalMediaUrl/);
  assert.match(createModal, /expira_en: buildExpiraEnIso\(\)/);
  assert.match(createModal, /is_activa: isActiva/);
  assert.match(createModal, /crearHistoria\(comercioId, payload\)/);
  assert.match(createModal, /onCreated\(nuevaHistoria\)/);
  assert.match(createModal, /onClose\(\)/);
  assert.match(storiesService, /export async function crearHistoria/);
});

test("formulario cambia de tema sin estado propio ni colores fisicos", () => {
  assert.doesNotMatch(
    createModal,
    /useTheme|resolvedTheme|data-theme|dark:|matchMedia\(|localStorage/
  );
  assert.doesNotMatch(createModal, /#[\da-f]{3,8}|\brgb\(|\brgba\(/i);
  assert.doesNotMatch(
    createModal,
    /(?:bg|text|border|ring|from|via|to)-(?:gray|slate|zinc|neutral|stone|white|black|red|green|emerald|orange|amber|yellow|blue|purple|pink)(?:\/|-\d|\b)/
  );
  assert.doesNotMatch(createModal, /interactive-bubble/);
});

test("media sigue siendo contenido y no se inventa preview", () => {
  assert.match(createModal, /accept="[\s\S]*image\/jpeg[\s\S]*video\/quicktime/);
  assert.doesNotMatch(createModal, /URL\.createObjectURL|<img\b|<video\b/);
});

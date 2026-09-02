import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const [viewer, mutation, service, button, styles] = await Promise.all([
  readSource("../src/features/stories/components/HistoriasViewer.jsx"),
  readSource("../src/features/stories/hooks/useEliminarHistoriaMutation.js"),
  readSource("../src/features/stories/services/historias_service.js"),
  readSource("../src/shared/components/primitives/Button.jsx"),
  readSource("../src/index.css"),
]);

test("owner y visitante reciben acciones contextuales mutuamente excluyentes", () => {
  assert.match(viewer, /historiaActual\?\.puede_administrar \? \([\s\S]*aria-label="Eliminar historia"[\s\S]*\) : historiaActual\?\.puede_administrar === false && !mediaError \? \([\s\S]*aria-label="Denunciar historia"/);
  assert.equal((viewer.match(/aria-label="Eliminar historia"/g) || []).length, 1);
  assert.equal((viewer.match(/aria-label="Denunciar historia"/g) || []).length, 1);
  assert.match(viewer, /aria-label="Denunciar historia"[\s\S]*setIsDenunciaOpen\(true\)/);
});

test("contextual y cierre comparten caja, Liquid y alineacion", () => {
  assert.match(viewer, /ml-3 flex shrink-0 items-center gap-2/);
  assert.match(viewer, /const STORY_HEADER_CONTROL_CLASSES =[\s\S]*h-8 min-h-8 w-8 min-w-8 shrink-0 rounded-full p-0/);
  assert.equal((viewer.match(/className=\{STORY_HEADER_CONTROL_CLASSES\}/g) || []).length, 2);
  assert.match(viewer, /className=\{`\$\{STORY_HEADER_CONTROL_CLASSES\} text-sm`\}/);
  assert.match(viewer, /aria-label="Cerrar historias"/);
  assert.match(button, /interactive-bubble interactive-bubble--liquid/);
  assert.match(button, /<InteractiveLiquidLayers \/>/);
  assert.doesNotMatch(viewer, /InteractiveLiquidLayers|interactive-bubble--liquid/);
  assert.match(viewer, /<Trash2[\s\S]*aria-hidden="true"[\s\S]*size=\{17\}[\s\S]*className="text-interactive-on-primary"[\s\S]*\/>/);
  assert.match(viewer, /<span aria-hidden="true" className="text-interactive-on-primary">[\s\S]*✕[\s\S]*<\/span>/);
});

test("eliminar conserva confirmacion, handler, servicio y reconciliacion", () => {
  assert.match(viewer, /onClick=\{handleOpenDeleteConfirmation\}/);
  assert.match(viewer, /setIsDeleteConfirmOpen\(true\)/);
  assert.match(viewer, /await eliminarHistoriaMutation\.mutateAsync\(\{ historiaId, comercioId \}\)/);
  assert.match(viewer, /¿Eliminar esta historia\?/);
  assert.match(service, /httpDelete\(`\/historias\/\$\{historiaId\}`/);
  assert.match(mutation, /queryKeys\.stories\.bySpace/);
  assert.match(mutation, /historias\.filter\(\(historia\) => historia\.id !== historiaId\)/);
  assert.match(mutation, /queryKeys\.stories\.bar\(\)/);
});

test("controles del visor conservan foco y no varian de geometria en active", () => {
  assert.match(viewer, /STORY_HEADER_CONTROL_CLASSES =[\s\S]*active:\[transform:none\]/);
  assert.match(styles, /\.interactive-bubble:focus-visible[\s\S]*outline: 2px solid var\(--bubble-focus\)/);
});

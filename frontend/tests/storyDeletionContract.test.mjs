import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { reconcileStoryDeletion } from "../src/features/stories/components/storyDeletionState.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(here, "..");
const read = (relativePath) =>
  fs.readFileSync(path.join(frontendRoot, relativePath), "utf8");

const historias = [1, 2, 3, 4, 5].map((id) => ({ id }));

test("eliminar la actual conserva la siguiente por identidad", () => {
  const result = reconcileStoryDeletion(historias, 2, 3);
  assert.deepEqual(result.historiasRestantes.map(({ id }) => id), [1, 2, 4, 5]);
  assert.equal(result.nextIndex, 2);
  assert.equal(result.historiasRestantes[result.nextIndex].id, 4);
  assert.equal(result.shouldClose, false);
});

test("eliminar la ultima selecciona la anterior y eliminar la unica cierra", () => {
  const last = reconcileStoryDeletion(historias, 4, 5);
  assert.equal(last.nextIndex, 3);
  assert.equal(last.historiasRestantes[last.nextIndex].id, 4);

  const only = reconcileStoryDeletion([{ id: 9 }], 0, 9);
  assert.deepEqual(only.historiasRestantes, []);
  assert.equal(only.shouldClose, true);
});

test("viewer usa la historia vigente, confirmacion compartida y no hace fetch directo", () => {
  const viewer = read("src/features/stories/components/HistoriasViewer.jsx");
  assert.match(viewer, /historiaActual\?\.puede_administrar/);
  assert.match(viewer, /const historiaId = historiaActual\?\.id/);
  assert.match(viewer, /<ActiveLayer/);
  assert.match(viewer, /¿Eliminar esta historia\?/);
  assert.match(viewer, /eliminarHistoriaMutation\.isPending/);
  assert.doesNotMatch(viewer, /fetch\s*\(/);
});

test("mutation reconcilia cache por espacio e invalida barra despues del backend", () => {
  const mutation = read("src/features/stories/hooks/useEliminarHistoriaMutation.js");
  assert.match(mutation, /queryKeys\.stories\.bySpace/);
  assert.match(mutation, /historia\.id !== historiaId/);
  assert.match(mutation, /queryKeys\.stories\.bar\(\)/);
  assert.match(mutation, /onSuccess/);
  assert.doesNotMatch(mutation, /onMutate/);
});

test("Feed y Perfil eliminan por ID de sus listas locales", () => {
  for (const file of [
    "src/features/feed/pages/FeedPage.jsx",
    "src/features/spaces/pages/PerfilComercioPage.jsx",
  ]) {
    const source = read(file);
    assert.match(source, /onHistoriaDeleted=\{handleHistoriaDeleted\}/);
    assert.match(source, /historia\.id !== historiaId/);
  }
});

test("la eliminacion conserva cleanup multimedia existente", () => {
  const viewer = read("src/features/stories/components/HistoriasViewer.jsx");
  const confirmation = viewer.slice(viewer.indexOf("async function handleConfirmDelete"));
  assert.match(confirmation, /pausarVideoActivo\(\)/);
  assert.match(confirmation, /limpiarErrorAdvanceTimeout\(\)/);
  assert.match(confirmation, /limpiarRaf\(\)/);
});

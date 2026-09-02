import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { reconcileStoryDeletion } from "../src/features/stories/components/storyDeletionState.js";
import { resolveStoryMediaFailure } from "../src/features/stories/components/storyMediaFailureState.js";
import { reconcileStoriesBarAfterDeletion } from "../src/features/stories/hooks/storyBarCache.js";

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

test("mutation reconcilia directamente espacio y barra sin refetch inmediato", () => {
  const mutation = read("src/features/stories/hooks/useEliminarHistoriaMutation.js");
  assert.match(mutation, /queryKeys\.stories\.bySpace/);
  assert.match(mutation, /historia\.id !== historiaId/);
  assert.match(mutation, /queryKeys\.stories\.bar\(\)/);
  assert.match(mutation, /reconcileStoriesBarAfterDeletion/);
  assert.match(mutation, /refetchType: "none"/);
  assert.match(mutation, /onSuccess/);
  assert.doesNotMatch(mutation, /onMutate/);
});

test("propietario conserva una historia rota y visitante avanza una sola vez", () => {
  const stories = [{ id: 1 }, { id: 2 }, { id: 3 }];
  const owner = resolveStoryMediaFailure({
    historias: stories,
    indexActual: 0,
    failedIds: new Set(),
    puedeAdministrar: true,
  });
  assert.equal(owner.shouldStay, true);
  assert.equal(owner.nextIndex, 0);

  const visitor = resolveStoryMediaFailure({
    historias: stories,
    indexActual: 0,
    failedIds: new Set(),
    puedeAdministrar: false,
  });
  assert.equal(visitor.shouldStay, false);
  assert.equal(visitor.shouldClose, false);
  assert.equal(visitor.nextIndex, 1);
});

test("visitante cierra cuando todas las historias restantes fallaron", () => {
  const result = resolveStoryMediaFailure({
    historias: [{ id: 1 }, { id: 2 }],
    indexActual: 1,
    failedIds: new Set([1]),
    puedeAdministrar: false,
  });
  assert.equal(result.shouldClose, true);
  assert.deepEqual([...result.failedIds], [1, 2]);
});

test("visitante descarta A, B y C una sola vez y cierra sin avances pendientes", () => {
  const historias = [{ id: "A" }, { id: "B" }, { id: "C" }];
  const idsMontados = [];
  const originalSetTimeout = globalThis.setTimeout;
  let timersProgramados = 0;
  let indexActual = 0;
  let failedIds = new Set();
  let resultado;

  globalThis.setTimeout = () => {
    timersProgramados += 1;
    return Symbol("unexpected-story-failure-timer");
  };

  try {
    while (indexActual !== -1) {
      const historiaActual = historias[indexActual];
      idsMontados.push(historiaActual.id);

      resultado = resolveStoryMediaFailure({
        historias,
        indexActual,
        failedIds,
        puedeAdministrar: false,
      });
      failedIds = resultado.failedIds;

      if (resultado.shouldClose) break;
      indexActual = resultado.nextIndex;
    }
  } finally {
    globalThis.setTimeout = originalSetTimeout;
  }

  assert.deepEqual(idsMontados, ["A", "B", "C"]);
  assert.equal(new Set(idsMontados).size, idsMontados.length);
  assert.deepEqual([...failedIds], ["A", "B", "C"]);
  assert.equal(resultado.shouldClose, true);
  assert.equal(resultado.nextIndex, -1);
  assert.equal(timersProgramados, 0);
});

test("eliminar decrementa barra y retira la ultima burbuja", () => {
  const items = [
    { comercioId: 6, cantidad: 2, pendientes: 2 },
    { comercioId: 7, cantidad: 4, pendientes: 1 },
  ];
  assert.deepEqual(reconcileStoriesBarAfterDeletion(items, 6), [
    { comercioId: 6, cantidad: 1, pendientes: 1 },
    items[1],
  ]);
  assert.deepEqual(
    reconcileStoriesBarAfterDeletion([{ comercioId: 6, cantidad: 1, pendientes: 1 }], 6),
    []
  );
});

test("fallo multimedia propio conserva mensaje, eliminar y limpieza sin timeout", () => {
  const viewer = read("src/features/stories/components/HistoriasViewer.jsx");
  const failureHandler = viewer.slice(
    viewer.indexOf("const manejarFalloMultimedia"),
    viewer.indexOf("// Reset fuerte al abrir")
  );
  assert.match(viewer, /El archivo de esta historia no está disponible/);
  assert.match(viewer, /mediaError && historiaActual\?\.puede_administrar/);
  assert.match(failureHandler, /limpiarRaf\(\)/);
  assert.doesNotMatch(failureHandler, /setTimeout|programarAvancePorError|errorAdvanceTimeoutRef/);
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
  assert.match(confirmation, /limpiarRaf\(\)/);
});

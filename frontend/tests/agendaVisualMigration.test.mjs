import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const [general, privateAgenda, hooks, service, activeLayer] = await Promise.all([
  readSource("../src/features/agenda/components/AgendaGeneralModal.jsx"),
  readSource("../src/features/agenda/components/AgendaPrivadaModal.jsx"),
  readSource("../src/features/agenda/hooks/useFeedGoAgenda.js"),
  readSource("../src/features/agenda/services/feedgo_agenda_service.js"),
  readSource("../src/core/components/ActiveLayer.jsx"),
]);

test("Agenda general y privada reutilizan ActiveLayer y shell semantico", () => {
  for (const source of [general, privateAgenda]) {
    assert.match(source, /<ActiveLayer/);
    assert.match(source, /backdropClassName="bg-overlay-backdrop"/);
    assert.match(source, /border-border bg-surface-elevated text-primary shadow-elevation/);
    assert.match(source, /labelledBy="agenda-/);
    assert.match(source, /describedBy="agenda-/);
  }
  assert.match(activeLayer, /createPortal/);
  assert.match(activeLayer, /lockBodyScroll/);
  assert.match(activeLayer, /event\.key === "Escape"/);
  assert.match(activeLayer, /event\.key !== "Tab"/);
});

test("Agenda general migra filtros, fecha, estados y listado", () => {
  assert.match(general, /<Input[\s\S]*type="date"/);
  assert.ok((general.match(/<Select\b/g) || []).length >= 3);
  assert.match(general, /<Skeleton\b/);
  assert.match(general, /<Alert variant="danger" role="alert"/);
  assert.match(general, /<Surface[\s\S]*as="article"/);
  assert.match(general, /<AgendaPrivadaModal/);
});

test("Agenda privada migra formulario y acciones con roles funcionales", () => {
  assert.ok((privateAgenda.match(/<Input\b/g) || []).length >= 4);
  assert.ok((privateAgenda.match(/<Select\b/g) || []).length >= 3);
  assert.match(privateAgenda, /<Textarea\b/);
  assert.match(privateAgenda, /variant="primary"/);
  assert.match(privateAgenda, /variant="secondary"/);
  assert.match(privateAgenda, /variant="success"/);
  assert.match(privateAgenda, /variant="danger"/);
  assert.match(privateAgenda, /<Alert variant="warning"/);
  assert.match(privateAgenda, /<Skeleton\b/);
  assert.doesNotMatch(privateAgenda, /<button\b|interactive-bubble/);
});

test("estados permanecen textuales ademas de sus roles visuales", () => {
  for (const state of ["activo", "completado", "cancelado"]) {
    assert.match(privateAgenda, new RegExp(state));
    assert.match(general, new RegExp(state));
  }
  assert.match(privateAgenda, /Archivado|archivado/);
  assert.match(privateAgenda, /Coincide con otros elementos/);
  assert.match(privateAgenda, /Completar/);
  assert.match(privateAgenda, /Cancelar/);
});

test("contratos de fecha, formulario y descarte permanecen", () => {
  assert.match(privateAgenda, /rangoIsoDelDia\(fecha\)/);
  assert.match(privateAgenda, /payloadDesdeForm\(\)/);
  assert.match(privateAgenda, /version_esperada = Number\(form\.version\)/);
  assert.match(privateAgenda, /window\.confirm\("Hay cambios sin guardar/);
  assert.match(privateAgenda, /crearMutation\.mutateAsync\(\{ comercioId, payload \}\)/);
  assert.match(privateAgenda, /actualizarMutation\.mutateAsync/);
  assert.match(privateAgenda, /cambiarEstadoMutation\.mutateAsync/);
  assert.match(general, /rangoIsoDelDia\(fecha\)/);
});

test("query keys, Cache-First e invalidaciones conservan ownership", () => {
  assert.match(hooks, /queryKeys\.agenda\.contexto/);
  assert.match(hooks, /queryKeys\.agenda\.elementos/);
  assert.match(hooks, /queryKeys\.agenda\.general/);
  assert.match(hooks, /placeholderData: \(previousData\) => previousData/g);
  assert.match(hooks, /staleTime: 1000 \* 30/);
  assert.ok((hooks.match(/queryClient\.invalidateQueries/g) || []).length >= 6);
  assert.match(service, /\/feedgo-agenda\/comercios/);
  assert.match(service, /\/feedgo-agenda\/mis\/elementos/);
});

test("Agenda no agrega colores fisicos ni logica manual de tema", () => {
  for (const source of [general, privateAgenda]) {
    assert.doesNotMatch(source, /#[\da-f]{3,8}|\brgb\(|\brgba\(/i);
    assert.doesNotMatch(
      source,
      /(?:bg|text|border|ring|from|via|to)-(?:gray|slate|zinc|neutral|stone|white|black|red|green|emerald|orange|amber|yellow|blue|purple|pink)(?:\/|-\d|\b)/
    );
    assert.doesNotMatch(
      source,
      /useTheme|resolvedTheme|data-theme|dark:|matchMedia\(|localStorage/
    );
  }
});

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function source(path) {
  return readFile(new URL(path, import.meta.url), "utf8");
}

const physicalUiColors =
  /(?:bg|text|border)-(?:white|gray|slate|zinc|neutral|red|amber|emerald)-(?:\d+|\[)|bg-950|text-r-/;
const manualTheme = /resolvedTheme|matchMedia|data-theme|dark:/;

test("detalle migra shell, estados y acciones a owners semanticos", async () => {
  const detail = await source(
    "../src/features/posts/pages/PublicacionDetallePage.jsx"
  );

  assert.match(detail, /bg-canvas text-primary/);
  assert.match(detail, /<Surface as="article"/);
  assert.match(detail, /<Skeleton/);
  assert.match(detail, /<Alert variant="danger" role="alert"/);
  assert.match(detail, /<InteraccionButton[\s\S]*type="like"/);
  assert.match(detail, /<InteraccionButton[\s\S]*type="guardar"/);
  assert.match(detail, /<Button[\s\S]*Denunciar[\s\S]*<\/Button>/);
  assert.doesNotMatch(detail, physicalUiColors);
  assert.doesNotMatch(detail, manualTheme);
});

test("media conserva solo el escenario negro documentado", async () => {
  const detail = await source(
    "../src/features/posts/pages/PublicacionDetallePage.jsx"
  );

  assert.equal((detail.match(/bg-black/g) || []).length, 1);
  assert.match(detail, /<video[\s\S]*playsInline[\s\S]*controls/);
  assert.match(detail, /<img[\s\S]*object-contain/);
  assert.match(detail, /Sin imagen/);
});

test("confirmacion de borrado reutiliza ActiveLayer y Button danger", async () => {
  const detail = await source(
    "../src/features/posts/pages/PublicacionDetallePage.jsx"
  );

  assert.match(detail, /<ActiveLayer[\s\S]*labelledBy="eliminar-publicacion-title"/);
  assert.match(detail, /closeOnBackdrop=\{!isDeletingPublicacion\}/);
  assert.match(detail, /closeOnEscape=\{!isDeletingPublicacion\}/);
  assert.match(detail, /onClick=\{handleConfirmarEliminarPublicacion\}[\s\S]*variant="danger"/);
  assert.match(detail, /onClick=\{handleCancelarEliminarPublicacion\}[\s\S]*variant="secondary"/);
});

test("DenunciaModal reutiliza ActiveLayer, formulario y estados compartidos", async () => {
  const modal = await source(
    "../src/features/moderation/components/DenunciaModal.jsx"
  );

  assert.match(modal, /<ActiveLayer/);
  assert.match(modal, /closeOnBackdrop=\{!isSubmitting\}/);
  assert.match(modal, /closeOnEscape=\{!isSubmitting\}/);
  assert.match(modal, /<Surface[\s\S]*as="form"/);
  assert.match(modal, /<Select/);
  assert.match(modal, /<Textarea/);
  assert.match(modal, /<Alert variant="warning"/);
  assert.match(modal, /<Alert variant="danger" role="alert"/);
  assert.match(modal, /<Alert variant="success" role="status"/);
  assert.doesNotMatch(modal, /document\.body\.style|addEventListener\("keydown"/);
  assert.doesNotMatch(modal, physicalUiColors);
  assert.doesNotMatch(modal, manualTheme);
});

test("denuncia preserva payload, limites y estados de submit", async () => {
  const modal = await source(
    "../src/features/moderation/components/DenunciaModal.jsx"
  );
  const service = await source(
    "../src/features/moderation/services/denuncias_service.js"
  );

  assert.match(modal, /recurso_tipo: recursoTipo/);
  assert.match(modal, /recurso_id: Number\(recursoId\)/);
  assert.match(modal, /motivo,[\s\S]*detalle,/);
  assert.match(modal, /DENUNCIA_DETALLE_MAX_LENGTH/);
  assert.match(modal, /!puedeEnviar \|\| isSubmitting \|\| Boolean\(successMessage\)/);
  assert.match(service, /\/moderacion\/denuncias/);
});

test("detalle preserva query cache e interacciones sociales", async () => {
  const detail = await source(
    "../src/features/posts/pages/PublicacionDetallePage.jsx"
  );
  const hook = await source("../src/features/posts/hooks/usePublicacionDetalle.js");

  assert.match(hook, /queryKeys\.posts\.detalle\(Number\(publicacionId\)\)/);
  assert.match(hook, /staleTime: 1000 \* 30/);
  assert.match(detail, /useToggleLikePublicacionMutation/);
  assert.match(detail, /useToggleGuardadoPublicacionMutation/);
  assert.match(detail, /setLiked\(snapshotLiked\)/);
  assert.match(detail, /setGuardada\(snapshotGuardada\)/);
});

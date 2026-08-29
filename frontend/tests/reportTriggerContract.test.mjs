import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const [detail, profile, viewer, modal, button] = await Promise.all([
  readSource("../src/features/posts/pages/PublicacionDetallePage.jsx"),
  readSource("../src/features/spaces/pages/PerfilComercioPage.jsx"),
  readSource("../src/features/stories/components/HistoriasViewer.jsx"),
  readSource("../src/features/moderation/components/DenunciaModal.jsx"),
  readSource("../src/shared/components/primitives/Button.jsx"),
]);

test("los tres disparadores publicos muestran solo puntos con nombre especifico", () => {
  for (const [source, label] of [
    [detail, "Denunciar publicación"],
    [profile, "Denunciar espacio"],
    [viewer, "Denunciar historia"],
  ]) {
    assert.match(source, new RegExp(`aria-label="${label}"[\\s\\S]*aria-hidden="true"[\\s\\S]*>\\s*\\.\\.\\.\\s*<\\/span>`));
  }

  assert.doesNotMatch(detail, />\s*Denunciar\s*<\/Button>/);
  assert.doesNotMatch(profile, />\s*Denunciar\s*<\/span>/);
  assert.doesNotMatch(viewer, />\s*Denunciar\s*<\/(?:button|Button)>/);
});

test("los disparadores conservan handlers, recurso e id", () => {
  assert.match(detail, /onClick=\{\(\) => setIsDenunciaOpen\(true\)\}/);
  assert.match(detail, /recursoTipo=\{RECURSO_DENUNCIA_PUBLICACION\}[\s\S]*recursoId=\{publicacionVisible\?\.id\}/);
  assert.match(profile, /onClick=\{\(\) => setIsDenunciaComercioOpen\(true\)\}/);
  assert.match(profile, /recursoTipo=\{RECURSO_DENUNCIA_COMERCIO\}[\s\S]*recursoId=\{comercio\?\.id\}/);
  assert.match(viewer, /setIsDenunciaOpen\(true\)/);
  assert.match(viewer, /recursoTipo=\{RECURSO_DENUNCIA_HISTORIA\}[\s\S]*recursoId=\{historiaActual\?\.id\}/);
});

test("ownership demostrado oculta publicacion, espacio e historia desde owners vigentes", () => {
  assert.match(detail, /useComercioDetalle\(comercioId\)/);
  assert.match(detail, /comercioOwnershipQuery\.data\?\.es_propietario/);
  assert.match(detail, /!esPropietarioPublicacion \? \([\s\S]*aria-label="Denunciar publicación"/);
  assert.match(profile, /!esComercioMio\(comercio\)[\s\S]*aria-label="Denunciar espacio"/);
  assert.match(profile, /Boolean\(comercioData\?\.es_propietario\)/);
  assert.match(viewer, /historiaActual\?\.puede_administrar === false[\s\S]*aria-label="Denunciar historia"/);
});

test("centrado, Liquid y texto adaptativo pertenecen al Button compartido", () => {
  for (const source of [detail, profile, viewer]) {
    assert.match(source, /inline-flex h-full w-full items-center justify-center text-lg leading-none text-primary/);
  }
  assert.match(button, /interactive-bubble interactive-bubble--liquid/);
  assert.match(button, /iconOnly && "h-10 w-10 shrink-0 rounded-full p-0"/);
});

test("el contenido y las acciones internas del modal permanecen intactos", () => {
  assert.match(modal, /id="denuncia-modal-title"/);
  assert.match(modal, /aria-label="Cerrar denuncia"/);
  assert.match(modal, /\{isSubmitting \? "Enviando\.\.\." : "Enviar denuncia"\}/);
  assert.match(modal, /recurso_tipo: recursoTipo/);
  assert.match(modal, /recurso_id: Number\(recursoId\)/);
  assert.doesNotMatch(modal, /aria-label="Denunciar (?:publicación|espacio|historia)"/);
});

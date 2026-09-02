import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const [detail, feed, card, publicationReport, profile, viewer, modal, button] = await Promise.all([
  readSource("../src/features/posts/pages/PublicacionDetallePage.jsx"),
  readSource("../src/features/feed/pages/FeedPage.jsx"),
  readSource("../src/features/posts/components/PublicacionCard.jsx"),
  readSource("../src/features/moderation/components/PublicacionReportControl.jsx"),
  readSource("../src/features/spaces/pages/PerfilComercioPage.jsx"),
  readSource("../src/features/stories/components/HistoriasViewer.jsx"),
  readSource("../src/features/moderation/components/DenunciaModal.jsx"),
  readSource("../src/shared/components/primitives/Button.jsx"),
]);

test("los tres disparadores publicos muestran solo puntos con nombre especifico", () => {
  for (const [source, label] of [
    [publicationReport, "Denunciar publicación"],
    [profile, "Denunciar espacio"],
    [viewer, "Denunciar historia"],
  ]) {
    assert.match(source, new RegExp(`aria-label="${label}"[\\s\\S]*aria-hidden="true"[\\s\\S]*>\\s*\\.\\.\\.\\s*<\\/span>`));
  }

  assert.doesNotMatch(publicationReport, />\s*Denunciar\s*<\/Button>/);
  assert.doesNotMatch(profile, />\s*Denunciar\s*<\/span>/);
  assert.doesNotMatch(viewer, />\s*Denunciar\s*<\/(?:button|Button)>/);
});

test("los disparadores conservan handlers, recurso e id", () => {
  assert.match(publicationReport, /onClick=\{\(\) => setIsOpen\(true\)\}/);
  assert.match(publicationReport, /recursoTipo=\{RECURSO_DENUNCIA_PUBLICACION\}[\s\S]*recursoId=\{publicacionId\}/);
  assert.match(profile, /onClick=\{\(\) => setIsDenunciaComercioOpen\(true\)\}/);
  assert.match(profile, /recursoTipo=\{RECURSO_DENUNCIA_COMERCIO\}[\s\S]*recursoId=\{comercio\?\.id\}/);
  assert.match(viewer, /setIsDenunciaOpen\(true\)/);
  assert.match(viewer, /recursoTipo=\{RECURSO_DENUNCIA_HISTORIA\}[\s\S]*recursoId=\{historiaActual\?\.id\}/);
});

test("ownership demostrado oculta publicacion, espacio e historia desde owners vigentes", () => {
  assert.match(detail, /useComercioDetalle\(comercioId\)/);
  assert.match(detail, /comercioOwnershipQuery\.data\?\.es_propietario/);
  assert.match(detail, /comercioOwnershipQuery\.isSuccess && !esPropietarioPublicacion \? \([\s\S]*<PublicacionReportControl/);
  assert.equal((feed.match(/useMisComercios\(/g) || []).length, 1);
  assert.match(feed, /new Set\(misComercios\.map\(\(comercio\) => Number\(comercio\.id\)\)\)/);
  assert.match(feed, /!estaAutenticado \|\|[\s\S]*misComerciosLoaded[\s\S]*!misComerciosIds\.has\(Number\(p\.comercio_id\)\)/);
  assert.doesNotMatch(card, /useComercioDetalle|useMisComercios/);
  assert.match(profile, /!esComercioMio\(comercio\) && comercio\?\.id[\s\S]*aria-label="Denunciar espacio"/);
  assert.match(profile, /Boolean\(comercioData\?\.es_propietario\)/);
  assert.match(viewer, /historiaActual\?\.puede_administrar === false[\s\S]*aria-label="Denunciar historia"/);
});

test("denuncia de espacio comparte fila con Volver sin reservar lugar al propietario", () => {
  assert.match(profile, /mb-4 flex items-center justify-end gap-2/);
  assert.match(profile, /aria-label="Denunciar espacio"[\s\S]*h-6 min-h-6 w-6 min-w-6 shrink-0 rounded-full p-0[\s\S]*← Volver/);
  assert.equal((profile.match(/aria-label="Denunciar espacio"/g) || []).length, 1);
  assert.doesNotMatch(profile, /\+Seguir[\s\S]*aria-label="Denunciar espacio"/);
});

test("centrado, Liquid y texto adaptativo pertenecen al Button compartido", () => {
  assert.match(publicationReport, /ml-auto h-\[34px\] min-h-\[34px\] w-\[34px\] min-w-\[34px\][\s\S]*text-interactive-on-primary/);
  assert.match(publicationReport, /inline-flex h-full w-full items-center justify-center text-base leading-none text-interactive-on-primary/);
  assert.match(profile, /inline-flex h-full w-full items-center justify-center text-\[12\.6px\] leading-none text-primary/);
  assert.match(viewer, /inline-flex h-full w-full items-center justify-center text-lg leading-none text-interactive-on-primary/);
  assert.match(button, /interactive-bubble interactive-bubble--liquid/);
  assert.match(button, /iconOnly && "h-10 w-10 shrink-0 rounded-full p-0"/);
});

test("Feed y detalle reutilizan un unico owner de denuncia de publicacion", () => {
  assert.match(card, /<InteraccionButton[\s\S]*type="guardar"[\s\S]*<PublicacionReportControl publicacionId=\{pub\?\.id\} \/>[\s\S]*<\/div>/);
  assert.match(detail, /flex flex-wrap items-center gap-3[\s\S]*type="guardar"[\s\S]*<PublicacionReportControl/);
  assert.match(card, /<PublicacionReportControl publicacionId=\{pub\?\.id\} \/>/);
  assert.match(detail, /<PublicacionReportControl publicacionId=\{publicacionVisible\?\.id\} \/>/);
  assert.equal((publicationReport.match(/<DenunciaModal\b/g) || []).length, 1);
  assert.equal((detail.match(/<DenunciaModal\b/g) || []).length, 0);
  assert.equal((card.match(/<DenunciaModal\b/g) || []).length, 0);
  assert.match(card, /showReportTrigger \? \([\s\S]*<PublicacionReportControl/);
  assert.match(modal, /const puedeEnviar = Boolean\(accessToken && motivo && recursoTipo && recursoId\)/);
});

test("el contenido y las acciones internas del modal permanecen intactos", () => {
  assert.match(modal, /id="denuncia-modal-title"/);
  assert.match(modal, /aria-label="Cerrar denuncia"/);
  assert.match(modal, /\{isSubmitting \? "Enviando\.\.\." : "Enviar denuncia"\}/);
  assert.match(modal, /recurso_tipo: recursoTipo/);
  assert.match(modal, /recurso_id: Number\(recursoId\)/);
  assert.doesNotMatch(modal, /aria-label="Denunciar (?:publicación|espacio|historia)"/);
});

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function source(path) {
  return readFile(new URL(path, import.meta.url), "utf8");
}

const forbiddenVisuals =
  /(?:bg|text|border)-(?:white|black|gray|slate|zinc|neutral|stone|orange|amber|red|green|blue)-|#[0-9a-f]{3,8}|rgba?\(/i;
const manualTheme = /resolvedTheme|localStorage|matchMedia|data-theme|dark:/;

test("el shell legal usa Surface, Alert y roles semanticos", async () => {
  const layout = await source(
    "../src/features/legal/components/LegalDocumentLayout.jsx"
  );

  assert.match(layout, /import \{ Alert, Surface \} from "@shared"/);
  assert.match(layout, /<Surface as="article" variant="elevated"/);
  assert.match(layout, /<Alert variant="warning"/);
  assert.match(layout, /text-primary/);
  assert.match(layout, /text-secondary/);
  assert.match(layout, /border-border/);
  assert.doesNotMatch(layout, forbiddenVisuals);
  assert.doesNotMatch(layout, manualTheme);
});

test("Terminos y Privacidad conservan secciones y headings semanticos", async () => {
  const terms = await source("../src/features/legal/pages/TermsPage.jsx");
  const privacy = await source(
    "../src/features/legal/pages/PrivacyPolicyPage.jsx"
  );

  for (const document of [terms, privacy]) {
    assert.match(document, /<section>/);
    assert.match(document, /<h2 className="mb-2 text-lg font-semibold text-primary"/);
    assert.doesNotMatch(document, forbiddenVisuals);
    assert.doesNotMatch(document, manualTheme);
  }
  assert.match(terms, /T.rminos y Condiciones/);
  assert.match(privacy, /Pol.tica de Privacidad/);
});

test("los links legales conservan semantica, destino y foco visible", async () => {
  const layout = await source(
    "../src/features/legal/components/LegalDocumentLayout.jsx"
  );
  const register = await source("../src/features/auth/pages/Registro.jsx");

  assert.match(layout, /<Link[\s\S]*to="\/registro"/);
  assert.match(layout, /underline/);
  assert.match(layout, /focus-visible:ring-focus-ring/);
  assert.equal((register.match(/target="_blank"/g) || []).length, 2);
  assert.match(register, /\/terminos-y-condiciones/);
  assert.match(register, /\/politica-de-privacidad/);
});

test("versionado y aceptaciones permanecen en sus owners", async () => {
  const layout = await source(
    "../src/features/legal/components/LegalDocumentLayout.jsx"
  );
  const hook = await source("../src/features/legal/hooks/useLegalDocument.js");
  const service = await source(
    "../src/features/legal/services/legalDocumentsService.js"
  );
  const register = await source("../src/features/auth/pages/Registro.jsx");

  assert.match(layout, /document\.version/);
  assert.match(hook, /queryKey: \["legal", "documents", "current"\]/);
  assert.match(service, /\/usuarios\/documentos-vigentes/);
  assert.match(register, /useState\(false\)[\s\S]*aceptaTerminos/);
  assert.match(register, /useState\(false\)[\s\S]*aceptaPrivacidad/);
  assert.match(register, /!aceptaTerminos \|\| !aceptaPrivacidad/);
});

test("las rutas legales publicas permanecen separadas bajo MainLayout", async () => {
  const router = await source("../src/core/router/AppRouter.jsx");

  assert.match(router, /<Route element=\{<MainLayout \/>\}>/);
  assert.match(router, /path="\/terminos-y-condiciones" element=\{<TermsPage \/>\}/);
  assert.match(
    router,
    /path="\/politica-de-privacidad" element=\{<PrivacyPolicyPage \/>\}/
  );
});

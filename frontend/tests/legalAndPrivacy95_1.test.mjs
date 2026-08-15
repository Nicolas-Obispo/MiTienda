import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function source(path) {
  return readFile(new URL(path, import.meta.url), "utf8");
}

test("Términos y Política son rutas públicas separadas", async () => {
  const router = await source("../src/core/router/AppRouter.jsx");
  assert.match(router, /\/terminos-y-condiciones/);
  assert.match(router, /\/politica-de-privacidad/);
  assert.match(router, /TermsPage/);
  assert.match(router, /PrivacyPolicyPage/);
});

test("registro conserva checkboxes separados y abre documentos sin perder formulario", async () => {
  const register = await source("../src/features/auth/pages/Registro.jsx");
  assert.match(register, /aceptaTerminos/);
  assert.match(register, /aceptaPrivacidad/);
  assert.equal((register.match(/target="_blank"/g) || []).length, 2);
  assert.doesNotMatch(register, /geolocation|getCurrentPosition|watchPosition/);
});

test("versión visible proviene del owner backend", async () => {
  const service = await source("../src/features/legal/services/legalDocumentsService.js");
  const hook = await source("../src/features/legal/hooks/useLegalDocument.js");
  assert.match(service, /\/usuarios\/documentos-vigentes/);
  assert.match(hook, /getCurrentLegalDocuments/);
  assert.doesNotMatch(service, /version\s*:\s*["']v1/);
});

test("documentos no inventan identidad institucional", async () => {
  const terms = await source("../src/features/legal/pages/TermsPage.jsx");
  const privacy = await source("../src/features/legal/pages/PrivacyPolicyPage.jsx");
  for (const document of [terms, privacy]) {
    assert.match(document, /pendiente/i);
    assert.doesNotMatch(document, /CUIT\s*\d/i);
    assert.doesNotMatch(document, /@feedgo/i);
  }
  assert.match(privacy, /Geoapify/);
  assert.match(privacy, /sin historial/i);
});

test("formulario administra privacidad con default público e invalida caches", async () => {
  const profile = await source("../src/features/auth/pages/ProfilePage.jsx");
  assert.match(profile, /mostrar_direccion_publicamente:\s*true/);
  assert.match(profile, /Mostrar mi dirección públicamente/);
  assert.match(profile, /queryKeys\.explore\.all/);
  assert.match(profile, /\["spaces", "seguidos"\]/);
});

test("detalle muestra ciudad privada y solo ofrece Cómo llegar con datos públicos", async () => {
  const detail = await source("../src/features/spaces/pages/PerfilComercioPage.jsx");
  assert.match(detail, /comercio\?\.ciudad/);
  assert.match(detail, /comercio\?\.direccion/);
  assert.match(detail, /comercio\?\.latitud.*comercio\?\.longitud/);
  assert.match(detail, /Cómo llegar/);
});

test("atribución territorial es genérica y no expone proveedor en el owner", async () => {
  const controls = await source("../src/shared/components/GeographicContextControls.jsx");
  const context = await source("../src/shared/location/GeographicContext.jsx");
  assert.match(controls, /context\.attribution/);
  assert.doesNotMatch(context, /geoapify|nominatim/i);
});

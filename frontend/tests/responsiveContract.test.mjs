import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const [button, alert, surface, controls, activeLayer, mainLayout, explore, followed, profile, spaceProfile, publicationCard, locationPicker, legal] =
  await Promise.all([
    readSource("../src/shared/components/primitives/Button.jsx"),
    readSource("../src/shared/components/primitives/Alert.jsx"),
    readSource("../src/shared/components/primitives/Surface.jsx"),
    readSource("../src/shared/components/primitives/FormControls.jsx"),
    readSource("../src/core/components/ActiveLayer.jsx"),
    readSource("../src/shared/layouts/MainLayout.jsx"),
    readSource("../src/features/explore/pages/ExplorarPage.jsx"),
    readSource("../src/features/spaces/pages/VerSeguidosPage.jsx"),
    readSource("../src/features/auth/pages/ProfilePage.jsx"),
    readSource("../src/features/spaces/pages/PerfilComercioPage.jsx"),
    readSource("../src/features/posts/components/PublicacionCard.jsx"),
    readSource("../src/shared/components/LocationPicker.jsx"),
    readSource("../src/features/legal/components/LegalDocumentLayout.jsx"),
  ]);

test("primitives permiten contraccion y contenido largo sin ocultarlo", () => {
  assert.match(surface, /min-w-0 rounded-2xl border/);
  assert.match(controls, /min-w-0 w-full rounded-xl border/);
  assert.match(button, /max-w-full whitespace-normal break-words text-center/);
  assert.match(alert, /min-w-0 break-words rounded-xl/);
});

test("ActiveLayer mantiene contenido alto accesible dentro del viewport", () => {
  assert.match(activeLayer, /items-start justify-center overflow-y-auto overscroll-contain/);
  assert.match(activeLayer, /relative z-10 my-auto outline-none/);
});

test("MainLayout controla overflow de navegacion sin ocultarlo globalmente", () => {
  assert.match(mainLayout, /min-w-0 flex-1 items-center gap-2 overflow-x-auto/);
  assert.doesNotMatch(mainLayout, /overflow-x-hidden/);
});

test("headers y tabs largos apilan o envuelven en movil", () => {
  assert.match(explore, /flex flex-col items-start gap-3 sm:flex-row/);
  assert.match(explore, /flex max-w-full flex-wrap items-center gap-2/);
  assert.match(followed, /flex flex-wrap gap-2/);
});

test("cards flexibles reservan media y contraen texto", () => {
  assert.match(followed, /h-16 w-16 shrink-0/);
  assert.match(followed, /min-w-0 flex-1/);
  assert.match(profile, /h-16 w-16 shrink-0/);
  assert.match(profile, /min-w-0 flex-1/);
  assert.match(publicationCard, /max-w-32 truncate[^"]*sm:max-w-48/);
});

test("perfil de espacio usa ancho valido y metadata envolvente", () => {
  assert.match(spaceProfile, /max-w-5xl/);
  assert.doesNotMatch(spaceProfile, /max-w-5x1|flex-nowrap/);
  assert.match(spaceProfile, /mt-3 flex flex-wrap items-center gap-1/);
  assert.match(spaceProfile, /max-w-full break-words rounded-full/);
});

test("mapa y documentos legales permanecen contenidos", () => {
  assert.match(locationPicker, /h-72 overflow-hidden rounded-xl border/);
  assert.match(legal, /mx-auto w-full max-w-3xl px-4/);
});

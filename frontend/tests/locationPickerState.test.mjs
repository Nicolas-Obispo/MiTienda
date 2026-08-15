import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  acceptDraftAddress,
  applyAddressProposal,
  canConfirmLocation,
  confirmLocation,
  createLocationDraft,
  invalidateLocationAfterAddressEdit,
  isCurrentOperation,
  selectCoordinates,
  selectSearchResult,
  updateDraftAddress,
} from "../src/shared/components/locationPickerState.js";

test("la referencia inicial no confirma ubicacion", () => {
  const draft = createLocationDraft();

  assert.equal(draft.mode, "reference");
  assert.equal(canConfirmLocation(draft), false);
  assert.equal(confirmLocation(draft), null);
});

test("una sugerencia solo se selecciona mediante accion explicita", () => {
  const initial = createLocationDraft({ direccion: "Sgto. Cabral 159" });
  const results = [
    { latitud: -31.25, longitud: -61.48, label: "Alternativa 1" },
    {
      latitud: -31.26,
      longitud: -61.49,
      label: "Alternativa 2",
      precision: "street",
      confidence: 0.72,
    },
  ];

  assert.equal(initial.latitude, null);
  const selected = selectSearchResult(initial, results[1]);
  assert.equal(selected.address, "Alternativa 2");
  assert.deepEqual(selected.position, [-31.26, -61.49]);
  assert.equal(selected.precision, "street");
  assert.equal(selected.confidence, 0.72);
  assert.equal(canConfirmLocation(selected), true);
});

test("click y drag modifican solo el borrador e invalidan coherencia", () => {
  const confirmed = createLocationDraft({
    direccion: "Sgto. Cabral 159",
    latitud: -31.25,
    longitud: -61.48,
  });

  const clicked = selectCoordinates(confirmed, -31.26, -61.49, "map");
  const dragged = selectCoordinates(clicked, -31.27, -61.5, "drag");

  assert.equal(clicked.coherent, false);
  assert.equal(dragged.coherent, false);
  assert.deepEqual(dragged.position, [-31.27, -61.5]);
  assert.equal(confirmLocation(dragged), null);
});

test("revisar direccion habilita confirmacion del conjunto", () => {
  const selected = selectCoordinates(
    createLocationDraft({ direccion: "Sgto. Cabral 159" }),
    -31.26,
    -61.49,
    "map"
  );
  const reviewed = acceptDraftAddress(selected);

  assert.deepEqual(confirmLocation(reviewed), {
    direccion: "Sgto. Cabral 159",
    latitud: -31.26,
    longitud: -61.49,
  });
});

test("editar direccion invalida coordenadas confirmadas del formulario", () => {
  const canonical = {
    direccion: "Sgto. Cabral 159",
    latitud: -31.25,
    longitud: -61.48,
  };

  const invalidated = invalidateLocationAfterAddressEdit(
    canonical,
    "Sgto. Cabral 245"
  );

  assert.equal(invalidated.direccion, "Sgto. Cabral 245");
  assert.equal(invalidated.latitud, null);
  assert.equal(invalidated.longitud, null);
});

test("editar direccion dentro del selector invalida confirmacion", () => {
  const canonical = createLocationDraft({
    direccion: "Sgto. Cabral 159",
    latitud: -31.25,
    longitud: -61.48,
  });
  const edited = updateDraftAddress(canonical, "Sgto. Cabral 245");

  assert.equal(edited.coherent, false);
  assert.equal(canConfirmLocation(edited), false);
});

test("cancelar y reabrir se reconstruye desde datos canonicos", () => {
  const canonical = {
    direccion: "Sgto. Cabral 159",
    latitud: -31.25,
    longitud: -61.48,
  };
  const draft = selectCoordinates(
    createLocationDraft(canonical),
    -31.3,
    -61.6,
    "drag"
  );
  const reopened = createLocationDraft(canonical);

  assert.notDeepEqual(draft.position, reopened.position);
  assert.equal(reopened.mode, "confirmed");
  assert.deepEqual(reopened.position, [-31.25, -61.48]);
});

test("una respuesta asincrona obsoleta no es vigente", () => {
  assert.equal(isCurrentOperation(4, 3), false);
  assert.equal(isCurrentOperation(4, 4), true);
});

test("una propuesta futura solo aplica al punto que la origino", () => {
  const current = selectCoordinates(
    createLocationDraft(),
    -31.26,
    -61.49,
    "drag"
  );
  const stale = applyAddressProposal(current, {
    direccion: "Direccion anterior",
    latitud: -31.25,
    longitud: -61.48,
  });
  const matching = applyAddressProposal(current, {
    direccion: "Direccion propuesta",
    latitud: -31.26,
    longitud: -61.49,
  });

  assert.equal(stale, current);
  assert.equal(matching.address, "Direccion propuesta");
  assert.equal(matching.coherent, true);
});

test("LocationPicker consume el contrato FeedGo y no conoce Nominatim", async () => {
  const source = await readFile(
    new URL("../src/shared/components/LocationPicker.jsx", import.meta.url),
    "utf8"
  );

  assert.match(source, /buscarDirecciones/);
  assert.match(source, /proponerDireccion/);
  assert.doesNotMatch(source, /nominatim/i);
  assert.doesNotMatch(source, /geoapify/i);
  assert.doesNotMatch(source, /openstreetmap\.org\/search/i);
});

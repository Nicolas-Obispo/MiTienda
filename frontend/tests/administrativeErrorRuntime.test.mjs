import assert from "node:assert/strict";
import test from "node:test";

import { administrativeErrorMessage } from "../src/features/administration/utils/administrativeErrorMessages.js";


test("runtime maps 401 without parsing backend text", () => {
  assert.equal(
    administrativeErrorMessage({ status: 401, detail: "private backend detail" }, "fallback"),
    "La sesión venció. Iniciá sesión nuevamente.",
  );
});

test("runtime maps 403 to an authorization-safe message", () => {
  assert.equal(
    administrativeErrorMessage({ status: 403 }, "fallback"),
    "No tenés permiso para realizar esta operación.",
  );
});

test("runtime maps 404 without exposing resource internals", () => {
  assert.equal(
    administrativeErrorMessage({ status: 404 }, "fallback"),
    "El recurso administrativo ya no existe.",
  );
});

test("runtime maps 409 to explicit refresh guidance", () => {
  assert.equal(
    administrativeErrorMessage({ status: 409 }, "fallback"),
    "El recurso cambió. Actualizá la información antes de continuar.",
  );
});

test("runtime maps 422 to controlled validation feedback", () => {
  assert.equal(
    administrativeErrorMessage({ status: 422 }, "fallback"),
    "Los datos enviados no son válidos.",
  );
});

test("runtime preserves the surface fallback for unexpected failures", () => {
  assert.equal(administrativeErrorMessage({ status: 503 }, "fallback seguro"), "fallback seguro");
  assert.equal(administrativeErrorMessage(undefined, "fallback seguro"), "fallback seguro");
});

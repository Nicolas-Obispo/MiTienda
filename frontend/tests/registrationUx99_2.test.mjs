import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  evaluarPasswordRegistro,
  passwordRegistroValida,
} from "../src/features/auth/services/registrationValidation.js";

const registro = await readFile(
  new URL("../src/features/auth/pages/Registro.jsx", import.meta.url),
  "utf8"
);
const authService = await readFile(
  new URL("../src/features/auth/services/authService.js", import.meta.url),
  "utf8"
);

test("politica visual de password coincide con el contrato ET99.2", () => {
  for (const password of [
    "Prue1a",
    "prueba12",
    "PRUEBA12",
    "PruebaAA",
    "Prue ba1",
    "Prueba\t1",
  ]) {
    assert.equal(passwordRegistroValida(password), false, password);
  }
  assert.equal(passwordRegistroValida("Prueba12"), true);
  assert.equal(evaluarPasswordRegistro("").sinEspacios, false);
  assert.equal(passwordRegistroValida(`Aa1${"x".repeat(69)}`), true);
  assert.equal(passwordRegistroValida(`Aa1${"x".repeat(70)}`), false);
  assert.equal(evaluarPasswordRegistro("Árbol1").mayuscula, true);

  assert.match(registro, /La contraseña debe tener:/);
  assert.match(registro, /Al menos 8 caracteres/);
  assert.match(registro, /Una mayúscula/);
  assert.match(registro, /Una minúscula/);
  assert.match(registro, /Un número/);
  assert.match(registro, /Sin espacios/);
  assert.doesNotMatch(registro, /72 bytes|UTF-8/i);
  assert.match(registro, /La contraseña es demasiado larga\./);
  assert.match(registro, /Las contraseñas no coinciden\./);
  assert.match(registro, /noValidate/);
  assert.doesNotMatch(registro, /minLength=/);
});

test("disponibilidad anticipada cancela y descarta respuestas obsoletas", () => {
  assert.match(authService, /\/usuarios\/email-disponibilidad/);
  assert.match(authService, /signal: options\.signal/);
  assert.match(registro, /checkValidity\(\)/);
  assert.match(registro, /new AbortController\(\)/);
  assert.match(registro, /solicitudEmailRef\.current !== solicitudId/);
  assert.match(registro, /window\.setTimeout\([\s\S]*500/);
  assert.match(registro, /resultado\.disponible \? "available" : "unavailable"/);
});

test("Usuario presenta disponibilidad y formato email con UX inline", () => {
  assert.match(authService, /error\?\.status === 409/);
  assert.match(authService, /REGISTRATION_EMAIL_UNAVAILABLE/);
  assert.match(registro, /label="Usuario"/);
  assert.match(registro, /placeholder="nombre@correo\.com"/);
  assert.match(registro, /Usuario disponible\./);
  assert.match(registro, /Este usuario ya está registrado\. Ingresá otro\./);
  assert.match(registro, /Ingresá un correo electrónico válido\./);
  assert.match(registro, /estadoDisponibilidad === "unavailable"/);
  assert.doesNotMatch(
    registro,
    /Este correo ya está registrado en FeedGo|Usar otro correo|HTTP 409|pertenece a una cuenta/
  );
});

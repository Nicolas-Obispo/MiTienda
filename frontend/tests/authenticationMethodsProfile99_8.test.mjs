import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const profile = await readFile(
  new URL("../src/features/auth/pages/ProfilePage.jsx", import.meta.url),
  "utf8",
);
const securityStart = profile.indexOf('perfilSection === "security"');
const securityEnd = profile.indexOf(') : (\n            <form', securityStart);
const securitySection = profile.slice(securityStart, securityEnd);
const menuStart = profile.indexOf('perfilSection === "menu"');
const menuEnd = profile.indexOf(') : perfilSection === "foto"', menuStart);
const editMenu = profile.slice(menuStart, menuEnd);

test("Seguridad y acceso deriva metodos exclusivamente desde /usuarios/me", () => {
  assert.match(profile, /const authenticationMethods = usuario\?\.authentication_methods \|\| \{\}/);
  assert.match(profile, /authenticationMethods\.has_password === true/);
  assert.match(profile, /authenticationMethods\.google_linked === true/);
  assert.match(profile, /Array\.isArray\(authenticationMethods\.usable_methods\)/);
  assert.match(profile, /authenticationMethods\.can_unlink_google === true/);
  assert.doesNotMatch(profile, /hasPassword \|\| googleLinked/);
});

test("password-only, Google-only y ambos preservan la ramificacion correcta", () => {
  assert.match(securitySection, /hasPassword \? \([\s\S]*<CambiarPasswordForm/);
  assert.match(securitySection, /\) : \([\s\S]*Agregar contraseña/);
  assert.match(securitySection, /googleLinked \? "Vinculada" : "No vinculada"/);
  assert.match(securitySection, /\{googleLinked \? \([\s\S]*\) : googleIdentityAvailable \?/);
  assert.match(securitySection, /canUnlinkGoogle && \([\s\S]*Desvincular Google/);
});

test("Google vinculada conserva estado cuando provider esta OFF y no revela internos", () => {
  assert.match(securitySection, /Google está vinculada, pero no está disponible actualmente\./);
  assert.match(profile, /useGoogleIdentityAvailability/);
  assert.doesNotMatch(securitySection, /provider_subject|snapshot|token|SID|oauth/i);
});

test("el menu sigue teniendo exactamente cuatro opciones y Seguridad reutiliza Cambiar contraseña", () => {
  assert.equal((editMenu.match(/<Button\b/g) || []).length, 5);
  assert.match(editMenu, />\s*Datos personales[\s\S]*>\s*Cambiar foto[\s\S]*>\s*Seguridad y acceso[\s\S]*>\s*Cambiar fondo/);
  assert.doesNotMatch(editMenu, /Vincular Google|Desvincular Google|Agregar contraseña/);
});

test("el owner de perfil usa servicios de auth y no fetch directo", () => {
  assert.match(profile, /addPasswordCredential/);
  assert.match(profile, /startGoogleLinkAuthorization/);
  assert.match(profile, /unlinkGoogleIdentity/);
  assert.match(profile, /reauthenticateWithPassword/);
  assert.match(profile, /startGoogleReauthentication/);
  assert.doesNotMatch(profile, /fetch\s*\(/);
});

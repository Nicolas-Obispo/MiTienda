import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const registro = await readFile(
  new URL("../src/features/auth/pages/Registro.jsx", import.meta.url),
  "utf8"
);
const login = await readFile(
  new URL("../src/features/auth/pages/Login.jsx", import.meta.url),
  "utf8"
);
const authSurfaces = `${registro}\n${login}`;

test("Registro y Login adoptan primitives semanticas", () => {
  for (const source of [registro, login]) {
    for (const primitive of ["Surface", "Button", "FormControl", "Input", "Alert"]) {
      assert.match(source, new RegExp(`<${primitive}\\b`));
    }
    assert.match(source, /bg-canvas/);
    assert.match(source, /text-primary/);
  }
});

test("formularios Auth delegan contraccion responsive en primitives", () => {
  assert.equal((authSurfaces.match(/className="w-full max-w-md p-6"/g) || []).length, 2);
  assert.doesNotMatch(authSurfaces, /min-w-\[|w-\[\d/);
});

test("submits conservan accion, loading y Button primary", () => {
  assert.match(registro, /onSubmit=\{manejarSubmitRegistro\}/);
  assert.match(registro, /disabled=\{cargando\}[\s\S]*variant="primary"/);
  assert.match(registro, /cargando \? "Creando cuenta\.\.\." : "Crear cuenta"/);

  assert.match(login, /onSubmit=\{manejarSubmitLogin\}/);
  assert.match(login, /disabled=\{cargando\}[\s\S]*variant="primary"/);
  assert.match(login, /cargando \? "Ingresando\.\.\." : "Ingresar"/);
  assert.doesNotMatch(authSurfaces, /<button\b/);
  assert.doesNotMatch(authSurfaces, /interactive-bubble/);
});

test("visibilidad de password mantiene controles accesibles", () => {
  assert.equal((authSurfaces.match(/iconOnly/g) || []).length, 3);
  assert.equal((authSurfaces.match(/aria-label=/g) || []).length, 3);
  assert.equal((authSurfaces.match(/aria-hidden="true"/g) || []).length, 3);
  assert.match(registro, /labelFor="registro-password"/);
  assert.match(registro, /id="registro-password"/);
  assert.match(login, /labelFor="login-password"/);
  assert.match(login, /id="login-password"/);
});

test("password toggle usa el slot trailing compartido dentro del Input", () => {
  assert.equal((authSurfaces.match(/trailingAction=/g) || []).length, 3);
  assert.doesNotMatch(authSurfaces, /absolute right-1 top-1\/2|-translate-y-1\/2/);
  assert.doesNotMatch(authSurfaces, /className="pr-12 text-sm"/);
  assert.equal((authSurfaces.match(/variant="ghost"/g) || []).length, 3);
});

test("Registro preserva aceptaciones legales separadas y desmarcadas", () => {
  assert.match(registro, /useState\(false\)[\s\S]*aceptaTerminos/);
  assert.match(registro, /useState\(false\)[\s\S]*aceptaPrivacidad/);
  assert.equal((registro.match(/type="checkbox"/g) || []).length, 2);
  assert.match(registro, /checked=\{aceptaTerminos\}/);
  assert.match(registro, /checked=\{aceptaPrivacidad\}/);
  assert.match(registro, /!aceptaTerminos \|\| !aceptaPrivacidad/);
  assert.match(registro, /aceptaTerminos,[\s\S]*aceptaPrivacidad,/);
});

test("links legales y navegacion conservan semantica de enlace", () => {
  assert.match(registro, /<Link[\s\S]*to="\/terminos-y-condiciones"/);
  assert.match(registro, /<Link[\s\S]*to="\/politica-de-privacidad"/);
  assert.match(registro, /<Link[\s\S]*to="\/login"/);
  assert.match(login, /<Link[\s\S]*to="\/registro"/);
  assert.doesNotMatch(authSurfaces, /asChild|role="link"/);
});

test("errores mantienen texto y semantica contextual", () => {
  assert.equal((authSurfaces.match(/<Alert role="alert"/g) || []).length, 2);
  assert.match(registro, /\{errorMensaje\}/);
  assert.match(login, /\{errorMensaje\}/);
});

test("superficies Auth no contienen tema manual ni colores fisicos evitables", () => {
  assert.doesNotMatch(authSurfaces, /#[\da-f]{3,8}|\brgb\(|\brgba\(/i);
  assert.doesNotMatch(
    authSurfaces,
    /(?:bg|text|border|from|via|to)-(?:gray|white|black|red|green|orange|amber|yellow|purple)-?\d*/
  );
  assert.doesNotMatch(
    authSurfaces,
    /resolvedTheme|data-theme|dark:|matchMedia\(|localStorage\./
  );
});

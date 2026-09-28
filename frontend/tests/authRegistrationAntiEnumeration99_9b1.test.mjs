import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const read = (path) => readFile(new URL(path, import.meta.url), "utf8");

test("Registro no consulta ni comunica disponibilidad de email", async () => {
  const [page, service, exports] = await Promise.all([
    read("../src/features/auth/pages/Registro.jsx"),
    read("../src/features/auth/services/authService.js"),
    read("../src/features/auth/index.js"),
  ]);

  assert.match(page, /registrarUsuario\(/);
  assert.doesNotMatch(page, /comprobarDisponibilidadEmail|estadoDisponibilidad|Usuario disponible|Comprobando correo/i);
  assert.doesNotMatch(service, /email-disponibilidad|REGISTRATION_EMAIL_UNAVAILABLE/);
  assert.doesNotMatch(exports, /comprobarDisponibilidadEmail|REGISTRATION_EMAIL_UNAVAILABLE/);
});

test("Registro no inicia sesión automáticamente y comunica el siguiente paso neutral", async () => {
  const page = await read("../src/features/auth/pages/Registro.jsx");

  assert.match(page, /Si pudimos crear la cuenta, ya podés ingresar\./);
  assert.doesNotMatch(page, /loginUsuario|useAuth|sessionStorage|registrationEmailStatus/);
});

test("todos los flujos que establecen password comunican el límite bcrypt", async () => {
  const sources = await Promise.all([
    read("../src/features/auth/pages/Registro.jsx"),
    read("../src/features/auth/pages/RestablecerPassword.jsx"),
    read("../src/features/auth/components/CambiarPasswordForm.jsx"),
    read("../src/features/auth/pages/ProfilePage.jsx"),
  ]);

  for (const source of sources) {
    assert.match(source, /72 bytes UTF-8/);
  }
});

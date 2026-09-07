import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { getInternalReturnTo } from "../src/core/navigation/internalReturnTo.js";

const root = new URL("../", import.meta.url);
const readText = (path) => readFile(new URL(path, root), "utf8");

test("ET99.6-A centraliza GET /usuarios/me en una query TanStack en memoria", async () => {
  const hook = await readText("src/features/auth/hooks/useCurrentUser.js");
  const keys = await readText("src/core/constants/queryKeys.js");

  assert.match(keys, /users:\s*\{\s*me:\s*\(\)\s*=>\s*\["users", "me"\]/s);
  assert.match(hook, /useQuery\(/);
  assert.match(hook, /queryKey:\s*queryKeys\.users\.me\(\)/);
  assert.match(hook, /queryFn:\s*\(\)\s*=>\s*getMe\(accessToken\)/);
  assert.match(hook, /enabled:\s*Boolean\(accessToken\)/);
  assert.doesNotMatch(hook, /localStorage|sessionStorage|indexedDB/i);
});

test("AuthContext expone la query como fuente única y limpia cache al cambiar sesión", async () => {
  const context = await readText("src/features/auth/context/AuthContext.jsx");

  assert.match(context, /useCurrentUser\(accessToken\)/);
  assert.match(context, /usuario:\s*currentUser\s*\|\|\s*null/);
  assert.doesNotMatch(context, /const\s*\[usuario\s*,\s*setUsuario\]/);
  assert.doesNotMatch(context, /getMe\(/);
  assert.match(context, /queryClient\.clear\(\)/);
  assert.match(context, /refetchCurrentUser\(/);
});

test("ProfilePage consume AuthContext sin copia, fetch ni storage de /me", async () => {
  const page = await readText("src/features/auth/pages/ProfilePage.jsx");

  assert.match(page, /usuario,\s*\n?\s*}\s*=\s*useAuth\(\)/s);
  assert.doesNotMatch(page, /usuarioMe|setUsuarioMe|loadUsuarioMe|getMe\(/);
  assert.doesNotMatch(page, /localStorage|sessionStorage|getToken\(/);
  assert.match(page, /await\s+refrescarUsuario\(\)/);
  assert.match(page, /enabled:\s*Boolean\(accessToken\)/);
});

test("ET99.6-B mantiene Datos personales dentro de /me y deja el teléfono verificado en sólo lectura", async () => {
  const page = await readText("src/features/auth/pages/ProfilePage.jsx");

  assert.match(page, /Datos personales/);
  assert.match(page, /name="fecha_nacimiento"/);
  assert.match(page, /name="telefono_e164"/);
  assert.match(page, /fecha_nacimiento:\s*perfilForm\.fecha_nacimiento/);
  assert.match(page, /telefono_e164:\s*perfilForm\.telefono_e164/);
  assert.match(page, /await\s+actualizarPerfilUsuario\(token, payload\)/);
  assert.match(page, /await\s+refrescarUsuario\(\)/);
  assert.match(page, /disabled=\{isSavingPerfil \|\| Boolean\(usuario\?\.telefono_verified_at\)\}/);
  assert.doesNotMatch(page, /calcularEdad|mayor(?:ía|ia)DeEdad/);
  assert.doesNotMatch(page, /localStorage|sessionStorage|indexedDB|Cache Storage|URLSearchParams/i);
});

test("ET99.6-C delega OTP al backend y no persiste challenge ni código", async () => {
  const page = await readText("src/features/auth/pages/ProfilePage.jsx");
  const service = await readText("src/features/auth/services/authService.js");

  assert.match(page, /solicitarVerificacionTelefono\(accessToken\)/);
  assert.match(page, /confirmarVerificacionTelefono\(accessToken/);
  assert.match(page, /challengeId: ""/);
  assert.match(page, /code: ""/);
  assert.match(page, /Enviar código|Enviar otro código/);
  assert.match(page, /Verificar teléfono/);
  assert.match(page, /await\s+refrescarUsuario\(\)/);
  assert.doesNotMatch(page, /localStorage|sessionStorage|indexedDB|URLSearchParams/i);
  assert.match(service, /\/usuarios\/me\/telefono-verificacion\/reenvio/);
  assert.match(service, /\/usuarios\/me\/telefono-verificacion\/confirmar/);
});

test("ET99.6-D renderiza derivados backend y los traduce sin recalcularlos", async () => {
  const page = await readText("src/features/auth/pages/ProfilePage.jsx");

  assert.match(page, /usuario\?\.perfil_completo === true/);
  assert.match(page, /usuario\.campos_perfil_faltantes/);
  assert.match(page, /usuario\?\.capabilities/);
  assert.match(page, /usuario\.pendientes_comerciales/);
  for (const field of [
    "provincia",
    "ciudad",
    "fecha_nacimiento",
    "email_verificado",
    "telefono",
    "telefono_verificado",
  ]) {
    assert.match(page, new RegExp(`${field}:`));
  }
  assert.doesNotMatch(page, /calcularEdad|mayor(?:ía|ia)DeEdad/);
});

test("returnTo acepta sólo rutas internas y no persiste navegación", () => {
  assert.equal(getInternalReturnTo("/perfil", "/feed"), "/perfil");
  assert.equal(getInternalReturnTo("/verificar-email?from=perfil", "/feed"), "/verificar-email?from=perfil");
  assert.equal(
    getInternalReturnTo("/comercios/4?tab=historias&token=secreto#token=otro", "/feed"),
    "/comercios/4?tab=historias"
  );
  assert.equal(getInternalReturnTo("https://attacker.example", "/feed"), "/feed");
  assert.equal(getInternalReturnTo("//attacker.example", "/feed"), "/feed");
  assert.equal(getInternalReturnTo("\\\\attacker.example", "/feed"), "/feed");
});

test("la cache privada sigue siendo sólo memoria y las APIs autenticadas son network-only", async () => {
  const queryClient = await readText("src/core/query/queryClient.js");
  const classifier = await readText("src/pwa/requestClassifier.js");

  assert.doesNotMatch(queryClient, /persistQueryClient|localStorage|sessionStorage|indexedDB/i);
  assert.match(classifier, /NETWORK_ONLY/);
  assert.match(classifier, /Authorization/i);
});

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { getInternalReturnTo } from "../src/core/navigation/internalReturnTo.js";
import {
  AUTH_TOKEN_STORAGE_KEY,
  getTokenFromStorageEvent,
  removeStoredAuthTokenIfCurrent,
  shouldClearAuthSession,
} from "../src/features/auth/context/authSessionTransition.js";

const root = new URL("../", import.meta.url);
const readText = (path) => readFile(new URL(path, root), "utf8");

test("ET99.6-A centraliza GET /usuarios/me en una query TanStack en memoria", async () => {
  const hook = await readText("src/features/auth/hooks/useCurrentUser.js");
  const keys = await readText("src/core/constants/queryKeys.js");

  assert.match(keys, /me:\s*\(sessionGeneration\)\s*=>/);
  assert.match(keys, /"users",\s*"me"/);
  assert.match(hook, /useQuery\(/);
  assert.match(hook, /queryKey:\s*queryKeys\.users\.me\(sessionGeneration\)/);
  assert.match(hook, /queryFn:\s*\(\{ signal \}\)\s*=>\s*getMe\(accessToken, \{ signal \}\)/);
  assert.match(hook, /enabled:\s*Boolean\(accessToken\)/);
  assert.doesNotMatch(hook, /localStorage|sessionStorage|indexedDB/i);
});

test("dos clientes coordinan token nuevo frente a un 401 tardío del token viejo", async () => {
  const context = await readText("src/features/auth/context/AuthContext.jsx");
  const service = await readText("src/features/auth/services/authService.js");

  const oldToken = "old-invalid-token";
  const newToken = "new-valid-token";
  let storedToken = oldToken;
  let storageWrites = 0;
  const sharedStorage = {
    getItem(key) {
      return key === AUTH_TOKEN_STORAGE_KEY ? storedToken : null;
    },
    setItem(key, value) {
      if (key === AUTH_TOKEN_STORAGE_KEY) storedToken = value;
      storageWrites += 1;
    },
    removeItem(key) {
      if (key === AUTH_TOKEN_STORAGE_KEY) storedToken = null;
      storageWrites += 1;
    },
  };

  const clientA = { token: oldToken, generation: 0 };
  const clientB = { token: oldToken, generation: 0 };
  let loginCount = 0;

  // B completa login y publica la nueva sesión en el storage compartido.
  loginCount += 1;
  sharedStorage.setItem(AUTH_TOKEN_STORAGE_KEY, newToken);
  clientB.token = newToken;
  clientB.generation += 1;

  // La request pendiente de A todavía pertenece a su generación/token viejo.
  assert.equal(
    shouldClearAuthSession(clientA.token, oldToken, clientA.generation, 0),
    true
  );
  assert.equal(removeStoredAuthTokenIfCurrent(sharedStorage, oldToken), false);
  assert.equal(sharedStorage.getItem(AUTH_TOKEN_STORAGE_KEY), newToken);

  // El evento storage adopta la sesión de B sin volver a escribirla (sin loop).
  const writesBeforeStorageEvent = storageWrites;
  const adoptedToken = getTokenFromStorageEvent(
    {
      key: AUTH_TOKEN_STORAGE_KEY,
      oldValue: oldToken,
      newValue: newToken,
      storageArea: sharedStorage,
    },
    sharedStorage
  );
  clientA.token = adoptedToken;
  clientA.generation += 1;
  assert.equal(storageWrites, writesBeforeStorageEvent);

  const privateRequest = (token) => ({ status: token === newToken ? 200 : 401 });
  assert.equal(privateRequest(clientB.token).status, 200);
  assert.equal(privateRequest(sharedStorage.getItem(AUTH_TOKEN_STORAGE_KEY)).status, 200);
  assert.equal(loginCount, 1);

  assert.match(context, /removeStoredAuthTokenIfCurrent\(localStorage, failedToken\)/);
  assert.match(context, /window\.addEventListener\("storage", handleStorage\)/);
  assert.match(context, /activeAccessTokenRef\.current = nextToken/);
  assert.match(context, /advanceSessionGeneration\(\)/);
  assert.doesNotMatch(context, /BroadcastChannel/);
  assert.match(service, /httpGet\("\/usuarios\/me", tokenJWT, \{ signal: options\.signal \}\)/);
});

test("un 401 activo limpia y un logout compartido se propaga sin loops", () => {
  const activeToken = "active-token";
  let storedToken = activeToken;
  let storageWrites = 0;
  const sharedStorage = {
    getItem: () => storedToken,
    removeItem() {
      storedToken = null;
      storageWrites += 1;
    },
  };

  assert.equal(shouldClearAuthSession(activeToken, activeToken, 4, 4), true);
  assert.equal(removeStoredAuthTokenIfCurrent(sharedStorage, activeToken), true);
  assert.equal(storedToken, null);

  const writesBeforeStorageEvent = storageWrites;
  const propagatedLogout = getTokenFromStorageEvent(
    {
      key: AUTH_TOKEN_STORAGE_KEY,
      oldValue: activeToken,
      newValue: null,
      storageArea: sharedStorage,
    },
    sharedStorage
  );
  assert.equal(propagatedLogout, null);
  assert.equal(storageWrites, writesBeforeStorageEvent);
  assert.equal(shouldClearAuthSession("newer-token", activeToken, 5, 4), false);
});

test("AuthContext expone la query como fuente única y limpia cache al cambiar sesión", async () => {
  const context = await readText("src/features/auth/context/AuthContext.jsx");

  assert.match(context, /useCurrentUser\(accessToken, sessionGeneration\)/);
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

test("el teléfono es requerido y el lanzamiento no expone OTP", async () => {
  const page = await readText("src/features/auth/pages/ProfilePage.jsx");
  const service = await readText("src/features/auth/services/authService.js");

  assert.match(page, /Teléfono/);
  assert.doesNotMatch(page, /Teléfono \(opcional\)/);
  assert.match(page, /Este teléfono todavía no está verificado\.|El teléfono es un dato requerido del perfil/i);
  assert.match(page, /telefono: "Agregá tu teléfono\."/);
  assert.doesNotMatch(page, /Enviar código|Enviar otro código|Verificar teléfono|phoneVerification/);
  assert.match(service, /\/usuarios\/me\/telefono-verificacion\/reenvio/);
  assert.match(service, /\/usuarios\/me\/telefono-verificacion\/confirmar/);
});

test("Editar perfil presenta datos personales y asteriscos sólo desde los faltantes backend", async () => {
  const page = await readText("src/features/auth/pages/ProfilePage.jsx");

  assert.match(page, /Correo electrónico/);
  assert.match(page, /usuario\?\.email \|\| "Correo no disponible"/);
  assert.match(page, /iniciarRemediationPerfil\("email_verificado"\)/);
  assert.match(page, /Verificado/);
  assert.match(page, /const esCampoPerfilFaltante = \(campo\) => camposPerfilFaltantes\.includes\(campo\)/);
  for (const field of ["provincia", "ciudad", "fecha_nacimiento", "telefono", "email_verificado"]) {
    assert.match(page, new RegExp(`esCampoPerfilFaltante\\("${field}"\\)`));
  }
  assert.doesNotMatch(page, /esCampoPerfilFaltante\("telefono_verificado"\)/);
  assert.match(page, /Este teléfono todavía no está verificado\./);
  assert.match(page, /editar-perfil-menu-title/);
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
    "telefono",
    "email_verificado",
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

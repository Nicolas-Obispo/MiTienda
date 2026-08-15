import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const [profile, authService, router] = await Promise.all([
  readSource("../src/features/auth/pages/ProfilePage.jsx"),
  readSource("../src/features/auth/services/authService.js"),
  readSource("../src/core/router/AppRouter.jsx"),
]);

const avatarDeclaration = profile.indexOf("const avatarUrl =");
const identityStart = profile.indexOf("return (", avatarDeclaration);
const identityEnd = profile.indexOf("{showPerfilForm && (", identityStart);
const identitySurface = profile.slice(identityStart, identityEnd);

test("la superficie real de identidad de usuario usa shell y owners semanticos", () => {
  assert.match(identitySurface, /min-h-screen bg-canvas text-primary/);
  assert.match(identitySurface, /<Surface as="section"/);
  assert.match(identitySurface, /aria-labelledby="mi-cuenta-title"/);
  assert.match(identitySurface, /border-border-strong bg-surface-subtle/);
  assert.match(identitySurface, /text-secondary/);
  assert.match(identitySurface, /text-muted/);
});

test("avatar permanece contenido y su shell es tematico", () => {
  assert.match(profile, /const avatarUrl = usuarioMe\?\.avatar_url \|\| ""/);
  assert.match(identitySurface, /src=\{avatarUrl\}/);
  assert.match(identitySurface, /alt="Foto de perfil"/);
  assert.match(identitySurface, /h-full w-full object-cover/);
  assert.match(identitySurface, /Sin foto/);
});

test("acciones directas usan Button y heredan una sola interactive-bubble", () => {
  assert.equal((identitySurface.match(/<Button\b/g) || []).length, 4);
  assert.match(identitySurface, /variant="primary"/);
  assert.match(identitySurface, /variant="secondary"/);
  assert.match(identitySurface, /variant="danger"/);
  assert.doesNotMatch(identitySurface, /<button\b|interactive-bubble/);
  assert.match(identitySurface, /onClick=\{abrirEdicionPerfil\}/);
  assert.match(identitySurface, /onClick=\{manejarLogout\}/);
});

test("success y error usan Alert sin alterar sus estados", () => {
  assert.match(identitySurface, /<Alert variant="success"/);
  assert.match(identitySurface, /<Alert variant="danger" role="alert"/);
  assert.match(identitySurface, /perfilSuccessMessage/);
  assert.match(identitySurface, /avatarErrorMessage/);
});

test("perfil conserva carga, endpoint y navegacion existentes", () => {
  assert.match(profile, /const data = await getMe\(token\)/);
  assert.match(profile, /useEffect\(\(\) => \{\s*loadUsuarioMe\(\)/);
  assert.match(authService, /return httpGet\("\/usuarios\/me", tokenJWT\)/);
  assert.match(router, /path="\/perfil"[\s\S]*<ProtectedRoute>[\s\S]*<ProfilePage \/>/);
});

test("no se inventan perfil de terceros, publicaciones, cards ni tabs", () => {
  assert.doesNotMatch(router, /usuarios\/:|perfil\/:/);
  assert.doesNotMatch(identitySurface, /PublicacionCard|role="tab"|useQuery/);
});

test("la superficie migrada no contiene tema manual ni colores fisicos", () => {
  assert.doesNotMatch(identitySurface, /#[\da-f]{3,8}|\brgb\(|\brgba\(/i);
  assert.doesNotMatch(identitySurface, /(?:bg|text|border|ring|from|via|to)-(?:gray|slate|zinc|neutral|stone|white|black|red|green|emerald|orange|amber|yellow|blue|purple|pink)(?:\/|-\d|\b)/);
  assert.doesNotMatch(identitySurface, /resolvedTheme|data-theme|dark:|matchMedia\(|localStorage\./);
});

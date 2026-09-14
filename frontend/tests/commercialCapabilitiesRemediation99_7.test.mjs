import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import test from "node:test";
import React from "react";
import { renderToString } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createServer } from "vite";

import { getInternalReturnTo } from "../src/core/navigation/internalReturnTo.js";

const root = new URL("../", import.meta.url);
const readText = (path) => readFile(new URL(path, root), "utf8");

test("http_service preserva exclusivamente status, detail y code estructurados", async () => {
  const service = await readText("src/core/services/http_service.js");

  assert.match(service, /constructor\(status, message, \{ detail = null, code = null \} = \{\}\)/);
  assert.match(service, /this\.detail = detail/);
  assert.match(service, /this\.code = code/);
  assert.match(service, /payload\.detail/);
  assert.match(service, /payload\.code/);
  assert.match(service, /\^\[a-z0-9_\]\{1,64\}\$/);
  assert.match(service, /safeErrorMessage\(response\.status\)/);
  assert.doesNotMatch(service, /this\.payload\s*=/);
});

test("el owner de remediation reconoce solo el 403 de capability y refresca /me", async () => {
  const hook = await readText(
    "src/features/auth/hooks/useCommercialCapabilityRemediation.js"
  );

  assert.match(hook, /COMMERCIAL_CAPABILITY_REQUIRED = "commercial_capability_required"/);
  assert.match(hook, /error\?\.status === 403/);
  assert.match(hook, /error\?\.code === COMMERCIAL_CAPABILITY_REQUIRED/);
  assert.match(hook, /await refrescarUsuario\(\)/);
  assert.match(hook, /usuario\?\.capabilities\?\.\[capability\] !== false/);
  assert.match(hook, /getInternalReturnTo/);
  assert.doesNotMatch(hook, /localStorage|sessionStorage|indexedDB/i);
});

test("las mutaciones comerciales anticipan UX y el 403 de ownership no se confunde", async () => {
  const [profile, commerce, post, story, hours, agenda] = await Promise.all([
    readText("src/features/auth/pages/ProfilePage.jsx"),
    readText("src/features/spaces/pages/PerfilComercioPage.jsx"),
    readText("src/features/posts/pages/PublicacionDetallePage.jsx"),
    readText("src/features/stories/components/CrearHistoriaModal.jsx"),
    readText("src/features/availability/components/HorariosAtencionEditor.jsx"),
    readText("src/features/agenda/components/AgendaPrivadaModal.jsx"),
  ]);

  assert.match(profile, /intentarAccionComercial\("puede_crear_espacio"\)/);
  assert.match(profile, /intentarAccionComercial\("puede_administrar_espacios"\)/);
  assert.match(commerce, /intentarAccionComercial\("puede_publicar_en_espacios"\)/);
  assert.match(post, /intentarAccionComercial\("puede_administrar_espacios"\)/);
  assert.match(story, /intentarAccionComercial\("puede_publicar_en_espacios"\)/);
  assert.match(hours, /manejarErrorCapability\(error\)/);
  assert.match(agenda, /manejarErrorCapability\(error\)/);
  assert.match(profile, /manejarErrorCapability\(error\)/);
  assert.doesNotMatch(profile, /error\?\.status === 403[\s\S]{0,80}capability/);
});

test("Profile usa derivados backend para remediation y conserva returnTo interno", async () => {
  const page = await readText("src/features/auth/pages/ProfilePage.jsx");

  assert.match(page, /searchParams\.get\("remediation"\) !== "commercial"/);
  assert.match(page, /const campo = camposPerfilFaltantes\[0\]/);
  assert.match(page, /getInternalReturnTo\(searchParams\.get\("returnTo"\), "\/perfil"\)/);
  assert.match(page, /navigate\("\/verificar-email", \{ state: \{ returnTo \} \}\)/);
  assert.match(page, /telefono: "perfil-telefono"/);
  assert.match(page, /aceptaciones_legales_pendientes/);
  assert.match(page, /mayoria_edad_requerida/);
  assert.doesNotMatch(page, /TodavÃ­a|NecesitÃ¡s|funciÃ³n/);
  assert.doesNotMatch(page, /calcularEdad|perfilCompleto\s*=\s*.*provincia/i);

  assert.equal(getInternalReturnTo("/perfil?returnTo=x&token=secret", "/feed"), "/perfil?returnTo=x");
  assert.equal(getInternalReturnTo("//attacker.example", "/feed"), "/feed");
});

test("/perfil concentra pendientes backend en una campana accesible sin duplicar derivados", async () => {
  const page = await readText("src/features/auth/pages/ProfilePage.jsx");

  assert.match(page, /showAccountPendingPanel/);
  assert.match(page, /Ver pendientes de la cuenta/);
  assert.match(page, /aria-controls="perfil-pendientes-panel"/);
  assert.match(page, /<ActiveLayer/);
  assert.match(page, /labelledBy="perfil-pendientes-title"/);
  assert.match(page, /initialFocusRef=\{accountPendingPanelCloseRef\}/);
  assert.match(page, /Estado del perfil/);
  assert.match(page, /Funciones comerciales/);
  assert.match(page, /pendientesComerciales\.map/);
  assert.match(page, /Mis espacios/);
  assert.match(page, /Estos son los espacios públicos que administrás desde esta/);
  assert.match(page, /!perfilCompleto/);
  assert.doesNotMatch(page, /calcularEdad|perfilCompleto\s*=\s*.*provincia/i);
});

test("PWA mantiene mutaciones y Authorization fuera de cache", async () => {
  const classifier = await readText("src/pwa/requestClassifier.js");
  assert.match(classifier, /method !== "GET" && method !== "HEAD"/);
  assert.match(classifier, /hasAuthorization\(request\)/);
  assert.match(classifier, /REQUEST_HANDLING\.NETWORK_ONLY/);
});

test("/perfil renderiza con /me loading y perfiles backend completos o incompletos", async () => {
  const originalWindow = globalThis.window;
  globalThis.window = {
    addEventListener() {},
    removeEventListener() {},
  };
  const vite = await createServer({
    root: fileURLToPath(root),
    appType: "custom",
    logLevel: "silent",
    server: { middlewareMode: true },
    ssr: { noExternal: ["leaflet", "react-leaflet"] },
    plugins: [
      {
        name: "profile-render-leaflet-stubs",
        enforce: "pre",
        resolveId(id) {
          if (id === "leaflet") return "\0profile-leaflet";
          if (id === "react-leaflet") return "\0profile-react-leaflet";
          return null;
        },
        load(id) {
          if (id === "\0profile-leaflet") {
            return "export default { Icon: { Default: { prototype: {}, mergeOptions() {} } } };";
          }
          if (id === "\0profile-react-leaflet") {
            return [
              'import React from "react";',
              'const Empty = () => React.createElement("div");',
              "export const MapContainer = Empty;",
              "export const Marker = Empty;",
              "export const TileLayer = Empty;",
              "export const useMap = () => ({ setView() {} });",
              "export const useMapEvents = () => ({});",
            ].join("\n");
          }
          return null;
        },
      },
    ],
  });

  try {
    const [{ default: ProfilePage }, { AuthContext }] = await Promise.all([
      vite.ssrLoadModule("/src/features/auth/pages/ProfilePage.jsx"),
      vite.ssrLoadModule("/src/features/auth/context/AuthContextCore.js"),
    ]);
    const users = [
      null,
      {
        id: 1,
        email: "persona@example.test",
        perfil_completo: false,
        campos_perfil_faltantes: ["fecha_nacimiento"],
        capabilities: {
          puede_crear_espacio: false,
          puede_administrar_espacios: false,
          puede_publicar_en_espacios: false,
        },
        pendientes_comerciales: ["perfil_incompleto"],
      },
      {
        id: 2,
        email: "persona-completa@example.test",
        perfil_completo: true,
        campos_perfil_faltantes: [],
        capabilities: {
          puede_crear_espacio: true,
          puede_administrar_espacios: true,
          puede_publicar_en_espacios: true,
        },
        pendientes_comerciales: [],
      },
    ];

    for (const usuario of users) {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const auth = {
        accessToken: usuario ? "opaque-bearer" : null,
        estaAutenticado: Boolean(usuario),
        usuario,
        isCargandoUsuario: usuario === null,
        refrescarUsuario: async () => usuario,
        logout: async () => {},
      };
      const tree = React.createElement(
        MemoryRouter,
        { initialEntries: ["/perfil"] },
        React.createElement(
          QueryClientProvider,
          { client: queryClient },
          React.createElement(
            AuthContext.Provider,
            { value: auth },
            React.createElement(ProfilePage)
          )
        )
      );

      assert.doesNotThrow(() => renderToString(tree));
      queryClient.clear();
    }
  } finally {
    await vite.close();
    if (originalWindow === undefined) delete globalThis.window;
    else globalThis.window = originalWindow;
  }
});

test("los derivados se inicializan antes del effect de remediation", async () => {
  const page = await readText("src/features/auth/pages/ProfilePage.jsx");
  const missingDeclaration = page.indexOf("const camposPerfilFaltantes =");
  const pendingDeclaration = page.indexOf("const pendientesComerciales =");
  const remediationEffect = page.indexOf(
    'searchParams.get("remediation") !== "commercial"'
  );

  assert.ok(missingDeclaration >= 0 && missingDeclaration < remediationEffect);
  assert.ok(pendingDeclaration >= 0 && pendingDeclaration < remediationEffect);
});

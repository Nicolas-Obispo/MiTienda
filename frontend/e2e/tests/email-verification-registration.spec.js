import { expect, test } from "@playwright/test";

test.use({ serviceWorkers: "block" });

function usuarioResponse(emailVerifiedAt = null) {
  return {
    id: 99,
    email: "manual@example.com",
    avatar_url: null,
    color_fondo: null,
    modo_activo: "explorador",
    onboarding_completo: false,
    provincia: null,
    ciudad: null,
    email_verified_at: emailVerifiedAt,
    email_verification_source: emailVerifiedAt ? "email_link" : null,
  };
}

test("registro conserva destino y verificacion usa el estado backend", async ({ page }) => {

  await page.route("**/api/usuarios/**", async (route) => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;

    if (pathname === "/api/usuarios/email-disponibilidad") {
      await route.fulfill({ json: { disponible: true } });
      return;
    }
    if (pathname === "/api/usuarios/registrar") {
      await route.fulfill({
        json: {
          ...usuarioResponse(),
          email_verification_status: "sent",
        },
      });
      return;
    }
    if (pathname === "/api/usuarios/login") {
      await route.fulfill({ json: { access_token: "jwt-e2e" } });
      return;
    }
    if (pathname === "/api/usuarios/me") {
      await route.fulfill({ json: usuarioResponse() });
      return;
    }
    await route.fallback();
  });

  await page.goto("/registro");
  await page.getByLabel("Usuario").fill("manual@example.com");
  await expect(page.getByText("Usuario disponible.")).toBeVisible();
  await page.getByLabel("Contraseña", { exact: true }).fill("Password1");
  await page.getByLabel("Confirmar contraseña").fill("Password1");
  for (const checkbox of await page.getByRole("checkbox").all()) await checkbox.check();
  await page.getByRole("button", { name: "Crear cuenta" }).click();

  await expect(page).toHaveURL(/\/verificar-email$/);
  await expect(page.getByText("Te enviamos un enlace para verificar tu cuenta.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Enviar otro enlace" })).toBeVisible();

  await page.evaluate(() => history.replaceState(null, "", "/verificar-email"));
  await page.reload();
  await expect(page).toHaveURL(/\/verificar-email$/);
  await expect(page.getByText("Verificá tu cuenta para continuar.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Enviar otro enlace" })).toBeVisible();
});

test("usuario ya verificado no ve reenvio", async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem("access_token", "jwt-e2e"));
  await page.route("**/api/usuarios/me", (route) => route.fulfill({
    json: usuarioResponse("2026-09-05T12:00:00Z"),
  }));

  await page.goto("/verificar-email");
  await expect(page.getByText("Listo, tu cuenta ya está verificada.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Enviar otro enlace" })).toHaveCount(0);
});

test("enlace realmente invalido conserva el contrato seguro", async ({ page }) => {
  await page.route("**/api/usuarios/email-verificacion/confirmar", (route) => route.fulfill({
    status: 400,
    json: { detail: "invalid" },
  }));
  await page.goto("/verificar-email#token=invalido");
  await expect(page).toHaveURL(/\/verificar-email$/);
  await expect(page.getByText("Este enlace ya no es válido. Pedí uno nuevo para continuar.")).toBeVisible();
});

test("token nuevo en la misma ruta se consume una sola vez", async ({ page }) => {
  let verifiedAt = null;
  let confirmCalls = 0;
  let meCalls = 0;
  await page.addInitScript(() => localStorage.setItem("access_token", "jwt-e2e"));
  await page.route("**/api/usuarios/me", async (route) => {
    meCalls += 1;
    await route.fulfill({ json: usuarioResponse(verifiedAt) });
  });
  await page.route("**/api/usuarios/email-verificacion/confirmar", async (route) => {
    confirmCalls += 1;
    verifiedAt = "2026-09-05T12:00:00Z";
    await route.fulfill({ json: { status: "verified" } });
  });

  await page.goto("/verificar-email");
  await expect(page.getByText("Verificá tu cuenta para continuar.")).toBeVisible();

  await page.evaluate(() => { window.location.hash = "token=token-nuevo"; });
  await expect(page).toHaveURL(/\/verificar-email$/);
  await expect.poll(() => confirmCalls).toBe(1);
  await expect.poll(() => meCalls).toBeGreaterThan(1);
  await expect(page.getByText("Listo, tu cuenta ya está verificada.")).toBeVisible();

  await page.evaluate(() => { window.location.hash = "token=token-nuevo"; });
  await expect(page).toHaveURL(/\/verificar-email$/);
  await page.waitForTimeout(100);
  expect(confirmCalls).toBe(1);

  await page.evaluate(() => { window.location.hash = "token=otro-token"; });
  await expect(page).toHaveURL(/\/verificar-email$/);
  await expect.poll(() => confirmCalls).toBe(2);
});

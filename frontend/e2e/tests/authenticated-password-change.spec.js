import { expect, test } from "@playwright/test";

test.use({ serviceWorkers: "block" });

const user = {
  id: 99,
  email: "manual@example.com",
  avatar_url: null,
  color_fondo: null,
  modo_activo: "explorador",
  onboarding_completo: false,
  provincia: "Buenos Aires",
  ciudad: "La Plata",
  email_verified_at: "2026-09-05T12:00:00Z",
  email_verification_source: "email_link",
};

async function openProfile(page, { passwordStatus = 200, openEdit = true, openPassword = true } = {}) {
  const requests = [];
  await page.addInitScript(() => localStorage.setItem("access_token", "jwt-e2e"));
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const entry = { method: request.method(), pathname: url.pathname, body: request.postDataJSON?.() };
    requests.push(entry);

    if (url.pathname === "/api/usuarios/me/password") {
      await route.fulfill({
        status: passwordStatus,
        json: passwordStatus === 200
          ? { status: "password_updated" }
          : { detail: { code: "password_change_failed" } },
      });
      return;
    }
    if (url.pathname === "/api/usuarios/me") {
      await route.fulfill({ json: user });
      return;
    }
    await route.fulfill({ json: [] });
  });

  await page.goto("/perfil");
  if (!openEdit) return requests;
  await page.getByRole("button", { name: "Editar perfil" }).click();
  await expect(page.getByRole("button", { name: "Cambiar foto" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Cambiar contraseña" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Cambiar fondo" })).toBeVisible();
  await expect(page.getByLabel("Fecha de nacimiento")).toHaveCount(0);
  if (openPassword) {
    await page.getByRole("button", { name: "Cambiar contraseña" }).click();
  }
  return requests;
}

test("Editar perfil abre primero las cuatro acciones y sólo después Datos personales", async ({ page }) => {
  await openProfile(page, { openPassword: false });
  await expect(page.getByRole("button", { name: "Datos personales" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Cambiar foto" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Cambiar contraseña" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Cambiar fondo" })).toBeVisible();
  await expect(page.getByLabel("Fecha de nacimiento")).toHaveCount(0);

  await page.getByRole("button", { name: "Datos personales" }).click();
  await expect(page.getByText("Correo electrónico")).toBeVisible();
  await expect(page.getByLabel("Fecha de nacimiento")).toBeVisible();
  await expect(page.getByLabel("Teléfono")).toBeVisible();
  await expect(page.getByLabel("Provincia")).toBeVisible();
  await expect(page.getByLabel("Ciudad")).toBeVisible();
});

test("la campana reduce el botón completo y conserva su nombre accesible", async ({ page }) => {
  await openProfile(page, { openEdit: false });
  const bell = page.getByRole("button", { name: /Ver pendientes de la cuenta/ });
  await expect(bell.locator("svg")).toHaveAttribute("width", "13");
  await expect(bell.locator("svg")).toHaveAttribute("height", "13");
  await expect(bell).toHaveCSS("width", "32px");
  await expect(bell).toHaveCSS("height", "32px");
});

test("cambio es un formulario hermano y sólo envía el password", async ({ page }) => {
  const requests = await openProfile(page);
  expect(await page.locator("form form").count()).toBe(0);
  await expect(page.getByRole("heading", { name: "Seguridad" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Cambiar contraseña" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Cambiar foto" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Cambiar fondo" })).toHaveCount(0);

  const passwordForm = page.getByRole("button", { name: "Actualizar contraseña" }).locator("xpath=ancestor::form");
  await expect(passwordForm.getByLabel("Cambiar foto")).toHaveCount(0);
  await expect(passwordForm.getByLabel("Provincia")).toHaveCount(0);
  await expect(passwordForm.getByLabel("Ciudad")).toHaveCount(0);
  await expect(passwordForm.getByRole("button", { name: "Guardar", exact: true })).toHaveCount(0);

  await page.getByLabel("Contraseña actual", { exact: true }).fill("Legacy1A");
  await page.getByLabel("Nueva contraseña", { exact: true }).fill("NuevaClave1");
  await page.getByLabel("Confirmar nueva contraseña", { exact: true }).fill("NuevaClave1");
  await page.getByRole("button", { name: "Actualizar contraseña" }).click();

  await expect(page.getByText("Listo, tu contraseña fue actualizada.")).toBeVisible();
  const passwordRequests = requests.filter((entry) => entry.pathname === "/api/usuarios/me/password");
  expect(passwordRequests).toEqual([{
    method: "PATCH",
    pathname: "/api/usuarios/me/password",
    body: { current_password: "Legacy1A", new_password: "NuevaClave1" },
  }]);
  expect(requests.filter((entry) => entry.method === "PATCH" && entry.pathname === "/api/usuarios/me")).toHaveLength(0);
  await expect(page.getByRole("button", { name: "Datos personales" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Cambiar foto" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Cambiar contraseña" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Cambiar fondo" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Seguridad" })).toHaveCount(0);
});

test("un error backend nunca muestra éxito", async ({ page }) => {
  await openProfile(page, { passwordStatus: 500 });
  await page.getByLabel("Contraseña actual", { exact: true }).fill("Legacy1A");
  await page.getByLabel("Nueva contraseña", { exact: true }).fill("NuevaClave1");
  await page.getByLabel("Confirmar nueva contraseña", { exact: true }).fill("NuevaClave1");
  await page.getByRole("button", { name: "Actualizar contraseña" }).click();
  await expect(page.getByText("Listo, tu contraseña fue actualizada.")).toHaveCount(0);
  await expect(page.getByText("No pudimos completar esto ahora. Intentá nuevamente en un momento.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Seguridad" })).toBeVisible();
  await expect(page.getByLabel("Contraseña actual", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Cambiar foto" })).toHaveCount(0);
});

test("Cancelar limpia secretos, no envía requests y vuelve al menú de edición", async ({ page }) => {
  const requests = await openProfile(page);
  await page.getByLabel("Contraseña actual", { exact: true }).fill("Legacy1A");
  await page.getByLabel("Nueva contraseña", { exact: true }).fill("NuevaClave1");
  await page.getByLabel("Confirmar nueva contraseña", { exact: true }).fill("distinta");
  await expect(page.getByText("Las contraseñas no coinciden.")).toBeVisible();

  const passwordForm = page.getByRole("button", { name: "Actualizar contraseña" }).locator("xpath=ancestor::form");
  await passwordForm.getByRole("button", { name: "Cancelar" }).click();

  expect(requests.filter((entry) => entry.pathname === "/api/usuarios/me/password")).toHaveLength(0);
  await expect(page.getByRole("button", { name: "Datos personales" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Cambiar contraseña" })).toBeVisible();

  await page.getByRole("button", { name: "Cambiar contraseña" }).click();
  await expect(page.getByLabel("Contraseña actual", { exact: true })).toHaveValue("");
  await expect(page.getByLabel("Nueva contraseña", { exact: true })).toHaveValue("");
  await expect(page.getByLabel("Confirmar nueva contraseña", { exact: true })).toHaveValue("");
  await expect(page.getByText("Las contraseñas no coinciden.")).toHaveCount(0);
});

test("formularios vuelven al menú y Volver o Perfil administrador regresan a la vista principal", async ({ page }) => {
  await openProfile(page, { openPassword: false });

  await page.getByRole("button", { name: "Datos personales" }).click();
  await expect(page.getByLabel("Fecha de nacimiento")).toBeVisible();
  await page.getByRole("button", { name: "Cancelar" }).click();
  await expect(page.getByRole("button", { name: "Datos personales" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Editar perfil" })).toHaveCount(0);

  await page.getByRole("button", { name: "Datos personales" }).click();
  await page.getByRole("button", { name: "Guardar" }).click();
  await expect(page.getByRole("button", { name: "Datos personales" })).toBeVisible();

  await page.getByRole("button", { name: "Cambiar foto" }).click();
  await expect(page.getByRole("heading", { name: "Cambiar foto" })).toBeVisible();
  await page.getByRole("button", { name: "Cancelar" }).click();
  await expect(page.getByRole("button", { name: "Cambiar foto" })).toBeVisible();

  await page.getByRole("button", { name: "Cambiar foto" }).click();
  await page.getByRole("button", { name: "Aplicar" }).click();
  await expect(page.getByRole("button", { name: "Cambiar foto" })).toBeVisible();

  await page.getByRole("button", { name: "Cambiar fondo" }).click();
  await expect(page.getByRole("heading", { name: "Cambiar fondo" })).toBeVisible();
  await page.getByRole("button", { name: "Aplicar" }).click();
  await expect(page.getByRole("button", { name: "Cambiar fondo" })).toBeVisible();

  await page.getByRole("button", { name: "Cambiar fondo" }).click();
  await page.getByRole("button", { name: "Cancelar" }).click();
  await expect(page.getByRole("button", { name: "Cambiar fondo" })).toBeVisible();

  await page.getByRole("button", { name: "Volver" }).click();
  await expect(page.getByRole("button", { name: "Editar perfil" })).toBeVisible();

  await page.getByRole("button", { name: "Editar perfil" }).click();
  await page.getByRole("button", { name: "Cambiar contraseña" }).click();
  await expect(page.getByRole("heading", { name: "Seguridad" })).toBeVisible();
  await page.getByRole("link", { name: "Perfil administrador" }).click();
  await expect(page.getByRole("button", { name: "Editar perfil" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Seguridad" })).toHaveCount(0);
});

test("visibilidad compartida y mismatch en vivo", async ({ page }) => {
  await openProfile(page);
  const current = page.getByLabel("Contraseña actual", { exact: true });
  await expect(current).toHaveAttribute("type", "password");
  await page.getByRole("button", { name: "Mostrar contraseña" }).first().click();
  await expect(current).toHaveAttribute("type", "text");
  await page.getByRole("button", { name: "Ocultar contraseña" }).first().click();
  await expect(current).toHaveAttribute("type", "password");

  await page.getByLabel("Nueva contraseña", { exact: true }).fill("NuevaClave1");
  const confirmation = page.getByLabel("Confirmar nueva contraseña", { exact: true });
  await confirmation.fill("NuevaClave2");
  await expect(page.getByText("Las contraseñas no coinciden.")).toBeVisible();
  await expect(confirmation).toHaveAttribute("aria-invalid", "true");
  await confirmation.fill("NuevaClave1");
  await expect(page.getByText("Las contraseñas no coinciden.")).toHaveCount(0);
});

test("Login, Registro y Restablecer usan el control compartido", async ({ page }) => {
  await page.goto("/login");
  const loginPassword = page.getByLabel("Contraseña", { exact: true });
  await page.getByRole("button", { name: "Mostrar contraseña" }).click();
  await expect(loginPassword).toHaveAttribute("type", "text");

  await page.goto("/registro");
  const registrationPassword = page.getByLabel("Contraseña", { exact: true });
  await page.getByRole("button", { name: "Mostrar contraseña" }).first().click();
  await expect(registrationPassword).toHaveAttribute("type", "text");

  await page.goto("/restablecer-password#token=e2e-secret");
  const resetPassword = page.getByLabel("Nueva contraseña", { exact: true });
  await page.getByRole("button", { name: "Mostrar contraseña" }).first().click();
  await expect(resetPassword).toHaveAttribute("type", "text");
  const confirmation = page.getByLabel("Confirmar contraseña", { exact: true });
  await confirmation.fill("distinta");
  await expect(page.getByText("Las contraseñas no coinciden.")).toBeVisible();
});

import { expect, test } from "@playwright/test";

const liveEmail = process.env.FEEDGO_LIVE_E2E_EMAIL;
const oldPassword = process.env.FEEDGO_LIVE_E2E_OLD_PASSWORD;
const newPassword = process.env.FEEDGO_LIVE_E2E_NEW_PASSWORD;
const liveBaseUrl = process.env.FEEDGO_LIVE_FRONTEND_URL || "http://127.0.0.1:5173";

test("cambio real persiste y Login adopta sólo la contraseña nueva", async ({ page }) => {
  test.skip(!liveEmail || !oldPassword || !newPassword, "Requiere una cuenta MySQL aislada para E2E live.");

  await page.goto(`${liveBaseUrl}/login`);
  await page.getByLabel("Email").fill(liveEmail);
  await page.getByLabel("Contraseña", { exact: true }).fill(oldPassword);
  await page.getByRole("button", { name: "Ingresar", exact: true }).click();
  await expect(page).toHaveURL(/\/feed$/);

  await page.goto(`${liveBaseUrl}/perfil`);
  await page.getByRole("button", { name: "Editar perfil" }).click();
  await page.getByRole("button", { name: "Cambiar contraseña" }).click();
  await page.getByLabel("Contraseña actual", { exact: true }).fill(oldPassword);
  await page.getByLabel("Nueva contraseña", { exact: true }).fill(newPassword);
  await page.getByLabel("Confirmar nueva contraseña", { exact: true }).fill(newPassword);
  await page.getByRole("button", { name: "Actualizar contraseña" }).click();
  await expect(page.getByText("Listo, tu contraseña fue actualizada.")).toBeVisible();
  await page.getByRole("button", { name: "Cancelar" }).click();
  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page).toHaveURL(/\/login$/);

  await page.getByLabel("Email").fill(liveEmail);
  await page.getByLabel("Contraseña", { exact: true }).fill(oldPassword);
  await page.getByRole("button", { name: "Ingresar", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);

  await page.getByLabel("Contraseña", { exact: true }).fill(newPassword);
  await page.getByRole("button", { name: "Ingresar", exact: true }).click();
  await expect(page).toHaveURL(/\/feed$/);
});

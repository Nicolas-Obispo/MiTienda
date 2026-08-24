import { expect, test } from "@playwright/test";

const WIDTHS = [320, 375, 430];

test("la navegación administrativa no se solapa en anchos móviles representativos", async ({ page }) => {
  await page.goto("/");

  for (const width of WIDTHS) {
    await page.setViewportSize({ width, height: 720 });
    await page.evaluate(() => {
      document.body.innerHTML = `
        <header class="border-b border-border bg-surface">
          <div data-testid="header-row" class="mx-auto flex w-full max-w-3xl flex-wrap items-center justify-between gap-2 px-3 py-2 sm:flex-nowrap sm:gap-0 sm:px-4 sm:py-3">
            <a data-testid="logo" class="interactive-bubble interactive-bubble--flush shrink-0 items-center"><span class="block h-9 w-9">FG</span></a>
            <nav data-testid="global-nav" class="flex min-w-0 flex-1 items-center gap-2 overflow-x-auto sm:flex-none sm:gap-4 sm:overflow-visible">
              <a class="interactive-bubble group shrink-0 text-xs sm:text-sm">Feed</a>
              <a class="interactive-bubble group shrink-0 text-xs font-semibold sm:text-sm">Perfil administrador</a>
              <a class="interactive-bubble group shrink-0 text-xs sm:text-sm">Tendencias</a>
              <a class="interactive-bubble group shrink-0 text-xs sm:text-sm">Seguidos</a>
              <a class="interactive-bubble group shrink-0 text-xs font-semibold sm:text-sm">Explorar</a>
            </nav>
            <div data-testid="admin-row" class="order-3 flex min-w-0 w-full items-center justify-end border-t border-border-subtle pt-2 sm:order-none sm:w-auto sm:shrink-0 sm:border-0 sm:pt-0">
              <a data-testid="admin-link" class="interactive-bubble group min-h-11 min-w-0 w-full justify-center whitespace-normal break-words text-center text-xs sm:w-auto sm:shrink-0 sm:text-sm">Administración operativa extendida</a>
            </div>
          </div>
        </header>`;
    });

    const boxes = await page.evaluate(() => {
      const box = (selector) => {
        const rect = document.querySelector(selector).getBoundingClientRect();
        return { left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom, width: rect.width };
      };
      return {
        header: box('[data-testid="header-row"]'),
        nav: box('[data-testid="global-nav"]'),
        adminRow: box('[data-testid="admin-row"]'),
        adminLink: box('[data-testid="admin-link"]'),
      };
    });

    expect(boxes.adminRow.top).toBeGreaterThanOrEqual(boxes.nav.bottom);
    expect(boxes.adminLink.left).toBeGreaterThanOrEqual(boxes.header.left);
    expect(boxes.adminLink.right).toBeLessThanOrEqual(boxes.header.right + 0.5);
    expect(boxes.adminLink.width).toBeGreaterThanOrEqual(44);
  }
});

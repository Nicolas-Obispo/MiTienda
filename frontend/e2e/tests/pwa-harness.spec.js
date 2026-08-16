import { expect, test } from "@playwright/test";

async function resetFixture(request) {
  const response = await request.post("/__pwa-e2e/reset");
  expect(response.ok()).toBeTruthy();
}

async function openControlledPage(page) {
  await page.goto("/");
  await expect(page).toHaveTitle("FeedGo");
  await page.waitForFunction(async () => {
    const registration = await navigator.serviceWorker.getRegistration();
    return Boolean(
      registration?.active?.state === "activated" &&
      globalThis.__FEEDGO_PWA_E2E__
    );
  });
  if (!await page.evaluate(() => Boolean(navigator.serviceWorker.controller))) {
    const context = page.context();
    await page.close();
    await new Promise((resolve) => setTimeout(resolve, 250));
    page = await context.newPage();
    await page.goto("/");
  }
  for (let attempt = 0; attempt < 2; attempt += 1) {
    if (await page.evaluate(() => Boolean(navigator.serviceWorker.controller))) break;
    await page.waitForTimeout(250);
    await page.reload();
  }
  const serviceWorkerEvidence = await page.evaluate(async () => {
    const registration = await navigator.serviceWorker.getRegistration();
    return {
      activeState: registration?.active?.state,
      controller: navigator.serviceWorker.controller?.scriptURL,
      installingState: registration?.installing?.state,
      scope: registration?.scope,
      waitingState: registration?.waiting?.state,
    };
  });
  expect(serviceWorkerEvidence.controller, JSON.stringify(serviceWorkerEvidence)).toBeTruthy();
  return page;
}

async function switchVersion(request, version) {
  const response = await request.post(`/__pwa-e2e/version/${version}`);
  expect(response.ok()).toBeTruthy();
}

async function setFault(request, fault) {
  const response = await request.post(`/__pwa-e2e/fault/${fault}`);
  expect(response.ok()).toBeTruthy();
}

async function installWaitingVersion(page, request) {
  await switchVersion(request, "n-plus-one");
  expect(await page.evaluate(() => globalThis.__FEEDGO_PWA_E2E__.checkForUpdate())).toBeTruthy();
  await page.waitForFunction(async () => {
    const registration = await navigator.serviceWorker.getRegistration();
    return Boolean(
      registration?.waiting &&
      globalThis.__FEEDGO_PWA_E2E__.getRuntimeState() === "update-available"
    );
  });
}

test.beforeEach(async ({ request }) => {
  await resetFixture(request);
});

test("carga build productivo, controla la pagina e inspecciona precache", async ({ page, context }) => {
  expect(await context.cookies()).toEqual([]);
  await page.goto("/__pwa-e2e/status");
  expect(await page.evaluate(async () => ({
    caches: await caches.keys(),
    registration: Boolean(await navigator.serviceWorker.getRegistration()),
  }))).toEqual({ caches: [], registration: false });
  page = await openControlledPage(page);

  const evidence = await page.evaluate(async () => {
    const cacheNames = await caches.keys();
    const entries = [];
    for (const cacheName of cacheNames) {
      const cache = await caches.open(cacheName);
      entries.push({ cacheName, urls: (await cache.keys()).map((request) => request.url) });
    }
    return {
      bridgeVersion: globalThis.__FEEDGO_PWA_E2E__.buildVersion,
      cacheNames,
      entries,
      controller: navigator.serviceWorker.controller.scriptURL,
    };
  });

  expect(evidence.bridgeVersion).toBe("N");
  expect(evidence.controller).toContain("/service-worker.js");
  expect(evidence.cacheNames.some((name) => name.startsWith("feedgo-precache-"))).toBeTruthy();
  expect(evidence.entries.flatMap((entry) => entry.urls).some((url) => url.includes("/api/"))).toBeFalsy();
});

test("primera visita offline limpia no finge disponibilidad", async ({ page, context }) => {
  await page.goto("/__pwa-e2e/status");
  expect(await page.evaluate(() => caches.keys())).toEqual([]);
  expect(await page.evaluate(async () => Boolean(await navigator.serviceWorker.getRegistration()))).toBe(false);

  await context.setOffline(true);
  await expect(page.goto("/explorar", { waitUntil: "domcontentloaded" })).rejects.toThrow();
});

test("contexto aislado soporta dos paginas y cambio de conectividad", async ({ page, context }) => {
  page = await openControlledPage(page);
  const secondPage = await context.newPage();
  await secondPage.goto("/");
  await expect(secondPage).toHaveTitle("FeedGo");
  expect(context.pages()).toHaveLength(2);

  await context.setOffline(true);
  await page.goto("/explorar");
  await expect(page).toHaveURL(/\/explorar$/);
  const timeOrigin = await page.evaluate(() => performance.timeOrigin);
  expect(await page.evaluate(async () => {
    try {
      await fetch("/__pwa-e2e/status?offline-check");
      return false;
    } catch {
      return true;
    }
  })).toBeTruthy();

  for (const method of ["POST", "PUT", "PATCH", "DELETE"]) {
    expect(await page.evaluate(async (requestMethod) => {
      try {
        const response = await fetch("/api/fixture/mutation", { method: requestMethod });
        return { resolved: true, status: response.status };
      } catch {
        return { resolved: false };
      }
    }, method)).toEqual({ resolved: false });
  }

  await context.setOffline(false);
  await expect.poll(() => page.evaluate(async () => {
    try {
      return (await fetch("/__pwa-e2e/status?online-check")).ok;
    } catch {
      return false;
    }
  })).toBeTruthy();
  expect(await page.evaluate(() => navigator.onLine)).toBe(true);
  expect(await page.evaluate(() => performance.timeOrigin)).toBe(timeOrigin);
  expect((await page.evaluate(() => caches.keys())).some((name) => name.startsWith("feedgo-precache-"))).toBeTruthy();
});

test("backend inaccesible y errores HTTP conservan semantica tecnica", async ({ page, request }) => {
  page = await openControlledPage(page);
  await page.evaluate(() => {
    globalThis.__pwaMessages = [];
    navigator.serviceWorker.addEventListener("message", ({ data }) => {
      globalThis.__pwaMessages.push(data?.type);
    });
  });

  await setFault(request, "api-unreachable");
  expect(await page.evaluate(async () => {
    try {
      await fetch("/api/fixture/status/200");
      return false;
    } catch {
      return true;
    }
  })).toBe(true);
  expect(await page.evaluate(() => navigator.onLine)).toBe(true);
  await expect.poll(() => page.evaluate(() => globalThis.__pwaMessages)).toContain("BACKEND_UNREACHABLE");

  await setFault(request, "none");
  for (const status of [401, 403, 404, 422, 500]) {
    expect(await page.evaluate(async (responseStatus) => {
      const response = await fetch(`/api/fixture/status/${responseStatus}`);
      return response.status;
    }, status)).toBe(status);
  }
  expect(await page.evaluate(() => navigator.onLine)).toBe(true);
  expect(await page.evaluate(() => globalThis.__pwaMessages.includes("BACKEND_REACHABLE"))).toBe(true);
  expect((await page.evaluate(async () => {
    const urls = [];
    for (const name of await caches.keys()) {
      const cache = await caches.open(name);
      urls.push(...(await cache.keys()).map(({ url }) => url));
    }
    return urls;
  })).some((url) => url.includes("/api/"))).toBe(false);
});

test("activacion explicita usa el owner real y recarga como maximo una vez", async ({ page, request }) => {
  page = await openControlledPage(page);
  await installWaitingVersion(page, request);

  let navigations = 0;
  page.on("framenavigated", (frame) => {
    if (frame === page.mainFrame()) navigations += 1;
  });

  let accepted = false;
  for (let attempt = 0; attempt < 6 && !accepted; attempt += 1) {
    accepted = await page.evaluate(() => globalThis.__FEEDGO_PWA_E2E__.requestActivation());
    if (!accepted) await page.waitForTimeout(500);
  }
  expect(accepted).toBeTruthy();
  await page.waitForFunction(() => sessionStorage.getItem("feedgo:pwa:last-activated-version"));
  await page.waitForTimeout(250);

  expect(navigations).toBe(1);
  expect(await page.evaluate(() => ({
    guard: sessionStorage.getItem("feedgo:pwa:last-activated-version"),
    version: globalThis.__FEEDGO_PWA_E2E__.buildVersion,
  }))).toMatchObject({ version: "N+1" });
});

test("activacion natural ocurre al cerrar clientes sin reload forzado", async ({ page, context, request }) => {
  page = await openControlledPage(page);
  await installWaitingVersion(page, request);
  expect(await page.evaluate(() => sessionStorage.getItem("feedgo:pwa:last-activated-version"))).toBeNull();

  await page.close();
  await new Promise((resolve) => setTimeout(resolve, 500));
  const reopened = await context.newPage();
  await reopened.goto("/");
  await reopened.waitForFunction(() => globalThis.__FEEDGO_PWA_E2E__?.buildVersion === "N+1");

  expect(await reopened.evaluate(() => performance.getEntriesByType("navigation").length)).toBe(1);
  expect(await reopened.evaluate(() => sessionStorage.getItem("feedgo:pwa:last-activated-version"))).toBeNull();
});

test("multitab bloquea activacion sin cerrar ni recargar paginas", async ({ page, context, request }) => {
  page = await openControlledPage(page);
  const secondPage = await context.newPage();
  await secondPage.goto("/");
  await secondPage.waitForFunction(() => Boolean(navigator.serviceWorker.controller));
  await installWaitingVersion(page, request);

  const firstUrl = page.url();
  const secondUrl = secondPage.url();
  expect(await page.evaluate(() => globalThis.__FEEDGO_PWA_E2E__.requestActivation())).toBeFalsy();

  expect(context.pages()).toHaveLength(2);
  expect(page.url()).toBe(firstUrl);
  expect(secondPage.url()).toBe(secondUrl);
  expect(await page.evaluate(() => sessionStorage.getItem("feedgo:pwa:last-activated-version"))).toBeNull();

  await secondPage.close();
  await page.close();
  await new Promise((resolve) => setTimeout(resolve, 500));
  const reopened = await context.newPage();
  await reopened.goto("/");
  await reopened.waitForFunction(() => globalThis.__FEEDGO_PWA_E2E__?.buildVersion === "N+1");
});

test("repair invoca el owner real y protege caches ajenos", async ({ page }) => {
  page = await openControlledPage(page);
  await page.evaluate(async () => {
    const corruptFeedGoCache = await caches.open("feedgo-precache-corrupt");
    await corruptFeedGoCache.put("/corrupt-fixture", new Response("corrupt"));
    await caches.open("other-capability-cache");
    localStorage.setItem("feedgo:test:jwt", "fixture-token");
    localStorage.setItem("feedgo:test:preferences", "fixture-preferences");
    localStorage.setItem("feedgo:test:geolocation", "fixture-location");
    await new Promise((resolve, reject) => {
      const request = indexedDB.open("other-capability-db", 1);
      request.onsuccess = () => { request.result.close(); resolve(); };
      request.onerror = () => reject(request.error);
    });
  });

  await expect
    .poll(() => page.evaluate(() => caches.has("feedgo-precache-corrupt")))
    .toBe(true);

  const result = await page.evaluate(() => globalThis.__FEEDGO_PWA_E2E__.repair());
  const evidence = await page.evaluate(async () => ({
    cacheNames: await caches.keys(),
    databaseNames: (await indexedDB.databases()).map(({ name }) => name),
    geolocation: localStorage.getItem("feedgo:test:geolocation"),
    jwt: localStorage.getItem("feedgo:test:jwt"),
    preferences: localStorage.getItem("feedgo:test:preferences"),
    registration: Boolean(await navigator.serviceWorker.getRegistration()),
  }));

  expect(result.unregistered).toEqual(["/service-worker.js"]);
  expect(result.deletedCaches.every((name) => name.startsWith("feedgo-precache-"))).toBeTruthy();
  expect(evidence.cacheNames).not.toContain("feedgo-precache-corrupt");
  expect(evidence.cacheNames).toContain("other-capability-cache");
  expect(evidence.databaseNames).toContain("other-capability-db");
  expect(evidence.jwt).toBe("fixture-token");
  expect(evidence.preferences).toBe("fixture-preferences");
  expect(evidence.geolocation).toBe("fixture-location");
  expect(evidence.registration).toBeTruthy();
});

test("update fallido conserva la version activa", async ({ page, request }) => {
  page = await openControlledPage(page);
  await switchVersion(request, "n-plus-one");
  await setFault(request, "update-failed");

  await expect(page.evaluate(() => globalThis.__FEEDGO_PWA_E2E__.checkForUpdate())).rejects.toThrow();
  expect(await page.evaluate(() => globalThis.__FEEDGO_PWA_E2E__.buildVersion)).toBe("N");
  expect(await page.evaluate(() => navigator.serviceWorker.controller?.state)).toBe("activated");
});

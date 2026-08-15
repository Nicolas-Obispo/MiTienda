import { deleteAllFeedGoPrecaches } from "./cacheCleanup.js";
import { PWA_SERVICE_WORKER_URL } from "./lifecycleContract.js";

function ownsFeedGoWorker(registration, appOrigin) {
  const worker = registration.installing || registration.waiting || registration.active;
  if (!worker?.scriptURL) return false;

  const scriptUrl = new URL(worker.scriptURL, appOrigin);
  return scriptUrl.origin === new URL(appOrigin).origin &&
    scriptUrl.pathname === PWA_SERVICE_WORKER_URL;
}

export async function repairPwaInfrastructure({
  serviceWorkerContainer,
  cacheStorage,
  appOrigin,
}) {
  const registrations = serviceWorkerContainer?.getRegistrations
    ? await serviceWorkerContainer.getRegistrations()
    : [];
  const ownedRegistrations = registrations.filter((registration) =>
    ownsFeedGoWorker(registration, appOrigin));

  const unregistered = [];
  for (const registration of ownedRegistrations) {
    if (await registration.unregister()) unregistered.push(PWA_SERVICE_WORKER_URL);
  }

  const deletedCaches = cacheStorage
    ? await deleteAllFeedGoPrecaches(cacheStorage)
    : [];

  return { unregistered, deletedCaches };
}

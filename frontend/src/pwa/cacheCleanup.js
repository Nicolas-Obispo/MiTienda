export const FEEDGO_PRECACHE_PREFIX = "feedgo-precache-";

export async function cleanupOldFeedGoPrecaches({
  cacheStorage,
  currentPrecacheName,
}) {
  const cacheNames = await cacheStorage.keys();
  const obsoleteNames = cacheNames.filter(
    (cacheName) =>
      cacheName.startsWith(FEEDGO_PRECACHE_PREFIX) &&
      cacheName !== currentPrecacheName,
  );

  await Promise.all(obsoleteNames.map((cacheName) => cacheStorage.delete(cacheName)));
  return obsoleteNames;
}

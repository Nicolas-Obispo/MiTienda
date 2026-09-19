const OPAQUE_HANDLE_PATTERN = /^[A-Za-z0-9_-]{32,128}$/;
const HANDLE_MEMORY_TTL_MS = 2 * 60 * 1000;
const exchangesByHandle = new Map();

export function getGoogleSessionHandle(search) {
  const params = new URLSearchParams(search);
  const handles = params.getAll("handle");

  if (handles.length !== 1 || params.size !== 1) return null;
  const [handle] = handles;
  return OPAQUE_HANDLE_PATTERN.test(handle) ? handle : null;
}

/**
 * React puede repetir efectos en desarrollo. Este coalescing vive sólo en
 * memoria y evita un segundo POST normal; el backend conserva la autoridad
 * one-use y no se guarda el handle en ningún storage ni cache de queries.
 */
export function exchangeGoogleSessionOnce(handle, exchange, purpose = "authentication") {
  const key = `${purpose}:${handle}`;
  const current = exchangesByHandle.get(key);
  if (current) return current;

  const request = Promise.resolve().then(() => exchange(handle));
  exchangesByHandle.set(key, request);
  const cleanupTimer = globalThis.setTimeout(
    () => exchangesByHandle.delete(key),
    HANDLE_MEMORY_TTL_MS,
  );
  // En Node el timer no debe mantener vivos los tests; en browser conserva la
  // misma vida efímera del handle.
  cleanupTimer?.unref?.();
  return request;
}

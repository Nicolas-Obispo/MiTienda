export const AUTH_TOKEN_STORAGE_KEY = "access_token";

export function normalizeAuthToken(value) {
  return value && value !== "null" && value !== "undefined" ? value : null;
}

export function shouldClearAuthSession(
  activeToken,
  requestToken = null,
  activeGeneration = null,
  requestGeneration = null
) {
  if (requestGeneration !== null && activeGeneration !== requestGeneration) {
    return false;
  }
  return !requestToken || activeToken === requestToken;
}

export function removeStoredAuthTokenIfCurrent(storage, requestToken = null) {
  const storedToken = normalizeAuthToken(storage.getItem(AUTH_TOKEN_STORAGE_KEY));
  if (requestToken && storedToken && storedToken !== requestToken) return false;
  if (storedToken) storage.removeItem(AUTH_TOKEN_STORAGE_KEY);
  return true;
}

export function getTokenFromStorageEvent(event, expectedStorage) {
  if (
    event?.key !== AUTH_TOKEN_STORAGE_KEY ||
    (event.storageArea && event.storageArea !== expectedStorage)
  ) {
    return undefined;
  }
  return normalizeAuthToken(event.newValue);
}

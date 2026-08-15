export const REQUEST_HANDLING = Object.freeze({
  NETWORK_ONLY: "network-only",
  NAVIGATION: "navigation-network-first",
  PRECACHE: "precache",
});

const FRONTEND_ROUTES = new Set([
  "/",
  "/terminos-y-condiciones",
  "/politica-de-privacidad",
  "/login",
  "/registro",
  "/feed",
  "/ranking",
  "/ver-seguidos",
  "/explorar",
  "/perfil",
]);

const FRONTEND_DYNAMIC_ROUTES = [
  /^\/comercios\/[^/]+\/?$/,
  /^\/publicaciones\/[^/]+\/?$/,
];

const SENSITIVE_PATH_PREFIXES = [
  "/uploads",
  "/media",
  "/geocoding",
];

function normalizePathname(pathname) {
  if (pathname === "/") return pathname;
  return pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;
}

function isFrontendNavigation(pathname) {
  const normalized = normalizePathname(pathname);
  return (
    FRONTEND_ROUTES.has(normalized) ||
    FRONTEND_DYNAMIC_ROUTES.some((pattern) => pattern.test(pathname))
  );
}

function isWithinPath(pathname, basePathname) {
  const base = normalizePathname(basePathname);
  if (base === "/") return true;
  return pathname === base || pathname.startsWith(`${base}/`);
}

function isApiRequest(url, appOrigin, apiUrl) {
  if (url.origin === apiUrl.origin && apiUrl.origin !== appOrigin) return true;

  return (
    url.origin === appOrigin &&
    apiUrl.origin === appOrigin &&
    normalizePathname(apiUrl.pathname) !== "/" &&
    isWithinPath(url.pathname, apiUrl.pathname)
  );
}

export function isConfiguredApiRequest({ requestUrl, appOrigin, apiBaseUrl }) {
  const normalizedAppOrigin = new URL(appOrigin).origin;
  return isApiRequest(
    new URL(requestUrl, normalizedAppOrigin),
    normalizedAppOrigin,
    new URL(apiBaseUrl, normalizedAppOrigin),
  );
}

function hasAuthorization(request) {
  return Boolean(request.headers?.has?.("Authorization"));
}

function toPrecachePath(entry, appOrigin) {
  const entryUrl = typeof entry === "string" ? entry : entry?.url;
  if (!entryUrl) return null;

  const url = new URL(entryUrl, appOrigin);
  return url.origin === appOrigin ? `${url.pathname}${url.search}` : null;
}

export function createRequestClassifier({
  appOrigin,
  apiBaseUrl,
  precacheEntries = [],
}) {
  const normalizedAppOrigin = new URL(appOrigin).origin;
  const apiUrl = new URL(apiBaseUrl, normalizedAppOrigin);
  const precachePaths = new Set(
    precacheEntries
      .map((entry) => toPrecachePath(entry, normalizedAppOrigin))
      .filter(Boolean),
  );

  return function classifyRequest(request) {
    const method = String(request.method || "GET").toUpperCase();
    if (method !== "GET" && method !== "HEAD") {
      return REQUEST_HANDLING.NETWORK_ONLY;
    }

    const url = new URL(request.url, normalizedAppOrigin);

    if (
      isApiRequest(url, normalizedAppOrigin, apiUrl) ||
      SENSITIVE_PATH_PREFIXES.some((prefix) => isWithinPath(url.pathname, prefix))
    ) {
      return REQUEST_HANDLING.NETWORK_ONLY;
    }

    if (hasAuthorization(request)) return REQUEST_HANDLING.NETWORK_ONLY;
    if (url.origin !== normalizedAppOrigin) return REQUEST_HANDLING.NETWORK_ONLY;

    if (
      method === "GET" &&
      request.mode === "navigate" &&
      isFrontendNavigation(url.pathname)
    ) {
      return REQUEST_HANDLING.NAVIGATION;
    }

    if (method === "GET" && precachePaths.has(`${url.pathname}${url.search}`)) {
      return REQUEST_HANDLING.PRECACHE;
    }

    return REQUEST_HANDLING.NETWORK_ONLY;
  };
}

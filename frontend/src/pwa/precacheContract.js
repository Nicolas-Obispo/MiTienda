export const PWA_PRECACHE_GLOB_PATTERNS = Object.freeze([
  "index.html",
  "assets/**/*.js",
  "assets/**/*.css",
  "theme-tokens.css",
  "theme-bootstrap.css",
  "theme-bootstrap.js",
  "manifest.json",
  "favicon-48.png",
  "apple-touch-icon-180.png",
  "icon-192.png",
  "icon-512.png",
  "icon-maskable-512.png",
  "logo_Feedgo.png",
]);

export const PWA_PRECACHE_GLOB_IGNORES = Object.freeze([
  "service-worker.js",
  "vite.svg",
  "icon-180.png",
  "**/*.map",
]);

export const PWA_REQUIRED_PRECACHE_URLS = Object.freeze([
  "/index.html",
  "/theme-tokens.css",
  "/theme-bootstrap.css",
  "/theme-bootstrap.js",
  "/manifest.json",
  "/favicon-48.png",
  "/apple-touch-icon-180.png",
  "/icon-192.png",
  "/icon-512.png",
  "/icon-maskable-512.png",
  "/logo_Feedgo.png",
]);

export const PWA_FORBIDDEN_PRECACHE_URLS = Object.freeze([
  "/service-worker.js",
  "/vite.svg",
  "/icon-180.png",
]);

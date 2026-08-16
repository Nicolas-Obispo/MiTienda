import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { fileURLToPath } from "node:url";
import path from "node:path";

const frontendRoot = path.resolve(fileURLToPath(new URL("../../", import.meta.url)));
const fixturesRoot = path.join(frontendRoot, ".pwa-fixtures");
const versions = Object.freeze({
  n: path.join(fixturesRoot, "version-n"),
  "n-plus-one": path.join(fixturesRoot, "version-n-plus-one"),
});
const allowedFaults = new Set([
  "none",
  "worker-invalid",
  "registration-failed",
  "asset-missing",
  "api-unreachable",
  "precache-incomplete",
  "update-failed",
]);
const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
};

let activeVersion = "n";
let fault = "none";

function sendJson(response, status, body) {
  response.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
  response.end(JSON.stringify(body));
}

function resolveFixturePath(root, pathname) {
  const relativePath = pathname === "/" ? "index.html" : pathname.replace(/^\/+/, "");
  const resolved = path.resolve(root, relativePath);
  return resolved.startsWith(`${root}${path.sep}`) ? resolved : null;
}

function serveFile(response, filePath) {
  const extension = path.extname(filePath).toLowerCase();
  const headers = { "Content-Type": contentTypes[extension] || "application/octet-stream" };
  if (path.basename(filePath) === "service-worker.js" || extension === ".html") {
    headers["Cache-Control"] = "no-store";
  }
  if (path.basename(filePath) === "service-worker.js") {
    headers["Service-Worker-Allowed"] = "/";
  }
  response.writeHead(200, headers);
  createReadStream(filePath).pipe(response);
}

export function createPwaFixtureServer() {
  return createServer((request, response) => {
  const url = new URL(request.url, "http://127.0.0.1:4173");

  if (request.method === "GET" && url.pathname === "/__pwa-e2e/status") {
    sendJson(response, 200, { activeVersion, fault });
    return;
  }
  if (request.method === "POST" && url.pathname === "/__pwa-e2e/reset") {
    activeVersion = "n";
    fault = "none";
    sendJson(response, 200, { activeVersion, fault });
    return;
  }
  if (request.method === "POST" && url.pathname.startsWith("/__pwa-e2e/version/")) {
    const requestedVersion = url.pathname.slice("/__pwa-e2e/version/".length);
    if (!versions[requestedVersion]) {
      sendJson(response, 400, { error: "unknown-version" });
      return;
    }
    activeVersion = requestedVersion;
    fault = "none";
    sendJson(response, 200, { activeVersion, fault });
    return;
  }
  if (request.method === "POST" && url.pathname.startsWith("/__pwa-e2e/fault/")) {
    const requestedFault = url.pathname.slice("/__pwa-e2e/fault/".length);
    if (!allowedFaults.has(requestedFault)) {
      sendJson(response, 400, { error: "unknown-fault" });
      return;
    }
    fault = requestedFault;
    sendJson(response, 200, { activeVersion, fault });
    return;
  }

  if (url.pathname.startsWith("/api/fixture/")) {
    if (fault === "api-unreachable") {
      request.socket.destroy();
      return;
    }

    const statusMatch = url.pathname.match(/^\/api\/fixture\/status\/(\d{3})$/);
    const status = statusMatch ? Number(statusMatch[1]) : 200;
    sendJson(response, status, { fixture: true, method: request.method, status });
    return;
  }

  if (url.pathname === "/service-worker.js") {
    if (fault === "registration-failed") {
      response.writeHead(404).end();
      return;
    }
    if (fault === "worker-invalid" || fault === "update-failed") {
      response.writeHead(200, {
        "Cache-Control": "no-store",
        "Content-Type": "text/javascript; charset=utf-8",
        "Service-Worker-Allowed": "/",
      });
      response.end("this is an intentionally invalid service worker {{{");
      return;
    }
  }

  if (
    (fault === "precache-incomplete" && url.pathname === "/theme-tokens.css") ||
    (fault === "asset-missing" && url.pathname.includes("/assets/"))
  ) {
    response.writeHead(404).end();
    return;
  }

  const root = versions[activeVersion];
  if (!existsSync(root)) {
    sendJson(response, 503, { error: "fixtures-not-built" });
    return;
  }

  let filePath = resolveFixturePath(root, decodeURIComponent(url.pathname));
  if (filePath && existsSync(filePath) && statSync(filePath).isFile()) {
    serveFile(response, filePath);
    return;
  }

  const acceptsHtml = request.headers.accept?.includes("text/html");
  if (request.method === "GET" && acceptsHtml && !path.extname(url.pathname)) {
    filePath = path.join(root, "index.html");
    serveFile(response, filePath);
    return;
  }

  response.writeHead(404).end();
  });
}

export function startPwaFixtureServer() {
  const server = createPwaFixtureServer();
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(4173, "127.0.0.1", () => resolve(server));
  });
}

const invokedAsScript = process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedAsScript) {
  await startPwaFixtureServer();
  process.stdout.write("FeedGo PWA fixture server: http://127.0.0.1:4173\n");
}

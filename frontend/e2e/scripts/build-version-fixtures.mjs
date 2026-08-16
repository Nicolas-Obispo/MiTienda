import { rmSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const frontendRoot = path.resolve(fileURLToPath(new URL("../../", import.meta.url)));
const fixturesRoot = path.join(frontendRoot, ".pwa-fixtures");

if (path.dirname(fixturesRoot) !== frontendRoot) {
  throw new Error("Directorio de fixtures fuera del frontend.");
}

const viteCli = path.join(frontendRoot, "node_modules", "vite", "bin", "vite.js");
for (const [version, directory] of [
  ["N", "version-n"],
  ["N+1", "version-n-plus-one"],
]) {
  rmSync(path.join(fixturesRoot, directory), { force: true, recursive: true });
  execFileSync(
    process.execPath,
    [viteCli, "build", "--mode", "pwa-e2e", "--outDir", `.pwa-fixtures/${directory}`],
    {
      cwd: frontendRoot,
      env: {
        ...process.env,
        FEEDGO_PWA_TEST_VERSION: version,
        VITE_API_URL: "http://127.0.0.1:4173/api",
      },
      stdio: "inherit",
    },
  );
}

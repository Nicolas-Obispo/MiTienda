import { startPwaFixtureServer } from "./scripts/pwa-fixture-server.mjs";

export default async function globalSetup() {
  const server = await startPwaFixtureServer();

  return async () => {
    server.closeAllConnections?.();
    await new Promise((resolve, reject) => {
      server.close((error) => error ? reject(error) : resolve());
    });
  };
}

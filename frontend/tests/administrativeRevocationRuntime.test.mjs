import assert from "node:assert/strict";
import test from "node:test";

import { QueryClient, QueryObserver, focusManager } from "@tanstack/react-query";

import { ADMINISTRATIVE_CAPABILITIES_QUERY_RUNTIME_OPTIONS } from "../src/features/administration/hooks/administrativeCapabilitiesQueryOptions.js";

function waitFor(predicate, timeoutMs = 1000) {
  const startedAt = Date.now();
  return new Promise((resolve, reject) => {
    const check = () => {
      if (predicate()) return resolve();
      if (Date.now() - startedAt >= timeoutMs) {
        return reject(new Error("Timeout esperando revalidacion de capacidades"));
      }
      setTimeout(check, 5);
    };
    check();
  });
}

test("focus revalidates the shared capability query and removes a revoked access", async () => {
  let serverCapabilities = ["operations.incidents.manage", "operations.status.read"];
  let requests = 0;
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
  });
  client.mount();

  const observer = new QueryObserver(client, {
    ...ADMINISTRATIVE_CAPABILITIES_QUERY_RUNTIME_OPTIONS,
    queryKey: ["administration", "capabilities", 32],
    queryFn: async () => {
      requests += 1;
      return { es_operador: true, capacidades: [...serverCapabilities] };
    },
  });
  const unsubscribe = observer.subscribe(() => {});

  try {
    await waitFor(() => observer.getCurrentResult().isSuccess);
    assert.deepEqual(observer.getCurrentResult().data.capacidades, [
      "operations.incidents.manage",
      "operations.status.read",
    ]);

    serverCapabilities = ["operations.incidents.manage"];
    focusManager.setFocused(false);
    focusManager.setFocused(true);

    await waitFor(
      () => requests >= 2 && observer.getCurrentResult().data?.capacidades.length === 1,
    );
    assert.deepEqual(observer.getCurrentResult().data.capacidades, [
      "operations.incidents.manage",
    ]);
  } finally {
    unsubscribe();
    client.unmount();
    client.clear();
    focusManager.setFocused(undefined);
  }
});

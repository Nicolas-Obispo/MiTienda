import { useSyncExternalStore } from "react";

import { connectivityRuntime } from "./connectivityRuntime.js";

export function useConnectivityState() {
  return useSyncExternalStore(
    connectivityRuntime.subscribe,
    connectivityRuntime.getSnapshot,
    connectivityRuntime.getSnapshot,
  );
}

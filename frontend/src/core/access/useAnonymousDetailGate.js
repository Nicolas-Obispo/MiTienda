import { useEffect } from "react";

import { scheduleAnonymousDetailGate } from "@core/access/anonymousDetailGate";

export function useAnonymousDetailGate({ enabled, ready, onExpire }) {
  useEffect(() => {
    if (!enabled || !ready) return undefined;
    return scheduleAnonymousDetailGate({ onExpire });
  }, [enabled, onExpire, ready]);
}

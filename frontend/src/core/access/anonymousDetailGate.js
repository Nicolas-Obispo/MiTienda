export const ANONYMOUS_DETAIL_DELAY_MS = 5000;

export function scheduleAnonymousDetailGate({ onExpire, setTimer = setTimeout, clearTimer = clearTimeout }) {
  const timerId = setTimer(onExpire, ANONYMOUS_DETAIL_DELAY_MS);
  return () => clearTimer(timerId);
}

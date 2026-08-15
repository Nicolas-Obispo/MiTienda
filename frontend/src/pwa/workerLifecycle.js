import { isActivationMessage, PWA_MESSAGE } from "./lifecycleContract.js";

export async function handleActivationRequest({
  data,
  responsePort,
  clientsObject,
  skipWaiting,
}) {
  if (!isActivationMessage(data)) return false;

  const activeWindows = await clientsObject.matchAll({
    type: "window",
    includeUncontrolled: true,
  });

  if (activeWindows.length > 1) {
    responsePort?.postMessage({
      type: PWA_MESSAGE.ACTIVATION_BLOCKED_MULTITAB,
      activationId: data.activationId,
    });
    return false;
  }

  try {
    await skipWaiting();
  } catch {
    responsePort?.postMessage({
      type: PWA_MESSAGE.ACTIVATION_FAILED,
      activationId: data.activationId,
    });
    return false;
  }

  responsePort?.postMessage({
    type: PWA_MESSAGE.ACTIVATION_ACCEPTED,
    activationId: data.activationId,
  });
  return true;
}

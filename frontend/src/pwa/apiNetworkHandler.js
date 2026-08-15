import { PWA_MESSAGE } from "./lifecycleContract.js";

export function createApiNetworkHandler({ fetchFunction, notifyClients }) {
  const notifySafely = async (message) => {
    try {
      await notifyClients(message);
    } catch {
      // La señal técnica nunca puede alterar la respuesta o el error de red.
    }
  };

  return async function handleApiRequest({ request }) {
    let response;
    try {
      response = await fetchFunction(request);
    } catch (transportError) {
      await notifySafely({ type: PWA_MESSAGE.BACKEND_UNREACHABLE });
      throw transportError;
    }

    await notifySafely({ type: PWA_MESSAGE.BACKEND_REACHABLE });
    return response;
  };
}

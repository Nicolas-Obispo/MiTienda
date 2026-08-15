import { CONNECTIVITY_STATE } from "@/pwa/connectivityRuntime";
import { useConnectivityState } from "@/pwa/useConnectivityState";
import Alert from "@shared/components/primitives/Alert";

export default function ConnectivityNotice() {
  const connectivity = useConnectivityState();

  if (
    connectivity !== CONNECTIVITY_STATE.OFFLINE &&
    connectivity !== CONNECTIVITY_STATE.BACKEND_UNREACHABLE
  ) {
    return null;
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pt-3">
      <Alert className="px-3 py-2 text-xs" role="status" variant="warning">
        {connectivity === CONNECTIVITY_STATE.OFFLINE
          ? "Sin conexión. Podés recorrer la aplicación, pero los datos y acciones que requieren servidor no están disponibles."
          : "Hay conexión, pero FeedGo no puede comunicarse con el servidor. Los datos pueden no estar actualizados."}
      </Alert>
    </div>
  );
}

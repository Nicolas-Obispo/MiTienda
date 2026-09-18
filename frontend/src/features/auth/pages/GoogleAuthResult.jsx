import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { getInternalReturnTo } from "@core/navigation/internalReturnTo";
import { useAuth } from "@features/auth/hooks/useAuth";
import { exchangeGoogleSession } from "@features/auth/services/authService";
import {
  exchangeGoogleSessionOnce,
  getGoogleSessionHandle,
} from "@features/auth/services/googleSessionResult";
import { Alert, Button, Surface } from "@shared";

export default function GoogleAuthResult() {
  const location = useLocation();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [initialHandle] = useState(() => getGoogleSessionHandle(location.search));
  const [state, setState] = useState(initialHandle ? "loading" : "invalid");

  useEffect(() => {
    const handle = initialHandle;
    // El handle es efímero: se elimina de la barra antes del canje y no se
    // conserva en estado, storage ni TanStack Query.
    if (location.search) navigate(location.pathname, { replace: true });
    if (!handle) return undefined;
    let active = true;

    void exchangeGoogleSessionOnce(handle, exchangeGoogleSession)
      .then((result) => {
        if (!active) return;
        if (result?.status === "authenticated" && typeof result.token === "string") {
          login(result.token);
          navigate(getInternalReturnTo(result.return_to, "/feed"), { replace: true });
          return;
        }

        setState(result?.status === "action_required" ? "action-required" : "invalid");
      })
      .catch(() => {
        if (active) setState("error");
      });

    return () => {
      active = false;
    };
  }, [initialHandle, location.pathname, location.search, login, navigate]);

  if (state === "loading") {
    return (
      <main className="mx-auto flex min-h-[50vh] w-full max-w-md items-center px-4">
        <Surface variant="elevated" className="w-full p-6 text-center">
          <p className="text-sm text-secondary">Completando el acceso…</p>
        </Surface>
      </main>
    );
  }

  const message = state === "action-required"
    ? "No pudimos completar este acceso. Iniciá sesión o creá una cuenta con tu método habitual."
    : "No pudimos completar el acceso con Google. Volvé a intentarlo desde FeedGo.";

  return (
    <main className="mx-auto flex min-h-[50vh] w-full max-w-md items-center px-4">
      <Surface variant="elevated" className="w-full space-y-4 p-6 text-center">
        <Alert role="alert" variant="danger" className="text-left">
          {message}
        </Alert>
        <div className="flex flex-wrap justify-center gap-3">
          <Button variant="primary" onClick={() => navigate("/login")}>
            Iniciar sesión
          </Button>
          <Button variant="ghost" onClick={() => navigate("/registro")}>
            Crear cuenta
          </Button>
        </div>
      </Surface>
    </main>
  );
}

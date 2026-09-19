import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { getInternalReturnTo } from "@core/navigation/internalReturnTo";
import { useAuth } from "@features/auth/hooks/useAuth";
import { exchangeGoogleReauthenticationSession } from "@features/auth/services/authService";
import {
  exchangeGoogleSessionOnce,
  getGoogleSessionHandle,
} from "@features/auth/services/googleSessionResult";
import { Alert, Button, Surface } from "@shared";

export default function GoogleReauthenticationResult() {
  const location = useLocation();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [initialHandle] = useState(() => getGoogleSessionHandle(location.search));
  const [state, setState] = useState(initialHandle ? "loading" : "invalid");

  useEffect(() => {
    const handle = initialHandle;
    if (location.search) navigate(location.pathname, { replace: true });
    if (!handle) return undefined;
    let active = true;

    void exchangeGoogleSessionOnce(
      handle,
      exchangeGoogleReauthenticationSession,
      "reauthentication",
    )
      .then((result) => {
        if (!active) return;
        if (result?.status === "authenticated" && typeof result.token === "string") {
          login(result.token);
          navigate(getInternalReturnTo(result.return_to, "/perfil?security=access"), { replace: true });
          return;
        }
        setState("invalid");
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
          <p className="text-sm text-secondary">Completando la reautenticacion...</p>
        </Surface>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-[50vh] w-full max-w-md items-center px-4">
      <Surface variant="elevated" className="w-full space-y-4 p-6 text-center">
        <Alert role="alert" variant="danger" className="text-left">
          No pudimos completar la reautenticacion con Google. Volve a intentarlo desde Seguridad y acceso.
        </Alert>
        <Button variant="primary" onClick={() => navigate("/perfil")}>
          Volver al perfil
        </Button>
      </Surface>
    </main>
  );
}

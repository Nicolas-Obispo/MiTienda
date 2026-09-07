import { useCallback, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import ActiveLayer from "@core/components/ActiveLayer";
import { ProtectedActionContext } from "@core/access/ProtectedActionContext";
import { getInternalReturnTo } from "@core/navigation/internalReturnTo";
import { useAuth } from "@features/auth";
import { Button, Surface } from "@shared";

const DEFAULT_MESSAGE =
  "Para hacer esto, necesitás crear una cuenta o iniciar sesión.";

export function ProtectedActionProvider({ children }) {
  const { estaAutenticado } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const loginButtonRef = useRef(null);
  const [wall, setWall] = useState(null);

  const closeAuthWall = useCallback(() => setWall(null), []);

  const requireAuthentication = useCallback(
    (options = {}) => {
      if (estaAutenticado) return false;

      const normalizedOptions =
        typeof options === "string" ? { message: options } : options;
      const currentContext = `${location.pathname}${location.search}`;
      setWall({
        message: normalizedOptions.message || DEFAULT_MESSAGE,
        returnTo: getInternalReturnTo(
          normalizedOptions.returnTo || currentContext,
          "/"
        ),
      });
      return true;
    },
    [estaAutenticado, location.pathname, location.search]
  );

  const value = useMemo(
    () => ({
      estaAutenticado,
      isAuthWallOpen: Boolean(wall),
      requireAuthentication,
      closeAuthWall,
    }),
    [closeAuthWall, estaAutenticado, requireAuthentication, wall]
  );

  function goToAuth(pathname) {
    const returnTo = wall?.returnTo || "/";
    const message = wall?.message || DEFAULT_MESSAGE;
    setWall(null);
    navigate(pathname, { state: { message, returnTo } });
  }

  return (
    <ProtectedActionContext.Provider value={value}>
      <div inert={wall ? true : undefined} aria-hidden={wall ? "true" : undefined}>
        {children}
      </div>

      {wall && (
        <ActiveLayer
          onClose={closeAuthWall}
          labelledBy="auth-wall-title"
          describedBy="auth-wall-description"
          initialFocusRef={loginButtonRef}
          contentClassName="mx-4 w-full max-w-md"
          backdropClassName="bg-overlay-backdrop backdrop-blur-sm"
          zIndex={1400}
        >
          <Surface variant="elevated" className="p-6 text-center">
            <img
              src="/logo_Feedgo.png"
              alt="FeedGo"
              className="mx-auto h-20 w-20 object-contain"
            />
            <h2 id="auth-wall-title" className="mt-3 text-xl font-semibold text-primary">
              Ingresá para continuar
            </h2>
            <p id="auth-wall-description" className="mt-2 text-sm text-secondary">
              {wall.message}
            </p>
            <div className="mt-5 flex flex-col gap-2 sm:flex-row sm:justify-center">
              <Button
                ref={loginButtonRef}
                type="button"
                onClick={() => goToAuth("/login")}
                variant="primary"
              >
                Iniciar sesión
              </Button>
              <Button
                type="button"
                onClick={() => goToAuth("/registro")}
                variant="secondary"
              >
                Crear cuenta
              </Button>
            </div>
          </Surface>
        </ActiveLayer>
      )}
    </ProtectedActionContext.Provider>
  );
}

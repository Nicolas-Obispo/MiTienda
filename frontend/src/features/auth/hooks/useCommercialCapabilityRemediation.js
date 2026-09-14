import { useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { getInternalReturnTo } from "@core/navigation/internalReturnTo";
import { useAuth } from "@features/auth/hooks/useAuth";

export const COMMERCIAL_CAPABILITY_REQUIRED = "commercial_capability_required";

export function isCommercialCapabilityError(error) {
  return (
    error?.status === 403 &&
    error?.code === COMMERCIAL_CAPABILITY_REQUIRED
  );
}

/**
 * Puente UX para capabilities comerciales. Nunca calcula permisos: el unico
 * dato preventivo es el derivado de /usuarios/me y el backend conserva la
 * autoridad final ante cualquier mutacion.
 */
export function useCommercialCapabilityRemediation() {
  const navigate = useNavigate();
  const location = useLocation();
  const { usuario, refrescarUsuario } = useAuth();

  const currentReturnTo = useCallback(
    (requestedReturnTo) =>
      getInternalReturnTo(
        requestedReturnTo || `${location.pathname}${location.search}`,
        "/perfil"
      ),
    [location.pathname, location.search]
  );

  const abrirRemediation = useCallback(
    async ({ returnTo } = {}) => {
      // Se refresca antes de renderizar remediation: los derivados son
      // exclusivamente backend-owned y pueden haber cambiado entre acciones.
      await refrescarUsuario();
      const safeReturnTo = currentReturnTo(returnTo);
      navigate(`/perfil?remediation=commercial&returnTo=${encodeURIComponent(safeReturnTo)}`);
    },
    [currentReturnTo, navigate, refrescarUsuario]
  );

  const intentarAccionComercial = useCallback(
    async (capability, options = {}) => {
      // `false` explicito permite anticipar UX; undefined mantiene el intento
      // normal para que una carga tardia de /me no se vuelva un bloqueo local.
      if (usuario?.capabilities?.[capability] !== false) return true;
      await abrirRemediation(options);
      return false;
    },
    [abrirRemediation, usuario]
  );

  const manejarErrorCapability = useCallback(
    async (error, options = {}) => {
      if (!isCommercialCapabilityError(error)) return false;
      await abrirRemediation(options);
      return true;
    },
    [abrirRemediation]
  );

  return {
    intentarAccionComercial,
    manejarErrorCapability,
  };
}

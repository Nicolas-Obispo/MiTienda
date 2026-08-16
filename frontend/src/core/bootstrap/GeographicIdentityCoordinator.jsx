import { useEffect } from "react";

import { useAuth } from "@features/auth/hooks/useAuth";
import { useGeographicContext } from "@shared/location/useGeographicContext";

export default function GeographicIdentityCoordinator({ children }) {
  const { estaAutenticado, usuario } = useAuth();
  const { reconcileIdentity } = useGeographicContext();
  const identityKey = estaAutenticado && usuario?.id ? `user:${usuario.id}` : "anonymous";

  useEffect(() => {
    reconcileIdentity({
      identityKey,
      profileTerritory: estaAutenticado && usuario?.ciudad && usuario?.provincia
        ? { city: usuario.ciudad, province: usuario.provincia }
        : null,
    });
  }, [estaAutenticado, identityKey, reconcileIdentity, usuario?.ciudad, usuario?.provincia]);

  return children;
}

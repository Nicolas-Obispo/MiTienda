import { useAuth } from "@features/auth";
import { useAdministrativeCapabilities } from "@features/administration/hooks/useAdministrativeCapabilities";

export function AdministrativeAccessGuard({
  capability,
  children,
  fallback = null,
  loadingFallback = null,
}) {
  const { estaAutenticado, isCargandoUsuario } = useAuth();
  const { isLoading, isError, tieneCapacidad } = useAdministrativeCapabilities();

  if (!estaAutenticado) return fallback;
  if (isCargandoUsuario || isLoading) return loadingFallback;
  if (isError || !tieneCapacidad(capability)) return fallback;

  return children;
}

import { Link, useLocation } from "react-router-dom";

import { useAdministrativeCapabilities } from "@features/administration/hooks/useAdministrativeCapabilities";

const NAVIGABLE_CAPABILITIES = [
  "moderation.reports.read",
  "operations.incidents.manage",
  "operations.status.read",
];

export function AdministrativeNavigationLink() {
  const location = useLocation();
  const { isLoading, isError, tieneCapacidad } = useAdministrativeCapabilities();
  const visible = !isLoading && !isError && NAVIGABLE_CAPABILITIES.some(tieneCapacidad);

  if (!visible) return null;
  return (
    <Link to="/administracion" className="interactive-bubble group min-h-11 min-w-0 w-full justify-center whitespace-normal break-words text-center text-xs sm:w-auto sm:shrink-0 sm:text-sm">
      <span className={location.pathname.startsWith("/administracion") ? "text-selected-text" : "text-secondary group-hover:text-primary"}>
        Administración
      </span>
    </Link>
  );
}

import { Link } from "react-router-dom";

import { Alert, Skeleton, Surface } from "@shared";
import { useAdministrativeCapabilities } from "@features/administration/hooks/useAdministrativeCapabilities";
import { useFocusOnAdministrativeError } from "@features/administration/hooks/useAdministrativeFocus";
import InteractiveLiquidLayers from "@shared/components/InteractiveLiquidLayers";

const SURFACES = [
  { capability: "moderation.reports.read", to: "/administracion/denuncias", title: "Denuncias", description: "Consultar denuncias recibidas." },
  { capability: "operations.incidents.manage", to: "/administracion/incidentes", title: "Incidentes", description: "Gestionar expedientes operativos." },
  { capability: "operations.status.read", to: "/administracion/operaciones/estado", title: "Estado operativo", description: "Consultar el estado diagnostico disponible." },
];

export function AdministrativeHomePage() {
  const { isLoading, isError, tieneCapacidad } = useAdministrativeCapabilities();
  const errorRef = useFocusOnAdministrativeError(isError);

  if (isLoading) return <Skeleton className="h-40 w-full" />;
  if (isError) return <Alert ref={errorRef} tabIndex={-1} variant="danger" className="outline-none">No se pudieron consultar tus capacidades administrativas.</Alert>;

  const available = SURFACES.filter(({ capability }) => tieneCapacidad(capability));

  return (
    <main className="mx-auto w-full max-w-5xl space-y-5 px-4 py-6 sm:px-6 sm:py-8" aria-labelledby="administration-title">
      <div>
        <h1 id="administration-title" className="text-2xl font-bold">Administración</h1>
        <p className="text-secondary">Accesos habilitados para tu operación.</p>
      </div>
      {available.length === 0 ? (
        <Alert>No tenés superficies administrativas disponibles.</Alert>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {available.map((surface) => (
            <Surface key={surface.to} className="flex min-w-0 flex-col p-4 sm:p-5">
              <h2 className="font-semibold">{surface.title}</h2>
              <p className="mb-3 text-sm text-secondary">{surface.description}</p>
              <Link className="interactive-bubble interactive-bubble--liquid mt-auto inline-flex min-h-11 w-full items-center justify-center text-sm font-semibold text-interactive-primary sm:w-auto" to={surface.to}>Abrir<InteractiveLiquidLayers /></Link>
            </Surface>
          ))}
        </div>
      )}
      {available.length > 0 ? <Surface className="p-4 sm:p-5">
        <h2 className="font-semibold">¿Necesitás ayuda?</h2>
        <p className="mt-1 text-sm text-secondary">Consultá cómo revisar denuncias, registrar decisiones, gestionar incidentes y usar el estado operativo de forma segura.</p>
        <Link className="interactive-bubble interactive-bubble--liquid mt-3 inline-flex min-h-11 w-full items-center justify-center text-sm font-semibold text-interactive-primary sm:w-auto" to="/administracion/guia">Abrir guía práctica<InteractiveLiquidLayers /></Link>
      </Surface> : null}
    </main>
  );
}

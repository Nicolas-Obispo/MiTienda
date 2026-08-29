import { useState } from "react";
import { Link } from "react-router-dom";

import { useAdministrativeCapabilities } from "@features/administration";
import { administrativeErrorMessage } from "@features/administration/utils/administrativeErrorMessages";
import { administrativeLabel } from "@features/administration/utils/administrativeLabels";
import { useFocusOnAdministrativeError } from "@features/administration/hooks/useAdministrativeFocus";
import {
  useOperationalResourceIntegrity,
  useOperationalStatus,
} from "@features/operations/hooks/useOperationalStatus";
import { Alert, Button, FormControl, Input, Select, Skeleton, Surface } from "@shared";
import InteractiveLiquidLayers from "@shared/components/InteractiveLiquidLayers";


function statusVariant(status) {
  if (status === "healthy") return "success";
  if (status === "unhealthy") return "danger";
  return "warning";
}


export default function OperationalStatusPage() {
  const status = useOperationalStatus();
  const capabilities = useAdministrativeCapabilities();
  const [draftType, setDraftType] = useState("historia");
  const [draftId, setDraftId] = useState("");
  const [target, setTarget] = useState(null);
  const integrity = useOperationalResourceIntegrity(target?.type, target?.id);
  const statusErrorRef = useFocusOnAdministrativeError(status.isError);
  const integrityErrorRef = useFocusOnAdministrativeError(integrity.isError);

  function inspect(event) {
    event.preventDefault();
    const resourceId = Number(draftId);
    if (Number.isInteger(resourceId) && resourceId > 0) {
      setTarget({ type: draftType, id: resourceId });
    }
  }

  return <main className="mx-auto w-full max-w-5xl space-y-5 px-4 py-6 sm:px-6 sm:py-8">
    <header>
      <h1 className="text-2xl font-semibold text-primary">Estado operativo seguro</h1>
      <p className="mt-2 text-sm text-secondary">
        Lectura volátil del proceso actual. No constituye historial, estado global, garantía de vigencia ni objetivo de recuperación.
      </p>
      <Link className="interactive-bubble interactive-bubble--liquid mt-3 inline-flex min-h-11 items-center text-link underline underline-offset-2" to="/administracion">Volver a Administración<InteractiveLiquidLayers /></Link>
    </header>

    {status.isLoading ? <Skeleton className="h-44 w-full" /> : null}
    {status.isError ? <Alert ref={statusErrorRef} tabIndex={-1} variant="danger" className="outline-none">{administrativeErrorMessage(status.error, "No se pudo consultar el estado operativo.")}</Alert> : null}
    {status.data ? <>
      <Surface className="p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-semibold text-primary">Salud del sistema</h2>
          <Button variant="secondary" className="min-h-11 w-full sm:w-auto" onClick={() => status.refetch()} disabled={status.isFetching}>Actualizar lectura</Button>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {status.data.health.components.map((component) => <Alert key={component.component} variant={statusVariant(component.status)}>
            <strong>{administrativeLabel(component.component)}</strong>: {administrativeLabel(component.status)}. {component.message}
          </Alert>)}
        </div>
      </Surface>

      <div className="grid gap-5 md:grid-cols-2">
        <Surface className="p-5">
          <h2 className="font-semibold text-primary">Worker de correo operativo</h2>
          <p className="mt-2 text-sm text-secondary">Estado local y volÃ¡til del proceso dedicado; no representa el estado global de un despliegue.</p>
          <p className="mt-4 text-sm font-medium text-primary">{administrativeLabel(status.data.operational_email_worker.status)}</p>
        </Surface>
        <Surface className="p-5">
          <h2 className="font-semibold text-primary">Evidencia de recuperación</h2>
          <p className="mt-2 text-sm text-secondary">Sólo informa disponibilidad y validez de evidencia; no ejecuta backup ni restore.</p>
          <dl className="mt-4 space-y-2 text-sm text-primary">
            <div><dt className="font-medium">Copia de seguridad</dt><dd>{administrativeLabel(status.data.recovery_evidence.backup.status)} · {administrativeLabel(status.data.recovery_evidence.backup.meaning)}</dd></div>
            <div><dt className="font-medium">Restauración</dt><dd>{administrativeLabel(status.data.recovery_evidence.restore.status)} · {administrativeLabel(status.data.recovery_evidence.restore.meaning)}</dd></div>
          </dl>
        </Surface>
        <Surface className="p-5">
          <h2 className="font-semibold text-primary">Señales recientes del proceso</h2>
          <p className="mt-2 text-sm text-secondary">Agregados locales sin etiquetas, payloads ni datos históricos.</p>
          {status.data.aggregates.length ? <ul className="mt-4 space-y-2 text-sm text-primary">{status.data.aggregates.map((item) => <li key={item.name}>{administrativeLabel(item.name)}: {item.value}</li>)}</ul> : <p className="mt-4 text-sm text-secondary">Sin muestras permitidas en este proceso.</p>}
        </Surface>
      </div>

      <Surface className="p-5">
        <h2 className="font-semibold text-primary">Eventos recientes de alerta</h2>
        <p className="mt-2 text-sm text-secondary">Son eventos volátiles del proceso actual; no demuestran que una condición continúe activa.</p>
        {status.data.alerts.length ? <ul className="mt-4 space-y-3">{status.data.alerts.map((alert) => <li key={alert.alert_id} className="text-sm text-primary"><strong>{administrativeLabel(alert.severity)}</strong> · {administrativeLabel(alert.rule_name, "Alerta operativa")} · {administrativeLabel(alert.status)}<br /><span className="text-secondary">{alert.message}</span></li>)}</ul> : <p className="mt-4 text-sm text-secondary">Sin eventos recientes.</p>}
      </Surface>
    </> : null}

    <Surface className="p-5">
      <h2 className="font-semibold text-primary">Inspección puntual de integridad</h2>
      <p className="mt-2 text-sm text-secondary">La consulta no modifica el recurso, no recorre el filesystem y no verifica URLs externas.</p>
      <form className="mt-4 grid min-w-0 gap-3 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]" onSubmit={inspect}>
        <FormControl label="Tipo de recurso"><Select value={draftType} onChange={(event) => setDraftType(event.target.value)}><option value="comercio">Comercio</option><option value="publicacion">Publicación</option><option value="historia">Historia</option></Select></FormControl>
        <FormControl label="ID"><Input type="number" min="1" required value={draftId} onChange={(event) => setDraftId(event.target.value)} /></FormControl>
        <Button type="submit" className="min-h-11 w-full self-end sm:w-auto">Inspeccionar</Button>
      </form>
      {integrity.isFetching ? <Skeleton className="mt-4 h-28 w-full" /> : null}
      {integrity.isError ? <Alert ref={integrityErrorRef} tabIndex={-1} variant="danger" className="mt-4 outline-none">{administrativeErrorMessage(integrity.error, "No se pudo consultar ese recurso.")}</Alert> : null}
      {integrity.data ? <div className="min-w-0 mt-4 space-y-2 text-sm text-primary">
        <p className="break-all"><strong>{administrativeLabel(integrity.data.resource_type)} #{integrity.data.resource_id}</strong></p>
        <p>Estado del contenido: {administrativeLabel(integrity.data.lifecycle)} · Moderación: {integrity.data.moderation_hidden ? "Oculto" : "Visible"}</p>
        <p>Archivo: {administrativeLabel(integrity.data.asset.kind)} · {administrativeLabel(integrity.data.asset.status)}</p>
        {integrity.data.issues.map((issue) => <Alert key={issue.code} variant="warning">{administrativeLabel(issue.code)}</Alert>)}
        {integrity.data.issues.length && capabilities.tieneCapacidad("operations.incidents.manage") ? <Link className="interactive-bubble interactive-bubble--liquid inline-flex min-h-11 w-full items-center justify-center text-link sm:w-auto" to="/administracion/incidentes">Abrir incidente mediante el flujo existente<InteractiveLiquidLayers /></Link> : null}
      </div> : null}
    </Surface>
  </main>;
}

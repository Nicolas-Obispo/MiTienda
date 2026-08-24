import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { MOTIVOS_DENUNCIA } from "@features/moderation/constants/denuncias";
import {
  useAdministrativeReportDetail,
  useAdministrativeReports,
  useCreateModerationDecision,
  useModerationDecisions,
} from "@features/moderation/hooks/useAdministrativeReports";
import { useAdministrativeCapabilities } from "@features/administration/hooks/useAdministrativeCapabilities";
import { administrativeErrorMessage } from "@features/administration/utils/administrativeErrorMessages";
import { administrativeLabel } from "@features/administration/utils/administrativeLabels";
import { useFocusOnAdministrativeError } from "@features/administration/hooks/useAdministrativeFocus";
import {
  Alert,
  Button,
  FormControl,
  Input,
  Select,
  Skeleton,
  Surface,
} from "@shared";

const INITIAL_FILTERS = Object.freeze({
  estado: "",
  recurso_tipo: "",
  recurso_id: "",
  motivo: "",
  desde: "",
  hasta: "",
  limit: 20,
});

function formatDate(value) {
  if (!value) return "Fecha no disponible";
  return new Intl.DateTimeFormat("es-AR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

function reportsErrorMessage(error, { detail = false } = {}) {
  return administrativeErrorMessage(error, detail
    ? "No pudimos consultar esta denuncia."
    : "No pudimos consultar las denuncias. Intentá nuevamente.");
}

function ReportsDetail({ reportId, onClose, titleRef }) {
  const detail = useAdministrativeReportDetail(reportId);
  const decisions = useModerationDecisions(reportId);
  const createDecision = useCreateModerationDecision(reportId);
  const { tieneCapacidad } = useAdministrativeCapabilities();
  const canDecide = tieneCapacidad("moderation.decisions.write");
  const [action, setAction] = useState("resolver_sin_accion");
  const [reason, setReason] = useState("sin_incumplimiento");
  const [foundation, setFoundation] = useState("");
  const [evidence, setEvidence] = useState("");
  const detailErrorRef = useFocusOnAdministrativeError(detail.isError);
  const decisionErrorRef = useFocusOnAdministrativeError(createDecision.isError);
  const effectiveAction = detail.data?.estado === "resuelta"
    ? "restaurar_recurso"
    : action;

  function submitDecision(event) {
    event.preventDefault();
    const current = detail.data;
    const isRestore = effectiveAction === "restaurar_recurso";
    createDecision.mutate({
      accion: effectiveAction,
      motivo_codigo: reason,
      fundamento: foundation,
      evidencia_resumen: evidence,
      expected_denuncia_version: current.version,
      expected_resource_revision: effectiveAction === "resolver_sin_accion" ? null : current.recurso_actual.moderation_revision,
      reverses_decision_id: isRestore ? current.recurso_actual.moderation_hidden_by_decision_id : null,
      idempotency_key: globalThis.crypto?.randomUUID?.() ?? `decision-${Date.now()}-${Math.random()}`,
    });
  }

  return (
    <Surface variant="elevated" className="min-w-0 p-4 sm:p-5">
      <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-start sm:justify-between">
        <h2 ref={titleRef} tabIndex={-1} className="break-words text-lg font-semibold text-primary outline-none">
          Detalle de denuncia
        </h2>
        <Button type="button" variant="ghost" onClick={onClose} className="min-h-11 w-full sm:w-auto">
          Cerrar
        </Button>
      </div>

      {detail.isLoading ? (
        <Skeleton className="mt-4 h-32 w-full" />
      ) : null}

      {detail.isError ? (
        <Alert ref={detailErrorRef} tabIndex={-1} variant="danger" role="alert" className="mt-4 outline-none">
          {reportsErrorMessage(detail.error, { detail: true })}
        </Alert>
      ) : null}

      {detail.data ? (
        <dl className="mt-4 space-y-3 text-sm">
          <div>
            <dt className="font-medium text-secondary">Motivo</dt>
            <dd className="text-primary">{administrativeLabel(detail.data.motivo)}</dd>
          </div>
          <div>
            <dt className="font-medium text-secondary">Detalle informado</dt>
            <dd className="whitespace-pre-wrap break-words text-primary">
              {detail.data.detalle || "Sin detalle adicional."}
            </dd>
          </div>
          <div>
            <dt className="font-medium text-secondary">Recurso</dt>
            <dd className="text-primary">
              {administrativeLabel(detail.data.recurso_tipo)} #{detail.data.recurso_id}
            </dd>
          </div>
          <div>
            <dt className="font-medium text-secondary">Disponibilidad actual</dt>
            <dd className="text-primary">
              {detail.data.recurso_actual.disponible
                ? "Disponible actualmente"
                : "No disponible actualmente"}
            </dd>
          </div>
          {detail.data.recurso_actual.ruta_publica ? (
            <div>
              <dt className="sr-only">Acceso al recurso</dt>
              <dd>
                <Link
                  className="text-link underline underline-offset-2"
                  to={detail.data.recurso_actual.ruta_publica}
                >
                  Abrir recurso público
                </Link>
              </dd>
            </div>
          ) : null}
          <div>
            <dt className="font-medium text-secondary">Recibida</dt>
            <dd className="text-primary">{formatDate(detail.data.creado_en)}</dd>
          </div>
        </dl>
      ) : null}

      {decisions.data?.length ? (
        <section className="mt-5 border-t border-default pt-4">
          <h3 className="font-medium text-primary">Trazabilidad</h3>
          <ul className="mt-2 space-y-2 text-sm text-secondary">
            {decisions.data.map((decision) => (
              <li key={decision.id}>
                {administrativeLabel(decision.accion)} · {administrativeLabel(decision.resultado)} · operador #{decision.operador_usuario_id} · {formatDate(decision.creado_en)}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {detail.data && canDecide && (
        detail.data.estado === "recibida"
        || detail.data.recurso_actual.moderation_hidden_by_decision_id
      ) ? (
        <form className="mt-5 space-y-3 border-t border-default pt-4" onSubmit={submitDecision}>
          <h3 className="font-medium text-primary">Registrar decisión</h3>
          <FormControl label="Acción" labelFor="moderation-action">
            <Select id="moderation-action" value={effectiveAction} onChange={(event) => setAction(event.target.value)}>
              {detail.data.estado === "recibida" ? <option value="resolver_sin_accion">Resolver sin acción</option> : null}
              {detail.data.estado === "recibida" && !detail.data.recurso_actual.moderation_hidden ? <option value="ocultar_recurso">Ocultar recurso</option> : null}
              {detail.data.estado === "resuelta" && detail.data.recurso_actual.moderation_hidden_by_decision_id ? <option value="restaurar_recurso">Restaurar ocultamiento</option> : null}
            </Select>
          </FormControl>
          <FormControl label="Motivo" labelFor="moderation-reason">
            <Select id="moderation-reason" value={reason} onChange={(event) => setReason(event.target.value)}>
              <option value="sin_incumplimiento">Sin incumplimiento</option>
              <option value="incumplimiento_confirmado">Incumplimiento confirmado</option>
              <option value="contenido_no_disponible">Contenido no disponible</option>
              <option value="correccion_operativa">Corrección operativa</option>
              <option value="otro">Otro</option>
            </Select>
          </FormControl>
          <FormControl label="Fundamento de la decisión" labelFor="moderation-foundation">
            <Input id="moderation-foundation" required maxLength="1000" value={foundation} onChange={(event) => setFoundation(event.target.value)} />
            <p className="mt-1 text-xs text-secondary">Explicá el criterio aplicado sin incluir datos privados ni secretos.</p>
          </FormControl>
          <FormControl label="Referencia de evidencia" labelFor="moderation-evidence">
            <Input id="moderation-evidence" required maxLength="1000" value={evidence} onChange={(event) => setEvidence(event.target.value)} />
            <p className="mt-1 text-xs text-secondary">Ingresá sólo una referencia opaca. No incluyas URLs, rutas, payloads, secretos ni datos privados.</p>
          </FormControl>
          {createDecision.isError ? <Alert ref={decisionErrorRef} tabIndex={-1} variant="danger" role="alert" className="outline-none">{administrativeErrorMessage(createDecision.error, "No se pudo registrar la decisión.")}</Alert> : null}
          <Button type="submit" className="min-h-11 w-full sm:w-auto" disabled={createDecision.isPending}>{createDecision.isPending ? "Registrando..." : "Confirmar decisión"}</Button>
        </form>
      ) : null}
    </Surface>
  );
}

export default function AdministrativeReportsPage() {
  const [filters, setFilters] = useState(INITIAL_FILTERS);
  const [selectedReportId, setSelectedReportId] = useState(null);
  const detailTitleRef = useRef(null);
  const detailTriggerRef = useRef(null);
  const restoreDetailFocusRef = useRef(false);
  const reports = useAdministrativeReports(filters);
  const listErrorRef = useFocusOnAdministrativeError(reports.isError);

  useEffect(() => {
    if (selectedReportId) detailTitleRef.current?.focus();
    else if (restoreDetailFocusRef.current) {
      restoreDetailFocusRef.current = false;
      detailTriggerRef.current?.focus();
    }
  }, [selectedReportId]);

  function closeDetail() {
    restoreDetailFocusRef.current = true;
    setSelectedReportId(null);
  }

  const items = useMemo(
    () => reports.data?.pages.flatMap((page) => page.items) ?? [],
    [reports.data],
  );
  const hasActiveFilters = Object.entries(filters).some(
    ([key, value]) => key !== "limit" && Boolean(value),
  );

  function updateFilter(name, value) {
    setSelectedReportId(null);
    setFilters((current) => ({ ...current, [name]: value }));
  }

  function clearFilters() {
    setSelectedReportId(null);
    setFilters(INITIAL_FILTERS);
  }

  function updateResourceType(value) {
    setSelectedReportId(null);
    setFilters((current) => ({
      ...current,
      recurso_tipo: value,
      recurso_id: "",
    }));
  }

  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
      <header>
        <h1 className="text-2xl font-semibold text-primary">
          Denuncias recibidas
        </h1>
        <p className="mt-1 text-sm text-secondary">
          Consulta y decisión operativa según tus capacidades administrativas.
        </p>
        <Link className="interactive-bubble mt-3 inline-flex min-h-11 items-center text-link underline underline-offset-2" to="/administracion">Volver a Administración</Link>
      </header>

      <Surface variant="subtle" className="mt-5 p-4">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <FormControl label="Estado" labelFor="reports-status">
            <Select
              id="reports-status"
              value={filters.estado}
              onChange={(event) => updateFilter("estado", event.target.value)}
            >
              <option value="">Todos</option>
              <option value="recibida">Recibida</option>
            </Select>
          </FormControl>

          <FormControl label="Tipo de recurso" labelFor="reports-resource-type">
            <Select
              id="reports-resource-type"
              value={filters.recurso_tipo}
              onChange={(event) => updateResourceType(event.target.value)}
            >
              <option value="">Todos</option>
              <option value="comercio">Comercio</option>
              <option value="publicacion">Publicación</option>
              <option value="historia">Historia</option>
            </Select>
          </FormControl>

          <FormControl label="ID de recurso" labelFor="reports-resource-id">
            <Input
              id="reports-resource-id"
              type="number"
              min="1"
              disabled={!filters.recurso_tipo}
              value={filters.recurso_id}
              onChange={(event) => updateFilter("recurso_id", event.target.value)}
            />
          </FormControl>

          <FormControl label="Motivo" labelFor="reports-reason">
            <Select
              id="reports-reason"
              value={filters.motivo}
              onChange={(event) => updateFilter("motivo", event.target.value)}
            >
              <option value="">Todos</option>
              {MOTIVOS_DENUNCIA.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </Select>
          </FormControl>

          <FormControl label="Desde" labelFor="reports-from">
            <Input
              id="reports-from"
              type="datetime-local"
              value={filters.desde}
              onChange={(event) => updateFilter("desde", event.target.value)}
            />
          </FormControl>

          <FormControl label="Hasta" labelFor="reports-until">
            <Input
              id="reports-until"
              type="datetime-local"
              value={filters.hasta}
              onChange={(event) => updateFilter("hasta", event.target.value)}
            />
          </FormControl>
        </div>

        {hasActiveFilters ? (
          <Button
            type="button"
            variant="secondary"
            onClick={clearFilters}
            className="mt-4 min-h-11 w-full sm:w-auto"
          >
            Limpiar filtros
          </Button>
        ) : null}
      </Surface>

      <div className="mt-5 grid min-w-0 gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(18rem,0.7fr)]">
        <section className="min-w-0" aria-label="Listado de denuncias">
          {reports.isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
            </div>
          ) : null}

          {reports.isError ? (
            <Alert ref={listErrorRef} tabIndex={-1} variant="danger" role="alert" className="outline-none">
              {reportsErrorMessage(reports.error)}
            </Alert>
          ) : null}

          {!reports.isLoading && !reports.isError && items.length === 0 ? (
            <Alert variant="info" role="status">
              {hasActiveFilters
                ? "No hay denuncias que coincidan con estos filtros."
                : "Todavía no hay denuncias registradas."}
            </Alert>
          ) : null}

          <div className="space-y-3">
            {items.map((report) => (
              <Surface key={report.id} variant="default" className="p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="break-words font-medium text-primary">
                      {administrativeLabel(report.recurso_tipo)} #{report.recurso_id}
                    </p>
                    <p className="mt-1 text-sm text-secondary">
                      {administrativeLabel(report.motivo)} · {formatDate(report.creado_en)}
                    </p>
                    {report.tiene_detalle ? (
                      <p className="mt-1 text-xs text-secondary">
                        Incluye detalle adicional
                      </p>
                    ) : null}
                  </div>
                  <Button
                    type="button"
                    variant="secondary"
                    ref={selectedReportId === report.id ? detailTriggerRef : undefined}
                    onClick={(event) => { detailTriggerRef.current = event.currentTarget; setSelectedReportId(report.id); }}
                    className="min-h-11 w-full sm:w-auto"
                  >
                    Ver detalle
                  </Button>
                </div>
              </Surface>
            ))}
          </div>

          {reports.hasNextPage ? (
            <Button
              type="button"
              variant="secondary"
              disabled={reports.isFetchingNextPage}
              onClick={() => reports.fetchNextPage()}
              className="mt-4 min-h-11 w-full sm:w-auto"
            >
              {reports.isFetchingNextPage ? "Cargando..." : "Cargar más"}
            </Button>
          ) : null}
        </section>

        <aside className="min-w-0" aria-label="Detalle administrativo de denuncia">
          {selectedReportId ? (
            <ReportsDetail
              reportId={selectedReportId}
              onClose={closeDetail}
              titleRef={detailTitleRef}
            />
          ) : (
            <Surface variant="subtle" className="p-5 text-sm text-secondary">
              Seleccioná una denuncia para consultar su detalle.
            </Surface>
          )}
        </aside>
      </div>
    </main>
  );
}

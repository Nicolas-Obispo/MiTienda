import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import InteractiveLiquidLayers from "@shared/components/InteractiveLiquidLayers";

import {
  useActOnOperationalIncident, useOpenOperationalIncident,
  useOperationalIncident, useOperationalIncidents, useOperationalIncidentTimeline,
} from "@features/incidents/hooks/useOperationalIncidents";
import { administrativeErrorMessage } from "@features/administration/utils/administrativeErrorMessages";
import { administrativeLabel } from "@features/administration/utils/administrativeLabels";
import { useFocusOnAdministrativeError } from "@features/administration/hooks/useAdministrativeFocus";
import { Alert, Button, FormControl, Input, Select, Skeleton, Surface } from "@shared";

const FILTERS = Object.freeze({ status: "", severity: "", owner_usuario_id: "", limit: 20 });
const uid = () => globalThis.crypto?.randomUUID?.() ?? `incident-${Date.now()}-${Math.random()}`;

function IncidentDetail({ publicId, onClose, titleRef }) {
  const detail = useOperationalIncident(publicId);
  const timeline = useOperationalIncidentTimeline(publicId);
  const lifecycleAction = useActOnOperationalIncident();
  const legalAction = useActOnOperationalIncident();
  const adjustmentAction = useActOnOperationalIncident();
  const detailErrorRef = useFocusOnAdministrativeError(detail.isError);
  const lifecycleErrorRef = useFocusOnAdministrativeError(lifecycleAction.isError);
  const legalErrorRef = useFocusOnAdministrativeError(legalAction.isError);
  const adjustmentErrorRef = useFocusOnAdministrativeError(adjustmentAction.isError);
  const [lifecycleSummary, setLifecycleSummary] = useState("");
  const [legalSummary, setLegalSummary] = useState("");
  const [adjustmentSummary, setAdjustmentSummary] = useState("");
  const [risk, setRisk] = useState("low");
  const [riskOwner, setRiskOwner] = useState("");
  const [riskReviewAt, setRiskReviewAt] = useState("");
  const [legalStatus, setLegalStatus] = useState("pending");
  const [dataImpact, setDataImpact] = useState("unknown");
  const [userCommunication, setUserCommunication] = useState("pending");
  const [authorityCommunication, setAuthorityCommunication] = useState("pending");
  const [legalDeadline, setLegalDeadline] = useState("");
  const [adjustment, setAdjustment] = useState("change_severity");
  const [adjustmentValue, setAdjustmentValue] = useState("sev3_medium");

  const nextActions = detail.data?.status === "open" ? ["start_investigation"]
    : detail.data?.status === "investigating" ? ["contain"]
      : detail.data?.status === "contained" ? ["resolve", "reopen"]
        : detail.data?.status === "resolved" ? ["review", "reopen"] : [];

  function submitAction(event) {
    event.preventDefault();
    const action = event.nativeEvent.submitter.value;
    const payload = { action, expected_version: detail.data.version, idempotency_key: uid(), summary: lifecycleSummary };
    if (action === "resolve") {
      payload.residual_risk_level = risk;
      payload.residual_risk_summary = lifecycleSummary;
      if (risk === "medium") {
        payload.residual_risk_owner_usuario_id = Number(riskOwner);
        payload.residual_risk_review_at = riskReviewAt;
      }
    }
    lifecycleAction.mutate({ publicId, payload }, { onSuccess: () => setLifecycleSummary("") });
  }

  function submitLegal(event) {
    event.preventDefault();
    legalAction.mutate({ publicId, payload: {
      action: "record_legal_assessment", expected_version: detail.data.version,
      idempotency_key: uid(), summary: legalSummary, legal_assessment_status: legalStatus,
      personal_data_impact: dataImpact, user_communication_status: userCommunication,
      authority_communication_status: authorityCommunication,
      ...(legalDeadline ? { legal_deadline_at: legalDeadline } : {}),
    } }, { onSuccess: () => setLegalSummary("") });
  }

  function submitAdjustment(event) {
    event.preventDefault();
    const payload = { action: adjustment, expected_version: detail.data.version, idempotency_key: uid(), summary: adjustmentSummary };
    if (adjustment === "change_severity") payload.severity = adjustmentValue;
    if (adjustment === "assign_owner") payload.owner_usuario_id = Number(adjustmentValue);
    adjustmentAction.mutate({ publicId, payload }, { onSuccess: () => setAdjustmentSummary("") });
  }

  return <Surface variant="elevated" className="min-w-0 p-4 sm:p-5">
    <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-start sm:justify-between"><h2 ref={titleRef} tabIndex={-1} className="break-all font-semibold text-primary outline-none">{publicId}</h2><Button variant="ghost" onClick={onClose} className="min-h-11 w-full sm:w-auto">Cerrar</Button></div>
    {detail.isLoading ? <Skeleton className="mt-4 h-32 w-full" /> : null}
    {detail.isError ? <Alert ref={detailErrorRef} tabIndex={-1} variant="danger" className="mt-4 outline-none">{administrativeErrorMessage(detail.error, "No se pudo consultar el incidente.")}</Alert> : null}
    {detail.data ? <dl className="mt-4 space-y-2 text-sm text-primary">
      <div><dt className="font-medium text-secondary">Estado</dt><dd>{administrativeLabel(detail.data.status)}</dd></div>
      <div><dt className="font-medium text-secondary">Severidad</dt><dd>{administrativeLabel(detail.data.severity)}</dd></div>
      <div><dt className="font-medium text-secondary">Responsable</dt><dd>Operador #{detail.data.owner_usuario_id}</dd></div>
      <div><dt className="font-medium text-secondary">Descripción inicial</dt><dd>{detail.data.summary_sanitized}</dd></div>
      <div><dt className="font-medium text-secondary">Riesgo residual</dt><dd>{administrativeLabel(detail.data.residual_risk_level, "Pendiente")}</dd></div>
    </dl> : null}
    {timeline.data?.length ? <section className="mt-5 border-t border-default pt-4"><h3 className="font-medium text-primary">Cronología</h3><ol className="mt-2 space-y-2 text-sm text-secondary">{timeline.data.map((item) => <li key={item.id}>{administrativeLabel(item.event_type)} · operador #{item.actor_usuario_id} · versión {item.resulting_incident_version}</li>)}</ol></section> : null}
    {detail.data && nextActions.length ? <form className="mt-5 space-y-3 border-t border-default pt-4" onSubmit={submitAction}>
      <h3 className="font-medium text-primary">Avanzar estado del incidente</h3>
      <FormControl label="Detalle del avance" labelFor="incident-action-summary"><Input id="incident-action-summary" required minLength="3" maxLength="1200" value={lifecycleSummary} onChange={(e) => setLifecycleSummary(e.target.value)} /><p className="mt-1 text-xs text-secondary">Describí el avance sin incluir secretos ni datos privados.</p></FormControl>
      {nextActions.includes("resolve") ? <>
        <FormControl label="Riesgo residual" labelFor="incident-risk"><Select id="incident-risk" value={risk} onChange={(e) => setRisk(e.target.value)}><option value="none">Ninguno</option><option value="low">Bajo</option><option value="medium">Medio</option><option value="high">Alto</option><option value="critical">Critico</option></Select></FormControl>
        {risk === "medium" ? <><FormControl label="Responsable del riesgo" labelFor="risk-owner"><Input id="risk-owner" type="number" min="1" required value={riskOwner} onChange={(e) => setRiskOwner(e.target.value)} /></FormControl><FormControl label="Fecha de revisión" labelFor="risk-review"><Input id="risk-review" type="datetime-local" required value={riskReviewAt} onChange={(e) => setRiskReviewAt(e.target.value)} /></FormControl></> : null}
      </> : null}
      {lifecycleAction.isError ? <Alert ref={lifecycleErrorRef} tabIndex={-1} variant="danger" className="outline-none">{administrativeErrorMessage(lifecycleAction.error, "No se pudo registrar el avance.")}</Alert> : null}
      <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">{nextActions.map((action) => <Button key={action} type="submit" value={action} className="min-h-11 w-full sm:w-auto" disabled={lifecycleAction.isPending}>{lifecycleAction.isPending ? "Registrando..." : administrativeLabel(action)}</Button>)}</div>
    </form> : null}
    {detail.data ? <form className="mt-5 space-y-3 border-t border-default pt-4" onSubmit={submitLegal}>
      <h3 className="font-medium text-primary">Evaluación legal mínima</h3>
      <FormControl label="Fundamento de la evaluación legal" labelFor="incident-legal-summary"><Input id="incident-legal-summary" required minLength="3" maxLength="1200" value={legalSummary} onChange={(e) => setLegalSummary(e.target.value)} /><p className="mt-1 text-xs text-secondary">Registrá el criterio operativo sin secretos ni datos privados.</p></FormControl>
      <FormControl label="Estado de revision" labelFor="legal-status"><Select id="legal-status" value={legalStatus} onChange={(e) => setLegalStatus(e.target.value)}><option value="pending">Pendiente</option><option value="not_required">No requerida</option><option value="required">Requerida</option><option value="completed">Completada</option></Select></FormControl>
      <FormControl label="Impacto en datos" labelFor="data-impact"><Select id="data-impact" value={dataImpact} onChange={(e) => setDataImpact(e.target.value)}><option value="unknown">Desconocido</option><option value="none">Sin impacto</option><option value="suspected">Sospechado</option><option value="confirmed">Confirmado</option></Select></FormControl>
      <FormControl label="Comunicacion a usuarios" labelFor="user-communication"><Select id="user-communication" value={userCommunication} onChange={(e) => setUserCommunication(e.target.value)}><option value="pending">Pendiente</option><option value="not_required">No requerida</option><option value="required">Requerida</option><option value="completed">Realizada</option></Select></FormControl>
      <FormControl label="Comunicacion a autoridad" labelFor="authority-communication"><Select id="authority-communication" value={authorityCommunication} onChange={(e) => setAuthorityCommunication(e.target.value)}><option value="pending">Pendiente</option><option value="not_required">No requerida</option><option value="required">Requerida</option><option value="completed">Realizada</option></Select></FormControl>
      <FormControl label="Plazo legal operativo" labelFor="legal-deadline"><Input id="legal-deadline" type="datetime-local" value={legalDeadline} onChange={(e) => setLegalDeadline(e.target.value)} /></FormControl>
      {legalAction.isError ? <Alert ref={legalErrorRef} tabIndex={-1} variant="danger" className="outline-none">{administrativeErrorMessage(legalAction.error, "No se pudo registrar la evaluación legal.")}</Alert> : null}
      <Button type="submit" variant="secondary" className="min-h-11 w-full sm:w-auto" disabled={legalAction.isPending || legalSummary.length < 3}>Registrar evaluación</Button>
    </form> : null}
    {detail.data && detail.data.status !== "reviewed" ? <form className="mt-5 space-y-3 border-t border-default pt-4" onSubmit={submitAdjustment}>
      <h3 className="font-medium text-primary">Ajustar responsable o severidad</h3>
      <FormControl label="Motivo del cambio" labelFor="incident-adjustment-summary"><Input id="incident-adjustment-summary" required minLength="3" maxLength="1200" value={adjustmentSummary} onChange={(e) => setAdjustmentSummary(e.target.value)} /><p className="mt-1 text-xs text-secondary">Explicá el cambio sin incluir secretos ni datos privados.</p></FormControl>
      <FormControl label="Ajuste" labelFor="incident-adjustment"><Select id="incident-adjustment" value={adjustment} onChange={(e) => { setAdjustment(e.target.value); setAdjustmentValue(e.target.value === "change_severity" ? detail.data.severity : String(detail.data.owner_usuario_id)); }}><option value="change_severity">Cambiar severidad</option><option value="assign_owner">Cambiar responsable</option></Select></FormControl>
      {adjustment === "change_severity" ? <FormControl label="Nueva severidad" labelFor="new-severity"><Select id="new-severity" value={adjustmentValue} onChange={(e) => setAdjustmentValue(e.target.value)}><option value="sev1_critical">SEV1 · Crítico</option><option value="sev2_high">SEV2 · Alto</option><option value="sev3_medium">SEV3 · Medio</option><option value="sev4_low">SEV4 · Bajo</option></Select></FormControl> : <FormControl label="ID del nuevo responsable" labelFor="new-owner"><Input id="new-owner" type="number" min="1" required value={adjustmentValue} onChange={(e) => setAdjustmentValue(e.target.value)} /></FormControl>}
      {adjustmentAction.isError ? <Alert ref={adjustmentErrorRef} tabIndex={-1} variant="danger" className="outline-none">{administrativeErrorMessage(adjustmentAction.error, "No se pudo registrar el ajuste.")}</Alert> : null}
      <Button type="submit" variant="secondary" className="min-h-11 w-full sm:w-auto" disabled={adjustmentAction.isPending || adjustmentSummary.length < 3 || (adjustment === "change_severity" && adjustmentValue === detail.data.severity)}>Registrar ajuste</Button>
    </form> : null}
  </Surface>;
}

export default function OperationalIncidentsPage() {
  const [filters, setFilters] = useState(FILTERS);
  const [selected, setSelected] = useState(null);
  const detailTitleRef = useRef(null);
  const detailTriggerRef = useRef(null);
  const restoreDetailFocusRef = useRef(false);
  const [form, setForm] = useState({ title: "", summary: "", incident_type: "availability", severity: "sev3_medium", owner_usuario_id: "", operational_deadline_at: "" });
  const incidents = useOperationalIncidents(filters);
  const openIncident = useOpenOperationalIncident();
  const openErrorRef = useFocusOnAdministrativeError(openIncident.isError);
  const listErrorRef = useFocusOnAdministrativeError(incidents.isError);
  const items = useMemo(() => incidents.data?.pages.flatMap((page) => page.items) ?? [], [incidents.data]);
  function update(name, value) { setForm((current) => ({ ...current, [name]: value })); }
  function submit(event) {
    event.preventDefault(); const payload = { ...form, owner_usuario_id: Number(form.owner_usuario_id), idempotency_key: uid() }; if (!payload.operational_deadline_at) delete payload.operational_deadline_at; openIncident.mutate({ payload });
  }
  useEffect(() => {
    if (selected) detailTitleRef.current?.focus();
    else if (restoreDetailFocusRef.current) {
      restoreDetailFocusRef.current = false;
      detailTriggerRef.current?.focus();
    }
  }, [selected]);
  function closeDetail() { restoreDetailFocusRef.current = true; setSelected(null); }
  return <main className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
    <h1 className="text-2xl font-semibold text-primary">Incidentes operativos</h1><p className="mt-1 text-sm text-secondary">Registro manual, cronología y gestión de estado. No reemplaza observabilidad ni recuperación.</p><Link className="interactive-bubble interactive-bubble--liquid mt-3 inline-flex min-h-11 items-center text-link underline underline-offset-2" to="/administracion">Volver a Administración<InteractiveLiquidLayers /></Link>
    <Surface variant="subtle" className="mt-5 p-4"><form className="grid gap-3 sm:grid-cols-2" onSubmit={submit}>
      <FormControl label="Titulo" labelFor="incident-title"><Input id="incident-title" required minLength="3" maxLength="160" value={form.title} onChange={(e) => update("title",e.target.value)} /></FormControl>
      <FormControl label="ID del operador responsable" labelFor="incident-owner"><Input id="incident-owner" type="number" min="1" required value={form.owner_usuario_id} onChange={(e) => update("owner_usuario_id",e.target.value)} /></FormControl>
      <FormControl label="Tipo" labelFor="incident-type"><Select id="incident-type" value={form.incident_type} onChange={(e) => update("incident_type",e.target.value)}><option value="availability">Disponibilidad</option><option value="security">Seguridad</option><option value="privacy">Privacidad</option><option value="data_integrity">Integridad de datos</option><option value="dependency">Dependencia</option><option value="storage_media">Storage/media</option><option value="configuration">Configuracion</option><option value="other">Otro</option></Select></FormControl>
      <FormControl label="Severidad" labelFor="incident-severity"><Select id="incident-severity" value={form.severity} onChange={(e) => update("severity",e.target.value)}><option value="sev1_critical">SEV1</option><option value="sev2_high">SEV2</option><option value="sev3_medium">SEV3</option><option value="sev4_low">SEV4</option></Select></FormControl>
      <FormControl label="Descripción inicial" labelFor="incident-summary" className="sm:col-span-2"><Input id="incident-summary" required minLength="3" maxLength="1200" value={form.summary} onChange={(e) => update("summary",e.target.value)} /><p className="mt-1 text-xs text-secondary">Describí el impacto sin incluir secretos ni datos privados.</p></FormControl>
      <FormControl label="Plazo operativo" labelFor="incident-deadline"><Input id="incident-deadline" type="datetime-local" value={form.operational_deadline_at} onChange={(e) => update("operational_deadline_at",e.target.value)} /></FormControl>
      {openIncident.isError ? <Alert ref={openErrorRef} tabIndex={-1} variant="danger" className="outline-none sm:col-span-2">{administrativeErrorMessage(openIncident.error, "No se pudo abrir el incidente.")}</Alert> : null}<Button type="submit" className="min-h-11 w-full sm:w-auto" disabled={openIncident.isPending}>Abrir incidente</Button>
    </form></Surface>
    <Surface variant="subtle" className="mt-5 p-4"><div className="grid gap-3 sm:grid-cols-3"><Select aria-label="Filtrar estado" value={filters.status} onChange={(e) => setFilters((f)=>({...f,status:e.target.value}))}><option value="">Todos los estados</option><option value="open">Abierto</option><option value="investigating">Investigando</option><option value="contained">Contenido</option><option value="resolved">Resuelto</option><option value="reviewed">Revisado</option></Select><Select aria-label="Filtrar severidad" value={filters.severity} onChange={(e)=>setFilters((f)=>({...f,severity:e.target.value}))}><option value="">Todas las severidades</option><option value="sev1_critical">SEV1</option><option value="sev2_high">SEV2</option><option value="sev3_medium">SEV3</option><option value="sev4_low">SEV4</option></Select></div></Surface>
    <div className="mt-5 grid min-w-0 gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]"><section className="min-w-0 space-y-3">{incidents.isLoading ? <Skeleton className="h-24 w-full" /> : null}{incidents.isError ? <Alert ref={listErrorRef} tabIndex={-1} variant="danger" className="outline-none">{administrativeErrorMessage(incidents.error, "No se pudieron consultar los incidentes.")}</Alert> : null}{!incidents.isLoading && !items.length ? <Alert variant="info">No hay incidentes registrados.</Alert> : null}{items.map((item)=><Surface key={item.public_id} className="min-w-0 p-4"><p className="break-all font-medium text-primary">{item.public_id} · {administrativeLabel(item.severity)}</p><p className="break-words text-sm text-secondary">{item.title} · {administrativeLabel(item.status)}</p><Button ref={selected === item.public_id ? detailTriggerRef : undefined} variant="secondary" onClick={(event)=>{ detailTriggerRef.current = event.currentTarget; setSelected(item.public_id); }} className="mt-2 min-h-11 w-full sm:w-auto">Ver expediente</Button></Surface>)}{incidents.hasNextPage ? <Button variant="secondary" className="min-h-11 w-full sm:w-auto" onClick={()=>incidents.fetchNextPage()}>Cargar más</Button> : null}</section><aside className="min-w-0">{selected ? <IncidentDetail publicId={selected} onClose={closeDetail} titleRef={detailTitleRef} /> : <Surface variant="subtle" className="p-5 text-secondary">Seleccioná un incidente.</Surface>}</aside></div>
  </main>;
}

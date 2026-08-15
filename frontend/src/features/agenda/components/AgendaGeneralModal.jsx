import { useMemo, useState } from "react";
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  X,
} from "lucide-react";

import { ActiveLayer } from "@core";
import { Alert, Button, Input, Select, Skeleton, Surface } from "@shared";
import { useAgendaGeneralElementos } from "@features/agenda/hooks/useFeedGoAgenda";
import { obtenerHttpStatus } from "@features/agenda/services/feedgo_agenda_service";
import AgendaPrivadaModal from "@features/agenda/components/AgendaPrivadaModal";

const TIPOS = [
  { value: "evento", label: "Evento" },
  { value: "tarea", label: "Tarea" },
  { value: "recordatorio", label: "Recordatorio" },
  { value: "bloqueo", label: "Bloqueo" },
];

const ESTADOS_FILTRO = [
  { value: "", label: "Todos" },
  { value: "activo", label: "Activos" },
  { value: "completado", label: "Completados" },
  { value: "cancelado", label: "Cancelados" },
];

function fechaInputDesdeDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function fechaInputHoy() {
  return fechaInputDesdeDate(new Date());
}

function rangoIsoDelDia(fecha) {
  const inicio = new Date(`${fecha}T00:00:00`);
  const fin = new Date(inicio);
  fin.setDate(fin.getDate() + 1);

  return {
    inicio: inicio.toISOString(),
    fin: fin.toISOString(),
  };
}

function moverFecha(fecha, dias) {
  const date = new Date(`${fecha}T00:00:00`);
  date.setDate(date.getDate() + dias);
  return fechaInputDesdeDate(date);
}

function formatearFecha(fecha) {
  return new Intl.DateTimeFormat("es-AR", {
    weekday: "long",
    day: "2-digit",
    month: "long",
  }).format(new Date(`${fecha}T00:00:00`));
}

function formatearFechaHora(value) {
  if (!value) return "Sin horario";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Sin horario";

  return new Intl.DateTimeFormat("es-AR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatearRango(elemento) {
  if (elemento.todo_el_dia) return "Todo el dia";
  if (!elemento.inicio) return "Sin fecha";
  if (!elemento.fin) return formatearFechaHora(elemento.inicio);

  const inicio = new Date(elemento.inicio);
  const fin = new Date(elemento.fin);

  if (Number.isNaN(inicio.getTime()) || Number.isNaN(fin.getTime())) {
    return "Sin horario";
  }

  const hora = new Intl.DateTimeFormat("es-AR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return `${hora.format(inicio)} - ${hora.format(fin)}`;
}

function ordenarItems(items) {
  return [...(items || [])].sort((a, b) => {
    const aInicio = a.elemento?.inicio;
    const bInicio = b.elemento?.inicio;

    if (!aInicio && !bInicio) return (a.elemento?.id || 0) - (b.elemento?.id || 0);
    if (!aInicio) return 1;
    if (!bInicio) return -1;
    return new Date(aInicio).getTime() - new Date(bInicio).getTime();
  });
}

function mensajeErrorAmigable(error) {
  const status = obtenerHttpStatus(error);

  if (status === 403) return "No tenes permiso para acceder a esta agenda.";
  if (status === 404) return "No se encontro la agenda solicitada.";
  if (status === 422 || status === 400) {
    return "Revisa los filtros antes de continuar.";
  }

  return error?.message || "No se pudo cargar la agenda general.";
}

export default function AgendaGeneralModal({ comercios = [], onClose }) {
  const [fecha, setFecha] = useState(() => fechaInputHoy());
  const [estadoFiltro, setEstadoFiltro] = useState("");
  const [tipoFiltro, setTipoFiltro] = useState("");
  const [comercioFiltro, setComercioFiltro] = useState("");
  const [agendaIndividualComercio, setAgendaIndividualComercio] = useState(null);

  const rango = useMemo(() => rangoIsoDelDia(fecha), [fecha]);
  const elementosQuery = useAgendaGeneralElementos({
    inicio: rango.inicio,
    fin: rango.fin,
    estado: estadoFiltro || null,
    tipo: tipoFiltro || null,
    comercioId: comercioFiltro || null,
  });
  const items = useMemo(
    () => ordenarItems(elementosQuery.data || []),
    [elementosQuery.data]
  );

  const comercioSeleccionado = useMemo(() => {
    if (!comercioFiltro) return null;
    return comercios.find((comercio) => Number(comercio.id) === Number(comercioFiltro));
  }, [comercioFiltro, comercios]);

  function abrirAgendaIndividual(comercio) {
    if (!comercio) return;
    setAgendaIndividualComercio(comercio);
  }

  return (
    <>
      <ActiveLayer
        onClose={onClose}
        backdropClassName="bg-overlay-backdrop"
        labelledBy="agenda-general-title"
        describedBy="agenda-general-description"
        contentClassName="mx-3 flex max-h-[92vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-border bg-surface-elevated text-primary shadow-elevation"
      >
        <header className="flex items-start justify-between gap-3 border-b border-border px-4 py-4">
          <div className="min-w-0">
            <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-brand">
              <CalendarDays size={14} aria-hidden="true" />
              Agenda general
            </p>
            <h2 id="agenda-general-title" className="mt-1 text-lg font-bold text-primary">
              Todos tus espacios
            </h2>
            <p id="agenda-general-description" className="mt-1 text-sm text-secondary">
              Consulta una vista cronologica integrada de tus agendas privadas.
            </p>
          </div>

          <Button
            iconOnly
            variant="ghost"
            onClick={onClose}
            aria-label="Cerrar agenda general"
          >
            <X size={18} aria-hidden="true" />
          </Button>
        </header>

        <div className="overflow-y-auto px-4 py-4">
          <Surface as="section" variant="subtle" className="rounded-xl p-3">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-sm font-semibold capitalize text-primary">
                  {formatearFecha(fecha)}
                </p>
                <p className="text-xs text-muted">Vista diaria cronologica</p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Button
                  iconOnly
                  variant="ghost"
                  onClick={() => setFecha(moverFecha(fecha, -1))}
                  aria-label="Dia anterior"
                >
                  <ChevronLeft size={18} aria-hidden="true" />
                </Button>
                <Input
                  type="date"
                  value={fecha}
                  onChange={(event) => setFecha(event.target.value || fechaInputHoy())}
                  className="min-h-10 w-auto rounded-lg px-3 py-2 text-sm"
                  aria-label="Fecha de agenda general"
                />
                <Button
                  iconOnly
                  variant="ghost"
                  onClick={() => setFecha(moverFecha(fecha, 1))}
                  aria-label="Dia siguiente"
                >
                  <ChevronRight size={18} aria-hidden="true" />
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => setFecha(fechaInputHoy())}
                  className="min-h-10 px-3 py-2 text-sm"
                >
                  Hoy
                </Button>
              </div>
            </div>

            <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-4">
              <label className="block md:col-span-2">
                <span className="text-xs text-secondary">Espacio</span>
                <Select
                  value={comercioFiltro}
                  onChange={(event) => setComercioFiltro(event.target.value)}
                  className="mt-1 rounded-lg px-3 py-2 text-sm"
                >
                  <option value="">Todos los espacios</option>
                  {comercios.map((comercio) => (
                    <option key={comercio.id} value={comercio.id}>
                      {comercio.nombre || "Espacio"}
                    </option>
                  ))}
                </Select>
              </label>

              <label className="block">
                <span className="text-xs text-secondary">Estado</span>
                <Select
                  value={estadoFiltro}
                  onChange={(event) => setEstadoFiltro(event.target.value)}
                  className="mt-1 rounded-lg px-3 py-2 text-sm"
                >
                  {ESTADOS_FILTRO.map((estado) => (
                    <option key={estado.value || "todos"} value={estado.value}>
                      {estado.label}
                    </option>
                  ))}
                </Select>
              </label>

              <label className="block">
                <span className="text-xs text-secondary">Tipo</span>
                <Select
                  value={tipoFiltro}
                  onChange={(event) => setTipoFiltro(event.target.value)}
                  className="mt-1 rounded-lg px-3 py-2 text-sm"
                >
                  <option value="">Todos</option>
                  {TIPOS.map((tipo) => (
                    <option key={tipo.value} value={tipo.value}>
                      {tipo.label}
                    </option>
                  ))}
                </Select>
              </label>
            </div>

            {comercioSeleccionado ? (
              <Button
                variant="ghost"
                onClick={() => abrirAgendaIndividual(comercioSeleccionado)}
                className="mt-3 min-h-10 gap-2 px-3 py-2 text-sm text-brand"
              >
                <ExternalLink size={16} aria-hidden="true" />
                Abrir agenda individual
              </Button>
            ) : null}
          </Surface>

          {elementosQuery.isError ? (
            <Alert variant="danger" role="alert" className="mt-4">
              {mensajeErrorAmigable(elementosQuery.error)}
            </Alert>
          ) : null}

          <section className="mt-4 space-y-2">
            {elementosQuery.isLoading && items.length === 0 ? (
              <Skeleton className="h-12 rounded-xl" />
            ) : null}

            {!elementosQuery.isLoading && items.length === 0 ? (
              <Surface className="rounded-xl border-dashed p-6 text-center">
                <p className="font-semibold text-primary">
                  No hay elementos para esta seleccion
                </p>
                <p className="mt-1 text-sm text-secondary">
                  Cambia la fecha, el espacio o los filtros para revisar otros elementos.
                </p>
              </Surface>
            ) : null}

            {items.map(({ comercio, contexto, elemento }) => (
              <Surface
                as="article"
                key={`${comercio.id}-${elemento.id}`}
                className="rounded-xl p-4"
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full border border-selected-border bg-selected-surface px-2 py-0.5 text-[11px] font-semibold text-selected-text">
                        {comercio.nombre || "Espacio"}
                      </span>
                      <span className="rounded-full border border-border bg-surface-subtle px-2 py-0.5 text-[11px] font-semibold text-secondary">
                        {TIPOS.find((tipo) => tipo.value === elemento.tipo)?.label ||
                          elemento.tipo}
                      </span>
                      <span className="text-xs text-muted">
                        {elemento.estado} - v{elemento.version}
                      </span>
                      {contexto.estado === "archivado" ? (
                        <span className="text-xs text-warning-text">Archivado</span>
                      ) : null}
                    </div>

                    <h3 className="mt-2 break-words font-semibold text-primary">
                      {elemento.titulo}
                    </h3>
                    <p className="mt-1 text-sm text-secondary">
                      {formatearRango(elemento)}
                    </p>
                    {elemento.descripcion ? (
                      <p className="mt-2 break-words text-sm text-secondary">
                        {elemento.descripcion}
                      </p>
                    ) : null}
                  </div>

                  <Button
                    variant="ghost"
                    onClick={() => abrirAgendaIndividual(comercio)}
                    className="min-h-9 gap-1 px-2 py-1.5 text-xs text-brand"
                  >
                    <ExternalLink size={14} aria-hidden="true" />
                    Abrir agenda
                  </Button>
                </div>
              </Surface>
            ))}
          </section>
        </div>
      </ActiveLayer>

      {agendaIndividualComercio ? (
        <AgendaPrivadaModal
          comercio={agendaIndividualComercio}
          backLabel="Volver a agenda general"
          onClose={() => setAgendaIndividualComercio(null)}
        />
      ) : null}
    </>
  );
}

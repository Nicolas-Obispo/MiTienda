import { useMemo, useState } from "react";
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  X,
} from "lucide-react";

import { ActiveLayer } from "@core";
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
        labelledBy="agenda-general-title"
        describedBy="agenda-general-description"
        contentClassName="mx-3 flex max-h-[92vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-gray-800 bg-gray-950 shadow-2xl"
      >
        <header className="flex items-start justify-between gap-3 border-b border-gray-800 px-4 py-4">
          <div className="min-w-0">
            <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-orange-300">
              <CalendarDays size={14} aria-hidden="true" />
              Agenda general
            </p>
            <h2 id="agenda-general-title" className="mt-1 text-lg font-bold text-white">
              Todos tus espacios
            </h2>
            <p id="agenda-general-description" className="mt-1 text-sm text-gray-400">
              Consulta una vista cronologica integrada de tus agendas privadas.
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="min-h-10 rounded-lg px-3 py-2 text-sm font-semibold text-gray-300 transition hover:bg-gray-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-orange-400"
            aria-label="Cerrar agenda general"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </header>

        <div className="overflow-y-auto px-4 py-4">
          <section className="rounded-xl bg-gray-900/60 p-3">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-sm font-semibold capitalize text-white">
                  {formatearFecha(fecha)}
                </p>
                <p className="text-xs text-gray-500">Vista diaria cronologica</p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => setFecha(moverFecha(fecha, -1))}
                  className="min-h-10 rounded-lg px-3 py-2 text-sm font-semibold text-gray-300 transition hover:bg-gray-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-orange-400"
                  aria-label="Dia anterior"
                >
                  <ChevronLeft size={18} aria-hidden="true" />
                </button>
                <input
                  type="date"
                  value={fecha}
                  onChange={(event) => setFecha(event.target.value || fechaInputHoy())}
                  className="min-h-10 rounded-lg border border-gray-800 bg-gray-950 px-3 py-2 text-sm text-white outline-none focus:border-orange-500"
                  aria-label="Fecha de agenda general"
                />
                <button
                  type="button"
                  onClick={() => setFecha(moverFecha(fecha, 1))}
                  className="min-h-10 rounded-lg px-3 py-2 text-sm font-semibold text-gray-300 transition hover:bg-gray-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-orange-400"
                  aria-label="Dia siguiente"
                >
                  <ChevronRight size={18} aria-hidden="true" />
                </button>
                <button
                  type="button"
                  onClick={() => setFecha(fechaInputHoy())}
                  className="min-h-10 rounded-lg px-3 py-2 text-sm font-semibold text-gray-300 transition hover:bg-gray-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-orange-400"
                >
                  Hoy
                </button>
              </div>
            </div>

            <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-4">
              <label className="block md:col-span-2">
                <span className="text-xs text-gray-400">Espacio</span>
                <select
                  value={comercioFiltro}
                  onChange={(event) => setComercioFiltro(event.target.value)}
                  className="mt-1 w-full rounded-lg border border-gray-800 bg-gray-950 px-3 py-2 text-sm text-white"
                >
                  <option value="">Todos los espacios</option>
                  {comercios.map((comercio) => (
                    <option key={comercio.id} value={comercio.id}>
                      {comercio.nombre || "Espacio"}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block">
                <span className="text-xs text-gray-400">Estado</span>
                <select
                  value={estadoFiltro}
                  onChange={(event) => setEstadoFiltro(event.target.value)}
                  className="mt-1 w-full rounded-lg border border-gray-800 bg-gray-950 px-3 py-2 text-sm text-white"
                >
                  {ESTADOS_FILTRO.map((estado) => (
                    <option key={estado.value || "todos"} value={estado.value}>
                      {estado.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block">
                <span className="text-xs text-gray-400">Tipo</span>
                <select
                  value={tipoFiltro}
                  onChange={(event) => setTipoFiltro(event.target.value)}
                  className="mt-1 w-full rounded-lg border border-gray-800 bg-gray-950 px-3 py-2 text-sm text-white"
                >
                  <option value="">Todos</option>
                  {TIPOS.map((tipo) => (
                    <option key={tipo.value} value={tipo.value}>
                      {tipo.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {comercioSeleccionado ? (
              <button
                type="button"
                onClick={() => abrirAgendaIndividual(comercioSeleccionado)}
                className="mt-3 inline-flex min-h-10 items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-orange-300 transition hover:bg-orange-950/30 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-orange-400"
              >
                <ExternalLink size={16} aria-hidden="true" />
                Abrir agenda individual
              </button>
            ) : null}
          </section>

          {elementosQuery.isError ? (
            <div className="mt-4 rounded-xl border border-red-900 bg-red-950/40 p-4 text-sm text-red-100">
              {mensajeErrorAmigable(elementosQuery.error)}
            </div>
          ) : null}

          <section className="mt-4 space-y-2">
            {elementosQuery.isLoading && items.length === 0 ? (
              <p className="rounded-xl bg-gray-900/60 p-4 text-sm text-gray-400">
                Cargando agenda general...
              </p>
            ) : null}

            {!elementosQuery.isLoading && items.length === 0 ? (
              <div className="rounded-xl border border-dashed border-gray-800 bg-gray-900/40 p-6 text-center">
                <p className="font-semibold text-white">
                  No hay elementos para esta seleccion
                </p>
                <p className="mt-1 text-sm text-gray-400">
                  Cambia la fecha, el espacio o los filtros para revisar otros elementos.
                </p>
              </div>
            ) : null}

            {items.map(({ comercio, contexto, elemento }) => (
              <article
                key={`${comercio.id}-${elemento.id}`}
                className="rounded-xl border border-gray-800 bg-gray-900/70 p-4"
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full bg-orange-950/40 px-2 py-0.5 text-[11px] font-semibold text-orange-200">
                        {comercio.nombre || "Espacio"}
                      </span>
                      <span className="rounded-full bg-gray-800 px-2 py-0.5 text-[11px] font-semibold text-gray-200">
                        {TIPOS.find((tipo) => tipo.value === elemento.tipo)?.label ||
                          elemento.tipo}
                      </span>
                      <span className="text-xs text-gray-500">
                        {elemento.estado} - v{elemento.version}
                      </span>
                      {contexto.estado === "archivado" ? (
                        <span className="text-xs text-yellow-300">Archivado</span>
                      ) : null}
                    </div>

                    <h3 className="mt-2 break-words font-semibold text-white">
                      {elemento.titulo}
                    </h3>
                    <p className="mt-1 text-sm text-gray-300">
                      {formatearRango(elemento)}
                    </p>
                    {elemento.descripcion ? (
                      <p className="mt-2 break-words text-sm text-gray-400">
                        {elemento.descripcion}
                      </p>
                    ) : null}
                  </div>

                  <button
                    type="button"
                    onClick={() => abrirAgendaIndividual(comercio)}
                    className="inline-flex min-h-9 items-center gap-1 rounded-lg px-2 py-1.5 text-xs font-semibold text-orange-200 transition hover:bg-orange-950/30 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-orange-400"
                  >
                    <ExternalLink size={14} aria-hidden="true" />
                    Abrir agenda
                  </button>
                </div>
              </article>
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

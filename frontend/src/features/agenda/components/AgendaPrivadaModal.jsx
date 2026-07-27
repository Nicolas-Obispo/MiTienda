import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  CalendarDays,
  Check,
  ChevronLeft,
  ChevronRight,
  CircleSlash,
  Pencil,
  Plus,
  X,
} from "lucide-react";

import { ActiveLayer } from "@core";
import {
  useActualizarElementoAgendaMutation,
  useAgendaContexto,
  useAgendaElementos,
  useCambiarEstadoElementoAgendaMutation,
  useCrearElementoAgendaMutation,
} from "@features/agenda/hooks/useFeedGoAgenda";
import { obtenerHttpStatus } from "@features/agenda/services/feedgo_agenda_service";

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

function fechaInputHoy() {
  return fechaInputDesdeDate(new Date());
}

function fechaInputDesdeDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function datetimeLocalDesdeIso(value) {
  if (!value) return "";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");

  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function isoDesdeDatetimeLocal(value) {
  if (!value) return null;

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;

  return date.toISOString();
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

function ordenarElementos(elementos) {
  return [...(elementos || [])].sort((a, b) => {
    if (!a.inicio && !b.inicio) return a.id - b.id;
    if (!a.inicio) return 1;
    if (!b.inicio) return -1;
    return new Date(a.inicio).getTime() - new Date(b.inicio).getTime();
  });
}

function crearFormularioInicial(fecha) {
  return {
    tipo: "evento",
    titulo: "",
    descripcion: "",
    inicio: `${fecha}T09:00`,
    fin: `${fecha}T10:00`,
    todo_el_dia: false,
    version: null,
  };
}

function formularioDesdeElemento(elemento, fecha) {
  if (!elemento) return crearFormularioInicial(fecha);

  return {
    tipo: elemento.tipo || "evento",
    titulo: elemento.titulo || "",
    descripcion: elemento.descripcion || "",
    inicio: datetimeLocalDesdeIso(elemento.inicio),
    fin: datetimeLocalDesdeIso(elemento.fin),
    todo_el_dia: Boolean(elemento.todo_el_dia),
    version: elemento.version,
  };
}

function formularioComparable(formulario) {
  return {
    tipo: formulario.tipo || "evento",
    titulo: formulario.titulo || "",
    descripcion: formulario.descripcion || "",
    inicio: formulario.inicio || "",
    fin: formulario.fin || "",
    todo_el_dia: Boolean(formulario.todo_el_dia),
  };
}

function formulariosIguales(a, b) {
  return JSON.stringify(formularioComparable(a)) === JSON.stringify(formularioComparable(b));
}

function mensajeErrorAmigable(error, { conflictoVersion = false } = {}) {
  const status = obtenerHttpStatus(error);

  if (status === 409 && conflictoVersion) {
    return "Este elemento fue modificado desde otra sesion. Actualiza la informacion antes de guardar nuevamente.";
  }

  if (status === 409) {
    return "La agenda no permite esta accion en el estado actual.";
  }

  if (status === 403) {
    return "No tenes permiso para acceder a esta agenda.";
  }

  if (status === 404) {
    return "No se encontro la agenda o el elemento solicitado.";
  }

  if (status === 422 || status === 400) {
    return "Revisa los campos del formulario antes de continuar.";
  }

  return error?.message || "No se pudo completar la operacion.";
}

export default function AgendaPrivadaModal({
  comercio,
  onClose,
  backLabel = null,
}) {
  const comercioId = comercio?.id;
  const [fecha, setFecha] = useState(() => fechaInputHoy());
  const [estadoFiltro, setEstadoFiltro] = useState("");
  const [tipoFiltro, setTipoFiltro] = useState("");
  const [modoFormulario, setModoFormulario] = useState(null);
  const [elementoEditando, setElementoEditando] = useState(null);
  const [form, setForm] = useState(() => crearFormularioInicial(fechaInputHoy()));
  const [formInicial, setFormInicial] = useState(() =>
    crearFormularioInicial(fechaInputHoy())
  );
  const [mensajeError, setMensajeError] = useState("");
  const [solapamientos, setSolapamientos] = useState(null);

  const rango = useMemo(() => rangoIsoDelDia(fecha), [fecha]);
  const contextoQuery = useAgendaContexto(comercioId, {
    enabled: Boolean(comercioId),
  });
  const contexto = contextoQuery.data?.contexto || null;
  const contextoArchivado = contexto?.estado === "archivado";
  const elementosQuery = useAgendaElementos(comercioId, {
    inicio: rango.inicio,
    fin: rango.fin,
    estado: estadoFiltro || null,
    tipo: tipoFiltro || null,
    enabled: Boolean(comercioId && contexto),
  });
  const crearMutation = useCrearElementoAgendaMutation();
  const actualizarMutation = useActualizarElementoAgendaMutation();
  const cambiarEstadoMutation = useCambiarEstadoElementoAgendaMutation();

  const elementos = useMemo(
    () => ordenarElementos(elementosQuery.data || []),
    [elementosQuery.data]
  );

  useEffect(() => {
    if (modoFormulario === "crear") {
      setForm((prev) => ({
        ...prev,
        inicio: prev.inicio || `${fecha}T09:00`,
        fin: prev.fin || `${fecha}T10:00`,
      }));
    }
  }, [fecha, modoFormulario]);

  function abrirCrear() {
    const formNuevo = crearFormularioInicial(fecha);
    setMensajeError("");
    setSolapamientos(null);
    setElementoEditando(null);
    setModoFormulario("crear");
    setForm(formNuevo);
    setFormInicial(formNuevo);
  }

  function abrirEditar(elemento) {
    const formEdicion = formularioDesdeElemento(elemento, fecha);
    setMensajeError("");
    setSolapamientos(null);
    setElementoEditando(elemento);
    setModoFormulario("editar");
    setForm(formEdicion);
    setFormInicial(formEdicion);
  }

  function hayCambiosSinGuardar() {
    return Boolean(modoFormulario) && !formulariosIguales(form, formInicial);
  }

  function confirmarDescarteSiHaceFalta() {
    if (!hayCambiosSinGuardar()) return true;
    return window.confirm("Hay cambios sin guardar. Si continuas, se van a descartar.");
  }

  function cerrarFormulario() {
    if (!confirmarDescarteSiHaceFalta()) return;
    setModoFormulario(null);
    setElementoEditando(null);
    setMensajeError("");
  }

  function handleRequestClose() {
    if (!confirmarDescarteSiHaceFalta()) return;
    onClose?.();
  }

  function handleFormChange(event) {
    const { name, value, type, checked } = event.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  function payloadDesdeForm() {
    const base = {
      tipo: form.tipo,
      titulo: form.titulo.trim(),
      descripcion: form.descripcion.trim() || null,
      inicio: isoDesdeDatetimeLocal(form.inicio),
      fin: isoDesdeDatetimeLocal(form.fin),
      todo_el_dia: Boolean(form.todo_el_dia),
    };

    if (modoFormulario === "editar") {
      base.version_esperada = Number(form.version);
    }

    return base;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (contextoArchivado) return;

    try {
      setMensajeError("");
      setSolapamientos(null);

      if (!form.titulo.trim()) {
        throw new Error("El titulo es obligatorio.");
      }

      const payload = payloadDesdeForm();
      const response =
        modoFormulario === "editar"
          ? await actualizarMutation.mutateAsync({
              comercioId,
              elementoId: elementoEditando.id,
              payload,
            })
          : await crearMutation.mutateAsync({ comercioId, payload });

      if (response?.hay_solapamiento) {
        setSolapamientos(response);
      }

      setModoFormulario(null);
      setElementoEditando(null);
      const formGuardado = formularioDesdeElemento(response?.elemento, fecha);
      setForm(formGuardado);
      setFormInicial(formGuardado);
    } catch (error) {
      const conflictoVersion =
        modoFormulario === "editar" && obtenerHttpStatus(error) === 409;
      setMensajeError(mensajeErrorAmigable(error, { conflictoVersion }));

      if (conflictoVersion) {
        elementosQuery.refetch();
      }
    }
  }

  async function cambiarEstado(elemento, estado) {
    if (contextoArchivado) return;

    try {
      setMensajeError("");
      setSolapamientos(null);
      await cambiarEstadoMutation.mutateAsync({
        comercioId,
        elementoId: elemento.id,
        versionEsperada: elemento.version,
        estado,
      });
    } catch (error) {
      const conflictoVersion = obtenerHttpStatus(error) === 409;
      setMensajeError(mensajeErrorAmigable(error, { conflictoVersion }));

      if (conflictoVersion) {
        elementosQuery.refetch();
      }
    }
  }

  const isMutating =
    crearMutation.isPending ||
    actualizarMutation.isPending ||
    cambiarEstadoMutation.isPending;

  return (
    <ActiveLayer
      onClose={handleRequestClose}
      labelledBy="agenda-privada-title"
      describedBy="agenda-privada-description"
      contentClassName="mx-3 flex max-h-[92vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl border border-gray-800 bg-gray-950 shadow-2xl"
    >
      <header className="flex items-start justify-between gap-3 border-b border-gray-800 px-4 py-4">
        <div className="min-w-0">
          <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-orange-300">
            <CalendarDays size={14} aria-hidden="true" />
            Agenda privada
          </p>
          <h2 id="agenda-privada-title" className="mt-1 truncate text-lg font-bold text-white">
            {comercio?.nombre || "Espacio"}
          </h2>
          <p id="agenda-privada-description" className="mt-1 text-sm text-gray-400">
            Organiza eventos, tareas, recordatorios y bloqueos internos.
          </p>
        </div>

        {backLabel ? (
          <button
            type="button"
            onClick={handleRequestClose}
            className="inline-flex min-h-10 items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-gray-300 transition hover:bg-gray-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-orange-400"
          >
            <ArrowLeft size={16} aria-hidden="true" />
            {backLabel}
          </button>
        ) : (
          <button
            type="button"
            onClick={handleRequestClose}
            className="min-h-10 rounded-lg px-3 py-2 text-sm font-semibold text-gray-300 transition hover:bg-gray-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-orange-400"
            aria-label="Cerrar agenda"
          >
            <X size={18} aria-hidden="true" />
          </button>
        )}
      </header>

      <div className="overflow-y-auto px-4 py-4">
        {contextoQuery.isError ? (
          <div className="rounded-xl border border-red-900 bg-red-950/40 p-4 text-sm text-red-100">
            {mensajeErrorAmigable(contextoQuery.error)}
          </div>
        ) : null}

        {contextoArchivado ? (
          <div className="mb-4 rounded-xl border border-yellow-900 bg-yellow-950/30 p-3 text-sm text-yellow-100">
            Este contexto de agenda esta archivado. Podes consultar elementos,
            pero no crear ni modificar.
          </div>
        ) : null}

        <section className="rounded-xl bg-gray-900/60 p-3">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
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
                aria-label="Fecha de agenda"
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

          <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-3">
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

            <div className="flex items-end">
              <button
                type="button"
                onClick={abrirCrear}
                disabled={contextoArchivado || contextoQuery.isLoading}
                className="flex min-h-10 w-full items-center justify-center gap-2 rounded-lg bg-orange-500 px-3 py-2 text-sm font-semibold text-white transition hover:bg-orange-400 disabled:opacity-60"
              >
                <Plus size={16} aria-hidden="true" />
                Crear elemento
              </button>
            </div>
          </div>
        </section>

        {mensajeError ? (
          <div className="mt-4 rounded-xl border border-red-900 bg-red-950/40 p-4 text-sm text-red-100">
            {mensajeError}
          </div>
        ) : null}

        {solapamientos?.hay_solapamiento ? (
          <div className="mt-4 rounded-xl border border-yellow-900 bg-yellow-950/30 p-4 text-sm text-yellow-100">
            <div className="flex gap-2">
              <AlertTriangle size={18} className="mt-0.5 shrink-0" aria-hidden="true" />
              <div>
                <p className="font-semibold">Coincide con otros elementos</p>
                <p className="mt-1 text-yellow-100/80">
                  La operacion fue guardada. Revisa estos horarios relacionados:
                </p>
                <ul className="mt-2 space-y-1">
                  {solapamientos.solapamientos.map((item) => (
                    <li key={item.id}>
                      {formatearRango(item)} - {item.titulo}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ) : null}

        {modoFormulario ? (
          <form
            onSubmit={handleSubmit}
            className="mt-4 rounded-xl border border-gray-800 bg-gray-900/70 p-4"
          >
            <div className="flex items-center justify-between gap-3">
              <p className="font-semibold text-white">
                {modoFormulario === "editar" ? "Editar elemento" : "Nuevo elemento"}
              </p>
              <button
                type="button"
                onClick={cerrarFormulario}
                className="rounded-lg px-3 py-2 text-sm font-semibold text-gray-300 transition hover:bg-gray-800"
              >
                Cancelar
              </button>
            </div>

            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <label className="block sm:col-span-2">
                <span className="text-xs text-gray-400">Titulo *</span>
                <input
                  name="titulo"
                  value={form.titulo}
                  onChange={handleFormChange}
                  className="mt-1 w-full rounded-lg border border-gray-800 bg-gray-950 px-3 py-2 text-sm text-white outline-none focus:border-orange-500"
                  placeholder="Ej: llamada con proveedor"
                />
              </label>

              <label className="block">
                <span className="text-xs text-gray-400">Tipo</span>
                <select
                  name="tipo"
                  value={form.tipo}
                  onChange={handleFormChange}
                  className="mt-1 w-full rounded-lg border border-gray-800 bg-gray-950 px-3 py-2 text-sm text-white"
                >
                  {TIPOS.map((tipo) => (
                    <option key={tipo.value} value={tipo.value}>
                      {tipo.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="flex items-end gap-2 rounded-lg bg-gray-950 px-3 py-2">
                <input
                  type="checkbox"
                  name="todo_el_dia"
                  checked={form.todo_el_dia}
                  onChange={handleFormChange}
                  className="h-4 w-4"
                />
                <span className="text-sm text-gray-200">Todo el dia</span>
              </label>

              <label className="block">
                <span className="text-xs text-gray-400">Inicio</span>
                <input
                  type="datetime-local"
                  name="inicio"
                  value={form.inicio}
                  onChange={handleFormChange}
                  className="mt-1 w-full rounded-lg border border-gray-800 bg-gray-950 px-3 py-2 text-sm text-white outline-none focus:border-orange-500"
                />
              </label>

              <label className="block">
                <span className="text-xs text-gray-400">Fin</span>
                <input
                  type="datetime-local"
                  name="fin"
                  value={form.fin}
                  onChange={handleFormChange}
                  className="mt-1 w-full rounded-lg border border-gray-800 bg-gray-950 px-3 py-2 text-sm text-white outline-none focus:border-orange-500"
                />
              </label>

              <label className="block sm:col-span-2">
                <span className="text-xs text-gray-400">Descripcion</span>
                <textarea
                  name="descripcion"
                  value={form.descripcion}
                  onChange={handleFormChange}
                  rows={3}
                  className="mt-1 w-full rounded-lg border border-gray-800 bg-gray-950 px-3 py-2 text-sm text-white outline-none focus:border-orange-500"
                  placeholder="Notas internas opcionales"
                />
              </label>
            </div>

            <button
              type="submit"
              disabled={isMutating || contextoArchivado}
              className="mt-4 min-h-10 rounded-lg bg-white px-4 py-2 text-sm font-semibold text-black transition hover:bg-gray-100 disabled:opacity-60"
            >
              {isMutating ? "Guardando..." : "Guardar"}
            </button>
          </form>
        ) : null}

        <section className="mt-4 space-y-2">
          {contextoQuery.isLoading && !contextoQuery.data ? (
            <p className="rounded-xl bg-gray-900/60 p-4 text-sm text-gray-400">
              Preparando agenda...
            </p>
          ) : null}

          {elementosQuery.isLoading && elementos.length === 0 ? (
            <p className="rounded-xl bg-gray-900/60 p-4 text-sm text-gray-400">
              Cargando elementos...
            </p>
          ) : null}

          {!elementosQuery.isLoading && elementos.length === 0 ? (
            <div className="rounded-xl border border-dashed border-gray-800 bg-gray-900/40 p-6 text-center">
              <p className="font-semibold text-white">No hay elementos para este dia</p>
              <p className="mt-1 text-sm text-gray-400">
                Crea un evento, tarea, recordatorio o bloqueo interno.
              </p>
            </div>
          ) : null}

          {elementos.map((elemento) => (
            <article
              key={elemento.id}
              className="rounded-xl border border-gray-800 bg-gray-900/70 p-4"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-gray-800 px-2 py-0.5 text-[11px] font-semibold text-gray-200">
                      {TIPOS.find((tipo) => tipo.value === elemento.tipo)?.label ||
                        elemento.tipo}
                    </span>
                    <span className="text-xs text-gray-500">
                      {elemento.estado} - v{elemento.version}
                    </span>
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

                <div className="flex flex-wrap gap-1.5">
                  <button
                    type="button"
                    onClick={() => abrirEditar(elemento)}
                    disabled={contextoArchivado || isMutating}
                    className="flex min-h-9 items-center gap-1 rounded-lg px-2 py-1.5 text-xs font-semibold text-gray-200 transition hover:bg-gray-800 disabled:opacity-50"
                  >
                    <Pencil size={14} aria-hidden="true" />
                    Editar
                  </button>
                  <button
                    type="button"
                    onClick={() => cambiarEstado(elemento, "completado")}
                    disabled={
                      contextoArchivado ||
                      isMutating ||
                      elemento.estado === "completado"
                    }
                    className="flex min-h-9 items-center gap-1 rounded-lg px-2 py-1.5 text-xs font-semibold text-green-200 transition hover:bg-green-950/40 disabled:opacity-50"
                  >
                    <Check size={14} aria-hidden="true" />
                    Completar
                  </button>
                  <button
                    type="button"
                    onClick={() => cambiarEstado(elemento, "cancelado")}
                    disabled={
                      contextoArchivado ||
                      isMutating ||
                      elemento.estado === "cancelado"
                    }
                    className="flex min-h-9 items-center gap-1 rounded-lg px-2 py-1.5 text-xs font-semibold text-red-200 transition hover:bg-red-950/40 disabled:opacity-50"
                  >
                    <CircleSlash size={14} aria-hidden="true" />
                    Cancelar
                  </button>
                </div>
              </div>
            </article>
          ))}
        </section>
      </div>
    </ActiveLayer>
  );
}

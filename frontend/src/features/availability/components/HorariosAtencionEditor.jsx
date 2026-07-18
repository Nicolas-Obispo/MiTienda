import { useEffect, useRef, useState } from "react";

import {
  useHorariosAtencion,
  useReemplazarHorariosAtencionMutation,
} from "@features/availability/hooks/useHorariosAtencion";

const DIAS_SEMANA = [
  { id: 0, nombre: "Lunes" },
  { id: 1, nombre: "Martes" },
  { id: 2, nombre: "Miercoles" },
  { id: 3, nombre: "Jueves" },
  { id: 4, nombre: "Viernes" },
  { id: 5, nombre: "Sabado" },
  { id: 6, nombre: "Domingo" },
];

const HORA_REGEX = /^([01]\d|2[0-3]):[0-5]\d$/;
let siguienteClientId = 0;

function crearClientId() {
  siguienteClientId += 1;
  return `franja-${siguienteClientId}`;
}

function normalizarHora(hora) {
  if (!hora) return "";
  return String(hora).slice(0, 5);
}

function obtenerClientId(franja) {
  if (franja.client_id) return franja.client_id;
  if (franja.id !== undefined && franja.id !== null) return `backend-${franja.id}`;
  return crearClientId();
}

function ordenarFranjas(franjas) {
  return [...franjas].sort((a, b) => {
    if (a.dia_semana !== b.dia_semana) {
      return a.dia_semana - b.dia_semana;
    }

    if (a.hora_apertura !== b.hora_apertura) {
      return a.hora_apertura.localeCompare(b.hora_apertura);
    }

    return a.hora_cierre.localeCompare(b.hora_cierre);
  });
}

function normalizarFranjasRespuesta(data) {
  const franjas = Array.isArray(data?.franjas) ? data.franjas : [];

  return ordenarFranjas(
    franjas.map((franja) => ({
      id: franja.id ?? null,
      client_id: obtenerClientId(franja),
      dia_semana: Number(franja.dia_semana),
      hora_apertura: normalizarHora(franja.hora_apertura),
      hora_cierre: normalizarHora(franja.hora_cierre),
    }))
  );
}

function validarFranjas(franjas) {
  for (const franja of franjas) {
    if (!franja.hora_apertura || !franja.hora_cierre) {
      return "Completá hora de apertura y cierre en todas las franjas.";
    }

    if (
      !HORA_REGEX.test(franja.hora_apertura) ||
      !HORA_REGEX.test(franja.hora_cierre)
    ) {
      return "Usá horarios válidos con formato HH:MM.";
    }

    if (franja.hora_apertura >= franja.hora_cierre) {
      return "La apertura debe ser anterior al cierre. No se permiten cruces de medianoche.";
    }
  }

  for (const dia of DIAS_SEMANA) {
    const franjasDia = ordenarFranjas(
      franjas.filter((franja) => franja.dia_semana === dia.id)
    );

    for (let index = 1; index < franjasDia.length; index += 1) {
      const anterior = franjasDia[index - 1];
      const actual = franjasDia[index];

      if (actual.hora_apertura < anterior.hora_cierre) {
        return `Hay franjas solapadas en ${dia.nombre.toLowerCase()}.`;
      }
    }
  }

  return "";
}

function getMensajeError(error) {
  const mensaje = String(error?.message || "Error de red.");

  if (mensaje.includes("HTTP 401")) return "La sesion vencio. Iniciá sesion nuevamente.";
  if (mensaje.includes("HTTP 403")) return "No tenes permiso para editar estos horarios.";
  if (mensaje.includes("HTTP 404")) return "No se encontro el comercio.";
  if (mensaje.includes("solap")) return "Hay horarios solapados. Revisá las franjas.";
  if (mensaje.includes("hora_apertura")) {
    return "La apertura debe ser anterior al cierre. No se permiten cruces de medianoche.";
  }

  return "No se pudieron guardar los horarios. Revisá tu conexion e intentá nuevamente.";
}

export default function HorariosAtencionEditor({ comercio, onClose }) {
  const comercioId = comercio?.id;
  const cerrarButtonRef = useRef(null);
  const [franjas, setFranjas] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");

  const horariosQuery = useHorariosAtencion(comercioId, {
    enabled: Boolean(comercioId),
  });
  const reemplazarMutation = useReemplazarHorariosAtencionMutation();

  useEffect(() => {
    cerrarButtonRef.current?.focus();
  }, []);

  useEffect(() => {
    if (!horariosQuery.data) return;

    let activo = true;

    queueMicrotask(() => {
      if (!activo) return;

      setFranjas(normalizarFranjasRespuesta(horariosQuery.data));
      setErrorMessage("");
    });

    return () => {
      activo = false;
    };
  }, [horariosQuery.data]);

  function agregarFranja(diaSemana) {
    setErrorMessage("");
    setFranjas((actuales) => [
      ...actuales,
      {
        id: null,
        client_id: crearClientId(),
        dia_semana: diaSemana,
        hora_apertura: "08:00",
        hora_cierre: "12:00",
      },
    ]);
  }

  function actualizarFranja(clientId, campo, valor) {
    setErrorMessage("");
    setFranjas((actuales) =>
      actuales.map((franja) =>
        franja.client_id === clientId
          ? {
              ...franja,
              [campo]: valor,
            }
          : franja
      )
    );
  }

  function eliminarFranja(clientId) {
    setErrorMessage("");
    setFranjas((actuales) =>
      actuales.filter((franja) => franja.client_id !== clientId)
    );
  }

  function dejarDiaSinAtencion(diaSemana) {
    setErrorMessage("");
    setFranjas((actuales) =>
      actuales.filter((franja) => franja.dia_semana !== diaSemana)
    );
  }

  function cancelarEdicion() {
    setFranjas(normalizarFranjasRespuesta(horariosQuery.data));
    setErrorMessage("");
    onClose();
  }

  async function guardarHorarios() {
    const franjasOrdenadas = ordenarFranjas(franjas);
    const errorValidacion = validarFranjas(franjasOrdenadas);

    if (errorValidacion) {
      setErrorMessage(errorValidacion);
      return;
    }

    const payloadFranjas = franjasOrdenadas.map((franja) => ({
      dia_semana: franja.dia_semana,
      hora_apertura: franja.hora_apertura,
      hora_cierre: franja.hora_cierre,
    }));

    try {
      setErrorMessage("");
      await reemplazarMutation.mutateAsync({
        comercioId,
        franjas: payloadFranjas,
      });
      onClose();
    } catch (error) {
      setErrorMessage(getMensajeError(error));
    }
  }

  const isLoadingSinCache =
    horariosQuery.isLoading && !horariosQuery.data && franjas.length === 0;
  const isSaving = reemplazarMutation.isPending;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 px-3 py-6">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="horarios-editor-title"
        className="flex max-h-full w-full max-w-3xl flex-col overflow-hidden rounded-2xl border border-gray-800 bg-gray-950 text-white shadow-2xl"
      >
        <div className="flex items-start justify-between gap-4 border-b border-gray-800 p-4">
          <div className="min-w-0">
            <h3 id="horarios-editor-title" className="text-lg font-semibold">
              Editar horarios
            </h3>
            <p className="mt-1 truncate text-sm text-gray-400">
              {comercio?.nombre || "Espacio"}
            </p>
          </div>

          <button
            ref={cerrarButtonRef}
            type="button"
            onClick={cancelarEdicion}
            className="rounded-full border border-gray-700 px-3 py-1 text-sm text-gray-300 hover:bg-gray-900"
          >
            Cerrar
          </button>
        </div>

        <div className="overflow-y-auto p-4">
          {isLoadingSinCache ? (
            <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
              <p className="text-sm text-gray-300">Cargando horarios...</p>
            </div>
          ) : (
            <div className="space-y-3">
              {DIAS_SEMANA.map((dia) => {
                const franjasDia = ordenarFranjas(
                  franjas.filter((franja) => franja.dia_semana === dia.id)
                );

                return (
                  <section
                    key={dia.id}
                    className="rounded-xl border border-gray-800 bg-gray-900/70 p-3"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <h4 className="text-sm font-semibold text-white">
                        {dia.nombre}
                      </h4>

                      {franjasDia.length > 0 ? (
                        <button
                          type="button"
                          onClick={() => dejarDiaSinAtencion(dia.id)}
                          className="rounded-lg border border-gray-700 px-2 py-1 text-xs text-gray-300 hover:bg-gray-800"
                        >
                          Sin atencion
                        </button>
                      ) : null}
                    </div>

                    {franjasDia.length === 0 ? (
                      <p className="mt-2 text-xs text-gray-500">
                        Sin horarios declarados.
                      </p>
                    ) : (
                      <div className="mt-3 space-y-2">
                        {franjasDia.map((franja, indexDia) => (
                          <div
                            key={franja.client_id}
                            className="grid grid-cols-1 gap-2 sm:grid-cols-[1fr_1fr_auto] sm:items-end"
                          >
                            <label className="text-xs text-gray-400">
                              Apertura
                              <input
                                type="time"
                                value={franja.hora_apertura}
                                onChange={(event) =>
                                  actualizarFranja(
                                    franja.client_id,
                                    "hora_apertura",
                                    event.target.value
                                  )
                                }
                                className="mt-1 w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white"
                              />
                            </label>

                            <label className="text-xs text-gray-400">
                              Cierre
                              <input
                                type="time"
                                value={franja.hora_cierre}
                                onChange={(event) =>
                                  actualizarFranja(
                                    franja.client_id,
                                    "hora_cierre",
                                    event.target.value
                                  )
                                }
                                className="mt-1 w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white"
                              />
                            </label>

                            <button
                              type="button"
                              onClick={() => eliminarFranja(franja.client_id)}
                              className="min-h-10 rounded-lg border border-red-900 bg-red-950/40 px-3 py-2 text-xs font-semibold text-red-200 hover:bg-red-950"
                              aria-label={`Eliminar franja ${indexDia + 1} de ${dia.nombre}`}
                            >
                              Eliminar
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    <button
                      type="button"
                      onClick={() => agregarFranja(dia.id)}
                      className="mt-3 min-h-10 rounded-lg border border-gray-700 px-3 py-2 text-xs font-semibold text-gray-200 hover:bg-gray-800"
                    >
                      {franjasDia.length > 0
                        ? "+ Agregar otra franja"
                        : "+ Agregar franja"}
                    </button>
                  </section>
                );
              })}
            </div>
          )}

          {errorMessage ? (
            <div className="mt-4 rounded-xl border border-red-900 bg-red-950/40 p-3">
              <p className="text-sm font-semibold text-red-200">Error</p>
              <p className="mt-1 text-sm text-red-100">{errorMessage}</p>
            </div>
          ) : null}
        </div>

        <div className="flex flex-col gap-2 border-t border-gray-800 p-4 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={cancelarEdicion}
            disabled={isSaving}
            className="min-h-11 rounded-xl border border-gray-700 px-4 py-2 text-sm font-semibold text-gray-200 hover:bg-gray-900 disabled:opacity-60"
          >
            Cancelar
          </button>

          <button
            type="button"
            onClick={guardarHorarios}
            disabled={isSaving || isLoadingSinCache}
            className="min-h-11 rounded-xl bg-white px-4 py-2 text-sm font-semibold text-gray-950 hover:opacity-90 disabled:opacity-60"
          >
            {isSaving ? "Guardando..." : "Guardar horarios"}
          </button>
        </div>
      </div>
    </div>
  );
}

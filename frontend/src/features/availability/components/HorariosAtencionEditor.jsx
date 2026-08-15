import { useEffect, useRef, useState } from "react";

import { ActiveLayer } from "@core";
import { Alert, Button, Skeleton, Surface } from "@shared";
import {
  useHorariosAtencion,
  useReemplazarHorariosAtencionMutation,
} from "@features/availability/hooks/useHorariosAtencion";
import HoraInput from "./HoraInput";

const DIAS_SEMANA = [
  { id: 0, nombre: "Lunes" },
  { id: 1, nombre: "Martes" },
  { id: 2, nombre: "Miercoles" },
  { id: 3, nombre: "Jueves" },
  { id: 4, nombre: "Viernes" },
  { id: 5, nombre: "Sabado" },
  { id: 6, nombre: "Domingo" },
];

const DIAS_HABILES = [0, 1, 2, 3, 4];
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

function crearFranjaLocal(
  diaSemana,
  horaApertura = "08:00",
  horaCierre = "12:00"
) {
  return {
    id: null,
    client_id: crearClientId(),
    dia_semana: diaSemana,
    hora_apertura: horaApertura,
    hora_cierre: horaCierre,
  };
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

function obtenerDia(diaSemana) {
  return DIAS_SEMANA.find((dia) => dia.id === diaSemana);
}

function obtenerFranjasDia(franjas, diaSemana) {
  return ordenarFranjas(
    franjas.filter((franja) => franja.dia_semana === diaSemana)
  );
}

function obtenerResumenDia(franjasDia) {
  if (franjasDia.length === 0) return "Cerrado";

  return franjasDia
    .map((franja) => `${franja.hora_apertura}-${franja.hora_cierre}`)
    .join(" · ");
}

function esDiaHabil(diaSemana) {
  return DIAS_HABILES.includes(Number(diaSemana));
}

function existenFranjasHabilesExceptoOrigen(franjas, diaOrigen) {
  return franjas.some(
    (franja) =>
      esDiaHabil(franja.dia_semana) && franja.dia_semana !== diaOrigen
  );
}

function validarFranjas(franjas) {
  for (const franja of franjas) {
    if (!franja.hora_apertura || !franja.hora_cierre) {
      return "Completa hora de apertura y cierre en todas las franjas.";
    }

    if (
      !HORA_REGEX.test(franja.hora_apertura) ||
      !HORA_REGEX.test(franja.hora_cierre)
    ) {
      return "Usa horarios validos con formato HH:MM.";
    }

    if (franja.hora_apertura >= franja.hora_cierre) {
      return "La apertura debe ser anterior al cierre. No se permiten cruces de medianoche.";
    }
  }

  for (const dia of DIAS_SEMANA) {
    const franjasDia = obtenerFranjasDia(franjas, dia.id);

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

function respuestaPerteneceAlComercio(data, comercioId) {
  if (!data || !comercioId) return false;
  return Number(data.comercio_id) === Number(comercioId);
}

function getMensajeError(error) {
  const mensaje = String(error?.message || "Error de red.");

  if (mensaje.includes("HTTP 401")) return "La sesion vencio. Inicia sesion nuevamente.";
  if (mensaje.includes("HTTP 403")) return "No tenes permiso para editar estos horarios.";
  if (mensaje.includes("HTTP 404")) return "No se encontro el comercio.";
  if (mensaje.includes("solap")) return "Hay horarios solapados. Revisa las franjas.";
  if (mensaje.includes("hora_apertura")) {
    return "La apertura debe ser anterior al cierre. No se permiten cruces de medianoche.";
  }

  return "No se pudieron guardar los horarios. Revisa tu conexion e intenta nuevamente.";
}

export default function HorariosAtencionEditor({ comercio, onClose }) {
  const comercioId = comercio?.id;
  const cerrarButtonRef = useRef(null);
  const [franjas, setFranjas] = useState([]);
  const [diaSeleccionado, setDiaSeleccionado] = useState(null);
  const [diaOrigenAplicar, setDiaOrigenAplicar] = useState(null);
  const [diasDestinoSeleccionados, setDiasDestinoSeleccionados] = useState([]);
  const [reemplazoConfirmado, setReemplazoConfirmado] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [aplicarErrorMessage, setAplicarErrorMessage] = useState("");
  const [horaInputAbiertoId, setHoraInputAbiertoId] = useState(null);

  const horariosQuery = useHorariosAtencion(comercioId, {
    enabled: Boolean(comercioId),
  });
  const reemplazarMutation = useReemplazarHorariosAtencionMutation();

  useEffect(() => {
    cerrarButtonRef.current?.focus();
  }, []);

  useEffect(() => {
    let activo = true;

    queueMicrotask(() => {
      if (!activo) return;

      setFranjas([]);
      setDiaSeleccionado(null);
      setDiaOrigenAplicar(null);
      setDiasDestinoSeleccionados([]);
      setReemplazoConfirmado(false);
      setErrorMessage("");
      setAplicarErrorMessage("");
      setHoraInputAbiertoId(null);
    });

    return () => {
      activo = false;
    };
  }, [comercioId]);

  useEffect(() => {
    if (!respuestaPerteneceAlComercio(horariosQuery.data, comercioId)) return;

    let activo = true;
    const franjasNormalizadas = normalizarFranjasRespuesta(horariosQuery.data);

    queueMicrotask(() => {
      if (!activo) return;

      setFranjas(franjasNormalizadas);
      setErrorMessage("");
      setAplicarErrorMessage("");
    });

    return () => {
      activo = false;
    };
  }, [comercioId, horariosQuery.data]);

  function limpiarFlujoAplicar() {
    setDiaOrigenAplicar(null);
    setDiasDestinoSeleccionados([]);
    setReemplazoConfirmado(false);
    setAplicarErrorMessage("");
  }

  function agregarFranja(diaSemana) {
    setErrorMessage("");
    setAplicarErrorMessage("");
    setFranjas((actuales) => [...actuales, crearFranjaLocal(diaSemana)]);
  }

  function actualizarFranja(clientId, campo, valor) {
    setErrorMessage("");
    setAplicarErrorMessage("");
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
    setAplicarErrorMessage("");
    setFranjas((actuales) =>
      actuales.filter((franja) => franja.client_id !== clientId)
    );
  }

  function dejarDiaSinAtencion(diaSemana) {
    setErrorMessage("");
    setAplicarErrorMessage("");
    setFranjas((actuales) =>
      actuales.filter((franja) => franja.dia_semana !== diaSemana)
    );
  }

  function volverAlResumen() {
    setDiaSeleccionado(null);
    limpiarFlujoAplicar();
    setHoraInputAbiertoId(null);
  }

  function abrirAplicarHorarios(diaOrigen) {
    const sugerirHabiles =
      esDiaHabil(diaOrigen) &&
      !existenFranjasHabilesExceptoOrigen(franjas, diaOrigen);
    const sugeridos = sugerirHabiles
      ? DIAS_HABILES.filter((diaSemana) => diaSemana !== diaOrigen)
      : [];

    setDiaOrigenAplicar(diaOrigen);
    setDiasDestinoSeleccionados(sugeridos);
    setReemplazoConfirmado(false);
    setAplicarErrorMessage("");
    setHoraInputAbiertoId(null);
  }

  function toggleDiaDestino(diaSemana) {
    setAplicarErrorMessage("");
    setReemplazoConfirmado(false);
    setDiasDestinoSeleccionados((actuales) =>
      actuales.includes(diaSemana)
        ? actuales.filter((dia) => dia !== diaSemana)
        : [...actuales, diaSemana]
    );
  }

  function aplicarHorariosADias() {
    if (diaOrigenAplicar === null) return;

    const franjasOrigen = obtenerFranjasDia(franjas, diaOrigenAplicar);
    const errorOrigen = validarFranjas(franjasOrigen);

    if (franjasOrigen.length === 0) {
      setAplicarErrorMessage("El dia de origen no tiene horarios para copiar.");
      return;
    }

    if (errorOrigen) {
      setAplicarErrorMessage(errorOrigen);
      return;
    }

    if (diasDestinoSeleccionados.length === 0) {
      setAplicarErrorMessage("Elegi al menos un dia de destino.");
      return;
    }

    const destinosConHorarios = diasDestinoSeleccionados.filter(
      (diaSemana) => obtenerFranjasDia(franjas, diaSemana).length > 0
    );

    if (destinosConHorarios.length > 0 && !reemplazoConfirmado) {
      setAplicarErrorMessage(
        "Hay dias seleccionados con horarios existentes. Confirma el reemplazo para continuar."
      );
      return;
    }

    setFranjas((actuales) => {
      const sinDestinos = actuales.filter(
        (franja) => !diasDestinoSeleccionados.includes(franja.dia_semana)
      );
      const copias = diasDestinoSeleccionados.flatMap((diaSemana) =>
        franjasOrigen.map((franja) =>
          crearFranjaLocal(diaSemana, franja.hora_apertura, franja.hora_cierre)
        )
      );

      return [...sinDestinos, ...copias];
    });

    limpiarFlujoAplicar();
  }

  function cancelarEdicion() {
    setFranjas(
      respuestaPerteneceAlComercio(horariosQuery.data, comercioId)
        ? normalizarFranjasRespuesta(horariosQuery.data)
        : []
    );
    setErrorMessage("");
    setAplicarErrorMessage("");
    setHoraInputAbiertoId(null);
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
  const diaActivo = obtenerDia(diaSeleccionado);
  const estaAplicandoHorarios = diaOrigenAplicar !== null;
  const franjasDiaActivo =
    diaSeleccionado === null ? [] : obtenerFranjasDia(franjas, diaSeleccionado);
  const franjasOrigen =
    diaOrigenAplicar === null ? [] : obtenerFranjasDia(franjas, diaOrigenAplicar);
  const destinosConHorarios = diasDestinoSeleccionados.filter(
    (diaSemana) => obtenerFranjasDia(franjas, diaSemana).length > 0
  );

  return (
    <ActiveLayer
      onClose={cancelarEdicion}
      labelledBy="horarios-editor-title"
      initialFocusRef={cerrarButtonRef}
      closeOnBackdrop={false}
      className="px-3 py-6"
      backdropClassName="bg-overlay-backdrop"
      contentClassName="flex max-h-full w-full max-w-2xl flex-col overflow-hidden rounded-2xl border border-border bg-surface-elevated text-primary shadow-elevation"
    >
        <div className="flex items-start justify-between gap-4 border-b border-border p-4">
          <div className="min-w-0">
            <h3 id="horarios-editor-title" className="text-lg font-semibold">
              {estaAplicandoHorarios
                ? "Aplicar horarios"
                : diaActivo
                  ? diaActivo.nombre
                  : "Editar horarios"}
            </h3>
            <p className="mt-1 truncate text-sm text-secondary">
              {comercio?.nombre || "Espacio"}
            </p>
          </div>

          <Button
            ref={cerrarButtonRef}
            type="button"
            onClick={cancelarEdicion}
            variant="secondary"
            className="px-3 py-2 text-sm"
          >
            Cerrar
          </Button>
        </div>

        <div className="overflow-y-auto p-4">
          {isLoadingSinCache ? (
            <Skeleton className="h-14 rounded-xl border border-border" />
          ) : estaAplicandoHorarios ? (
            <div className="space-y-4">
              <Surface variant="subtle" className="rounded-xl p-3">
                <p className="text-xs uppercase tracking-wide text-muted">
                  Origen
                </p>
                <p className="mt-1 text-sm font-semibold text-primary">
                  {obtenerDia(diaOrigenAplicar)?.nombre}
                </p>
                <p className="mt-1 text-sm text-secondary">
                  {obtenerResumenDia(franjasOrigen)}
                </p>
              </Surface>

              <fieldset className="space-y-2">
                <legend className="text-sm font-semibold text-primary">
                  Elegi los dias de destino
                </legend>
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                  {DIAS_SEMANA.map((dia) => {
                    const esOrigen = dia.id === diaOrigenAplicar;
                    const estaSeleccionado = diasDestinoSeleccionados.includes(
                      dia.id
                    );
                    const tieneHorarios =
                      !esOrigen && obtenerFranjasDia(franjas, dia.id).length > 0;

                    return (
                      <label
                        key={dia.id}
                        className={`flex min-h-12 items-center justify-between gap-3 rounded-xl px-3 py-2 text-sm transition ${
                          esOrigen
                            ? "bg-disabled-surface text-disabled-text"
                            : "bg-surface-subtle text-primary hover:bg-surface"
                        }`}
                      >
                        <span>
                          <span className="font-medium">{dia.nombre}</span>
                          {tieneHorarios ? (
                            <span className="block text-xs text-warning-text">
                              Tiene horarios, se reemplazaran
                            </span>
                          ) : null}
                        </span>
                        <input
                          type="checkbox"
                          checked={estaSeleccionado}
                          disabled={esOrigen}
                          onChange={() => toggleDiaDestino(dia.id)}
                          className="h-4 w-4 rounded border-border-strong bg-surface text-interactive-primary"
                        />
                      </label>
                    );
                  })}
                </div>
              </fieldset>

              {destinosConHorarios.length > 0 ? (
                <label className="flex items-start gap-3 rounded-xl bg-warning-surface p-3 text-sm text-warning-text">
                  <input
                    type="checkbox"
                    checked={reemplazoConfirmado}
                    onChange={(event) => {
                      setReemplazoConfirmado(event.target.checked);
                      setAplicarErrorMessage("");
                    }}
                    className="mt-0.5 h-4 w-4 rounded border-warning-border bg-surface"
                  />
                  <span>
                    Confirmo reemplazar los horarios existentes de los dias
                    seleccionados.
                  </span>
                </label>
              ) : null}

              {aplicarErrorMessage ? (
                <p className="rounded-xl bg-danger-surface p-3 text-sm text-danger-text" role="alert">
                  {aplicarErrorMessage}
                </p>
              ) : null}

              <div className="flex flex-col gap-2 sm:flex-row sm:justify-end">
                <Button
                  type="button"
                  onClick={limpiarFlujoAplicar}
                  variant="secondary"
                  className="min-h-11 px-4 py-2 text-sm"
                >
                  Cancelar
                </Button>
                <Button
                  type="button"
                  onClick={aplicarHorariosADias}
                  variant="primary"
                  className="min-h-11 px-4 py-2 text-sm"
                >
                  Aplicar horarios
                </Button>
              </div>
            </div>
          ) : diaActivo ? (
            <div className="space-y-4">
              <Button
                type="button"
                onClick={volverAlResumen}
                variant="secondary"
                className="px-3 py-2 text-sm"
              >
                Volver al resumen semanal
              </Button>

              <Surface as="section" variant="subtle" className="rounded-xl p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h4 className="text-sm font-semibold text-primary">
                      {diaActivo.nombre}
                    </h4>
                    <p className="mt-1 text-xs text-muted">
                      {obtenerResumenDia(franjasDiaActivo)}
                    </p>
                  </div>

                  {franjasDiaActivo.length > 0 ? (
                    <Button
                      type="button"
                      onClick={() => dejarDiaSinAtencion(diaActivo.id)}
                      variant="secondary"
                      className="min-h-10 px-3 py-2 text-xs"
                    >
                      Marcar cerrado
                    </Button>
                  ) : null}
                </div>

                {franjasDiaActivo.length === 0 ? (
                  <p className="mt-4 rounded-lg bg-surface p-3 text-sm text-muted">
                    Este dia esta cerrado.
                  </p>
                ) : (
                  <div className="mt-4 space-y-3">
                    {franjasDiaActivo.map((franja, indexDia) => (
                      <div
                        key={franja.client_id}
                        className="grid grid-cols-1 gap-2 sm:grid-cols-[1fr_1fr_auto] sm:items-end"
                      >
                        <HoraInput
                          id={`${franja.client_id}-apertura`}
                          label="Apertura"
                          value={franja.hora_apertura}
                          isOpen={
                            horaInputAbiertoId ===
                            `${franja.client_id}-apertura`
                          }
                          onOpenChange={(isOpen) =>
                            setHoraInputAbiertoId(
                              isOpen ? `${franja.client_id}-apertura` : null
                            )
                          }
                          onChange={(valor) =>
                            actualizarFranja(
                              franja.client_id,
                              "hora_apertura",
                              valor
                            )
                          }
                        />

                        <HoraInput
                          id={`${franja.client_id}-cierre`}
                          label="Cierre"
                          value={franja.hora_cierre}
                          isOpen={
                            horaInputAbiertoId === `${franja.client_id}-cierre`
                          }
                          onOpenChange={(isOpen) =>
                            setHoraInputAbiertoId(
                              isOpen ? `${franja.client_id}-cierre` : null
                            )
                          }
                          onChange={(valor) =>
                            actualizarFranja(
                              franja.client_id,
                              "hora_cierre",
                              valor
                            )
                          }
                        />

                        <Button
                          type="button"
                          onClick={() => eliminarFranja(franja.client_id)}
                          variant="danger"
                          className="min-h-10 px-3 py-2 text-xs"
                          aria-label={`Eliminar franja ${indexDia + 1} de ${diaActivo.nombre}`}
                        >
                          Eliminar
                        </Button>
                      </div>
                    ))}
                  </div>
                )}

                <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
                  <Button
                    type="button"
                    onClick={() => agregarFranja(diaActivo.id)}
                    variant="secondary"
                    className="min-h-10 px-3 py-2 text-sm"
                  >
                    {franjasDiaActivo.length > 0
                      ? "+ Agregar otra franja"
                      : "+ Agregar franja"}
                  </Button>

                  {franjasDiaActivo.length > 0 ? (
                    <Button
                      type="button"
                      onClick={() => abrirAplicarHorarios(diaActivo.id)}
                      variant="secondary"
                      className="min-h-10 px-3 py-2 text-sm"
                    >
                      Aplicar estos horarios a otros dias
                    </Button>
                  ) : null}
                </div>
              </Surface>
            </div>
          ) : (
            <div className="space-y-2">
              {DIAS_SEMANA.map((dia) => {
                const franjasDia = obtenerFranjasDia(franjas, dia.id);

                return (
                  <Button
                    key={dia.id}
                    type="button"
                    onClick={() => setDiaSeleccionado(dia.id)}
                    variant="secondary"
                    className="flex min-h-14 w-full items-center justify-between gap-3 px-3 py-2 text-left"
                  >
                    <span className="min-w-0">
                      <span className="block text-sm font-semibold text-primary">
                        {dia.nombre}
                      </span>
                      <span
                        className={`mt-0.5 block truncate text-sm ${
                          franjasDia.length > 0
                            ? "text-secondary"
                            : "text-muted"
                        }`}
                      >
                        {obtenerResumenDia(franjasDia)}
                      </span>
                    </span>
                    <span className="shrink-0 text-xs font-semibold text-secondary">
                      Editar
                    </span>
                  </Button>
                );
              })}
            </div>
          )}

          {errorMessage ? (
            <Alert variant="danger" role="alert" className="mt-4 p-3">
              <p className="text-sm font-semibold">Error</p>
              <p className="mt-1 text-sm">{errorMessage}</p>
            </Alert>
          ) : null}
        </div>

        <div className="flex flex-col gap-2 border-t border-border p-4 sm:flex-row sm:justify-between">
          <Button
            type="button"
            onClick={cancelarEdicion}
            disabled={isSaving}
            variant="secondary"
            className="min-h-11 px-4 py-2 text-sm"
          >
            Cancelar
          </Button>

          <Button
            type="button"
            onClick={guardarHorarios}
            disabled={isSaving || isLoadingSinCache}
            variant="primary"
            className="min-h-11 px-4 py-2 text-sm"
          >
            {isSaving ? "Guardando..." : "Guardar horarios"}
          </Button>
        </div>
    </ActiveLayer>
  );
}

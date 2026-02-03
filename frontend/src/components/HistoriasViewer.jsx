/**
 * HistoriasViewer.jsx
 * -------------------------------------------------------
 * Viewer de Historias (UI tipo Instagram).
 *
 * Responsabilidad:
 * - Mostrar historias en modo pantalla completa (modal).
 * - Permitir avanzar/retroceder entre historias.
 * - Auto-advance con timer.
 *
 * Reglas:
 * - Este componente NO hace requests.
 * - Recibe las historias por props (la página decide cómo cargarlas).
 */

import React, { useEffect, useMemo, useState } from "react";

/**
 * getMediaUrlFromHistoria
 * -------------------------------------------------------
 * Qué hace:
 * - Devuelve la URL del media de una historia, soportando ambos formatos:
 *   - media_url (snake_case típico de backend Python)
 *   - mediaUrl (camelCase típico de frontend)
 *
 * Por qué existe:
 * - Evita que el viewer dependa del shape exacto del backend.
 *
 * @param {Object} historia
 * @returns {string|null}
 */
function getMediaUrlFromHistoria(historia) {
  if (!historia) return null;

  // Backend probable (snake_case)
  if (typeof historia.media_url === "string" && historia.media_url.trim() !== "") {
    return historia.media_url;
  }

  // Frontend probable (camelCase)
  if (typeof historia.mediaUrl === "string" && historia.mediaUrl.trim() !== "") {
    return historia.mediaUrl;
  }

  return null;
}

/**
 * HistoriasViewer
 * -------------------------------------------------------
 * Qué hace:
 * - Renderiza un modal fullscreen con una historia activa.
 * - Click izquierda: anterior
 * - Click derecha: siguiente
 * - Botón X: cerrar
 * - Barra de progreso simple arriba
 *
 * @param {Object} props
 * @param {boolean} props.isOpen - si el viewer está visible
 * @param {() => void} props.onClose - cerrar viewer
 * @param {Array} props.historias - lista de historias a reproducir
 * @param {string} props.titulo - título a mostrar (ej: nombre del comercio)
 * @returns {JSX.Element|null}
 */
export default function HistoriasViewer({
  isOpen,
  onClose,
  historias = [],
  titulo = "Historias",
}) {
  /**
   * indexActual:
   * - Controla qué historia se está mostrando.
   */
  const [indexActual, setIndexActual] = useState(0);

  /**
   * progreso:
   * - 0 a 100 para simular barra de tiempo (auto-advance).
   */
  const [progreso, setProgreso] = useState(0);

  /**
   * historiaActual:
   * - La historia a mostrar según indexActual.
   */
  const historiaActual = useMemo(() => {
    if (!Array.isArray(historias) || historias.length === 0) return null;
    return historias[Math.min(indexActual, historias.length - 1)];
  }, [historias, indexActual]);

  /**
   * mediaUrl:
   * - URL normalizada del media (soporta snake_case y camelCase).
   */
  const mediaUrl = useMemo(() => {
    return getMediaUrlFromHistoria(historiaActual);
  }, [historiaActual]);

  /**
   * resetAlAbrir:
   * - Cada vez que se abre, arrancamos desde la primera historia.
   */
  useEffect(() => {
    if (isOpen) {
      setIndexActual(0);
      setProgreso(0);
    }
  }, [isOpen]);

  /**
   * cerrar:
   * - Cierra el viewer y resetea progreso.
   */
  function cerrar() {
    setProgreso(0);
    if (typeof onClose === "function") onClose();
  }

  /**
   * avanzar:
   * - Pasa a la siguiente historia.
   * - Si es la última, cierra.
   */
  function avanzar() {
    setIndexActual((prev) => {
      const next = prev + 1;
      if (next >= historias.length) {
        cerrar();
        return prev;
      }
      return next;
    });
  }

  /**
   * retroceder:
   * - Vuelve a la historia anterior.
   */
  function retroceder() {
    setIndexActual((prev) => Math.max(0, prev - 1));
    setProgreso(0);
  }

  /**
   * autoAdvanceTimer:
   * - Simula el “avance automático” de historias.
   * - Si llega a 100%, pasa a la siguiente.
   */
  useEffect(() => {
    if (!isOpen) return;
    if (!historiaActual) return;

    const tickMs = 50; // cada 50ms
    const duracionMs = 5000; // 5s por historia
    const delta = (100 * tickMs) / duracionMs;

    const intervalId = setInterval(() => {
      setProgreso((prev) => {
        const next = prev + delta;

        if (next >= 100) {
          /**
           * Si termina el tiempo, avanzamos.
           * - Si ya estamos en la última, cerramos.
           */
          avanzar();
          return 0;
        }

        return next;
      });
    }, tickMs);

    return () => clearInterval(intervalId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, historiaActual, indexActual]);

  /**
   * handleKeyDown:
   * - ESC cierra
   * - Flecha derecha avanza
   * - Flecha izquierda retrocede
   */
  useEffect(() => {
    if (!isOpen) return;

    function handleKeyDown(e) {
      if (e.key === "Escape") cerrar();
      if (e.key === "ArrowRight") avanzar();
      if (e.key === "ArrowLeft") retroceder();
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, historias]);

  /**
   * Si no está abierto, no renderizamos nada.
   */
  if (!isOpen) return null;

  /**
   * Si no hay historias, renderizamos modal simple con mensaje.
   */
  if (!historiaActual) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90">
        <div className="w-full max-w-md rounded-2xl border border-white/10 bg-gray-950 p-5 text-white">
          <div className="flex items-center justify-between">
            <div className="font-semibold">{titulo}</div>
            <button
              type="button"
              className="rounded-xl border border-white/10 px-3 py-1 text-sm"
              onClick={cerrar}
            >
              Cerrar
            </button>
          </div>
          <p className="mt-4 text-sm opacity-80">No hay historias para mostrar.</p>
        </div>
      </div>
    );
  }

  /**
   * Si la historia existe pero no tiene mediaUrl válido:
   * - Mostramos un fallback visual y permitimos avanzar.
   */
  if (!mediaUrl) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black">
        <div className="w-full max-w-md rounded-2xl border border-white/10 bg-gray-950 p-5 text-white">
          <div className="flex items-center justify-between">
            <div className="font-semibold">{titulo}</div>
            <button
              type="button"
              className="rounded-xl border border-white/10 px-3 py-1 text-sm"
              onClick={cerrar}
            >
              ✕
            </button>
          </div>

          <p className="mt-4 text-sm opacity-80">
            Esta historia no tiene media válido.
          </p>

          <div className="mt-4 flex gap-2">
            <button
              type="button"
              className="flex-1 rounded-xl border border-white/10 px-3 py-2 text-sm"
              onClick={retroceder}
            >
              Anterior
            </button>
            <button
              type="button"
              className="flex-1 rounded-xl border border-white/10 px-3 py-2 text-sm"
              onClick={avanzar}
            >
              Siguiente
            </button>
          </div>
        </div>
      </div>
    );
  }

  /**
   * Render modal fullscreen.
   */
  return (
    <div className="fixed inset-0 z-50 bg-black">
      {/* Header + barras de progreso */}
      <div className="absolute left-0 right-0 top-0 z-10 px-3 pt-3">
        {/* Barras de progreso por historia */}
        <div className="mb-3 flex gap-1">
          {historias.map((h, i) => {
            /**
             * Cada historia tiene su barra:
             * - anteriores: 100%
             * - actual: progreso
             * - futuras: 0%
             */
            const width = i < indexActual ? 100 : i === indexActual ? progreso : 0;

            return (
              <div
                key={h?.id || i}
                className="h-1 flex-1 overflow-hidden rounded-full bg-white/20"
              >
                <div className="h-full bg-white" style={{ width: `${width}%` }} />
              </div>
            );
          })}
        </div>

        {/* Título + botón cerrar */}
        <div className="flex items-center justify-between text-white">
          <div className="truncate pr-3 text-sm font-semibold">{titulo}</div>
          <button
            type="button"
            className="rounded-xl border border-white/10 px-3 py-1 text-sm"
            onClick={cerrar}
          >
            ✕
          </button>
        </div>
      </div>

      {/* Zonas de click (izquierda/centro/derecha) */}
      <div className="absolute inset-0 flex">
        {/* Zona izquierda: retroceder */}
        <button
          type="button"
          className="h-full w-1/3"
          onClick={retroceder}
          aria-label="Historia anterior"
          title="Anterior"
        />

        {/* Zona centro: contenido */}
        <div className="flex h-full w-1/3 items-center justify-center">
          <div className="mx-auto flex h-full w-full max-w-md items-center justify-center px-3">
            <img
              src={mediaUrl}
              alt="Historia"
              className="max-h-[85vh] w-full rounded-2xl object-contain"
              loading="eager"
            />
          </div>
        </div>

        {/* Zona derecha: avanzar */}
        <button
          type="button"
          className="h-full w-1/3"
          onClick={avanzar}
          aria-label="Historia siguiente"
          title="Siguiente"
        />
      </div>
    </div>
  );
}

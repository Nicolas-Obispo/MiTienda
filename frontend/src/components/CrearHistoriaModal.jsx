/**
 * CrearHistoriaModal.jsx
 * -------------------------------------------------------
 * Modal reutilizable para crear una Historia desde un Comercio.
 *
 * Nota importante:
 * - El backend actual crea historias con JSON (media_url), NO upload de archivo.
 * - expira_en es requerido por backend => si el usuario no elige fecha,
 *   seteamos default: ahora + 24hs.
 */

import { useEffect, useState } from "react";
import { crearHistoria } from "../services/historias_service";

export default function CrearHistoriaModal({
  isOpen,
  comercioId,
  onClose,
  onCreated,
}) {
  // UI state
  const [mediaUrl, setMediaUrl] = useState("");
  const [expiraEn, setExpiraEn] = useState(""); // datetime-local (string)
  const [isActiva, setIsActiva] = useState(true);

  // UX state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // Reset cuando se abre/cierra
  useEffect(() => {
    if (!isOpen) return;

    setMediaUrl("");
    setExpiraEn("");
    setIsActiva(true);
    setIsSubmitting(false);
    setErrorMsg("");
  }, [isOpen]);

  // Si no está abierto, no renderizamos nada
  if (!isOpen) return null;

  function validarFormulario() {
    if (!comercioId) return "Falta comercioId (no se puede crear historia).";
    if (!mediaUrl.trim()) return "Ingresá una URL en media_url.";
    return "";
  }

  function buildExpiraEnIso() {
    // Si el usuario eligió fecha => ISO
    if (expiraEn) {
      return new Date(expiraEn).toISOString();
    }

    // Default UX: ahora + 24h (backend requiere expira_en)
    const now = new Date();
    const plus24 = new Date(now.getTime() + 24 * 60 * 60 * 1000);
    return plus24.toISOString();
  }

  async function handleSubmit(e) {
    e.preventDefault();

    const validationError = validarFormulario();
    if (validationError) {
      setErrorMsg(validationError);
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMsg("");

      const payload = {
        media_url: mediaUrl.trim(),
        expira_en: buildExpiraEnIso(),
        is_activa: isActiva,
      };

      const nuevaHistoria = await crearHistoria(comercioId, payload);

      if (onCreated) onCreated(nuevaHistoria);
      onClose();
    } catch (err) {
      setErrorMsg(err?.message || "No se pudo crear la historia.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Overlay */}
      <button
        type="button"
        className="absolute inset-0 bg-black/70"
        onClick={onClose}
        aria-label="Cerrar modal"
      />

      {/* Caja modal (tema oscuro para evitar texto invisible) */}
      <div className="relative z-10 w-[92%] max-w-md rounded-2xl border border-white/10 bg-gray-950 p-4 shadow-xl">
        <div className="mb-3">
          <h2 className="text-lg font-semibold text-white">Nueva historia</h2>
          <p className="text-sm text-white/70">
            Pegá una URL de imagen (por ahora el viewer usa &lt;img&gt;).
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          {/* media_url */}
          <div className="space-y-1">
            <label className="text-sm font-medium text-white">media_url *</label>
            <input
              className="w-full rounded-xl border border-white/10 bg-gray-900 px-3 py-2 text-sm text-white caret-white placeholder:text-white/40 outline-none focus:border-white/30"
              placeholder="https://..."
              value={mediaUrl}
              onChange={(e) => setMediaUrl(e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          {/* expira_en */}
          <div className="space-y-1">
            <label className="text-sm font-medium text-white">
              expira_en (opcional, default 24h)
            </label>
            <input
              type="datetime-local"
              className="w-full rounded-xl border border-white/10 bg-gray-900 px-3 py-2 text-sm text-white caret-white outline-none focus:border-white/30"
              value={expiraEn}
              onChange={(e) => setExpiraEn(e.target.value)}
              disabled={isSubmitting}
            />
            <p className="text-xs text-white/50">
              Si lo dejás vacío, se publica con vencimiento automático en 24hs.
            </p>
          </div>

          {/* is_activa */}
          <div className="flex items-center gap-2">
            <input
              id="is_activa"
              type="checkbox"
              className="h-4 w-4 accent-white"
              checked={isActiva}
              onChange={(e) => setIsActiva(e.target.checked)}
              disabled={isSubmitting}
            />
            <label htmlFor="is_activa" className="text-sm text-white">
              is_activa
            </label>
          </div>

          {/* Error */}
          {errorMsg ? (
            <div className="rounded-xl border border-red-500/30 bg-red-950/40 px-3 py-2 text-sm text-red-200 break-words">
              {errorMsg}
            </div>
          ) : null}

          {/* Acciones */}
          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              className="rounded-xl border border-white/15 bg-white/5 px-4 py-2 text-sm text-white hover:bg-white/10"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancelar
            </button>

            <button
              type="submit"
              className="rounded-xl bg-white px-4 py-2 text-sm text-black disabled:opacity-60"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Publicando..." : "Publicar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

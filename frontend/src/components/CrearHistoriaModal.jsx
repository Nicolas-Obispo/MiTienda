/**
 * CrearHistoriaModal.jsx
 * -------------------------------------------------------
 * Modal reutilizable para crear una Historia desde un Comercio.
 *
 * ETAPA 46:
 * - Upload real de imagen:
 *   1) El usuario elige un archivo (File)
 *   2) Frontend sube el archivo a /media/upload (✅ requiere JWT)
 *   3) Backend devuelve { url }
 *   4) Creamos la historia con media_url = url (persistido en BD)
 *
 * Nota:
 * - expira_en es requerido por backend => si el usuario no elige fecha,
 *   seteamos default: ahora + 24hs.
 */

import { useContext, useEffect, useState } from "react";
import { crearHistoria } from "../services/historias_service";
import { uploadImagen } from "../services/media_service";
import { AuthContext } from "../context/AuthContext";

export default function CrearHistoriaModal({
  isOpen,
  comercioId,
  onClose,
  onCreated,
}) {
  // ✅ Token real desde AuthContext (backend manda)
  const { accessToken } = useContext(AuthContext);

  // UI state
  const [mediaUrl, setMediaUrl] = useState(""); // fallback opcional (URL manual)
  const [selectedFile, setSelectedFile] = useState(null); // File elegido por el usuario
  const [expiraEn, setExpiraEn] = useState(""); // datetime-local (string)
  const [isActiva, setIsActiva] = useState(true);

  // UX state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // Reset cuando se abre/cierra
  useEffect(() => {
    if (!isOpen) return;

    setMediaUrl("");
    setSelectedFile(null);
    setExpiraEn("");
    setIsActiva(true);
    setIsSubmitting(false);
    setErrorMsg("");
  }, [isOpen]);

  // Si no está abierto, no renderizamos nada
  if (!isOpen) return null;

  function validarFormulario() {
    if (!comercioId) return "Falta comercioId (no se puede crear historia).";

    // Regla UX: se permite 1 de 2:
    // - archivo seleccionado (recomendado)
    // - o URL manual (fallback)
    const hasFile = !!selectedFile;
    const hasUrl = !!mediaUrl.trim();

    if (!hasFile && !hasUrl) {
      return "Elegí una imagen o pegá una URL.";
    }

    // ✅ Si hay archivo, el upload requiere JWT
    if (hasFile && !accessToken) {
      return "Necesitás iniciar sesión para subir una imagen.";
    }

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

  async function resolveMediaUrl() {
    // 1) Si hay archivo, subimos y usamos la URL del backend (con JWT)
    if (selectedFile) {
      const { url } = await uploadImagen(selectedFile, accessToken);
      return url;
    }

    // 2) Fallback: URL manual
    return mediaUrl.trim();
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

      // Backend manda: primero obtenemos una URL válida (upload o manual)
      const finalMediaUrl = await resolveMediaUrl();

      const payload = {
        media_url: finalMediaUrl,
        expira_en: buildExpiraEnIso(),
        is_activa: isActiva,
      };

      const nuevaHistoria = await crearHistoria(comercioId, payload);

      if (onCreated) onCreated(nuevaHistoria);
      onClose();
    } catch (err) {
      // Con fetch, el error viene en err.message (ej: "HTTP 401 - ...")
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
            Subí una imagen (requiere sesión) o pegá una URL (fallback).
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          {/* Upload archivo */}
          <div className="space-y-1">
            <label className="text-sm font-medium text-white">
              Imagen (upload) *
            </label>

            <input
              type="file"
              accept="image/*"
              className="w-full rounded-xl border border-white/10 bg-gray-900 px-3 py-2 text-sm text-white file:mr-3 file:rounded-lg file:border-0 file:bg-white file:px-3 file:py-1.5 file:text-sm file:text-black"
              disabled={isSubmitting}
              onChange={(e) => {
                const file = e.target.files?.[0] || null;
                setSelectedFile(file);

                // Si el usuario elige archivo, limpiamos la URL manual para evitar ambigüedad
                if (file) setMediaUrl("");
              }}
            />

            {selectedFile ? (
              <p className="text-xs text-white/60 break-words">
                Archivo: <span className="text-white">{selectedFile.name}</span>
              </p>
            ) : (
              <p className="text-xs text-white/50">
                Recomendado. El backend lo guarda y devuelve una URL.
              </p>
            )}
          </div>

          {/* media_url (fallback) */}
          <div className="space-y-1">
            <label className="text-sm font-medium text-white">
              media_url (fallback)
            </label>
            <input
              className="w-full rounded-xl border border-white/10 bg-gray-900 px-3 py-2 text-sm text-white caret-white placeholder:text-white/40 outline-none focus:border-white/30 disabled:opacity-60"
              placeholder="https://..."
              value={mediaUrl}
              onChange={(e) => {
                setMediaUrl(e.target.value);

                // Si el usuario pega URL, limpiamos archivo para evitar ambigüedad
                if (e.target.value.trim()) setSelectedFile(null);
              }}
              disabled={isSubmitting}
            />
            <p className="text-xs text-white/50">
              Solo si querés pegar una URL externa. Si elegís archivo arriba,
              esto se limpia.
            </p>
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

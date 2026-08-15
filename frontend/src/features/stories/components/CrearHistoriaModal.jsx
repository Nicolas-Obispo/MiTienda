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

import { useEffect, useState } from "react";
import { ActiveLayer } from "@core";
import { useAuth } from "@features/auth";
import { crearHistoria } from "@features/stories";
import { Alert, Button, Input, Surface, uploadImagen } from "@shared";

export default function CrearHistoriaModal({
  isOpen,
  comercioId,
  onClose,
  onCreated,
}) {
  // ✅ Token real desde AuthContext (backend manda)
  const { accessToken } = useAuth();

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
    <ActiveLayer
      onClose={onClose}
      labelledBy="crear-historia-title"
      describedBy="crear-historia-description"
      contentClassName="w-[92%] max-w-md"
    >
      <Surface variant="elevated" className="max-h-[calc(100dvh-2rem)] overflow-y-auto p-4">
        <div className="mb-3">
          <h2 id="crear-historia-title" className="text-lg font-semibold text-primary">Nueva historia</h2>
          <p id="crear-historia-description" className="text-sm text-secondary">
            Subí una imagen o video para compartir en tu historia.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          {/* Upload archivo */}
          <div className="space-y-1">
            <label htmlFor="historia-media" className="text-sm font-medium text-secondary">
              Imagen o video
            </label>

            <Input
              id="historia-media"
              type="file"
              accept="
                image/jpeg,
                image/png,
                image/webp,
                video/mp4,
                video/webm,
                video/ogg,
                video/quicktime
              "
              className="text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-interactive-primary file:px-3 file:py-1.5 file:text-sm file:font-semibold file:text-interactive-on-primary"
              disabled={isSubmitting}
              onChange={(e) => {
                const file = e.target.files?.[0] || null;
                setSelectedFile(file);

                // Si el usuario elige archivo, limpiamos la URL manual para evitar ambigüedad
                if (file) setMediaUrl("");
              }}
            />

            {selectedFile ? (
              <p className="break-words text-xs text-secondary">
                Seleccionado: <span className="text-primary">{selectedFile.name}</span>
              </p>
            ) : (
              <p className="text-xs text-muted">
                Recomendado. El backend lo guarda y devuelve una URL.
              </p>
            )}
          </div>

          {/* media_url (fallback oculto MVP) */}
          <div className="hidden">
            <label htmlFor="historia-media-url" className="text-sm font-medium text-secondary">
              media_url (fallback)
            </label>
            <Input
              id="historia-media-url"
              className="text-sm"
              placeholder="https://..."
              value={mediaUrl}
              onChange={(e) => {
                setMediaUrl(e.target.value);

                // Si el usuario pega URL, limpiamos archivo para evitar ambigüedad
                if (e.target.value.trim()) setSelectedFile(null);
              }}
              disabled={isSubmitting}
            />
            <p className="text-xs text-muted">
              Solo si querés pegar una URL externa. Si elegís archivo arriba,
              esto se limpia.
            </p>
          </div>

          {/* expira_en */}
          <div className="hidden">
            <label htmlFor="historia-expira-en" className="text-sm font-medium text-secondary">
              expira_en (opcional, default 24h)
            </label>
            <Input
              id="historia-expira-en"
              type="datetime-local"
              className="text-sm"
              value={expiraEn}
              onChange={(e) => setExpiraEn(e.target.value)}
              disabled={isSubmitting}
            />
            <p className="text-xs text-muted">
              Si lo dejás vacío, se publica con vencimiento automático en 24hs.
            </p>
          </div>

          {/* is_activa */}
          <div className="hidden items-center gap-2">
            <Input
              id="is_activa"
              type="checkbox"
              className="h-4 w-4 accent-brand"
              checked={isActiva}
              onChange={(e) => setIsActiva(e.target.checked)}
              disabled={isSubmitting}
            />
            <label htmlFor="is_activa" className="text-sm text-primary">
              is_activa
            </label>
          </div>

          {/* Error */}
          {errorMsg ? (
            <Alert variant="danger" role="alert" className="break-words px-3 py-2">
              {errorMsg}
            </Alert>
          ) : null}

          {/* Acciones */}
          <div className="flex items-center justify-end gap-2 pt-2">
            <Button
              variant="secondary"
              className="px-4 py-2 text-sm"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancelar
            </Button>

            <Button
              type="submit"
              variant="primary"
              className="px-4 py-2 text-sm"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Publicando..." : "Publicar"}
            </Button>
          </div>
        </form>
      </Surface>
    </ActiveLayer>
  );
}

import { useEffect, useState } from "react";

import {
  DENUNCIA_DETALLE_MAX_LENGTH,
  MOTIVOS_DENUNCIA,
} from "@features/moderation/constants/denuncias";
import { useAuth } from "@features/auth";
import { crearDenunciaContenido } from "@features/moderation/services/denuncias_service";

export default function DenunciaModal({
  isOpen,
  onClose,
  recursoTipo,
  recursoId,
  titulo = "Denunciar contenido",
}) {
  const { accessToken } = useAuth();
  const [motivo, setMotivo] = useState("");
  const [detalle, setDetalle] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    if (!isOpen) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    setMotivo("");
    setDetalle("");
    setIsSubmitting(false);
    setErrorMessage("");
    setSuccessMessage("");
  }, [isOpen, recursoTipo, recursoId]);

  useEffect(() => {
    if (!isOpen) return;

    const onKeyDown = (event) => {
      if (event.key === "Escape" && !isSubmitting) {
        event.stopPropagation();
        onClose?.();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isOpen, isSubmitting, onClose]);

  if (!isOpen) return null;

  const puedeEnviar = Boolean(accessToken && motivo && recursoTipo && recursoId);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!puedeEnviar || isSubmitting) return;

    try {
      setIsSubmitting(true);
      setErrorMessage("");
      setSuccessMessage("");

      await crearDenunciaContenido(
        {
          recurso_tipo: recursoTipo,
          recurso_id: Number(recursoId),
          motivo,
          detalle,
        },
        accessToken
      );

      setSuccessMessage("Recibimos tu denuncia para revision.");
    } catch (error) {
      setErrorMessage(
        error?.message || "No pudimos registrar la denuncia en este momento."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-[1200] flex items-center justify-center bg-black/75 px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="denuncia-modal-title"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !isSubmitting) {
          onClose?.();
        }
      }}
    >
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md rounded-2xl border border-gray-800 bg-gray-950 p-5 text-left shadow-2xl"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2
              id="denuncia-modal-title"
              className="text-lg font-semibold text-white"
            >
              {titulo}
            </h2>
            <p className="mt-1 text-sm text-gray-400">
              La denuncia registra una solicitud de revision. No elimina ni
              oculta automaticamente el contenido.
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="rounded-full border border-gray-700 px-3 py-1 text-sm text-gray-300 hover:bg-gray-800 disabled:opacity-60"
            aria-label="Cerrar denuncia"
          >
            x
          </button>
        </div>

        {!accessToken ? (
          <div className="mt-5 rounded-xl border border-amber-800 bg-amber-950/30 p-4 text-sm text-amber-100">
            Inicia sesion para enviar una denuncia.
          </div>
        ) : (
          <div className="mt-5 space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-200">
                Motivo
              </label>
              <select
                value={motivo}
                onChange={(event) => setMotivo(event.target.value)}
                className="w-full rounded-xl border border-gray-700 bg-gray-900 px-3 py-3 text-sm text-white outline-none focus:border-white"
                required
              >
                <option value="">Selecciona un motivo</option>
                {MOTIVOS_DENUNCIA.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-200">
                Detalle opcional
              </label>
              <textarea
                value={detalle}
                onChange={(event) =>
                  setDetalle(
                    event.target.value.slice(0, DENUNCIA_DETALLE_MAX_LENGTH)
                  )
                }
                maxLength={DENUNCIA_DETALLE_MAX_LENGTH}
                rows={4}
                className="w-full resize-none rounded-xl border border-gray-700 bg-gray-900 px-3 py-3 text-sm text-white outline-none placeholder:text-gray-500 focus:border-white"
                placeholder="Agrega contexto si es necesario."
              />
              <p className="mt-1 text-xs text-gray-500">
                {detalle.length}/{DENUNCIA_DETALLE_MAX_LENGTH}
              </p>
            </div>
          </div>
        )}

        {errorMessage ? (
          <p className="mt-4 rounded-xl border border-red-800 bg-red-950/30 p-3 text-sm text-red-100">
            {errorMessage}
          </p>
        ) : null}

        {successMessage ? (
          <p className="mt-4 rounded-xl border border-emerald-800 bg-emerald-950/30 p-3 text-sm text-emerald-100">
            {successMessage}
          </p>
        ) : null}

        <div className="mt-5 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="rounded-full border border-gray-700 px-4 py-2 text-sm font-semibold text-white hover:bg-gray-800 disabled:opacity-60"
          >
            Cerrar
          </button>

          <button
            type="submit"
            disabled={!puedeEnviar || isSubmitting || Boolean(successMessage)}
            className="rounded-full bg-white px-4 py-2 text-sm font-semibold text-gray-950 hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "Enviando..." : "Enviar denuncia"}
          </button>
        </div>
      </form>
    </div>
  );
}

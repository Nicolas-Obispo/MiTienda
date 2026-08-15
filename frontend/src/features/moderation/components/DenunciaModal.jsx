import { useEffect, useState } from "react";

import {
  DENUNCIA_DETALLE_MAX_LENGTH,
  MOTIVOS_DENUNCIA,
} from "@features/moderation/constants/denuncias";
import { useAuth } from "@features/auth";
import { crearDenunciaContenido } from "@features/moderation/services/denuncias_service";
import { ActiveLayer } from "@core";
import {
  Alert,
  Button,
  FormControl,
  Select,
  Surface,
  Textarea,
} from "@shared";

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

    setMotivo("");
    setDetalle("");
    setIsSubmitting(false);
    setErrorMessage("");
    setSuccessMessage("");
  }, [isOpen, recursoTipo, recursoId]);

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
    <ActiveLayer
      onClose={onClose}
      closeOnBackdrop={!isSubmitting}
      closeOnEscape={!isSubmitting}
      labelledBy="denuncia-modal-title"
      describedBy="denuncia-modal-description"
      zIndex={1200}
      contentClassName="mx-4 w-full max-w-md"
    >
      <Surface
        as="form"
        variant="elevated"
        onSubmit={handleSubmit}
        className="max-h-[92vh] overflow-y-auto p-5 text-left"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2
              id="denuncia-modal-title"
              className="text-lg font-semibold text-primary"
            >
              {titulo}
            </h2>
            <p
              id="denuncia-modal-description"
              className="mt-1 text-sm text-secondary"
            >
              La denuncia registra una solicitud de revision. No elimina ni
              oculta automaticamente el contenido.
            </p>
          </div>

          <Button
            iconOnly
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            variant="ghost"
            aria-label="Cerrar denuncia"
          >
            x
          </Button>
        </div>

        {!accessToken ? (
          <Alert variant="warning" className="mt-5">
            Inicia sesion para enviar una denuncia.
          </Alert>
        ) : (
          <div className="mt-5 space-y-4">
            <FormControl label="Motivo" labelFor="denuncia-motivo">
              <Select
                id="denuncia-motivo"
                value={motivo}
                onChange={(event) => setMotivo(event.target.value)}
                className="px-3 py-3 text-sm"
                required
              >
                <option value="">Selecciona un motivo</option>
                {MOTIVOS_DENUNCIA.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </Select>
            </FormControl>

            <FormControl
              label="Detalle opcional"
              labelFor="denuncia-detalle"
              help={`${detalle.length}/${DENUNCIA_DETALLE_MAX_LENGTH}`}
              helpId="denuncia-detalle-help"
            >
              <Textarea
                id="denuncia-detalle"
                aria-describedby="denuncia-detalle-help"
                value={detalle}
                onChange={(event) =>
                  setDetalle(
                    event.target.value.slice(0, DENUNCIA_DETALLE_MAX_LENGTH)
                  )
                }
                maxLength={DENUNCIA_DETALLE_MAX_LENGTH}
                rows={4}
                className="resize-none px-3 py-3 text-sm"
                placeholder="Agrega contexto si es necesario."
              />
            </FormControl>
          </div>
        )}

        {errorMessage ? (
          <Alert variant="danger" role="alert" className="mt-4">
            {errorMessage}
          </Alert>
        ) : null}

        {successMessage ? (
          <Alert variant="success" role="status" className="mt-4">
            {successMessage}
          </Alert>
        ) : null}

        <div className="mt-5 flex justify-end gap-3">
          <Button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            variant="secondary"
            className="px-4 py-2 text-sm"
          >
            Cerrar
          </Button>

          <Button
            type="submit"
            disabled={!puedeEnviar || isSubmitting || Boolean(successMessage)}
            variant="primary"
            className="px-4 py-2 text-sm"
          >
            {isSubmitting ? "Enviando..." : "Enviar denuncia"}
          </Button>
        </div>
      </Surface>
    </ActiveLayer>
  );
}

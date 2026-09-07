import { useState } from "react";

import DenunciaModal from "@features/moderation/components/DenunciaModal";
import { RECURSO_DENUNCIA_PUBLICACION } from "@features/moderation/constants/denuncias";
import { Button } from "@shared";
import { useProtectedAction } from "@core";

export default function PublicacionReportControl({ publicacionId }) {
  const [isOpen, setIsOpen] = useState(false);
  const { requireAuthentication } = useProtectedAction();

  if (!publicacionId) return null;

  return (
    <>
      <Button
        type="button"
        onClick={() => {
          if (requireAuthentication()) return;
          setIsOpen(true);
        }}
        variant="secondary"
        iconOnly
        aria-label="Denunciar publicación"
        className="ml-auto h-[34px] min-h-[34px] w-[34px] min-w-[34px] shrink-0 rounded-full p-0 text-interactive-on-primary"
      >
        <span
          aria-hidden="true"
          className="inline-flex h-full w-full items-center justify-center text-base leading-none text-interactive-on-primary"
        >
          ...
        </span>
      </Button>

      <DenunciaModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        recursoTipo={RECURSO_DENUNCIA_PUBLICACION}
        recursoId={publicacionId}
        titulo="Denunciar publicacion"
      />
    </>
  );
}

import { Link } from "react-router-dom";

import { useLegalDocument } from "@features/legal/hooks/useLegalDocument";
import { Alert, Surface } from "@shared";

export default function LegalDocumentLayout({ type, title, children }) {
  const { document, isLoading, error } = useLegalDocument(type);

  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-8 sm:py-10">
      <Surface as="article" variant="elevated" className="p-5 sm:p-8">
        <header className="border-b border-border pb-5">
          <h1 className="text-2xl font-bold text-primary sm:text-3xl">{title}</h1>
          <p className="mt-2 text-sm text-secondary" aria-live="polite">
            {isLoading && "Verificando versión vigente…"}
            {document && `Versión vigente: ${document.version}`}
            {error && "No fue posible verificar la versión vigente."}
          </p>
          <Alert variant="warning" className="mt-4">
            Documento implementado para validación técnica. Su habilitación
            productiva requiere completar la identificación del responsable y el
            canal formal de contacto definidos como pendientes por el Gobierno.
          </Alert>
        </header>

        <div className="legal-document mt-6 space-y-6 text-secondary leading-7">
          {children}
        </div>

        <footer className="mt-8 border-t border-border pt-5 text-sm">
          <Link
            to="/registro"
            className="font-semibold text-interactive-primary underline decoration-2 underline-offset-4 transition-colors hover:text-interactive-primary-hover focus-visible:rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring"
          >
            Volver al registro
          </Link>
        </footer>
      </Surface>
    </main>
  );
}

import { Link } from "react-router-dom";
import { Alert } from "@shared";

export function AdministrativeAccessDenied() {
  return <main className="mx-auto w-full max-w-3xl px-4 py-8">
    <Alert variant="danger" role="alert">No tenés permiso para acceder a esta sección administrativa.</Alert>
    <Link className="interactive-bubble mt-4 inline-flex min-h-11 items-center text-link underline underline-offset-2" to="/administracion">Volver a Administración</Link>
  </main>;
}

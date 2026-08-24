import { Link } from "react-router-dom";

import { AdministrativeAccessDenied } from "@features/administration/components/AdministrativeAccessDenied";
import { useAdministrativeCapabilities } from "@features/administration/hooks/useAdministrativeCapabilities";
import { Alert, Skeleton, Surface } from "@shared";

const GUIDE_SECTIONS = [
  {
    title: "Acceso y capacidades",
    content: "La portada muestra solamente las herramientas habilitadas para tu cuenta. Los permisos pueden cambiar durante la sesión; si perdés acceso, volvé a Administración y actualizá la página.",
  },
  {
    title: "Portada administrativa",
    content: "Usá la portada para ingresar a Denuncias, Incidentes o Estado Operativo. Que una herramienta no aparezca significa que tu cuenta no tiene esa capacidad; no intentes reemplazarla con accesos directos.",
  },
  {
    title: "Consulta de denuncias",
    content: "Filtrá el listado, abrí una denuncia y revisá el recurso actual. La identidad del denunciante es confidencial. La disponibilidad actual del recurso no demuestra cómo estaba cuando se creó la denuncia.",
  },
  {
    title: "Decisiones, fundamento y evidencia",
    content: "Elegí una acción, explicá el fundamento y registrá únicamente una referencia opaca de evidencia. Cada decisión queda atribuida y forma parte de una trazabilidad que no se reescribe.",
  },
  {
    title: "Ocultamiento y restauración causal",
    content: "Ocultar afecta la visibilidad por moderación, no el estado elegido por el dueño. Restaurá sólo el ocultamiento vigente que la pantalla permite revertir; una resolución sin acción no concede derecho a restaurar.",
  },
  {
    title: "Gestión de incidentes",
    content: "Abrí el expediente con severidad y responsable, registrá la evaluación legal, iniciá la investigación, documentá hallazgos y contención, resolvé el incidente y completá la revisión. Los cambios concurrentes pueden exigir actualizar y revisar nuevamente antes de continuar.",
  },
  {
    title: "Límites de Estado Operativo",
    content: "La pantalla ofrece una lectura local, volátil y no histórica. No prueba el estado global, la vigencia de un backup ni un objetivo de recuperación, y no ejecuta backup, restauración o reparación.",
  },
  {
    title: "Canal operativo por correo",
    content: "Determinados eventos administrativos pueden generar un aviso al canal operativo configurado. El correo es una señal complementaria: no reemplaza la bandeja, el expediente ni la trazabilidad. Un fallo de entrega no revierte la operación realizada.",
  },
  {
    title: "Errores y recuperación",
    content: "Ante datos inválidos, corregí el formulario indicado. Ante un conflicto, actualizá el expediente antes de decidir. Si perdés conexión, conservá el contexto, recuperá la red y repetí únicamente la consulta o acción que no haya sido confirmada.",
  },
];

export function AdministrativeGuidePage() {
  const { capacidades, isError, isLoading } = useAdministrativeCapabilities();

  if (isLoading) return <Skeleton className="h-48 w-full" />;
  if (isError || capacidades.length === 0) return <AdministrativeAccessDenied />;

  return <main className="mx-auto w-full max-w-4xl space-y-5 px-4 py-6 sm:px-6 sm:py-8">
    <header>
      <h1 className="text-2xl font-semibold text-primary">Guía práctica de Administración</h1>
      <p className="mt-2 text-sm text-secondary">Orientación operativa para usar las herramientas habilitadas sin exponer información sensible.</p>
      <Link className="interactive-bubble mt-3 inline-flex min-h-11 items-center text-link underline underline-offset-2" to="/administracion">Volver a Administración</Link>
    </header>

    <Alert variant="warning" role="note">
      Nunca ingreses secretos, contraseñas, datos privados, URLs internas, rutas de archivos ni payloads. Usá descripciones mínimas y referencias opacas.
    </Alert>

    <div className="grid gap-4 md:grid-cols-2">
      {GUIDE_SECTIONS.map((section) => <Surface as="section" key={section.title} className="min-w-0 p-4 sm:p-5">
        <h2 className="font-semibold text-primary">{section.title}</h2>
        <p className="mt-2 text-sm leading-6 text-secondary">{section.content}</p>
      </Surface>)}
    </div>
  </main>;
}

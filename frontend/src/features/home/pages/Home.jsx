import { Link } from "react-router-dom";
import { useAuth } from "@features/auth";
import { Surface } from "@shared";

export default function Home() {
  const { estaAutenticado } = useAuth();

  return (
    <div className="min-h-[calc(100vh-64px)] bg-canvas text-primary">
      <Surface
        as="section"
        variant="elevated"
        className="relative overflow-hidden rounded-3xl p-6"
      >
        <div
          className="absolute inset-0 bg-gradient-to-br from-brand/15 via-surface to-canvas-subtle"
          aria-hidden="true"
        />

        <div className="relative z-10">
          <p className="mb-3 inline-flex rounded-full border border-brand/30 bg-surface-subtle px-3 py-1 text-xs font-semibold text-brand">
            Descubrimiento local
          </p>

          <h1 className="text-4xl font-black leading-tight tracking-tight sm:text-5xl">
            FeedGo!
          </h1>

          <p className="mt-3 text-xl font-semibold text-secondary">
            Tu vidriera digital para descubrir negocios, servicios y profesionales cerca tuyo.
          </p>

          <p className="mt-4 max-w-xl text-base leading-7 text-secondary">
            Explorá publicaciones, perfiles y novedades de negocios, servicios y profesionales de tu zona.
            Encontrá lo que te interesa, guardalo y volvé cuando quieras.
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link
              to="/explorar"
              className="interactive-bubble interactive-bubble--primary-action rounded-2xl bg-interactive-primary px-5 py-3 text-center text-sm font-bold text-interactive-on-primary hover:bg-interactive-primary-hover"
            >
              <span>Explorar sin registrarme</span>
            </Link>

            {estaAutenticado ? (
              <Link
                to="/feed"
                className="interactive-bubble interactive-bubble--secondary rounded-2xl bg-surface-subtle px-5 py-3 text-center text-sm font-bold text-primary hover:bg-surface"
              >
                <span>Ir a mi feed</span>
              </Link>
            ) : (
              <Link
                to="/registro"
                className="interactive-bubble interactive-bubble--secondary rounded-2xl bg-surface-subtle px-5 py-3 text-center text-sm font-bold text-primary hover:bg-surface"
              >
                <span>Crear cuenta gratis</span>
              </Link>
            )}
          </div>

          <p className="mt-4 text-xs text-muted">
            Podés explorar sin cuenta. Solo necesitás registrarte para guardar,
            dar like o personalizar tu experiencia.
          </p>
        </div>
      </Surface>

      <section className="mt-6 grid gap-4 md:grid-cols-3">
        <Surface className="p-5">
          <h2 className="text-lg font-bold">
            Descubrí negocios y servicios
          </h2>
          <p className="mt-2 text-sm leading-6 text-secondary">
            Conocé perfiles, publicaciones y novedades de negocios, servicios y profesionales
            activos en tu zona desde un solo lugar.
          </p>
        </Surface>

        <Surface className="p-5">
          <h2 className="text-lg font-bold">
            Explorá sin registrarte
          </h2>
          <p className="mt-2 text-sm leading-6 text-secondary">
            Entrá, mirá y conocé MiPlaza sin compromiso. Registrarte solo hace
            falta cuando quieras interactuar.
          </p>
        </Surface>

        <Surface className="p-5">
          <h2 className="text-lg font-bold">
            Guardá lo que te interesa
          </h2>
          <p className="mt-2 text-sm leading-6 text-secondary">
            Creá tu cuenta para guardar publicaciones, dar like y recibir una
            experiencia más personalizada.
          </p>
        </Surface>
      </section>
    </div>
  );
}

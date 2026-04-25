import { Link } from "react-router-dom";
import { useAuth } from "../context/useAuth";

export default function Home() {
  const { estaAutenticado } = useAuth();

  return (
    <div className="min-h-[calc(100vh-64px)] bg-gray-950 text-white">
      <section className="relative overflow-hidden rounded-3xl border border-gray-800 bg-gray-900 p-6 shadow-xl">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-700/30 via-gray-950 to-black" />

        <div className="relative z-10">
          <p className="mb-3 inline-flex rounded-full border border-white/10 bg-white/10 px-3 py-1 text-xs font-semibold text-purple-100">
            Descubrimiento local
          </p>

          <h1 className="text-4xl font-black leading-tight tracking-tight sm:text-5xl">
            MiPlaza
          </h1>

          <p className="mt-4 max-w-xl text-base leading-7 text-gray-200">
            MiPlaza es tu vidriera digital: te acercamos los comercios,
            productos y ofertas de tu zona en un solo lugar.
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link
              to="/explorar"
              className="rounded-2xl bg-white px-5 py-3 text-center text-sm font-bold text-gray-950 hover:opacity-90"
            >
              Explora y conocenos!
            </Link>

            {estaAutenticado ? (
              <Link
                to="/feed"
                className="rounded-2xl border border-white/20 bg-white/10 px-5 py-3 text-center text-sm font-bold text-white hover:bg-white/15"
              >
                Ir al Feed
              </Link>
            ) : (
              <Link
                to="/login"
                className="rounded-2xl border border-white/20 bg-white/10 px-5 py-3 text-center text-sm font-bold text-white hover:bg-white/15"
              >
                Registrarme
              </Link>
            )}
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-4">
        <div className="rounded-2xl border border-gray-800 bg-gray-900 p-5">
          <h2 className="text-lg font-bold">Descubrí negocios cerca tuyo</h2>
          <p className="mt-2 text-sm leading-6 text-gray-400">
            Entrá a explorar, conocé perfiles de comercios y encontrá contenido
            publicado por negocios de tu zona.
          </p>
        </div>

        <div className="rounded-2xl border border-gray-800 bg-gray-900 p-5">
          <h2 className="text-lg font-bold">Guardá lo que te interesa</h2>
          <p className="mt-2 text-sm leading-6 text-gray-400">
            Cuando inicies sesión vas a poder dar me gusta, guardar
            publicaciones y seguir explorando contenido personalizado.
          </p>
        </div>
      </section>
    </div>
  );
}
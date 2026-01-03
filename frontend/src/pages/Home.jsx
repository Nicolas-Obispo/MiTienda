/**
 * Home.jsx
 * ----------------
 * Página principal (UI).
 *
 * OBJETIVO (ETAPA 32.A):
 * - Que el Home tenga look & feel consistente con el Feed.
 * - Sin lógica nueva. Solo UI y navegación.
 */

import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header simple, consistente con el estilo general */}
      <div className="sticky top-0 z-10 border-b border-gray-800 bg-gray-950/80 backdrop-blur">
        <div className="mx-auto max-w-3xl px-4 py-4">
          <h1 className="text-xl font-bold">Inicio</h1>
          <p className="text-sm text-gray-400">
            MiPlaza — descubrimiento local
          </p>
        </div>
      </div>

      {/* Contenido */}
      <main className="mx-auto max-w-3xl px-4 py-10">
        <section className="rounded-2xl border border-gray-800 bg-gray-950 p-6">
          <h2 className="text-2xl font-semibold leading-tight">
            Bienvenidos a MiPlaza
          </h2>

          <p className="mt-2 text-gray-300">
            Este frontend consume el backend estable (ETAPA 31). En esta etapa
            estamos puliendo UI sin tocar lógica del servidor.
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            {/* CTA principal al Feed */}
            <Link
              to="/feed"
              className="rounded-xl bg-purple-600 px-4 py-2 text-sm font-semibold hover:bg-purple-500"
            >
              Ir al Feed
            </Link>

            {/* Botón secundario: Login (si existe ruta) */}
            <Link
              to="/login"
              className="rounded-xl border border-gray-700 bg-gray-900 px-4 py-2 text-sm font-semibold hover:bg-gray-800"
            >
              Login
            </Link>
          </div>
        </section>

        {/* Bloque informativo (UI pura) */}
        <section className="mt-6 grid gap-4 sm:grid-cols-2">
          <div className="rounded-2xl border border-gray-800 bg-gray-950 p-5">
            <h3 className="font-semibold">Feed</h3>
            <p className="mt-2 text-sm text-gray-400">
              Lista de publicaciones con métricas: likes, guardados y liked_by_me.
            </p>
          </div>

          <div className="rounded-2xl border border-gray-800 bg-gray-950 p-5">
            <h3 className="font-semibold">Historias</h3>
            <p className="mt-2 text-sm text-gray-400">
              UI preparada para mostrar historias por comercio (sin cambios backend).
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}

/**
 * Home.jsx
 * ----------------
 * Página principal (UI).
 *
 * OBJETIVO (ETAPA 32.A):
 * - Que el Home tenga look & feel consistente con el Feed.
 * - Sin lógica nueva. Solo UI y navegación.
 *
 * ETAPA 40:
 * - Acceso rápido a Perfil de comercio (/comercios/:id) para testear la feature.
 */

import { Link, useNavigate } from "react-router-dom";
import { useMemo, useState } from "react";
import { useAuth } from "../context/useAuth";

export default function Home() {
  const navigate = useNavigate();
  const { estaAutenticado } = useAuth();

  // ID de comercio para navegación rápida (test)
  const [comercioIdInput, setComercioIdInput] = useState("1");

  const comercioIdLimpio = useMemo(() => {
    const n = Number(comercioIdInput);
    return Number.isFinite(n) && n > 0 ? n : null;
  }, [comercioIdInput]);

  function irAComercio() {
    if (!comercioIdLimpio) return;
    navigate(`/comercios/${comercioIdLimpio}`);
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header simple, consistente con el estilo general */}
      <div className="sticky top-0 z-10 border-b border-gray-800 bg-gray-950/80 backdrop-blur">
        <div className="mx-auto max-w-3xl px-4 py-4">
          <h1 className="text-xl font-bold">Inicio</h1>
          <p className="text-sm text-gray-400">MiPlaza — descubrimiento local</p>
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

            {/* Login solo si NO hay sesión (coherente con el layout) */}
            {!estaAutenticado && (
              <Link
                to="/login"
                className="rounded-xl border border-gray-700 bg-gray-900 px-4 py-2 text-sm font-semibold hover:bg-gray-800"
              >
                Login
              </Link>
            )}
          </div>
        </section>

        {/* ETAPA 40: Acceso rápido al Perfil de comercio (solo si hay sesión) */}
        {estaAutenticado && (
          <section className="mt-6 rounded-2xl border border-gray-800 bg-gray-950 p-6">
            <h3 className="text-lg font-semibold text-white">
              Ir a un comercio (test)
            </h3>
            <p className="mt-2 text-sm text-gray-400">
              Usá esto para abrir el perfil del comercio por ID:{" "}
              <span className="text-gray-200 font-semibold">
                /comercios/:id
              </span>
            </p>

            <div className="mt-4 flex flex-wrap items-center gap-3">
              <input
                type="number"
                min="1"
                value={comercioIdInput}
                onChange={(e) => setComercioIdInput(e.target.value)}
                className="w-40 rounded-xl border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-100 outline-none focus:border-gray-500"
                placeholder="ID comercio"
              />

              <button
                type="button"
                onClick={irAComercio}
                disabled={!comercioIdLimpio}
                className={[
                  "rounded-xl px-4 py-2 text-sm font-semibold border transition",
                  comercioIdLimpio
                    ? "bg-green-950/40 text-green-300 border-green-800 hover:bg-green-950/60"
                    : "bg-gray-900 text-gray-500 border-gray-800 cursor-not-allowed",
                ].join(" ")}
              >
                Ver comercio
              </button>

              {comercioIdLimpio && (
                <span className="text-xs text-gray-500">
                  Abrirá:{" "}
                  <code className="bg-gray-900 border border-gray-800 px-2 py-1 rounded">
                    /comercios/{comercioIdLimpio}
                  </code>
                </span>
              )}
            </div>
          </section>
        )}

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

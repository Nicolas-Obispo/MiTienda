 /**
 * RankingPage.jsx
 * ----------------
 * ETAPA 34 (FRONTEND):
 * - Pantalla de Ranking consumiendo /ranking/publicaciones
 * - Sin tocar backend
 *
 * Responsabilidad:
 * - Cargar ranking y renderizarlo.
 * - Manejar estados (loading / error / empty).
 */

import { useEffect, useState } from "react";
import { fetchRankingPublicaciones } from "../services/feed_service";

/**
 * MetricBadge
 * Badge reutilizable para métricas.
 */
function MetricBadge({ label, value, icon }) {
  return (
    <div className="inline-flex items-center rounded-full border border-gray-800 bg-gray-900 px-3 py-1 text-xs text-gray-200">
      <span className="mr-1" aria-hidden="true">
        {icon}
      </span>

      <span className="mr-1 text-gray-400">{label}</span>

      <span className="font-semibold text-white">{value}</span>
    </div>
  );
}

/**
 * PublicacionCard (Ranking)
 * Card simple y consistente con el estilo del Feed.
 */
function PublicacionCard({ pub, index }) {
  return (
    <article className="rounded-2xl border border-gray-800 bg-gray-950 p-5">
      <header className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center justify-center rounded-xl border border-gray-800 bg-gray-900 px-2 py-1 text-xs font-semibold text-gray-200">
              #{index + 1}
            </span>

            <h2 className="text-base sm:text-lg font-semibold text-white leading-snug">
              {pub.titulo}
            </h2>
          </div>

          <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
            <span className="rounded-md border border-gray-800 bg-gray-900 px-2 py-0.5">
              ID #{pub.id}
            </span>
            <span className="hidden sm:inline">•</span>
            <span className="hidden sm:inline">MiPlaza</span>
          </div>
        </div>

        <div className="shrink-0 rounded-full px-3 py-1 text-xs font-semibold border bg-gray-900 text-gray-300 border-gray-800">
          Ranking
        </div>
      </header>

      <div className="mt-4">
        {pub.descripcion ? (
          <p className="text-sm sm:text-base text-gray-200 leading-relaxed">
            {pub.descripcion}
          </p>
        ) : (
          <p className="text-sm text-gray-500 italic">Sin descripción.</p>
        )}
      </div>

      <footer className="mt-5 flex flex-wrap items-center gap-2">
        <MetricBadge label="Likes" value={pub.likes_count} icon="👍" />
        <MetricBadge label="Guardados" value={pub.guardados_count} icon="⭐" />
        <MetricBadge label="Interacciones" value={pub.interacciones_count} icon="🔥" />
      </footer>
    </article>
  );
}

export default function RankingPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [publicaciones, setPublicaciones] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");

  async function loadRanking() {
    try {
      setIsLoading(true);
      setErrorMessage("");

      const data = await fetchRankingPublicaciones();
      const items = Array.isArray(data) ? data : data?.items || [];

      setPublicaciones(items);
    } catch (error) {
      setErrorMessage(error.message || "Error desconocido cargando el ranking.");
      setPublicaciones([]);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadRanking();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <main className="mx-auto max-w-3xl px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-xl sm:text-2xl font-bold text-white">Ranking</h1>
          <p className="mt-1 text-sm text-gray-400">
            Publicaciones ordenadas por score (likes + recencia).
          </p>
        </div>

        {/* Estado: Loading */}
        {isLoading && (
          <div className="space-y-3">
            <div className="h-28 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
            <div className="h-28 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
            <div className="h-28 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
          </div>
        )}

        {/* Estado: Error */}
        {!isLoading && errorMessage && (
          <div className="rounded-2xl border border-red-900 bg-red-950/40 p-5">
            <p className="font-semibold text-red-200">Error</p>
            <p className="mt-2 text-red-100 break-words">{errorMessage}</p>
          </div>
        )}

        {/* Estado: Vacío */}
        {!isLoading && !errorMessage && publicaciones.length === 0 && (
          <div className="rounded-2xl border border-gray-800 bg-gray-950 p-6 text-center">
            <p className="text-gray-200 font-semibold">No hay publicaciones</p>
            <p className="mt-2 text-gray-400 text-sm">
              Cuando existan publicaciones con actividad, aparecerán acá.
            </p>
          </div>
        )}

        {/* Estado: OK */}
        {!isLoading && !errorMessage && publicaciones.length > 0 && (
          <div className="space-y-4">
            {publicaciones.map((p, idx) => (
              <PublicacionCard key={p.id} pub={p} index={idx} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

/**
 * FeedPage.jsx
 * ----------------
 * ETAPA 32.A (UI):
 * - Pulimos la interfaz del feed (solo frontend).
 * - Mantenemos EXACTAMENTE la misma lógica de carga.
 * - No tocamos backend ni endpoints.
 */

import { useEffect, useState } from "react";
import { fetchFeedPublicaciones } from "../services/feed_service";

/**
 * MetricBadge
 * - Espaciado correcto entre icono, texto y valor
 * - Mejor legibilidad
 * - Sin emojis pegados al texto
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
 * PublicacionCard
 * - Card con mejor jerarquía (título, meta, descripción)
 * - Métricas compactas y alineadas
 * - Estado liked_by_me como "pill" en header
 */
function PublicacionCard({ pub }) {
  return (
    <article className="rounded-2xl border border-gray-800 bg-gray-950 p-5">
      <header className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h2 className="text-base sm:text-lg font-semibold text-white leading-snug">
            {pub.titulo}
          </h2>

          <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
            <span className="rounded-md border border-gray-800 bg-gray-900 px-2 py-0.5">
              ID #{pub.id}
            </span>
            {/* Placeholder futuro: fecha / comercio / sección */}
            <span className="hidden sm:inline">•</span>
            <span className="hidden sm:inline">MiPlaza</span>
          </div>
        </div>

        <div
          className={[
            "shrink-0 rounded-full px-3 py-1 text-xs font-semibold border",
            pub.liked_by_me
              ? "bg-green-950/40 text-green-300 border-green-800"
              : "bg-gray-900 text-gray-300 border-gray-800",
          ].join(" ")}
          title="Estado de Like del usuario"
        >
          {pub.liked_by_me ? "Te gustó" : "No te gustó"}
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

      <footer className="mt-5 flex flex-wrap gap-2">
        <MetricBadge label="Likes" value={pub.likes_count} icon="👍" />
        <MetricBadge label="Guardados" value={pub.guardados_count} icon="⭐" />
        <MetricBadge label="Liked" value={pub.liked_by_me ? "Sí" : "No"} icon="📌" />
      </footer>
    </article>
  );
}


/**
 * Pantalla principal del Feed
 * - Mantiene la misma lógica de carga
 * - Mejora visual: header, contenedor, estados UI
 */
export default function FeedPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [publicaciones, setPublicaciones] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");

  async function loadFeed() {
    try {
      setIsLoading(true);
      setErrorMessage("");

      const data = await fetchFeedPublicaciones();
      const items = Array.isArray(data) ? data : data?.items || [];

      setPublicaciones(items);
    } catch (error) {
      setErrorMessage(error.message || "Error desconocido cargando el feed.");
      setPublicaciones([]);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadFeed();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white">

      {/* Contenido */}
      <main className="mx-auto max-w-3xl px-4 py-8">
        {/* Estado: Loading */}
        {isLoading && (
          <div className="space-y-3">
            {/* Skeleton simple */}
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

            <p className="mt-3 text-sm text-gray-200">
              Si ves <b>401</b>, verificá que exista{" "}
              <code className="bg-gray-800 px-1 rounded">access_token</code> en
              localStorage.
            </p>
          </div>
        )}

        {/* Estado: Vacío */}
        {!isLoading && !errorMessage && publicaciones.length === 0 && (
          <div className="rounded-2xl border border-gray-800 bg-gray-950 p-6 text-center">
            <p className="text-gray-200 font-semibold">No hay publicaciones</p>
            <p className="mt-2 text-gray-400 text-sm">
              Cuando existan publicaciones activas, aparecerán acá.
            </p>
          </div>
        )}

        {/* Estado: OK */}
        {!isLoading && !errorMessage && publicaciones.length > 0 && (
          <div className="space-y-4">
            {publicaciones.map((p) => (
              <PublicacionCard key={p.id} pub={p} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

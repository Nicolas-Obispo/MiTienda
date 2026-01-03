/**
 * RankingPage.jsx
 * ----------------
 * ETAPA 35 (Ranking interactivo):
 * - Like + Guardar desde Ranking (reutiliza endpoints existentes)
 * - Optimistic UI con rollback
 * - Locks por publicación para evitar doble click
 *
 * Backend:
 * - GET /ranking/publicaciones
 * - POST /likes/publicaciones/{publicacion_id} (toggle)
 * - GET /publicaciones/guardadas
 * - POST /publicaciones/guardadas
 * - DELETE /publicaciones/guardadas/{publicacion_id}
 */

import { useEffect, useMemo, useState } from "react";
import {
  fetchRankingPublicaciones,
  fetchPublicacionesGuardadas,
  toggleLikePublicacion,
  guardarPublicacion,
  quitarPublicacionGuardada,
} from "../services/feed_service";

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
 * ActionButton
 * Botón chico y consistente para acciones (like/guardar)
 */
function ActionButton({ children, onClick, disabled, variant = "neutral", title }) {
  const base =
    "inline-flex items-center justify-center rounded-xl px-3 py-2 text-xs sm:text-sm font-semibold border transition select-none";
  const styles = {
    neutral: "bg-gray-900 text-gray-200 border-gray-800 hover:bg-gray-800",
    active: "bg-green-950/40 text-green-300 border-green-800 hover:bg-green-950/60",
  };

  return (
    <button
      type="button"
      className={[base, styles[variant], disabled ? "opacity-50 cursor-not-allowed" : ""].join(" ")}
      onClick={onClick}
      disabled={disabled}
      title={title}
    >
      {children}
    </button>
  );
}

/**
 * PublicacionCard (Ranking)
 * Card consistente con el estilo del Feed, con acciones.
 */
function PublicacionCard({
  pub,
  index,
  isActingLike,
  isActingSave,
  onToggleLike,
  onToggleSave,
}) {
  const likeVariant = pub.liked_by_me ? "active" : "neutral";
  const saveVariant = pub.guardada_by_me ? "active" : "neutral";

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

      {/* Acciones */}
      <div className="mt-5 flex flex-wrap items-center gap-2">
        <ActionButton
          variant={likeVariant}
          disabled={isActingLike}
          onClick={onToggleLike}
          title="Dar/Quitar like"
        >
          {isActingLike ? "Procesando..." : pub.liked_by_me ? "👍 Te gustó" : "👍 Like"}
        </ActionButton>

        <ActionButton
          variant={saveVariant}
          disabled={isActingSave}
          onClick={onToggleSave}
          title="Guardar/Quitar de guardados"
        >
          {isActingSave
            ? "Procesando..."
            : pub.guardada_by_me
            ? "⭐ Guardada"
            : "⭐ Guardar"}
        </ActionButton>
      </div>

      {/* Métricas */}
      <footer className="mt-5 flex flex-wrap items-center gap-2">
        <MetricBadge label="Likes" value={pub.likes_count} icon="👍" />
        <MetricBadge label="Guardados" value={pub.guardados_count} icon="⭐" />
        <MetricBadge label="Interacciones" value={pub.interacciones_count} icon="🔥" />
        <MetricBadge label="Liked" value={pub.liked_by_me ? "Sí" : "No"} icon="📌" />
        <MetricBadge label="Guardada" value={pub.guardada_by_me ? "Sí" : "No"} icon="💾" />
      </footer>
    </article>
  );
}

export default function RankingPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [publicaciones, setPublicaciones] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");

  // Locks por publicación
  const [likeLocks, setLikeLocks] = useState({});
  const [saveLocks, setSaveLocks] = useState({});

  const likeLocksMemo = useMemo(() => likeLocks, [likeLocks]);
  const saveLocksMemo = useMemo(() => saveLocks, [saveLocks]);

  function setLock(setter, pubId, value) {
    setter((prev) => ({ ...prev, [pubId]: value }));
  }

  async function loadRanking() {
    try {
      setIsLoading(true);
      setErrorMessage("");

      const [rankingData, guardadasData] = await Promise.all([
        fetchRankingPublicaciones(),
        fetchPublicacionesGuardadas(),
      ]);

      const items = Array.isArray(rankingData) ? rankingData : rankingData?.items || [];
      const guardadasItems = Array.isArray(guardadasData)
        ? guardadasData
        : guardadasData?.items || [];

      const guardadasSet = new Set(
        guardadasItems
          .map((g) => g?.publicacion_id)
          .filter((id) => typeof id === "number")
      );

      const merged = items.map((p) => ({
        ...p,
        guardada_by_me: guardadasSet.has(p.id),
      }));

      setPublicaciones(merged);
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

  async function handleToggleLike(pubId) {
    if (likeLocksMemo[pubId]) return;

    setLock(setLikeLocks, pubId, true);

    const snapshot = publicaciones;

    setPublicaciones((prev) =>
      prev.map((p) => {
        if (p.id !== pubId) return p;

        const nextLiked = !p.liked_by_me;
        const nextLikesCount = Math.max(
          0,
          (p.likes_count || 0) + (nextLiked ? 1 : -1)
        );

        return { ...p, liked_by_me: nextLiked, likes_count: nextLikesCount };
      })
    );

    try {
      await toggleLikePublicacion(pubId);
    } catch (error) {
      setPublicaciones(snapshot);
      setErrorMessage(error.message || "Error al togglear like.");
    } finally {
      setLock(setLikeLocks, pubId, false);
    }
  }

  async function handleToggleSave(pubId) {
    if (saveLocksMemo[pubId]) return;

    setLock(setSaveLocks, pubId, true);

    const snapshot = publicaciones;

    const current = publicaciones.find((p) => p.id === pubId);
    const estabaGuardada = Boolean(current?.guardada_by_me);

    setPublicaciones((prev) =>
      prev.map((p) => {
        if (p.id !== pubId) return p;

        const nextGuardada = !p.guardada_by_me;
        const nextGuardadosCount = Math.max(
          0,
          (p.guardados_count || 0) + (nextGuardada ? 1 : -1)
        );

        return {
          ...p,
          guardada_by_me: nextGuardada,
          guardados_count: nextGuardadosCount,
        };
      })
    );

    try {
      if (estabaGuardada) {
        await quitarPublicacionGuardada(pubId);
      } else {
        await guardarPublicacion(pubId);
      }
    } catch (error) {
      setPublicaciones(snapshot);
      setErrorMessage(error.message || "Error al guardar/quitar guardado.");
    } finally {
      setLock(setSaveLocks, pubId, false);
    }
  }

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
              <PublicacionCard
                key={p.id}
                pub={p}
                index={idx}
                isActingLike={Boolean(likeLocksMemo[p.id])}
                isActingSave={Boolean(saveLocksMemo[p.id])}
                onToggleLike={() => handleToggleLike(p.id)}
                onToggleSave={() => handleToggleSave(p.id)}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

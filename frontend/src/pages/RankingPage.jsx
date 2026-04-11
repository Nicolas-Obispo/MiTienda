/**
 * RankingPage.jsx
 * ----------------
 * ETAPA 35 (Ranking interactivo):
 * - Like + Guardar desde Ranking (reutiliza endpoints existentes)
 * - Optimistic UI con rollback
 * - Locks por publicación para evitar doble click
 *
 * ETAPA 38 (Refactor UI):
 * - Usa PublicacionCard común
 *
 * ETAPA 39 (Fix UI):
 * - Optimistic UI también para interacciones_count
 * - FIX BUG: Ranking no siempre trae liked_by_me real -> lo tomamos desde Feed por ID
 *
 * ETAPA 56:
 * - Vista en grid
 * - Cards compactas tipo app visual
 */

import { useEffect, useMemo, useState } from "react";
import {
  fetchRankingPublicaciones,
  fetchFeedPublicaciones,
  fetchPublicacionesGuardadas,
  toggleLikePublicacion,
  guardarPublicacion,
  quitarPublicacionGuardada,
} from "../services/feed_service";

import PublicacionCard from "../components/PublicacionCard";

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

      // Ranking define el orden, Feed define liked_by_me real por usuario
      const [rankingData, feedData, guardadasData] = await Promise.all([
        fetchRankingPublicaciones(),
        fetchFeedPublicaciones(),
        fetchPublicacionesGuardadas(),
      ]);

      const rankingItems = Array.isArray(rankingData)
        ? rankingData
        : rankingData?.items || [];

      const feedItems = Array.isArray(feedData)
        ? feedData
        : feedData?.items || [];

      const guardadasItems = Array.isArray(guardadasData)
        ? guardadasData
        : guardadasData?.items || [];

      // Map de liked_by_me desde Feed
      const feedById = new Map(
        feedItems
          .filter((p) => p && typeof p.id === "number")
          .map((p) => [p.id, p])
      );

      // Guardadas por usuario
      const guardadasSet = new Set(
        guardadasItems
          .map((g) => g?.id)
          .filter((id) => typeof id === "number")
      );

      // Merge final
      const merged = rankingItems.map((p) => {
        const feedMatch = feedById.get(p.id);

        const likedByMe =
          feedMatch?.liked_by_me ??
          p?.liked_by_me ??
          p?.is_liked ??
          false;

        return {
          ...p,
          liked_by_me: Boolean(likedByMe),
          guardada_by_me: guardadasSet.has(p.id),
        };
      });

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

  /**
   * Optimistic Like
   */
  async function handleToggleLike(pubId) {
    if (likeLocksMemo[pubId]) return;

    setLock(setLikeLocks, pubId, true);

    const snapshot = publicaciones;

    setPublicaciones((prev) =>
      prev.map((p) => {
        if (p.id !== pubId) return p;

        const currentLiked = Boolean(p.liked_by_me);
        const nextLiked = !currentLiked;
        const delta = nextLiked ? 1 : -1;

        const nextLikesCount = Math.max(0, (p.likes_count || 0) + delta);
        const nextInteraccionesCount = Math.max(
          0,
          (p.interacciones_count || 0) + delta
        );

        return {
          ...p,
          liked_by_me: nextLiked,
          likes_count: nextLikesCount,
          interacciones_count: nextInteraccionesCount,
        };
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

  /**
   * Optimistic Guardado
   */
  async function handleToggleSave(pubId) {
    if (saveLocksMemo[pubId]) return;

    setLock(setSaveLocks, pubId, true);

    const snapshot = publicaciones;

    const current = publicaciones.find((p) => p.id === pubId);
    const estabaGuardada = Boolean(current?.guardada_by_me);

    setPublicaciones((prev) =>
      prev.map((p) => {
        if (p.id !== pubId) return p;

        const currentSaved = Boolean(p.guardada_by_me);
        const nextSaved = !currentSaved;
        const delta = nextSaved ? 1 : -1;

        const nextGuardadosCount = Math.max(0, (p.guardados_count || 0) + delta);
        const nextInteraccionesCount = Math.max(
          0,
          (p.interacciones_count || 0) + delta
        );

        return {
          ...p,
          guardada_by_me: nextSaved,
          guardados_count: nextGuardadosCount,
          interacciones_count: nextInteraccionesCount,
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
      <main className="mx-auto max-w-5xl px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-xl sm:text-2xl font-bold text-white">Ranking</h1>
          <p className="mt-1 text-sm text-gray-400">
            Publicaciones ordenadas por score (likes + recencia).
          </p>
        </div>

        {/* Estado: Loading */}
        {isLoading && (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-3 gap-3">
            <div className="aspect-square rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
            <div className="aspect-square rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
            <div className="aspect-square rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
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
          <div
            className="
              grid
              grid-cols-2
              sm:grid-cols-3
              md:grid-cols-3
              gap-3
            "
          >
            {publicaciones.map((p, idx) => (
              <PublicacionCard
                key={p.id}
                pub={p}
                rankIndex={idx}
                headerRightBadgeText="Ranking"
                isActingLike={Boolean(likeLocksMemo[p.id])}
                isActingSave={Boolean(saveLocksMemo[p.id])}
                onToggleLike={() => handleToggleLike(p.id)}
                onToggleSave={() => handleToggleSave(p.id)}
                compact
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
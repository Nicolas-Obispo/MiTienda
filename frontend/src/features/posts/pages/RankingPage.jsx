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
} from "@features/posts";

import { PublicacionCard } from "@features/posts";

import {
  optimisticToggleGuardado,
  optimisticToggleLike,
  toggleGuardado,
  toggleLike,
  useSocialInteractions,
} from "@features/social";

export default function RankingPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [publicaciones, setPublicaciones] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");
  const {
    likeLocks,
    saveLocks,
    setLikeLock,
    setSaveLock,
    isLikeLocked,
    isSaveLocked,
  } = useSocialInteractions();

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
    if (isLikeLocked(pubId)) return;

    setLikeLock(pubId, true);

    const snapshot = publicaciones;

    setPublicaciones((prev) => optimisticToggleLike(prev, pubId));

    try {
      await toggleLike(pubId);
    } catch (error) {
      setPublicaciones(snapshot);
      setErrorMessage(error.message || "Error al togglear like.");
    } finally {
      setLikeLock(pubId, false);
    }
  }

  /**
   * Optimistic Guardado
   */
  async function handleToggleSave(pubId) {
    if (isSaveLocked(pubId)) return;

    setSaveLock(pubId, true);

    const snapshot = publicaciones;

    const current = publicaciones.find((p) => p.id === pubId);
    const estabaGuardada = Boolean(current?.guardada_by_me);

    setPublicaciones((prev) => optimisticToggleGuardado(prev, pubId));

    try {
      await toggleGuardado({
          publicacionId: pubId,
          estabaGuardada,
        });
    } catch (error) {
      setPublicaciones(snapshot);
      setErrorMessage(error.message || "Error al guardar/quitar guardado.");
    } finally {
      setSaveLock(pubId, false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <main className="mx-auto max-w-5xl px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-xl sm:text-2xl font-bold text-white">Tendencias</h1>
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
                isActingLike={Boolean(likeLocks[p.id])}
                isActingSave={Boolean(saveLocks[p.id])}
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










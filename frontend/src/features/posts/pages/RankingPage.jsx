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

import { useEffect, useState } from "react";

import {
  fetchFeedPublicaciones,
} from "@features/posts";

import { PublicacionCard } from "@features/posts";
import { usePublicacionesGuardadas } from "@features/posts";
import { useRankingPublicaciones } from "@features/posts/hooks/useRankingPublicaciones";
import { Alert, Skeleton, Surface } from "@shared";

import {
  optimisticToggleGuardado,
  optimisticToggleLike,
  useSocialInteractions,
  useToggleLikePublicacionMutation,
  useToggleGuardadoPublicacionMutation,
} from "@features/social";

export default function RankingPage() {
  const {
    data: rankingData = [],
    isLoading: isRankingLoading,
    error: rankingQueryError,
  } = useRankingPublicaciones();
  const {
    data: guardadasData = [],
  } = usePublicacionesGuardadas();

  const [isLoading, setIsLoading] = useState(true);
  const [rankingHydratado, setRankingHydratado] = useState(false);
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

    const toggleLikeMutation =
    useToggleLikePublicacionMutation();

  const toggleGuardadoMutation =
    useToggleGuardadoPublicacionMutation();

  async function loadRanking({ mantenerVisible = false } = {}) {
    try {
      if (!mantenerVisible && publicaciones.length === 0) {
        setIsLoading(true);
      }

      setErrorMessage("");

      // Ranking define el orden, Feed define liked_by_me real por usuario
      const feedData = await fetchFeedPublicaciones();

      if (rankingQueryError) {
        throw rankingQueryError;
      }

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
      setRankingHydratado(true);
    } catch (error) {
      setErrorMessage(error.message || "Error desconocido cargando el ranking.");
      setRankingHydratado(true);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    const rankingItems = Array.isArray(rankingData)
      ? rankingData
      : rankingData?.items || [];

    const hidratoDesdeCache =
      rankingItems.length > 0 && publicaciones.length === 0;

    if (hidratoDesdeCache) {
      setPublicaciones(rankingItems);
      setIsLoading(false);
    }

    if (isRankingLoading && publicaciones.length === 0 && rankingItems.length === 0) {
      return;
    }

    loadRanking({
      mantenerVisible: hidratoDesdeCache || publicaciones.length > 0,
    });
  }, [rankingData, isRankingLoading, rankingQueryError]);

  /**
   * Optimistic Like
   */
  async function handleToggleLike(pubId) {
    if (isLikeLocked(pubId)) return;

    setLikeLock(pubId, true);

    const snapshot = publicaciones;

    setPublicaciones((prev) => optimisticToggleLike(prev, pubId));

    try {
      await toggleLikeMutation.mutateAsync(pubId);
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
      await toggleGuardadoMutation.mutateAsync({
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
    <div className="min-h-screen bg-canvas text-primary">
      <main className="mx-auto max-w-5xl px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-xl font-bold sm:text-2xl">Tendencias</h1>
          <p className="mt-1 text-sm text-secondary">
            Publicaciones ordenadas por score (likes + recencia).
          </p>
        </div>

        {/* Estado: Loading */}
        {isLoading && publicaciones.length === 0 && (
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 sm:gap-3 md:grid-cols-3">
            <Skeleton className="aspect-square rounded-2xl border border-border" />
            <Skeleton className="aspect-square rounded-2xl border border-border" />
            <Skeleton className="aspect-square rounded-2xl border border-border" />
          </div>
        )}

        {/* Estado: Error */}
        {!isLoading && errorMessage && (
          <Alert variant="danger" role="alert" className="p-5">
            <p className="font-semibold">Error</p>
            <p className="mt-2 break-words">{errorMessage}</p>
          </Alert>
        )}

        {/* Estado: Vacío */}
        {rankingHydratado && !isLoading && !isRankingLoading && !errorMessage && publicaciones.length === 0 && (
          <Surface variant="subtle" className="p-6 text-center">
            <p className="font-semibold">No hay publicaciones</p>
            <p className="mt-2 text-sm text-secondary">
              Cuando existan publicaciones con actividad, aparecerán acá.
            </p>
          </Surface>
        )}

        {/* Estado: OK */}
        {!errorMessage && publicaciones.length > 0 && (
          <div
            className="
              grid
              grid-cols-2
              sm:grid-cols-3
              md:grid-cols-3
              gap-2
              sm:gap-3
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










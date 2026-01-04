/**
 * ProfilePage.jsx
 * ----------------
 * ETAPA 39 (Perfil de usuario) - 39.1 Guardados
 *
 * Objetivo:
 * - Mostrar publicaciones guardadas del usuario (GET /publicaciones/guardadas)
 * - Reutilizar PublicacionCard común
 * - Mantener interacción Like/Guardar con optimistic UI (reutiliza endpoints existentes)
 *
 * ETAPA 39 (Fix UI):
 * - Optimistic UI también para interacciones_count (likes + guardados)
 *
 * Nota:
 * - Sin cambios en backend (usa endpoints existentes)
 */

import { useEffect, useMemo, useState } from "react";
import PublicacionCard from "../components/PublicacionCard";
import {
  fetchPublicacionesGuardadas,
  toggleLikePublicacion,
  guardarPublicacion,
  quitarPublicacionGuardada,
} from "../services/feed_service";

export default function ProfilePage() {
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

  async function loadGuardadas() {
    try {
      setIsLoading(true);
      setErrorMessage("");

      const guardadasData = await fetchPublicacionesGuardadas();

      const guardadasItems = Array.isArray(guardadasData)
        ? guardadasData
        : guardadasData?.items || [];

      // Normalizamos para que todas queden como publicaciones “guardadas por mí”
      // Soporta varios formatos de backend sin romper:
      // - viene como publicación directa
      // - viene envuelta como { publicacion: {...} }
      const normalized = guardadasItems
        .map((g) => {
          if (g && typeof g.id === "number") return g;
          if (g?.publicacion && typeof g.publicacion.id === "number") return g.publicacion;
          return null;
        })
        .filter(Boolean)
        .map((p) => ({
          ...p,
          guardada_by_me: true,
        }));

      setPublicaciones(normalized);
    } catch (error) {
      setErrorMessage(error.message || "Error desconocido cargando guardados.");
      setPublicaciones([]);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadGuardadas();
  }, []);

  /**
   * Optimistic Like:
   * - Toggle inmediato de liked_by_me
   * - Ajusta likes_count +1 o -1
   * - Ajusta interacciones_count +1 o -1
   * - Si falla backend, revertimos
   */
  async function handleToggleLike(pubId) {
    if (likeLocksMemo[pubId]) return;

    setLock(setLikeLocks, pubId, true);

    const snapshot = publicaciones;

    setPublicaciones((prev) =>
      prev.map((p) => {
        if (p.id !== pubId) return p;

        const nextLiked = !p.liked_by_me;
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
   * Optimistic Guardado:
   * - En “Mis guardados”, si quitás guardado, desaparece de la lista
   * - Ajusta interacciones_count de forma coherente (+1/-1) para mantener consistencia visual
   * - Si falla backend, revertimos
   */
  async function handleToggleSave(pubId) {
    if (saveLocksMemo[pubId]) return;

    setLock(setSaveLocks, pubId, true);

    const snapshot = publicaciones;

    const current = publicaciones.find((p) => p.id === pubId);
    const estabaGuardada = Boolean(current?.guardada_by_me);

    // Optimistic update
    if (estabaGuardada) {
      // En esta vista, quitar guardado => se elimina del listado
      setPublicaciones((prev) => prev.filter((p) => p.id !== pubId));
    } else {
      // Caso raro: si por algún motivo no estaba marcada, la marcamos y subimos interacciones/guardados
      setPublicaciones((prev) =>
        prev.map((p) => {
          if (p.id !== pubId) return p;

          const nextGuardadosCount = Math.max(0, (p.guardados_count || 0) + 1);
          const nextInteraccionesCount = Math.max(
            0,
            (p.interacciones_count || 0) + 1
          );

          return {
            ...p,
            guardada_by_me: true,
            guardados_count: nextGuardadosCount,
            interacciones_count: nextInteraccionesCount,
          };
        })
      );
    }

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
          <h1 className="text-xl sm:text-2xl font-bold text-white">Mi Perfil</h1>
          <p className="mt-1 text-sm text-gray-400">Mis publicaciones guardadas.</p>
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
            <p className="text-gray-200 font-semibold">No tenés guardados</p>
            <p className="mt-2 text-gray-400 text-sm">
              Guardá publicaciones desde el Feed o Ranking y van a aparecer acá.
            </p>
          </div>
        )}

        {/* Estado: OK */}
        {!isLoading && !errorMessage && publicaciones.length > 0 && (
          <div className="space-y-4">
            {publicaciones.map((p) => (
              <PublicacionCard
                key={p.id}
                pub={p}
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

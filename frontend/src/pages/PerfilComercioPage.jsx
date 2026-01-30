/**
 * PerfilComercioPage.jsx
 * -----------------------
 * ETAPA 40 — Perfil de comercio (40.1 UI + 40.2 Data básica)
 *
 * Backend (Swagger):
 * - GET /comercios/{comercio_id}
 * - GET /publicaciones/comercios/{comercio_id}
 * - GET /historias/comercios/{comercio_id}
 *
 * Frontend:
 * - Ruta prevista: /comercios/:id (protegida)
 * - Reutiliza PublicacionCard para publicaciones del comercio
 * - Historias (por ahora) se muestran como lista simple (ETAPA 42 hará viewer)
 */

import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import PublicacionCard from "../components/PublicacionCard";
import {
  getComercioById,
  getHistoriasDeComercio,
  getPublicacionesDeComercio,
} from "../services/comercios_service";
import {
  fetchPublicacionesGuardadas,
  toggleLikePublicacion,
  guardarPublicacion,
  quitarPublicacionGuardada,
} from "../services/feed_service";

export default function CommerceProfilePage() {
  const { id } = useParams();
  const comercioId = Number(id);

  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  const [comercio, setComercio] = useState(null);
  const [historias, setHistorias] = useState([]);
  const [publicaciones, setPublicaciones] = useState([]);

  // Locks por publicación (like/guardar)
  const [likeLocks, setLikeLocks] = useState({});
  const [saveLocks, setSaveLocks] = useState({});

  const likeLocksMemo = useMemo(() => likeLocks, [likeLocks]);
  const saveLocksMemo = useMemo(() => saveLocks, [saveLocks]);

  function setLock(setter, pubId, value) {
    setter((prev) => ({ ...prev, [pubId]: value }));
  }

  async function loadAll() {
    if (!comercioId || Number.isNaN(comercioId)) {
      setErrorMessage("ID de comercio inválido.");
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setErrorMessage("");

      const [comercioData, publicacionesData, historiasData, guardadasData] =
        await Promise.all([
          getComercioById(comercioId),
          getPublicacionesDeComercio(comercioId),
          getHistoriasDeComercio(comercioId),
          fetchPublicacionesGuardadas(),
        ]);

      const pubs = Array.isArray(publicacionesData)
        ? publicacionesData
        : publicacionesData?.items || [];

      const hist = Array.isArray(historiasData)
        ? historiasData
        : historiasData?.items || [];

      const guardadasItems = Array.isArray(guardadasData)
        ? guardadasData
        : guardadasData?.items || [];

      const guardadasSet = new Set(
        guardadasItems
          .map((g) => g?.publicacion_id)
          .filter((pid) => typeof pid === "number")
      );

      // En publicaciones por comercio, liked_by_me debería venir del backend (como feed/ranking)
      // Solo normalizamos guardada_by_me con el set de guardadas.
      const mergedPubs = pubs.map((p) => ({
        ...p,
        guardada_by_me: guardadasSet.has(p.id),
      }));

      setComercio(comercioData);
      setHistorias(hist);
      setPublicaciones(mergedPubs);
    } catch (error) {
      setErrorMessage(error.message || "Error desconocido cargando perfil del comercio.");
      setComercio(null);
      setHistorias([]);
      setPublicaciones([]);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [comercioId]);

  // Optimistic Like (incluye interacciones_count)
  async function handleToggleLike(pubId) {
    if (likeLocksMemo[pubId]) return;

    setLock(setLikeLocks, pubId, true);
    const snapshot = publicaciones;

    setPublicaciones((prev) =>
      prev.map((p) => {
        if (p.id !== pubId) return p;

        const nextLiked = !Boolean(p.liked_by_me);
        const delta = nextLiked ? 1 : -1;

        return {
          ...p,
          liked_by_me: nextLiked,
          likes_count: Math.max(0, (p.likes_count || 0) + delta),
          interacciones_count: Math.max(0, (p.interacciones_count || 0) + delta),
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

  // Optimistic Guardado (incluye interacciones_count)
  async function handleToggleSave(pubId) {
    if (saveLocksMemo[pubId]) return;

    setLock(setSaveLocks, pubId, true);
    const snapshot = publicaciones;

    const current = publicaciones.find((p) => p.id === pubId);
    const estabaGuardada = Boolean(current?.guardada_by_me);

    setPublicaciones((prev) =>
      prev.map((p) => {
        if (p.id !== pubId) return p;

        const nextSaved = !Boolean(p.guardada_by_me);
        const delta = nextSaved ? 1 : -1;

        return {
          ...p,
          guardada_by_me: nextSaved,
          guardados_count: Math.max(0, (p.guardados_count || 0) + delta),
          interacciones_count: Math.max(0, (p.interacciones_count || 0) + delta),
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
          <h1 className="text-xl sm:text-2xl font-bold text-white">
            Perfil de comercio
          </h1>
          <p className="mt-1 text-sm text-gray-400">
            Comercio ID: <span className="text-gray-200 font-semibold">{id}</span>
          </p>
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="space-y-3">
            <div className="h-24 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
            <div className="h-28 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
            <div className="h-28 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
          </div>
        )}

        {/* Error */}
        {!isLoading && errorMessage && (
          <div className="rounded-2xl border border-red-900 bg-red-950/40 p-5">
            <p className="font-semibold text-red-200">Error</p>
            <p className="mt-2 text-red-100 break-words">{errorMessage}</p>
          </div>
        )}

        {/* Contenido */}
        {!isLoading && !errorMessage && (
          <>
            {/* Card Comercio */}
            <section className="rounded-2xl border border-gray-800 bg-gray-950 p-5">
              <h2 className="text-lg font-semibold text-white">
                {comercio?.nombre ?? "Comercio"}
              </h2>

              <div className="mt-2 text-sm text-gray-300 space-y-1">
                {comercio?.descripcion && (
                  <p className="text-gray-200">{comercio.descripcion}</p>
                )}

                <p className="text-gray-400">
                  Estado:{" "}
                  <span className="text-gray-200 font-semibold">
                    {comercio?.is_activo ? "Activo" : "Inactivo"}
                  </span>
                </p>
              </div>
            </section>

            {/* Historias */}
            <section className="mt-6">
              <h3 className="text-base font-semibold text-white">Historias</h3>

              {historias.length === 0 ? (
                <div className="mt-3 rounded-2xl border border-gray-800 bg-gray-950 p-5">
                  <p className="text-gray-300">No hay historias todavía.</p>
                  <p className="mt-1 text-sm text-gray-500">
                    (El viewer tipo Instagram lo hacemos en ETAPA 42)
                  </p>
                </div>
              ) : (
                <div className="mt-3 space-y-2">
                  {historias.map((h) => (
                    <div
                      key={h.id}
                      className="rounded-2xl border border-gray-800 bg-gray-950 p-4"
                    >
                      <p className="text-sm text-gray-200 font-semibold">
                        Historia #{h.id}
                      </p>
                      {h.titulo && (
                        <p className="mt-1 text-sm text-gray-300">{h.titulo}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Publicaciones */}
            <section className="mt-6">
              <h3 className="text-base font-semibold text-white">
                Publicaciones
              </h3>

              {publicaciones.length === 0 ? (
                <div className="mt-3 rounded-2xl border border-gray-800 bg-gray-950 p-5">
                  <p className="text-gray-300">
                    Este comercio no tiene publicaciones todavía.
                  </p>
                </div>
              ) : (
                <div className="mt-3 space-y-4">
                  {publicaciones.map((p) => (
                    <PublicacionCard
                      key={p.id}
                      pub={p}
                      headerRightBadgeText="Comercio"
                      isActingLike={Boolean(likeLocksMemo[p.id])}
                      isActingSave={Boolean(saveLocksMemo[p.id])}
                      onToggleLike={() => handleToggleLike(p.id)}
                      onToggleSave={() => handleToggleSave(p.id)}
                    />
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </main>
    </div>
  );
}

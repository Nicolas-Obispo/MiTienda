/**
 * FeedPage.jsx
 * ----------------
 * ETAPA 33 (Interacciones desde el Feed):
 * - Like desde la UI (endpoint existente)
 * - Guardar/Quitar guardado desde la UI (endpoints existentes)
 * - Optimistic UI (sin recargar feed completo)
 * - Sin cambios backend
 *
 * ETAPA 39 (Fix UI):
 * - Optimistic UI también para interacciones_count (likes + guardados)
 *
 * ETAPA 41 (Historias UI tipo Instagram):
 * - Barra horizontal de historias arriba del Feed (UI)
 * - Historias se cargan por comercio (backend real: GET /historias/comercios/{comercio_id})
 * - Viewer tipo Instagram (modal) al tocar una burbuja
 * - Pulido: cerrar viewer al cambiar de ruta (evita modal “colgado”)
 */

import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import PublicacionCard from "../components/PublicacionCard";
import HistoriasBar from "../components/HistoriasBar";
import HistoriasViewer from "../components/HistoriasViewer";

import {
  fetchFeedPublicaciones,
  fetchPublicacionesGuardadas,
  toggleLikePublicacion,
  guardarPublicacion,
  quitarPublicacionGuardada,
} from "../services/feed_service";

import { fetchHistoriasPorComercio } from "../services/historias_service";

export default function FeedPage() {
  const navigate = useNavigate();

  /**
   * location:
   * - Se usa para detectar cambios de ruta y cerrar viewer si estaba abierto.
   */
  const location = useLocation();

  /**
   * Estado principal del Feed
   */
  const [isLoading, setIsLoading] = useState(true);
  const [publicaciones, setPublicaciones] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");

  /**
   * Estado de Historias (Barra)
   * - historiasItems: lista de burbujas por comercio (lo que consume HistoriasBar)
   * - historiasErrorMessage: error específico de historias (no bloquea el feed)
   */
  const [historiasItems, setHistoriasItems] = useState([]);
  const [historiasErrorMessage, setHistoriasErrorMessage] = useState("");

  /**
   * Estado del viewer de historias (modal tipo Instagram)
   * - viewerIsOpen: controla visibilidad
   * - viewerTitulo: título mostrado (ej: nombre del comercio)
   * - viewerHistorias: lista de historias del comercio seleccionado
   */
  const [viewerIsOpen, setViewerIsOpen] = useState(false);
  const [viewerTitulo, setViewerTitulo] = useState("Historias");
  const [viewerHistorias, setViewerHistorias] = useState([]);

  /**
   * Locks por publicación para evitar doble click mientras pega al backend
   */
  const [likeLocks, setLikeLocks] = useState({}); // { [pubId]: true }
  const [saveLocks, setSaveLocks] = useState({}); // { [pubId]: true }

  const likeLocksMemo = useMemo(() => likeLocks, [likeLocks]);
  const saveLocksMemo = useMemo(() => saveLocks, [saveLocks]);

  /**
   * cerrarViewer
   * Cierra el viewer y limpia estados asociados.
   *
   * Por qué existe:
   * - Evita repetir el mismo bloque en varios lugares.
   * - Garantiza que siempre se cierre de la misma manera.
   */
  function cerrarViewer() {
    setViewerIsOpen(false);
    setViewerHistorias([]);
    setViewerTitulo("Historias");
  }

  /**
   * closeOnRouteChange
   * Si cambia la ruta mientras el viewer está abierto:
   * - cerramos el modal
   * - limpiamos estados
   *
   * Por qué:
   * - Evita que el viewer quede abierto sobre otra pantalla.
   */
  useEffect(() => {
    if (viewerIsOpen) {
      cerrarViewer();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  /**
   * setLock
   * Helper para setear locks por id de publicación.
   *
   * @param {Function} setter - setState del lock
   * @param {number} pubId - id de publicación
   * @param {boolean} value - lock true/false
   */
  function setLock(setter, pubId, value) {
    setter((prev) => ({ ...prev, [pubId]: value }));
  }

  /**
   * buildHistoriasBarItemsFromFeed
   * Construye los items para HistoriasBar basándose en los comercios presentes en el feed.
   *
   * Importante:
   * - Backend real solo permite traer historias por comercio.
   * - Tomamos comercios del feed para no inventar endpoint "recientes".
   * - Si un comercio NO tiene historias, no aparece en la barra.
   *
   * @param {Array} feedItems - publicaciones ya cargadas/mergeadas
   * @returns {Promise<void>}
   */
  async function buildHistoriasBarItemsFromFeed(feedItems) {
    try {
      setHistoriasErrorMessage("");

      /**
       * Extraemos IDs únicos de comercios desde el feed.
       * - Usamos varios posibles campos para no romper si cambia el shape:
       *   comercio_id / comercioId / comercio?.id
       */
      const comercioIdsUnicos = [];
      const seen = new Set();

      for (const p of feedItems) {
        const comercioId =
          p?.comercio_id ?? p?.comercioId ?? p?.comercio?.id ?? null;

        if (typeof comercioId === "number" && !seen.has(comercioId)) {
          seen.add(comercioId);
          comercioIdsUnicos.push(comercioId);
        }
      }

      /**
       * Evitamos disparar demasiadas requests si el feed es enorme.
       * - Cap simple: primeros 15 comercios únicos.
       */
      const comercioIds = comercioIdsUnicos.slice(0, 15);

      /**
       * Para mostrar nombre/thumbnail en la barra, intentamos deducirlos del feed.
       * - nombre: comercio_nombre / comercioNombre / comercio?.nombre
       * - thumbnailUrl: comercio_logo_url / comercioLogoUrl / comercio?.logo_url
       */
      const comercioMeta = new Map();
      for (const p of feedItems) {
        const id = p?.comercio_id ?? p?.comercioId ?? p?.comercio?.id ?? null;
        if (typeof id !== "number") continue;

        if (!comercioMeta.has(id)) {
          const nombre =
            p?.comercio_nombre ??
            p?.comercioNombre ??
            p?.comercio?.nombre ??
            `Comercio ${id}`;

          const thumbnailUrl =
            p?.comercio_logo_url ??
            p?.comercioLogoUrl ??
            p?.comercio?.logo_url ??
            null;

          comercioMeta.set(id, { nombre, thumbnailUrl });
        }
      }

      /**
       * Traemos historias por comercio en paralelo.
       * - Si un comercio da error, NO tiramos abajo todo: lo tratamos como "sin historias".
       */
      const results = await Promise.all(
        comercioIds.map(async (comercioId) => {
          try {
            const historias = await fetchHistoriasPorComercio(comercioId);
            const list = Array.isArray(historias)
              ? historias
              : historias?.items || [];

            return { comercioId, historias: list };
          } catch (e) {
            return { comercioId, historias: [] };
          }
        })
      );

      /**
       * Construimos items para HistoriasBar:
       * - Solo incluimos comercios con al menos 1 historia.
       */
      const items = results
        .filter((r) => Array.isArray(r.historias) && r.historias.length > 0)
        .map((r) => {
          const meta = comercioMeta.get(r.comercioId) || {
            nombre: `Comercio ${r.comercioId}`,
            thumbnailUrl: null,
          };

          return {
            comercioId: r.comercioId,
            nombre: meta.nombre,
            thumbnailUrl: meta.thumbnailUrl,
            cantidad: r.historias.length,
          };
        });

      setHistoriasItems(items);
    } catch (error) {
      /**
       * Si falla algo inesperado, mostramos error solo de historias.
       * - El feed sigue funcionando.
       */
      setHistoriasItems([]);
      setHistoriasErrorMessage(
        error?.message || "Error desconocido cargando historias."
      );
    }
  }

  /**
   * loadFeed
   * Carga feed + guardadas y mergea guardada_by_me.
   * Luego dispara carga de HistoriasBar basándose en comercios del feed.
   */
  async function loadFeed() {
    try {
      setIsLoading(true);
      setErrorMessage("");

      const [feedData, guardadasData] = await Promise.all([
        fetchFeedPublicaciones(),
        fetchPublicacionesGuardadas(),
      ]);

      const feedItems = Array.isArray(feedData)
        ? feedData
        : feedData?.items || [];
      const guardadasItems = Array.isArray(guardadasData)
        ? guardadasData
        : guardadasData?.items || [];

      const guardadasSet = new Set(
        guardadasItems
          .map((g) => g?.publicacion_id)
          .filter((id) => typeof id === "number")
      );

      const merged = feedItems.map((p) => ({
        ...p,
        guardada_by_me: guardadasSet.has(p.id),
      }));

      setPublicaciones(merged);

      /**
       * ETAPA 41:
       * Construimos barra de historias desde comercios presentes en el feed.
       * - No bloqueamos el render del feed.
       */
      buildHistoriasBarItemsFromFeed(merged);
    } catch (error) {
      setErrorMessage(error.message || "Error desconocido cargando el feed.");
      setPublicaciones([]);

      /**
       * Si el feed falla, limpiamos historias (no mostramos data vieja).
       */
      setHistoriasItems([]);
      setHistoriasErrorMessage("");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadFeed();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /**
   * handleClickHistoriaComercio
   * Al tocar una burbuja:
   * - Trae historias del comercio desde backend (endpoint real)
   * - Abre el viewer (modal tipo Instagram)
   *
   * Backend:
   * - GET /historias/comercios/{comercio_id}
   *
   * @param {number} comercioId
   */
  async function handleClickHistoriaComercio(comercioId) {
    try {
      /**
       * Buscamos metadata del comercio desde la barra para el título del viewer.
       * - Si no existe, usamos fallback.
       */
      const item = historiasItems.find((i) => i.comercioId === comercioId);
      const titulo = item?.nombre || `Comercio ${comercioId}`;

      /**
       * Traemos historias reales del backend.
       * - Si no devuelve array, forzamos a [] para evitar romper el viewer.
       */
      const historias = await fetchHistoriasPorComercio(comercioId);
      const list = Array.isArray(historias) ? historias : [];

      /**
       * Si no hay historias, por ahora navegamos al perfil del comercio
       * (esto evita abrir un viewer vacío).
       */
      if (list.length === 0) {
        navigate(`/comercios/${comercioId}`);
        return;
      }

      /**
       * Seteamos estados del viewer y lo abrimos.
       */
      setViewerTitulo(titulo);
      setViewerHistorias(list);
      setViewerIsOpen(true);
    } catch (error) {
      /**
       * Si falla, hacemos fallback al perfil del comercio.
       */
      navigate(`/comercios/${comercioId}`);
    }
  }

  /**
   * Optimistic Like:
   * - Toggle inmediato de liked_by_me
   * - Ajusta likes_count +1 o -1 según corresponda
   * - Ajusta interacciones_count +1 o -1 (porque interacciones = likes + guardados)
   * - Si falla backend, revertimos
   */
  async function handleToggleLike(pubId) {
    if (likeLocksMemo[pubId]) return;

    setLock(setLikeLocks, pubId, true);

    // Snapshot para revertir si falla
    const snapshot = publicaciones;

    // Optimistic update
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
      // Revertimos si falla
      setPublicaciones(snapshot);
      setErrorMessage(error.message || "Error al togglear like.");
    } finally {
      setLock(setLikeLocks, pubId, false);
    }
  }

  /**
   * Optimistic Guardado:
   * - Toggle inmediato de guardada_by_me
   * - Ajusta guardados_count +1 o -1
   * - Ajusta interacciones_count +1 o -1 (porque interacciones = likes + guardados)
   * - Si falla backend, revertimos
   */
  async function handleToggleSave(pubId) {
    if (saveLocksMemo[pubId]) return;

    setLock(setSaveLocks, pubId, true);

    const snapshot = publicaciones;

    // Determinamos estado actual para elegir endpoint
    const current = publicaciones.find((p) => p.id === pubId);
    const estabaGuardada = Boolean(current?.guardada_by_me);

    // Optimistic update
    setPublicaciones((prev) =>
      prev.map((p) => {
        if (p.id !== pubId) return p;

        const nextGuardada = !p.guardada_by_me;
        const delta = nextGuardada ? 1 : -1;

        const nextGuardadosCount = Math.max(
          0,
          (p.guardados_count || 0) + delta
        );

        const nextInteraccionesCount = Math.max(
          0,
          (p.interacciones_count || 0) + delta
        );

        return {
          ...p,
          guardada_by_me: nextGuardada,
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
      <main className="mx-auto max-w-3xl px-4 py-8">
        {/* ETAPA 41: Barra de Historias (no bloquea el feed) */}
        {!isLoading && !errorMessage && (
          <div className="mb-4">
            <HistoriasBar
              items={historiasItems}
              onClickComercio={handleClickHistoriaComercio}
            />

            {/* Error de historias: se muestra discreto y NO bloquea el feed */}
            {historiasErrorMessage ? (
              <div className="mt-2 rounded-xl border border-yellow-900 bg-yellow-950/30 p-3 text-sm text-yellow-200">
                {historiasErrorMessage}
              </div>
            ) : null}
          </div>
        )}

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

      {/* ETAPA 41: Viewer de Historias (modal tipo Instagram) */}
      <HistoriasViewer
        isOpen={viewerIsOpen}
        onClose={() => {
          /**
           * Al cerrar:
           * - ocultamos modal
           * - limpiamos data para no mostrar historias viejas en la próxima apertura
           */
          cerrarViewer();
        }}
        historias={viewerHistorias}
        titulo={viewerTitulo}
      />
    </div>
  );
}

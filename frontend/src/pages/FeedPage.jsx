/**
 * FeedPage.jsx
 * ----------------
 * ETAPA 33: Like + Guardar/Quitar (optimistic UI)
 * ETAPA 39: Optimistic también en interacciones_count
 * ETAPA 41: Historias (barra + viewer tipo Instagram)
 * ETAPA 43: Marcar historia como vista al abrir el viewer (primera historia)
 * ETAPA 44 (parcial): Autoplay entre comercios (cuando termina un comercio, pasa al siguiente)
 * ETAPA 44: Visto/No visto REAL (backend devuelve vista_by_me)
 */

import { useEffect, useMemo, useRef, useState } from "react";
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

import {
  fetchHistoriasPorComercio,
  marcarHistoriaVista,
} from "../services/historias_service";

export default function FeedPage() {
  const navigate = useNavigate();
  const location = useLocation();

  // -----------------------------
  // Estado principal del Feed
  // -----------------------------
  const [isLoading, setIsLoading] = useState(true);
  const [publicaciones, setPublicaciones] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");

  // -----------------------------
  // Estado de Historias (Barra)
  // -----------------------------
  const [historiasItems, setHistoriasItems] = useState([]);
  const [historiasErrorMessage, setHistoriasErrorMessage] = useState("");

  // -----------------------------
  // Estado del Viewer (Modal)
  // -----------------------------
  const [viewerIsOpen, setViewerIsOpen] = useState(false);
  const [viewerTitulo, setViewerTitulo] = useState("Historias");
  const [viewerHistorias, setViewerHistorias] = useState([]);

  // Evita marcar vista 2 veces por la misma apertura
  const ultimaHistoriaVistaMarcadaRef = useRef(null);

  // ✅ Autoplay entre comercios (cola/orden)
  const viewerComercioIdRef = useRef(null);
  const historiasOrdenRef = useRef([]); // [{ comercioId, nombre }]

  // Locks por publicación (like/guardar)
  const [likeLocks, setLikeLocks] = useState({});
  const [saveLocks, setSaveLocks] = useState({});

  const likeLocksMemo = useMemo(() => likeLocks, [likeLocks]);
  const saveLocksMemo = useMemo(() => saveLocks, [saveLocks]);

  // -----------------------------
  // Helpers
  // -----------------------------
  function setLock(setter, pubId, value) {
    setter((prev) => ({ ...prev, [pubId]: value }));
  }

  function cerrarViewer() {
    setViewerIsOpen(false);
    setViewerHistorias([]);
    setViewerTitulo("Historias");
    ultimaHistoriaVistaMarcadaRef.current = null;
    viewerComercioIdRef.current = null;
  }

  // Si cambia la ruta con el viewer abierto, cerramos (evita modal “colgado”)
  useEffect(() => {
    if (viewerIsOpen) cerrarViewer();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  // ✅ Mantener el orden actual de la barra para autoplay
  useEffect(() => {
    historiasOrdenRef.current = (historiasItems || []).map((i) => ({
      comercioId: i.comercioId,
      nombre: i.nombre,
    }));
  }, [historiasItems]);

  /**
   * Preload de imágenes en background (no bloquea UI).
   * - Evita pantalla negra en la primer historia cuando se abre por primera vez.
   */
  function preloadHistoriasImages(historias, max = 10) {
    if (!Array.isArray(historias) || historias.length === 0) return;

    const urls = [];
    for (const h of historias) {
      const url = h?.media_url;
      if (url && typeof url === "string") {
        urls.push(url);
        if (urls.length >= max) break;
      }
    }

    const doPreload = () => {
      for (const url of urls) {
        const img = new Image();
        img.decoding = "async";
        img.loading = "eager";
        img.src = url;
      }
    };

    if (typeof window !== "undefined" && "requestIdleCallback" in window) {
      window.requestIdleCallback(doPreload, { timeout: 1200 });
    } else {
      setTimeout(doPreload, 0);
    }
  }

  /**
   * ETAPA 44:
   * - El backend devuelve vista_by_me (estado real por usuario).
   * - El frontend SOLO calcula "pendientes" desde ese flag para UI.
   */
  function calcularPendientes(historiasList) {
    const list = Array.isArray(historiasList) ? historiasList : [];
    return list.filter((h) => !Boolean(h?.vista_by_me)).length;
  }

  /**
   * ETAPA 44:
   * Recalcula el item de un comercio (cantidad + pendientes) consultando backend.
   * - Se usa después de marcar vista para que aro/contador se actualicen sin parches.
   */
  async function refrescarItemHistoriasComercio(comercioId) {
    try {
      const historias = await fetchHistoriasPorComercio(comercioId);
      const list = Array.isArray(historias) ? historias : historias?.items || [];

      const cantidad = list.length;
      const pendientes = calcularPendientes(list);

      setHistoriasItems((prev) =>
        (prev || []).map((it) =>
          it.comercioId === comercioId ? { ...it, cantidad, pendientes } : it
        )
      );
    } catch {
      // Si falla, no rompemos nada. Queda el estado anterior.
    }
  }

  /**
   * Construye items para la barra desde comercios presentes en el feed
   * y precarga algunas imágenes en background.
   */
  async function buildHistoriasBarItemsFromFeed(feedItems) {
    try {
      setHistoriasErrorMessage("");

      // ✅ Normaliza IDs: acepta number o string numérico ("7")
      function normalizarId(value) {
        const n = Number(value);
        return Number.isFinite(n) ? n : null;
      }

      const comercioIdsUnicos = [];
      const seen = new Set();

      for (const p of feedItems) {
        const raw =
          p?.comercio_id ?? p?.comercioId ?? p?.comercio?.id ?? null;

        const comercioId = normalizarId(raw);

        if (comercioId !== null && !seen.has(comercioId)) {
          seen.add(comercioId);
          comercioIdsUnicos.push(comercioId);
        }
      }

      const comercioIds = comercioIdsUnicos.slice(0, 15);

      // Meta (nombre/logo) deducida del feed
      const comercioMeta = new Map();
      for (const p of feedItems) {
        const raw = p?.comercio_id ?? p?.comercioId ?? p?.comercio?.id ?? null;
        const id = normalizarId(raw);
        if (id === null) continue;

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

      // Traemos historias por comercio en paralelo
      const results = await Promise.all(
        comercioIds.map(async (comercioId) => {
          try {
            const historias = await fetchHistoriasPorComercio(comercioId);
            const list = Array.isArray(historias)
              ? historias
              : historias?.items || [];
            return { comercioId, historias: list };
          } catch {
            return { comercioId, historias: [] };
          }
        })
      );

      // Precarga liviana global (primeras historias encontradas)
      let preloadedCount = 0;
      const MAX_PRELOAD_TOTAL = 20;

      for (const r of results) {
        if (preloadedCount >= MAX_PRELOAD_TOTAL) break;
        const historias = r?.historias || [];
        const slice = historias.slice(0, 2);
        preloadHistoriasImages(slice, 2);
        preloadedCount += slice.length;
      }

      // Items para la barra (solo comercios con historias)
      const items = results
        .filter((r) => Array.isArray(r.historias) && r.historias.length > 0)
        .map((r) => {
          const meta = comercioMeta.get(r.comercioId) || {
            nombre: `Comercio ${r.comercioId}`,
            thumbnailUrl: null,
          };

          // ETAPA 44: pendientes reales por usuario (backend manda vista_by_me)
          const pendientes = calcularPendientes(r.historias);

          return {
            comercioId: r.comercioId,
            nombre: meta.nombre,
            thumbnailUrl: meta.thumbnailUrl,
            cantidad: r.historias.length,
            pendientes, // <- nuevo: HistoriasBar lo usa para aro/contador/orden
          };
        });

      setHistoriasItems(items);
    } catch (error) {
      setHistoriasItems([]);
      setHistoriasErrorMessage(
        error?.message || "Error desconocido cargando historias."
      );
    }
  }

  // -----------------------------
  // Carga inicial del Feed
  // -----------------------------
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

      // Historias (no bloquea el feed)
      buildHistoriasBarItemsFromFeed(merged);
    } catch (error) {
      setErrorMessage(error?.message || "Error desconocido cargando el feed.");
      setPublicaciones([]);
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

  // -----------------------------
  // Historias: autoplay siguiente comercio
  // -----------------------------
  async function abrirSiguienteComercioHistorias() {
    try {
      const orden = historiasOrdenRef.current || [];
      const actualId = viewerComercioIdRef.current;

      if (!actualId || orden.length === 0) {
        cerrarViewer();
        return;
      }

      const idx = orden.findIndex((x) => x.comercioId === actualId);
      const next = idx >= 0 ? orden[idx + 1] : null;

      if (!next) {
        cerrarViewer();
        return;
      }

      const nextId = next.comercioId;
      const nextTitulo = next.nombre || `Comercio ${nextId}`;

      const historias = await fetchHistoriasPorComercio(nextId);
      const list = Array.isArray(historias) ? historias : [];

      if (list.length === 0) {
        // Si justo ese comercio quedó sin historias, saltamos al siguiente
        viewerComercioIdRef.current = nextId;
        return abrirSiguienteComercioHistorias();
      }

      preloadHistoriasImages(list, 3);

      // Abrimos el siguiente grupo
      viewerComercioIdRef.current = nextId;
      setViewerTitulo(nextTitulo);
      setViewerHistorias(list);
      setViewerIsOpen(true);

      // Marcar vista de primera historia (sin bloquear)
      const primeraHistoriaId = list?.[0]?.id ?? null;
      if (
        typeof primeraHistoriaId === "number" &&
        ultimaHistoriaVistaMarcadaRef.current !== primeraHistoriaId
      ) {
        ultimaHistoriaVistaMarcadaRef.current = primeraHistoriaId;

        setTimeout(() => {
          marcarHistoriaVista(primeraHistoriaId)
            .then(() => {
              // ETAPA 44: refresca el aro/contador de ese comercio con info real del backend
              refrescarItemHistoriasComercio(nextId);
            })
            .catch(() => {});
        }, 0);
      }
    } catch {
      cerrarViewer();
    }
  }

  // -----------------------------
  // Historias: click en burbuja
  // -----------------------------
  async function handleClickHistoriaComercio(comercioId) {
    try {
      const item = historiasItems.find((i) => i.comercioId === comercioId);
      const titulo = item?.nombre || `Comercio ${comercioId}`;

      const historias = await fetchHistoriasPorComercio(comercioId);
      const list = Array.isArray(historias) ? historias : [];

      if (list.length === 0) {
        navigate(`/comercios/${comercioId}`);
        return;
      }

      preloadHistoriasImages(list, 3);

      // ✅ set comercio actual (para autoplay)
      viewerComercioIdRef.current = comercioId;

      setViewerTitulo(titulo);
      setViewerHistorias(list);
      setViewerIsOpen(true);

      // ETAPA 43/44: marcar vista (primera historia) sin bloquear UI
      const primeraHistoriaId = list?.[0]?.id ?? null;

      if (
        typeof primeraHistoriaId === "number" &&
        ultimaHistoriaVistaMarcadaRef.current !== primeraHistoriaId
      ) {
        ultimaHistoriaVistaMarcadaRef.current = primeraHistoriaId;

        setTimeout(() => {
          marcarHistoriaVista(primeraHistoriaId)
            .then(() => {
              // ETAPA 44: refresca el aro/contador de ese comercio con info real del backend
              refrescarItemHistoriasComercio(comercioId);
            })
            .catch(() => {});
        }, 0);
      }
    } catch {
      navigate(`/comercios/${comercioId}`);
    }
  }

  // -----------------------------
  // Interacciones: Like
  // -----------------------------
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
      setErrorMessage(error?.message || "Error al togglear like.");
    } finally {
      setLock(setLikeLocks, pubId, false);
    }
  }

  // -----------------------------
  // Interacciones: Guardar/Quitar
  // -----------------------------
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
      setErrorMessage(error?.message || "Error al guardar/quitar guardado.");
    } finally {
      setLock(setSaveLocks, pubId, false);
    }
  }

  // -----------------------------
  // Render
  // -----------------------------
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <main className="mx-auto max-w-3xl px-4 py-8">
        {/* Barra de Historias */}
        {!isLoading && !errorMessage && (
          <div className="mb-4">
            <HistoriasBar
              items={historiasItems}
              onClickComercio={handleClickHistoriaComercio}
            />

            {historiasErrorMessage ? (
              <div className="mt-2 rounded-xl border border-yellow-900 bg-yellow-950/30 p-3 text-sm text-yellow-200">
                {historiasErrorMessage}
              </div>
            ) : null}
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div className="space-y-3">
            <div className="h-28 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
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

        {/* Vacío */}
        {!isLoading && !errorMessage && publicaciones.length === 0 && (
          <div className="rounded-2xl border border-gray-800 bg-gray-950 p-6 text-center">
            <p className="text-gray-200 font-semibold">No hay publicaciones</p>
            <p className="mt-2 text-gray-400 text-sm">
              Cuando existan publicaciones activas, aparecerán acá.
            </p>
          </div>
        )}

        {/* OK */}
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

      {/* Viewer tipo Instagram */}
      <HistoriasViewer
        isOpen={viewerIsOpen}
        onClose={cerrarViewer}
        onEnd={abrirSiguienteComercioHistorias}
        historias={viewerHistorias}
        titulo={viewerTitulo}
      />
    </div>
  );
}

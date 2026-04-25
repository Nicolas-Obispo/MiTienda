/**
 * FeedPage.jsx
 * ----------------
 * ETAPA 58: Feed híbrido recomendado
 * - Home / Feed: scroll vertical tipo reels
 * - Explorar: mantiene grid de discovery
 * - Backend sigue siendo fuente de verdad
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
  fetchHistoriasBarItems,
  marcarHistoriaVista,
} from "../services/historias_service";

export default function FeedPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const [isLoading, setIsLoading] = useState(true);
  const [publicaciones, setPublicaciones] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");

  const [historiasItems, setHistoriasItems] = useState([]);
  const [historiasErrorMessage, setHistoriasErrorMessage] = useState("");

  const [viewerIsOpen, setViewerIsOpen] = useState(false);
  const [viewerTitulo, setViewerTitulo] = useState("Historias");
  const [viewerHistorias, setViewerHistorias] = useState([]);

  const ultimaHistoriaVistaMarcadaRef = useRef(null);
  const viewerComercioIdRef = useRef(null);
  const historiasOrdenRef = useRef([]);

  const [likeLocks, setLikeLocks] = useState({});
  const [saveLocks, setSaveLocks] = useState({});

  const likeLocksMemo = useMemo(() => likeLocks, [likeLocks]);
  const saveLocksMemo = useMemo(() => saveLocks, [saveLocks]);

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

  useEffect(() => {
    if (viewerIsOpen) cerrarViewer();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  useEffect(() => {
    historiasOrdenRef.current = (historiasItems || []).map((i) => ({
      comercioId: i.comercioId,
      nombre: i.nombre,
    }));
  }, [historiasItems]);

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

  async function loadHistoriasBar() {
    try {
      setHistoriasErrorMessage("");
      const data = await fetchHistoriasBarItems();
      const items = Array.isArray(data) ? data : data?.items || [];
      setHistoriasItems(items);
    } catch (error) {
      setHistoriasItems([]);
      setHistoriasErrorMessage(
        error?.message || "Error desconocido cargando historias."
      );
    }
  }

  async function refrescarItemHistoriasComercio() {
    await loadHistoriasBar();
  }

  async function loadFeed() {
    try {
      setIsLoading(true);
      setErrorMessage("");

      const [feedData, guardadasData] = await Promise.all([
        fetchFeedPublicaciones(),
        fetchPublicacionesGuardadas(),
      ]);

      const feedItems = Array.isArray(feedData) ? feedData : feedData?.items || [];

      const guardadasItems = Array.isArray(guardadasData)
        ? guardadasData
        : guardadasData?.items || [];

      const guardadasSet = new Set(
        guardadasItems
          .map((g) => g?.id)
          .filter((id) => typeof id === "number")
      );

      const merged = feedItems.map((p) => ({
        ...p,
        guardada_by_me: guardadasSet.has(p.id),
      }));

      setPublicaciones(merged);
      loadHistoriasBar();
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
        viewerComercioIdRef.current = nextId;
        return abrirSiguienteComercioHistorias();
      }

      preloadHistoriasImages(list, 3);

      viewerComercioIdRef.current = nextId;
      setViewerTitulo(nextTitulo);
      setViewerHistorias(list);
      setViewerIsOpen(true);

      const primeraHistoriaId = list?.[0]?.id ?? null;

      if (
        typeof primeraHistoriaId === "number" &&
        ultimaHistoriaVistaMarcadaRef.current !== primeraHistoriaId
      ) {
        ultimaHistoriaVistaMarcadaRef.current = primeraHistoriaId;

        setTimeout(() => {
          marcarHistoriaVista(primeraHistoriaId)
            .then(() => refrescarItemHistoriasComercio())
            .catch(() => {});
        }, 0);
      }
    } catch {
      cerrarViewer();
    }
  }

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

      viewerComercioIdRef.current = comercioId;
      setViewerTitulo(titulo);
      setViewerHistorias(list);
      setViewerIsOpen(true);

      const primeraHistoriaId = list?.[0]?.id ?? null;

      if (
        typeof primeraHistoriaId === "number" &&
        ultimaHistoriaVistaMarcadaRef.current !== primeraHistoriaId
      ) {
        ultimaHistoriaVistaMarcadaRef.current = primeraHistoriaId;

        setTimeout(() => {
          marcarHistoriaVista(primeraHistoriaId)
            .then(() => refrescarItemHistoriasComercio())
            .catch(() => {});
        }, 0);
      }
    } catch {
      navigate(`/comercios/${comercioId}`);
    }
  }

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

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <main className="mx-auto max-w-2xl px-3 py-4 sm:px-4 sm:py-6">
        {!isLoading && !errorMessage && (
          <div className="-mx-3 mb-4 border-b border-gray-800 bg-gray-950 px-3 py-3 sm:-mx-4 sm:px-4">
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

        {isLoading && (
          <div className="space-y-4">
            <div className="h-[70vh] rounded-3xl border border-gray-800 bg-gray-900 animate-pulse" />
            <div className="h-[70vh] rounded-3xl border border-gray-800 bg-gray-900 animate-pulse" />
          </div>
        )}

        {!isLoading && errorMessage && (
          <div className="rounded-2xl border border-red-900 bg-red-950/40 p-5">
            <p className="font-semibold text-red-200">Error</p>
            <p className="mt-2 text-red-100 break-words">{errorMessage}</p>
          </div>
        )}

        {!isLoading && !errorMessage && publicaciones.length === 0 && (
          <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6 text-center">
            <p className="font-semibold text-gray-200">No hay publicaciones</p>
            <p className="mt-2 text-sm text-gray-400">
              Cuando existan publicaciones activas, aparecerán acá.
            </p>
          </div>
        )}

        {!isLoading && !errorMessage && publicaciones.length > 0 && (
          <section className="space-y-6">
            {publicaciones.map((p) => (
              <article
                key={p.id}
                className="
                  min-h-[72vh]
                  scroll-mt-24
                  rounded-3xl
                  border
                  border-gray-800
                  bg-gray-900
                  shadow-xl
                  overflow-hidden
                "
              >
                <PublicacionCard
                  pub={p}
                  isActingLike={Boolean(likeLocksMemo[p.id])}
                  isActingSave={Boolean(saveLocksMemo[p.id])}
                  onToggleLike={() => handleToggleLike(p.id)}
                  onToggleSave={() => handleToggleSave(p.id)}
                  compactActions={true}
                />
              </article>
            ))}
          </section>
        )}
      </main>

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
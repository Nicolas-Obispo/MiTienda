/**
 * FeedPage.jsx
 * ----------------
 * ETAPA 58: Feed híbrido recomendado
 * - Home / Feed: scroll vertical tipo reels
 * - Explorar: mantiene grid de discovery
 * - Backend sigue siendo fuente de verdad
 */

import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { PublicacionCard } from "@features/posts";
import { HistoriasBar } from "@features/stories";
import { HistoriasViewer } from "@features/stories";
import { getMediaUrlFromAny } from "@shared";
import { useFeedPublicaciones } from "@features/feed/hooks/useFeedPublicaciones";

import {
  optimisticToggleGuardado,
  optimisticToggleLike,
  useSocialInteractions,
  useToggleLikePublicacionMutation,
  useToggleGuardadoPublicacionMutation,
} from "@features/social";

import { fetchPublicacionesGuardadas } from "@features/posts";

import {
  fetchHistoriasPorComercio,
  fetchHistoriasBarItems,
  marcarHistoriaVista,
} from "@features/stories";

export default function FeedPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const {
    data: feedData = [],
    isLoading: isFeedLoading,
    error: feedQueryError,
  } = useFeedPublicaciones();

  const [isLoading, setIsLoading] = useState(true);
  const [publicaciones, setPublicaciones] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");

  const [historiasItems, setHistoriasItems] = useState([]);
  const [historiasErrorMessage, setHistoriasErrorMessage] = useState("");

  const [viewerIsOpen, setViewerIsOpen] = useState(false);
  const [viewerTitulo, setViewerTitulo] = useState("Historias");
  const [viewerHistorias, setViewerHistorias] = useState([]);
  const [showWelcomeModal, setShowWelcomeModal] = useState(false);

  const ultimaHistoriaVistaMarcadaRef = useRef(null);
  const historiasPendientesRef = useRef(new Set());
  const viewerComercioIdRef = useRef(null);
  const historiasOrdenRef = useRef([]);

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

  async function cerrarViewer() {
    await loadHistoriasBar();

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

  useEffect(() => {
    loadHistoriasBar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function preloadHistoriasImages(historias, max = 10) {
    if (!Array.isArray(historias) || historias.length === 0) return;

    const urls = [];

    for (const h of historias) {
      const url = getMediaUrlFromAny(h);
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
    // IMPORTANTE:
    // No refrescar mientras el viewer está abierto,
    // porque cambia el orden/estado de historias
    // y rompe la navegación automática.

    if (viewerIsOpen) return;

    await loadHistoriasBar();
  }

  async function loadFeed() {
    try {
      setErrorMessage("");

      if (feedQueryError) {
        throw feedQueryError;
      }

      const feedItems = Array.isArray(feedData)
        ? feedData
        : feedData?.items || [];

      const guardadasData = await fetchPublicacionesGuardadas();

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
      setIsLoading(false);
    } catch (error) {
      setErrorMessage(error?.message || "Error desconocido cargando el feed.");
      setPublicaciones([]);
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (isFeedLoading) return;

    loadFeed();

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isFeedLoading, feedQueryError]);


  useEffect(() => {
    if (feedQueryError) {
      setErrorMessage(
        feedQueryError?.message || "Error desconocido cargando el feed."
      );
      setIsLoading(false);
      return;
    }

    if (isFeedLoading && publicaciones.length === 0) {
      setIsLoading(true);
      return;
    }

    if (!isFeedLoading && publicaciones.length > 0) {
      setIsLoading(false);
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isFeedLoading, feedQueryError]);

  useEffect(() => {
    const shouldShowWelcome =
      sessionStorage.getItem("show_miplaza_welcome") === "true";

    if (shouldShowWelcome) {
      setShowWelcomeModal(true);
      sessionStorage.removeItem("show_miplaza_welcome");
    }
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
    } catch {
      cerrarViewer();
    }
  }

  async function abrirAnteriorComercioHistorias() {
    try {
      const orden = historiasOrdenRef.current || [];
      const actualId = viewerComercioIdRef.current;

      if (!actualId || orden.length === 0) {
        return;
      }

      const idx = orden.findIndex((x) => x.comercioId === actualId);
      const prev = idx > 0 ? orden[idx - 1] : null;

      if (!prev) {
        return;
      }

      const prevId = prev.comercioId;
      const prevTitulo = prev.nombre || `Comercio ${prevId}`;

      const historias = await fetchHistoriasPorComercio(prevId);
      const list = Array.isArray(historias) ? historias : [];

      if (list.length === 0) {
        viewerComercioIdRef.current = prevId;
        return abrirAnteriorComercioHistorias();
      }

      preloadHistoriasImages(list, 3);

      viewerComercioIdRef.current = prevId;
      setViewerTitulo(prevTitulo);
      setViewerHistorias(list);
      setViewerIsOpen(true);
    } catch {
      // silencioso
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

    } catch {
      navigate(`/comercios/${comercioId}`);
    }
  }

  async function handleToggleLike(pubId) {
    if (isLikeLocked(pubId)) return;

    setLikeLock(pubId, true);
    const snapshot = publicaciones;

    setPublicaciones((prev) => optimisticToggleLike(prev, pubId));

    try {
      await toggleLikeMutation.mutateAsync(pubId);
    } catch (error) {
      setErrorMessage(error?.message || "Error al togglear like.");
    } finally {
      setLikeLock(pubId, false);
    }
  }

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
      setErrorMessage(error?.message || "Error al guardar/quitar guardado.");
    } finally {
      setSaveLock(pubId, false);
    }
  }

  async function handleHistoriaVisible(historiaId) {
    if (typeof historiaId !== "number") return;

    if (ultimaHistoriaVistaMarcadaRef.current === historiaId) return;

    ultimaHistoriaVistaMarcadaRef.current = historiaId;

    // Evita requests duplicados simultáneos
    if (historiasPendientesRef.current.has(historiaId)) return;

    historiasPendientesRef.current.add(historiaId);

    try {
      await marcarHistoriaVista(historiaId);
    } catch {
      // silencioso
    } finally {
      historiasPendientesRef.current.delete(historiaId);
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

        {!isLoading && !isFeedLoading && !errorMessage && publicaciones.length === 0 && (
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
                  isActingLike={Boolean(likeLocks[p.id])}
                  isActingSave={Boolean(saveLocks[p.id])}
                  onToggleLike={() => handleToggleLike(p.id)}
                  onToggleSave={() => handleToggleSave(p.id)}
                  compactActions={true}
                />
              </article>
            ))}
          </section>
        )}
      </main>

        {showWelcomeModal && (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 px-4 backdrop-blur-sm">
      <div className="w-full max-w-md overflow-hidden rounded-3xl border border-orange-500/30 bg-gray-950 shadow-2xl">
        
    {/* Header visual */}
    <div className="relative overflow-hidden bg-gradient-to-br from-orange-500 via-orange-400 to-amber-300 px-6 py-8 text-center">
        <div className="absolute inset-0 opacity-10">
          <div className="h-full w-full bg-[radial-gradient(circle_at_top_right,white,transparent_45%)]" />
        </div>

      <h2
        className="
          relative
          -mt-3
          text-5xl
          font-black
          tracking-tight
          text-white
          drop-shadow-lg
        "
      style={{
        fontFamily: "'Nunito', sans-serif",
        fontWeight: 900,
      }}
      >
        ¡Bienvenido!
      </h2>

      <div className="mt-4 relative mx-auto flex h58 w-58 items-center justify-center overflow-hidden rounded-full bg-gray-950 ring-4 ring-white/40 shadow-4xl">
        <img
          src="/logo_Feedgo.png"
          alt="MiPlaza"
          className="h-full w-full object-contain p-5"
        />
      </div>

    </div>

      {/* Contenido */}
      <div className="px-6 py-6 text-center">
        <p
          className="
            relative
            -mt-3
            text-2xl
            font-black
            tracking-tight
            text-white
            drop-shadow-lg
          "
          style={{
            fontFamily: "'Nunito', sans-serif",
            fontWeight: 800,
          }}
        >
          Tu vidriera digital
        </p>

          <p className="mt-2 text-sm leading-7 text-gray-300">
            Descubrí comercios, servicios profesionales y espacios cerca tuyo.
          </p>

          <p className="mt-3 text-sm leading-7 text-gray-400">
            Explorá publicaciones, mirá historias, guardá lo que te interesa,
            seguí espacios y encontrá nuevas oportunidades en tu ciudad.
          </p>

          <div className="mt-6 rounded-2xl border border-amber-300/20 bg-amber-200/10 p-4 backdrop-blur-sm">
            <p className="text-sm text-orange-200">
              MiPlaza no solo conecta personas, negocios y oportunidades en un solo lugar.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setShowWelcomeModal(false)}
            className="
              mt-7
              w-full
              rounded-2xl
              bg-gradient-to-r
              from-orange-500
              via-orange-400
              to-amber-300
              px-4
              py-3
              text-sm
              font-black
              text-white
              shadow-xl
              transition
              hover:scale-[1.02]
              hover:opacity-95
              active:scale-[0.99]
            "
          >
            Empezar a explorar
          </button>
        </div>
      </div>
    </div>
  )}

      <HistoriasViewer
        isOpen={viewerIsOpen}
        onClose={cerrarViewer}
        onEnd={abrirSiguienteComercioHistorias}
        onPrevious={abrirAnteriorComercioHistorias}
        onHistoriaVisible={handleHistoriaVisible}
        historias={viewerHistorias}
        titulo={viewerTitulo}
      />
    </div>
  );
}




















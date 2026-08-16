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
import { ActiveLayer } from "@core";

import { PublicacionCard } from "@features/posts";
import { HistoriasBar } from "@features/stories";
import { HistoriasViewer } from "@features/stories";
import { Alert, Button, getMediaUrlFromAny, Skeleton, Surface } from "@shared";
import { useFeedPublicaciones } from "@features/feed/hooks/useFeedPublicaciones";

import {
  optimisticToggleGuardado,
  optimisticToggleLike,
  useSocialInteractions,
  useToggleLikePublicacionMutation,
  useToggleGuardadoPublicacionMutation,
} from "@features/social";

import { usePublicacionesGuardadas } from "@features/posts";

import {
  collectStoryImageUrls,
  fetchHistoriasPorComercio,
  marcarHistoriaVista,
  useHistoriasBar,
} from "@features/stories";

export default function FeedPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const {
    data: feedData = [],
    isLoading: isFeedLoading,
    error: feedQueryError,
  } = useFeedPublicaciones();

  const {
    data: guardadasData = [],
  } = usePublicacionesGuardadas();

  const {
    data: historiasItems = [],
    isLoading: isHistoriasBarLoading,
    error: historiasBarError,
    refetch: refetchHistoriasBar,
  } = useHistoriasBar();

  const [isLoading, setIsLoading] = useState(true);
  const [feedHydratado, setFeedHydratado] = useState(false);
  const [publicaciones, setPublicaciones] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");
  const historiasErrorMessage = historiasBarError
    ? historiasBarError.message || "Error desconocido cargando historias."
    : "";

  const [viewerIsOpen, setViewerIsOpen] = useState(false);
  const [viewerTitulo, setViewerTitulo] = useState("Historias");
  const [viewerHistorias, setViewerHistorias] = useState([]);
  const [showWelcomeModal, setShowWelcomeModal] = useState(false);

  const ultimaHistoriaVistaMarcadaRef = useRef(null);
  const historiasPendientesRef = useRef(new Set());
  const viewerComercioIdRef = useRef(null);
  const historiasOrdenRef = useRef([]);
  const historiasPorComercioRef = useRef({});
  const huboVistasNuevasRef = useRef(false);
  const welcomeActionRef = useRef(null);

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
    if (huboVistasNuevasRef.current) {
      await refetchHistoriasBar();
    }

    setViewerIsOpen(false);
    setViewerHistorias([]);
    setViewerTitulo("Historias");
    ultimaHistoriaVistaMarcadaRef.current = null;
    viewerComercioIdRef.current = null;
    huboVistasNuevasRef.current = false;
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

    const urls = collectStoryImageUrls(historias, getMediaUrlFromAny, max);

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

  async function getHistoriasDeComercio(comercioId) {
    const cache = historiasPorComercioRef.current;

    if (Array.isArray(cache[comercioId])) {
      return cache[comercioId];
    }

    const historias = await fetchHistoriasPorComercio(comercioId);
    const list = Array.isArray(historias) ? historias : [];

    if (list.length > 0) {
      cache[comercioId] = list;
    }

    return list;
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
      setFeedHydratado(true);
      setIsLoading(false);
    } catch (error) {
      setErrorMessage(error?.message || "Error desconocido cargando el feed.");
      setFeedHydratado(true);
      setIsLoading(false);
    }
  }

  useEffect(() => {
    const feedItems = Array.isArray(feedData)
      ? feedData
      : feedData?.items || [];

    if (feedItems.length > 0 && publicaciones.length === 0) {
      setPublicaciones(feedItems);
      setIsLoading(false);
    }

    if (isFeedLoading && publicaciones.length === 0 && feedItems.length === 0) {
      return;
    }

    loadFeed();

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [feedData, guardadasData, isFeedLoading, feedQueryError]);


  useEffect(() => {
    if (feedQueryError) {
      setErrorMessage(
        feedQueryError?.message || "Error desconocido cargando el feed."
      );
      setIsLoading(false);
      return;
    }

    setIsLoading(!feedHydratado && publicaciones.length === 0);

  }, [feedHydratado, isFeedLoading, feedQueryError, publicaciones.length]);

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

      const list = await getHistoriasDeComercio(nextId);

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

      const list = await getHistoriasDeComercio(prevId);

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

      const list = await getHistoriasDeComercio(comercioId);

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
      huboVistasNuevasRef.current = true;
    } catch {
      // silencioso
    } finally {
      historiasPendientesRef.current.delete(historiaId);
    }
  }

  function handleHistoriaDeleted(historiaId) {
    const comercioId = viewerComercioIdRef.current;

    setViewerHistorias((prev) =>
      prev.filter((historia) => historia.id !== historiaId)
    );

    if (comercioId && Array.isArray(historiasPorComercioRef.current[comercioId])) {
      historiasPorComercioRef.current[comercioId] =
        historiasPorComercioRef.current[comercioId].filter(
          (historia) => historia.id !== historiaId
        );
    }
  }

  return (
    <div className="min-h-screen bg-canvas text-primary">
      <main className="mx-auto max-w-2xl px-3 py-4 sm:px-4 sm:py-6">
        {!isLoading &&
          !errorMessage &&
          !(isHistoriasBarLoading && historiasItems.length === 0) && (
          <div className="-mx-3 mb-4 border-b border-border bg-surface px-3 py-3 sm:-mx-4 sm:px-4">
            <HistoriasBar
              items={historiasItems}
              onClickComercio={handleClickHistoriaComercio}
            />

            {historiasErrorMessage ? (
              <Alert variant="warning" role="status" className="mt-2 text-sm">
                {historiasErrorMessage}
              </Alert>
            ) : null}
          </div>
        )}

        {isLoading && publicaciones.length === 0 && (
          <div className="space-y-4">
            <Skeleton className="h-[70vh] rounded-3xl border border-border" />
            <Skeleton className="h-[70vh] rounded-3xl border border-border" />
          </div>
        )}

        {!isLoading && errorMessage && (
          <Alert variant="danger" role="alert" className="p-5">
            <p className="font-semibold">Error</p>
            <p className="mt-2 break-words">{errorMessage}</p>
          </Alert>
        )}

        {feedHydratado && !isLoading && !isFeedLoading && !errorMessage && publicaciones.length === 0 && (
          <Surface variant="subtle" className="p-6 text-center">
            <p className="font-semibold">No hay publicaciones</p>
            <p className="mt-2 text-sm text-secondary">
              Cuando existan publicaciones activas, aparecerán acá.
            </p>
          </Surface>
        )}

        {!isLoading && !errorMessage && publicaciones.length > 0 && (
          <section className="space-y-6">
            {publicaciones.map((p) => (
              <Surface
                key={p.id}
                variant="elevated"
                className="
                  min-h-[72vh]
                  scroll-mt-24
                  rounded-3xl
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
              </Surface>
            ))}
          </section>
        )}
      </main>

        {showWelcomeModal && (
    <ActiveLayer
      onClose={() => setShowWelcomeModal(false)}
      labelledBy="feed-welcome-title"
      describedBy="feed-welcome-description"
      initialFocusRef={welcomeActionRef}
      closeOnBackdrop={false}
      closeOnEscape={false}
      className="px-4"
      backdropClassName="bg-overlay-backdrop backdrop-blur-sm"
      contentClassName="w-full max-w-md"
      zIndex={200}
    >
      <Surface variant="elevated" className="max-h-[calc(100dvh-2rem)] overflow-y-auto rounded-3xl">
        
    {/* Header visual */}
    <div className="relative overflow-hidden bg-interactive-primary px-6 py-8 text-center text-interactive-on-primary">

      <h2
        id="feed-welcome-title"
        className="
          relative
          -mt-3
          text-5xl
          font-black
          tracking-tight
          drop-shadow-lg
        "
      style={{
        fontFamily: "'Nunito', sans-serif",
        fontWeight: 900,
      }}
      >
        ¡Bienvenido!
      </h2>

      <div className="relative mx-auto mt-4 flex h-58 w-58 items-center justify-center overflow-hidden rounded-full bg-canvas ring-4 ring-interactive-on-primary shadow-2xl">
        <img
          src="/logo_Feedgo.png"
          alt="FeedGo"
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
            drop-shadow-lg
          "
          style={{
            fontFamily: "'Nunito', sans-serif",
            fontWeight: 800,
          }}
        >
          Tu vidriera digital
        </p>

          <p id="feed-welcome-description" className="mt-2 text-sm leading-7 text-secondary">
            Descubrí comercios, servicios profesionales y espacios cerca tuyo.
          </p>

          <p className="mt-3 text-sm leading-7 text-muted">
            Explorá publicaciones, mirá historias, guardá lo que te interesa,
            seguí espacios y encontrá nuevas oportunidades en tu ciudad.
          </p>

          <Surface variant="subtle" className="mt-6 p-4">
            <p className="text-sm text-brand">
              MiPlaza no solo conecta personas, negocios y oportunidades en un solo lugar.
            </p>
          </Surface>

          <Button
            ref={welcomeActionRef}
            type="button"
            onClick={() => setShowWelcomeModal(false)}
            variant="primary"
            className="mt-7 text-sm font-black leading-5"
          >
            Empezar a explorar
          </Button>
        </div>
      </Surface>
    </ActiveLayer>
  )}

      <HistoriasViewer
        isOpen={viewerIsOpen}
        onClose={cerrarViewer}
        onEnd={abrirSiguienteComercioHistorias}
        onPrevious={abrirAnteriorComercioHistorias}
        onHistoriaVisible={handleHistoriaVisible}
        onHistoriaDeleted={handleHistoriaDeleted}
        historias={viewerHistorias}
        titulo={viewerTitulo}
      />
    </div>
  );
}












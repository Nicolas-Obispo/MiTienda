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
import { getMediaUrlFromAny } from "../utils/mediaUrl";

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
  const [showWelcomeModal, setShowWelcomeModal] = useState(false);

  const ultimaHistoriaVistaMarcadaRef = useRef(null);
  const historiasPendientesRef = useRef(new Set());
  const viewerComercioIdRef = useRef(null);
  const historiasOrdenRef = useRef([]);

  const [likeLocks, setLikeLocks] = useState({});
  const [saveLocks, setSaveLocks] = useState({});

  const likeLocksMemo = useMemo(() => likeLocks, [likeLocks]);
  const saveLocksMemo = useMemo(() => saveLocks, [saveLocks]);

  function setLock(setter, pubId, value) {
    setter((prev) => ({ ...prev, [pubId]: value }));
  }

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

      // Cargamos historias aparte, sin frenar el Feed.
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

    const shouldShowWelcome =
      sessionStorage.getItem("show_miplaza_welcome") === "true";

    if (shouldShowWelcome) {
      setShowWelcomeModal(true);
      sessionStorage.removeItem("show_miplaza_welcome");
    }

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
          src="/logo_miplaza.png"
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
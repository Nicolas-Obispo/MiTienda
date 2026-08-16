import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { Trash2 } from "lucide-react";
import { ActiveLayer } from "@core";
import { Button, Surface, getMediaUrlFromAny } from "@shared";
import {
  toggleLikeHistoria,
  useEliminarHistoriaMutation,
} from "@features/stories";
import DenunciaModal from "@features/moderation/components/DenunciaModal";
import { RECURSO_DENUNCIA_HISTORIA } from "@features/moderation/constants/denuncias";
import {
  isStoryVideoUrl,
  pauseStoryVideo,
  playStoryVideo,
} from "./storyMediaLifecycle";
import { reconcileStoryDeletion } from "./storyDeletionState";
import "./HistoriasViewer.css";

const DURACION_MS_DEFAULT = 4500;

export default function HistoriasViewer({
  isOpen,
  onClose,
  onEnd,
  onPrevious,
  onHistoriaVisible,
  onHistoriaDeleted,
  historias,
  titulo,
}) {
  const historiasList = useMemo(
    () => (Array.isArray(historias) ? historias : []),
    [historias]
  );

  const [indexActual, setIndexActual] = useState(0);
  const [progreso, setProgreso] = useState(0);
  const [mediaLista, setMediaLista] = useState(false);
  const [cycleKey, setCycleKey] = useState(0);

  const [likedByMe, setLikedByMe] = useState(false);
  const [isLikingHistoria, setIsLikingHistoria] = useState(false);
  const [showFlyingHeart, setShowFlyingHeart] = useState(false);
  const [isDenunciaOpen, setIsDenunciaOpen] = useState(false);
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
  const [deleteError, setDeleteError] = useState("");

  const imgRef = useRef(null);
  const videoRef = useRef(null);
  const rafRef = useRef(null);
  const startTimeRef = useRef(null);
  const runIdRef = useRef(0);
  const errorAdvanceTimeoutRef = useRef(null);
  const startedVideoRef = useRef(null);
  const advanceLockedRef = useRef(false);
  const deletionTransitionRef = useRef(null);
  const eliminarHistoriaMutation = useEliminarHistoriaMutation();

  const limpiarRaf = useCallback(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  const limpiarErrorAdvanceTimeout = useCallback(() => {
    if (errorAdvanceTimeoutRef.current !== null) {
      clearTimeout(errorAdvanceTimeoutRef.current);
      errorAdvanceTimeoutRef.current = null;
    }
  }, []);

  const pausarVideoActivo = useCallback(() => {
    pauseStoryVideo(videoRef.current);
  }, []);

  const cerrarViewer = useCallback(() => {
    pausarVideoActivo();
    limpiarErrorAdvanceTimeout();
    limpiarRaf();
    onClose?.();
  }, [limpiarErrorAdvanceTimeout, limpiarRaf, onClose, pausarVideoActivo]);

  const finalizarGrupo = useCallback(() => {
    // ✅ Si hay onEnd, delegamos al padre (FeedPage) para pasar al próximo comercio
    if (typeof onEnd === "function") {
      limpiarRaf();
      onEnd();
      return;
    }
    // fallback: si no hay onEnd, cerramos como antes
    cerrarViewer();
  }, [onEnd, limpiarRaf, cerrarViewer]);

  const irSiguiente = useCallback(() => {
    if (!isOpen) return;
    if (historiasList.length === 0) return;
    if (advanceLockedRef.current) return;

    advanceLockedRef.current = true;
    pausarVideoActivo();
    limpiarErrorAdvanceTimeout();

    setIndexActual((prev) => {
      if (prev >= historiasList.length - 1) {
        // ✅ en vez de cerrar, avisamos que terminó el grupo
        setTimeout(() => finalizarGrupo(), 0);
        return prev;
      }
      return prev + 1;
    });
  }, [
    isOpen,
    historiasList.length,
    finalizarGrupo,
    limpiarErrorAdvanceTimeout,
    pausarVideoActivo,
  ]);

  const irAnterior = useCallback(() => {
    if (!isOpen) return;
    if (historiasList.length === 0) return;

    pausarVideoActivo();
    limpiarErrorAdvanceTimeout();
    advanceLockedRef.current = false;

    setIndexActual((prev) => {
      if (prev <= 0) {
        if (typeof onPrevious === "function") {
          setTimeout(() => onPrevious(), 0);
        }

        return prev;
      }

      return prev - 1;
    });
  }, [
    isOpen,
    historiasList.length,
    onPrevious,
    limpiarErrorAdvanceTimeout,
    pausarVideoActivo,
  ]);

  const programarAvancePorError = useCallback(() => {
    limpiarErrorAdvanceTimeout();
    const expectedRun = runIdRef.current;
    errorAdvanceTimeoutRef.current = setTimeout(() => {
      errorAdvanceTimeoutRef.current = null;
      if (runIdRef.current === expectedRun) irSiguiente();
    }, 120);
  }, [irSiguiente, limpiarErrorAdvanceTimeout]);

  // Reset fuerte al abrir
  useEffect(() => {
    if (!isOpen) return;

    setCycleKey((k) => k + 1);
    const deletionTransition = deletionTransitionRef.current;
    if (
      deletionTransition &&
      !historiasList.some((historia) => historia.id === deletionTransition.id)
    ) {
      setIndexActual(deletionTransition.nextIndex);
      deletionTransitionRef.current = null;
    } else {
      setIndexActual(0);
    }
    setProgreso(0);
    setMediaLista(false);

    startTimeRef.current = null;
    runIdRef.current += 1;
    advanceLockedRef.current = false;
    startedVideoRef.current = null;
    limpiarErrorAdvanceTimeout();
    limpiarRaf();

    return () => {
      pausarVideoActivo();
      limpiarErrorAdvanceTimeout();
      runIdRef.current += 1;
      limpiarRaf();
    };
  }, [
    isOpen,
    historiasList,
    limpiarErrorAdvanceTimeout,
    limpiarRaf,
    pausarVideoActivo,
  ]);

  // Si abre sin historias -> cerrar
  useEffect(() => {
    if (!isOpen) return;
    if (historiasList.length > 0) return;

    const t = setTimeout(() => onClose?.(), 0);
    return () => clearTimeout(t);
  }, [isOpen, historiasList.length, onClose]);

  // Al cambiar historia: reset y esperar load
  useEffect(() => {
    if (!isOpen) return;
    if (historiasList.length === 0) return;

    setProgreso(0);
    setMediaLista(false);
    startTimeRef.current = null;
    advanceLockedRef.current = false;
    startedVideoRef.current = null;

    runIdRef.current += 1;
    limpiarErrorAdvanceTimeout();
    limpiarRaf();
  }, [
    isOpen,
    indexActual,
    historiasList.length,
    limpiarErrorAdvanceTimeout,
    limpiarRaf,
  ]);

  const historiaActual = historiasList[indexActual];
  const historiaMediaUrl = getMediaUrlFromAny(historiaActual);
  useEffect(() => {
    if (!isOpen) return;
    if (!historiaActual?.id) return;

    onHistoriaVisible?.(historiaActual.id);
  }, [isOpen, historiaActual?.id, onHistoriaVisible]);

  const historiaEsVideo = isStoryVideoUrl(historiaMediaUrl);

  useEffect(() => {
  setLikedByMe(Boolean(historiaActual?.liked_by_me));
  setShowFlyingHeart(false);
  }, [historiaActual]);

  useEffect(() => {
    if (!isOpen) return;
    if (!historiaMediaUrl) return;

    const t = setTimeout(() => {
      const el = imgRef.current;
      if (el && el.complete && el.naturalWidth > 0) {
        setMediaLista(true);
      }
    }, 0);

    return () => clearTimeout(t);
  }, [isOpen, historiaMediaUrl, cycleKey, indexActual]);

  useEffect(() => {
    if (!isOpen) {
      pausarVideoActivo();
      limpiarErrorAdvanceTimeout();
      return undefined;
    }

    const handleVisibilityChange = () => {
      const video = videoRef.current;
      if (document.hidden) {
        pauseStoryVideo(video);
        return;
      }

      if (video && mediaLista && startedVideoRef.current === video) {
        playStoryVideo(video, document);
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [isOpen, mediaLista, limpiarErrorAdvanceTimeout, pausarVideoActivo]);

  useEffect(
    () => () => {
      pausarVideoActivo();
      limpiarErrorAdvanceTimeout();
    },
    [limpiarErrorAdvanceTimeout, pausarVideoActivo]
  );

  // Timer RAF: solo cuando mediaLista=true
  useEffect(() => {
    if (!isOpen) return;
    if (historiasList.length === 0) return;
    if (!mediaLista) return;
    if (isDenunciaOpen || isDeleteConfirmOpen) return;

    const myRun = ++runIdRef.current;

    limpiarRaf();
    startTimeRef.current = null;

    const tick = (ts) => {
      if (runIdRef.current !== myRun) return;

      if (!startTimeRef.current) startTimeRef.current = ts;

      const elapsed = ts - startTimeRef.current;
      const p = Math.min(1, elapsed / DURACION_MS_DEFAULT);

      setProgreso(p);

      if (p >= 1) {
        irSiguiente();
        return;
      }

      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);

    return () => {
      if (runIdRef.current === myRun) runIdRef.current += 1;
      limpiarRaf();
    };
  }, [
    isOpen,
    historiasList.length,
    mediaLista,
    isDenunciaOpen,
    isDeleteConfirmOpen,
    limpiarRaf,
    irSiguiente,
  ]);

  // Teclado
  useEffect(() => {
    if (!isOpen) return;

    const onKeyDown = (e) => {
      if (isDenunciaOpen || isDeleteConfirmOpen) return;

      if (e.key === "Escape") cerrarViewer();
      if (e.key === "ArrowLeft") irAnterior();
      if (e.key === "ArrowRight") irSiguiente();
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [
    isOpen,
    isDenunciaOpen,
    isDeleteConfirmOpen,
    cerrarViewer,
    irAnterior,
    irSiguiente,
  ]);

  if (!isOpen) return null;
  if (historiasList.length === 0) return null;

  const getBarValue = (i) => {
    if (i < indexActual) return 1;
    if (i === indexActual) return progreso;
    return 0;
  };

  async function handleToggleLikeHistoria(e) {
    e.preventDefault();
    e.stopPropagation();

    if (!historiaActual?.id) return;
    if (isLikingHistoria) return;

    const snapshotLiked = likedByMe;

    try {
      setIsLikingHistoria(true);

    const nextLiked = !likedByMe;

    if (nextLiked) {
      setShowFlyingHeart(true);

      setTimeout(() => {
        setShowFlyingHeart(false);
      }, 900);
    }

    setLikedByMe(nextLiked);

      const data = await toggleLikeHistoria(historiaActual.id);

      setLikedByMe(Boolean(data?.liked));
    } catch {
      setLikedByMe(snapshotLiked);
    } finally {
      setIsLikingHistoria(false);
    }
  }

  function handleOpenDeleteConfirmation(event) {
    event.preventDefault();
    event.stopPropagation();
    if (!historiaActual?.puede_administrar) return;

    setDeleteError("");
    setIsDeleteConfirmOpen(true);
  }

  function handleCloseDeleteConfirmation() {
    if (eliminarHistoriaMutation.isPending) return;
    setIsDeleteConfirmOpen(false);
    setDeleteError("");
  }

  async function handleConfirmDelete() {
    const historiaId = historiaActual?.id;
    const comercioId = historiaActual?.comercio_id;
    if (!historiaId || !comercioId || eliminarHistoriaMutation.isPending) return;

    const deletionState = reconcileStoryDeletion(
      historiasList,
      indexActual,
      historiaId
    );
    if (!deletionState.shouldClose) {
      deletionTransitionRef.current = {
        id: historiaId,
        nextIndex: deletionState.nextIndex,
      };
    }

    try {
      setDeleteError("");
      await eliminarHistoriaMutation.mutateAsync({ historiaId, comercioId });

      pausarVideoActivo();
      limpiarErrorAdvanceTimeout();
      limpiarRaf();

      setIsDeleteConfirmOpen(false);
      onHistoriaDeleted?.(historiaId);

      if (deletionState.shouldClose && typeof onHistoriaDeleted !== "function") {
        cerrarViewer();
      }
    } catch (error) {
      deletionTransitionRef.current = null;
      setDeleteError(
        error?.publicMessage || error?.message || "No se pudo eliminar la historia."
      );
    }
  }

    const heartFlyAnimation = `
    @keyframes heartFly {
      0% {
        transform: translateY(0px) scale(1);
        opacity: 1;
      }

      15% {
        transform: translateY(0px) scale(1.18);
        opacity: 1;
      }

    100% {
      transform:
        translateX(-320px)
        translateY(340px)
        scale(0.22);

      opacity: 0;
    }
    `;

  return (
    <div
      className="historias-viewer-fixed fixed inset-0 z-50 bg-black"
      data-visual-contract="fixed-media"
    >
      <style>{heartFlyAnimation}</style>
      <div className="absolute inset-x-0 top-0 z-[100] p-3">
        <div className="flex gap-1">
          {historiasList.map((_, i) => (
            <div
              key={i}
              className="h-1 flex-1 rounded bg-white/25 overflow-hidden"
            >
              <div
                className="h-full bg-white"
                style={{ width: `${getBarValue(i) * 100}%` }}
              />
            </div>
          ))}
        </div>

        <div className="mt-3 flex items-center justify-between">
          <div className="min-w-0">
            <p className="text-sm font-semibold text-white truncate">
              {titulo || "Historias"}
            </p>
            <p className="text-xs text-white/70">
              {indexActual + 1} / {historiasList.length}
            </p>
          </div>

          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              setIsDenunciaOpen(true);
            }}
            className="relative z-[999] ml-3 rounded-full bg-white/10 px-3 py-1 text-sm text-white hover:bg-white/20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
          >
            Denunciar
          </button>

          {historiaActual?.puede_administrar ? (
            <button
              type="button"
              aria-label="Eliminar historia"
              title="Eliminar historia"
              onClick={handleOpenDeleteConfirmation}
              className="relative z-[999] ml-2 inline-flex h-8 w-8 items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              <Trash2 aria-hidden="true" size={17} />
            </button>
          ) : null}

          <button
            type="button"
            aria-label="Cerrar historias"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              cerrarViewer();
            }}
            className="relative z-[999] ml-2 rounded-full bg-white/10 px-3 py-1 text-sm text-white hover:bg-white/20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
          >
            ✕
          </button>
        </div>
      </div>

      <div className="absolute inset-0 z-10 flex items-center justify-center">
        {historiaMediaUrl ? (
          historiaEsVideo ? (
            <video
              ref={videoRef}
              key={`${cycleKey}-${indexActual}-${historiaMediaUrl}`}
              src={historiaMediaUrl}
              muted
              playsInline
              preload="metadata"
              className="h-full w-full object-contain"
              onLoadedMetadata={(event) => {
                const video = event.currentTarget;
                if (video === videoRef.current && startedVideoRef.current !== video) {
                  startedVideoRef.current = video;
                  video.currentTime = 0;
                  playStoryVideo(video, document).then((started) => {
                    if (video !== videoRef.current || startedVideoRef.current !== video) {
                      return;
                    }

                    if (started) {
                      setMediaLista(true);
                      return;
                    }

                    setMediaLista(false);
                    programarAvancePorError();
                  });
                }
              }}
              onLoadedData={(event) => {
                const video = event.currentTarget;
                if (video === videoRef.current && startedVideoRef.current === video) {
                  setMediaLista(true);
                }
              }}
              onEnded={irSiguiente}
              onError={() => {
                setMediaLista(false);
                programarAvancePorError();
              }}
            />
          ) : (
            <img
              ref={imgRef}
              key={`${cycleKey}-${indexActual}-${historiaMediaUrl}`}
              src={historiaMediaUrl}
              alt={`Historia ${historiaActual.id}`}
              decoding="async"
              className="h-full w-full object-contain"
              draggable="false"
              onLoad={() => setMediaLista(true)}
              onError={() => {
                setMediaLista(false);
                programarAvancePorError();
              }}
            />
          )
        ) : (
          <div className="text-white/70 text-sm">Historia sin media_url</div>
        )}
      </div>

      {/* Corazón animado */}
      {showFlyingHeart ? (
        <div className="pointer-events-none absolute inset-0 z-50 flex items-center justify-center">
          <div
            className="
              text-[20rem]
              leading-none
              drop-shadow-2xl
              animate-[heartFly_900ms_ease-in-out_forwards]
              motion-reduce:animate-none
            "
          >
            ❤️
          </div>
        </div>
      ) : !likedByMe ? (
        <div className="pointer-events-none absolute inset-0 z-40 flex items-center justify-center">
          <button
            type="button"
            aria-label="Me gusta"
            onClick={handleToggleLikeHistoria}
            className="group pointer-events-auto flex h-[20rem] w-[20rem] items-center justify-center rounded-full focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="rgba(255,255,255,0.72)"
              strokeWidth="0.25"
              className="
                h-[20rem]
                w-[20rem]
                cursor-pointer
                opacity-0
                transition
                duration-200
                group-hover:opacity-100
                drop-shadow-2xl
              "
              aria-hidden="true"
            >
              <path d="M12 20.5 C12 20.5, 3 14.5, 3 8.8 C3 5.8, 5.2 4, 8 4 C10 4, 11.2 5.1, 12 6.2 C12.8 5.1, 14 4, 16 4 C18.8 4, 21 5.8, 21 8.8 C21 14.5, 12 20.5, 12 20.5Z" />
            </svg>
          </button>
        </div>
      ) : null}

      {/* Like persistente abajo */}
      {likedByMe ? (
        <div className="absolute bottom-6 left-6 z-40">
          <button
            type="button"
            aria-label="Quitar me gusta"
            className="
              text-2xl
              drop-shadow-lg
              transition
              duration-200
              hover:scale-110
              active:scale-95
              focus-visible:outline
              focus-visible:outline-2
              focus-visible:outline-offset-2
              focus-visible:outline-white
            "
            onClick={handleToggleLikeHistoria}
          >
            ❤️
          </button>
        </div>
      ) : null}

      <div className="absolute inset-0 z-20 flex"></div>

      <div className="absolute inset-x-0 bottom-0 top-20 z-30 flex">
        <button
          type="button"
          className="group flex h-full w-1/2 items-center justify-start bg-transparent px-6 focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-white"
          onClick={irAnterior}
          aria-label="Historia anterior"
        >
          <span className="opacity-0 transition group-hover:opacity-80 text-5xl text-white">
            ‹
          </span>
        </button>

        <button
          type="button"
          className="group flex h-full w-1/2 items-center justify-end bg-transparent px-6 focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-white"
          onClick={irSiguiente}
          aria-label="Siguiente historia"
        >
          <span className="opacity-0 transition group-hover:opacity-80 text-5xl text-white">
            ›
          </span>
        </button>
      </div>
      <DenunciaModal
        isOpen={isDenunciaOpen}
        onClose={() => setIsDenunciaOpen(false)}
        recursoTipo={RECURSO_DENUNCIA_HISTORIA}
        recursoId={historiaActual?.id}
        titulo="Denunciar historia"
      />
      {isDeleteConfirmOpen ? (
        <ActiveLayer
          onClose={handleCloseDeleteConfirmation}
          closeOnBackdrop={!eliminarHistoriaMutation.isPending}
          closeOnEscape={!eliminarHistoriaMutation.isPending}
          labelledBy="eliminar-historia-title"
          contentClassName="mx-4 w-full max-w-sm"
        >
          <Surface variant="elevated" className="p-5">
            <p
              id="eliminar-historia-title"
              className="text-lg font-semibold text-primary"
            >
              Eliminar historia
            </p>
            <p className="mt-2 text-sm text-secondary">
              ¿Eliminar esta historia?
            </p>
            {deleteError ? (
              <p className="mt-3 text-sm text-danger" role="alert">
                {deleteError}
              </p>
            ) : null}
            <div className="mt-5 flex justify-end gap-3">
              <Button
                type="button"
                variant="secondary"
                onClick={handleCloseDeleteConfirmation}
                disabled={eliminarHistoriaMutation.isPending}
              >
                Cancelar
              </Button>
              <Button
                type="button"
                variant="danger"
                onClick={handleConfirmDelete}
                disabled={eliminarHistoriaMutation.isPending}
              >
                {eliminarHistoriaMutation.isPending ? "Eliminando..." : "Eliminar"}
              </Button>
            </div>
          </Surface>
        </ActiveLayer>
      ) : null}
    </div>
  );
}

import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { getMediaUrlFromAny } from "../utils/mediaUrl";
import { toggleLikeHistoria } from "../services/historias_service";

const DURACION_MS_DEFAULT = 4500;

export default function HistoriasViewer({
  isOpen,
  onClose,
  onEnd,
  onPrevious,
  onHistoriaVisible,
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

  const imgRef = useRef(null);
  const videoRef = useRef(null);
  const rafRef = useRef(null);
  const startTimeRef = useRef(null);
  const runIdRef = useRef(0);

  const limpiarRaf = useCallback(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  const cerrarViewer = useCallback(() => {
    limpiarRaf();
    onClose?.();
  }, [limpiarRaf, onClose]);

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

    setIndexActual((prev) => {
      if (prev >= historiasList.length - 1) {
        // ✅ en vez de cerrar, avisamos que terminó el grupo
        setTimeout(() => finalizarGrupo(), 0);
        return prev;
      }
      return prev + 1;
    });
  }, [isOpen, historiasList.length, finalizarGrupo]);

  const irAnterior = useCallback(() => {
    if (!isOpen) return;
    if (historiasList.length === 0) return;

    setIndexActual((prev) => {
      if (prev <= 0) {
        if (typeof onPrevious === "function") {
          setTimeout(() => onPrevious(), 0);
        }

        return prev;
      }

      return prev - 1;
    });
  }, [isOpen, historiasList.length, onPrevious]);

  // Reset fuerte al abrir
  useEffect(() => {
    if (!isOpen) return;

    setCycleKey((k) => k + 1);
    setIndexActual(0);
    setProgreso(0);
    setMediaLista(false);

    startTimeRef.current = null;
    runIdRef.current += 1;
    limpiarRaf();

    return () => {
      runIdRef.current += 1;
      limpiarRaf();
    };
  }, [isOpen, historiasList, limpiarRaf]);

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

    runIdRef.current += 1;
    limpiarRaf();
  }, [isOpen, indexActual, historiasList.length, limpiarRaf]);

  const historiaActual = historiasList[indexActual];
  const historiaMediaUrl = getMediaUrlFromAny(historiaActual);
  useEffect(() => {
    if (!isOpen) return;
    if (!historiaActual?.id) return;

    onHistoriaVisible?.(historiaActual.id);
  }, [isOpen, historiaActual?.id, onHistoriaVisible]);

    function esVideo(url) {
    if (!url || typeof url !== "string") return false;

    return [".mp4", ".webm", ".ogg", ".mov"].some((ext) =>
      url.toLowerCase().includes(ext)
    );
  }

  const historiaEsVideo = esVideo(historiaMediaUrl);

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

  // Timer RAF: solo cuando mediaLista=true
  useEffect(() => {
    if (!isOpen) return;
    if (historiasList.length === 0) return;
    if (!mediaLista) return;

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
  }, [isOpen, historiasList.length, mediaLista, limpiarRaf, irSiguiente]);

  // Teclado
  useEffect(() => {
    if (!isOpen) return;

    const onKeyDown = (e) => {
      if (e.key === "Escape") cerrarViewer();
      if (e.key === "ArrowLeft") irAnterior();
      if (e.key === "ArrowRight") irSiguiente();
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isOpen, cerrarViewer, irAnterior, irSiguiente]);

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
      setLikedByMe(false);
    } finally {
      setIsLikingHistoria(false);
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
    <div className="fixed inset-0 z-50 bg-black">
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
            onMouseDown={(e) => {
              e.preventDefault();
              e.stopPropagation();
              cerrarViewer();
            }}
            className="relative z-[999] ml-3 rounded-full bg-white/10 px-3 py-1 text-sm text-white hover:bg-white/20"
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
              autoPlay
              muted
              playsInline
              className="h-full w-full object-contain"
              onLoadedData={() => {
                setMediaLista(true);

                const video = videoRef.current;
                if (video) {
                  video.currentTime = 0;
                  video.play().catch(() => {});
                }
              }}
              onEnded={irSiguiente}
              onError={() => {
                setMediaLista(false);
                setTimeout(() => irSiguiente(), 120);
              }}
            />
          ) : (
            <img
              ref={imgRef}
              key={`${cycleKey}-${indexActual}-${historiaMediaUrl}`}
              src={historiaMediaUrl}
              alt={`Historia ${historiaActual.id}`}
              className="h-full w-full object-contain"
              draggable="false"
              onLoad={() => setMediaLista(true)}
              onError={() => {
                setMediaLista(false);
                setTimeout(() => irSiguiente(), 120);
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
            "
          >
            ❤️
          </div>
        </div>
      ) : !likedByMe ? (
        <div className="pointer-events-none absolute inset-0 z-40 flex items-center justify-center">
          <div className="group pointer-events-auto flex h-[20rem] w-[20rem] items-center justify-center">
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
              onClick={handleToggleLikeHistoria}
            >
              <path d="M12 20.5 C12 20.5, 3 14.5, 3 8.8 C3 5.8, 5.2 4, 8 4 C10 4, 11.2 5.1, 12 6.2 C12.8 5.1, 14 4, 16 4 C18.8 4, 21 5.8, 21 8.8 C21 14.5, 12 20.5, 12 20.5Z" />
            </svg>
          </div>
        </div>
      ) : null}

      {/* Like persistente abajo */}
      {likedByMe ? (
        <div className="absolute bottom-6 left-6 z-40">
          <button
            type="button"
            className="
              text-2xl
              drop-shadow-lg
              transition
              duration-200
              hover:scale-110
              active:scale-95
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
          className="group flex h-full w-1/2 items-center justify-start bg-transparent px-6 focus:outline-none"
          onClick={irAnterior}
          aria-label="Historia anterior"
        >
          <span className="opacity-0 transition group-hover:opacity-80 text-5xl text-white">
            ‹
          </span>
        </button>

        <button
          type="button"
          className="group flex h-full w-1/2 items-center justify-end bg-transparent px-6 focus:outline-none"
          onClick={irSiguiente}
          aria-label="Siguiente historia"
        >
          <span className="opacity-0 transition group-hover:opacity-80 text-5xl text-white">
            ›
          </span>
        </button>
      </div>
    </div>
  );
}

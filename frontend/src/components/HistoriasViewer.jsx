import { useEffect, useMemo, useRef, useState, useCallback } from "react";

const DURACION_MS_DEFAULT = 4500;

export default function HistoriasViewer({
  isOpen,
  onClose,
  onEnd, // ✅ NUEVO: se llama cuando termina la última historia
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

  const imgRef = useRef(null);
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
        setTimeout(() => cerrarViewer(), 0);
        return prev;
      }
      return prev - 1;
    });
  }, [isOpen, historiasList.length, cerrarViewer]);

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

  // Fix cache: si ya está cargada, activar mediaLista
  useEffect(() => {
    if (!isOpen) return;
    if (!historiaActual?.media_url) return;

    const t = setTimeout(() => {
      const el = imgRef.current;
      if (el && el.complete && el.naturalWidth > 0) {
        setMediaLista(true);
      }
    }, 0);

    return () => clearTimeout(t);
  }, [isOpen, historiaActual?.media_url, cycleKey, indexActual]);

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

  return (
    <div className="fixed inset-0 z-50 bg-black">
      <div className="absolute inset-x-0 top-0 z-30 p-3">
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
              {indexActual + 1} / {historiasList.length} • ID{" "}
              {historiaActual?.id ?? "-"}
            </p>
          </div>

          <button
            type="button"
            onClick={cerrarViewer}
            className="ml-3 rounded-full bg-white/10 px-3 py-1 text-sm text-white hover:bg-white/20"
          >
            ✕
          </button>
        </div>
      </div>

      <div className="absolute inset-0 z-10 flex items-center justify-center">
        {historiaActual?.media_url ? (
          <img
            ref={imgRef}
            key={`${cycleKey}-${indexActual}-${historiaActual.media_url}`}
            src={historiaActual.media_url}
            alt={`Historia ${historiaActual.id}`}
            className="h-full w-full object-contain"
            draggable="false"
            onLoad={() => setMediaLista(true)}
            onError={() => {
              setMediaLista(false);
              setTimeout(() => irSiguiente(), 120);
            }}
          />
        ) : (
          <div className="text-white/70 text-sm">Historia sin media_url</div>
        )}
      </div>

      <div className="absolute inset-0 z-20 flex">
        <button
          type="button"
          className="w-1/2 h-full bg-transparent focus:outline-none"
          onClick={irAnterior}
          aria-label="Historia anterior"
        />
        <button
          type="button"
          className="w-1/2 h-full bg-transparent focus:outline-none"
          onClick={irSiguiente}
          aria-label="Siguiente historia"
        />
      </div>
    </div>
  );
}

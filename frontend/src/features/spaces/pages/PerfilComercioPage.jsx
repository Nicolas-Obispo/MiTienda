/**
 * PerfilComercioPage.jsx
 * -----------------------
 * ETAPA 58
 * - Perfil de comercio mantiene vista tipo perfil/Instagram
 * - Publicaciones del comercio en cuadrícula
 * - Feed principal queda vertical, pero el comercio queda como galería
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ActiveLayer, useAnonymousDetailGate, useProtectedActionRedirect } from "@core";

import { PublicacionCard } from "@features/posts";
import { CrearHistoriaModal } from "@features/stories";
import { HistoriasViewer } from "@features/stories";
import {
  BarChart3,
  Camera,
  MapPin,
  MessageCircle,
  PlusCircle,
} from "lucide-react";
import {
  Alert,
  Button,
  Input,
  Skeleton,
  Surface,
  Textarea,
  getMediaUrlFromAny,
  uploadImagen,
} from "@shared";

import {
  optimisticToggleGuardado,
  optimisticToggleLike,
  useSocialInteractions,
  useToggleGuardadoPublicacionMutation,
  useToggleLikePublicacionMutation,
} from "@features/social";

import {
  crearPublicacionDeComercio,
  useComercioDetalle,
  useEstadoSeguimientoEspacio,
  usePublicacionesComercio,
  useToggleSeguimientoEspacioMutation,
} from "@features/spaces";

import {
  marcarHistoriaVista,
  useHistoriasComercio,
} from "@features/stories";

import {
  usePublicacionesGuardadas,
} from "@features/posts";

import {
  obtenerMetricasSocialesEspacio,
  obtenerComparacionMetricasSocialesEspacio,
} from "@features/spaces";

import {
  obtenerAnalyticsEspacio,
} from "@features/spaces";

import AgendaPrivadaModal from "@features/agenda/components/AgendaPrivadaModal";
import EstadoHorarioBadge from "@features/availability/components/EstadoHorarioBadge";
import DenunciaModal from "@features/moderation/components/DenunciaModal";
import { RECURSO_DENUNCIA_COMERCIO } from "@features/moderation/constants/denuncias";
import InteractiveLiquidLayers from "@shared/components/InteractiveLiquidLayers";

function puedeCargarMetricasPrivadas({
  comercioId,
  estaAutenticado,
  comercioResuelto,
  esPropietario,
  isEstadisticasOpen,
}) {
  return Boolean(
    comercioId &&
    !Number.isNaN(comercioId) &&
    estaAutenticado &&
    comercioResuelto &&
    esPropietario === true &&
    isEstadisticasOpen
  );
}

export default function CommerceProfilePage() {
  const { id } = useParams();
  const comercioId = Number(id);
  const navigate = useNavigate();
  const {
    estaAutenticado,
    requireAuthentication: usuarioDebeLoguearse,
  } = useProtectedActionRedirect();
  const [perfilHydratado, setPerfilHydratado] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [noticeMessage, setNoticeMessage] = useState("");

  const [comercio, setComercio] = useState(null);
  const [historias, setHistorias] = useState([]);
  const [viewerIsOpen, setViewerIsOpen] = useState(false);
  const [viewerHistorias, setViewerHistorias] = useState([]);
  const ultimaHistoriaVistaMarcadaRef = useRef(null);
  const [publicaciones, setPublicaciones] = useState([]);

  const openAnonymousDetailGate = useCallback(() => {
    usuarioDebeLoguearse(
      "Creá tu cuenta o iniciá sesión para seguir explorando este espacio."
    );
  }, [usuarioDebeLoguearse]);

  useAnonymousDetailGate({
    enabled: !estaAutenticado,
    ready: Boolean(comercio),
    onExpire: openAnonymousDetailGate,
  });

  const [isCrearHistoriaOpen, setIsCrearHistoriaOpen] = useState(false);
  const [isCrearPublicacionOpen, setIsCrearPublicacionOpen] = useState(false);
  const [isEstadisticasOpen, setIsEstadisticasOpen] = useState(false);
  const [agendaComercio, setAgendaComercio] = useState(null);
  const [isDenunciaComercioOpen, setIsDenunciaComercioOpen] = useState(false);

  const [publicacionForm, setPublicacionForm] = useState({
    titulo: "",
    descripcion: "",
    imagen_url: "",
  });

  const [imagenFile, setImagenFile] = useState(null);
  const [isCreatingPublicacion, setIsCreatingPublicacion] = useState(false);

  const {
    likeLocks,
    saveLocks,
    setLikeLock,
    setSaveLock,
    isLikeLocked,
    isSaveLocked,
  } = useSocialInteractions();

  const toggleLikeMutation = useToggleLikePublicacionMutation();
  const toggleGuardadoMutation = useToggleGuardadoPublicacionMutation();
  const token = getAccessToken();
  const comercioQuery = useComercioDetalle(comercioId);
  const publicacionesQuery = usePublicacionesComercio(comercioId);
  const historiasQuery = useHistoriasComercio(comercioId);
  const guardadasQuery = usePublicacionesGuardadas({
    enabled: Boolean(token),
  });

  const seguimientoQuery = useEstadoSeguimientoEspacio(comercioId, {
    enabled: estaAutenticado,
  });
  const toggleSeguimientoMutation = useToggleSeguimientoEspacioMutation({
    comercioId,
    comercio: comercioQuery.data,
  });

  const [metricasSociales, setMetricasSociales] = useState(null);
  const [comparacionMetricas, setComparacionMetricas] = useState(null);
  const [analyticsEspacio, setAnalyticsEspacio] = useState(null);

function esComercioMio(comercioData) {
    return Boolean(comercioData?.es_propietario);
  }

  const puedoCrearHistoria = esComercioMio(comercio);
  const comercioImagenUrl = getMediaUrlFromAny(comercio);

  function getAccessToken() {
    return localStorage.getItem("access_token");
  }

  function normalizarItems(data) {
    return Array.isArray(data) ? data : data?.items || [];
  }

  function mergePublicacionesConGuardadas(publicacionesData, guardadasData) {
    const pubs = normalizarItems(publicacionesData);
    const guardadasItems = normalizarItems(guardadasData);

    const guardadasSet = new Set(
      guardadasItems
        .map((g) => g?.id ?? g?.publicacion_id)
        .filter((pid) => typeof pid === "number")
    );

    return pubs.map((p) => ({
      ...p,
      guardada_by_me: Boolean(p.guardada_by_me) || guardadasSet.has(p.id),
    }));
  }

  async function loadDatosSecundarios(isCurrent = () => true) {
    if (!comercioId || Number.isNaN(comercioId)) {
      setErrorMessage("ID de comercio inválido.");
      return;
    }

    try {
      const accessToken = getAccessToken();

      if (!accessToken) return;

      const [metricasData, comparacionData, analyticsData] = await Promise.all([

        // ETAPA 62 — métricas sociales reales
          obtenerMetricasSocialesEspacio(comercioId),
          obtenerComparacionMetricasSocialesEspacio(comercioId),
          obtenerAnalyticsEspacio(comercioId),
      ]);

      if (!isCurrent()) return;

      // ETAPA 62
      setMetricasSociales(metricasData);
      setComparacionMetricas(comparacionData);
      setAnalyticsEspacio(analyticsData);
    } catch {
      // No bloqueamos el perfil si fallan métricas o analytics.
    }
  }

  async function refreshHistorias() {
    if (!comercioId || Number.isNaN(comercioId)) return;

    try {
      const { data: historiasData } = await historiasQuery.refetch();
      const hist = normalizarItems(historiasData);

      setHistorias(hist);
    } catch (error) {
      setErrorMessage(error.message || "Error refrescando historias.");
    }
  }

  async function refreshPublicaciones() {
    if (!comercioId || Number.isNaN(comercioId)) return;

    try {
      const accessToken = getAccessToken();

      const [publicacionesResult, guardadasResult] = await Promise.all([
        publicacionesQuery.refetch(),
        accessToken ? guardadasQuery.refetch() : Promise.resolve({ data: [] }),
      ]);

      const mergedPubs = mergePublicacionesConGuardadas(
        publicacionesResult.data,
        guardadasResult.data
      );

      setPublicaciones(mergedPubs);
    } catch (error) {
      if (publicaciones.length > 0) {
        setNoticeMessage(
          "No se pudieron actualizar las publicaciones. Seguís viendo la última información disponible."
        );
      } else {
        setErrorMessage(error.message || "Error refrescando publicaciones.");
      }
    }
  }

  useEffect(() => {
    if (!comercioQuery.data) return;

    setComercio(comercioQuery.data);
    setPerfilHydratado(true);
    setErrorMessage("");
  }, [comercioQuery.data]);

  useEffect(() => {
    if (!publicacionesQuery.data) return;

    const mergedPubs = mergePublicacionesConGuardadas(
      publicacionesQuery.data,
      guardadasQuery.data
    );

    setPublicaciones(mergedPubs);
    setPerfilHydratado(true);
    setErrorMessage("");
  }, [publicacionesQuery.data, guardadasQuery.data]);

  useEffect(() => {
    if (!historiasQuery.data) return;

    setHistorias(normalizarItems(historiasQuery.data));
    setPerfilHydratado(true);
    setErrorMessage("");
  }, [historiasQuery.data]);

  useEffect(() => {
    const principalError =
      comercioQuery.error || publicacionesQuery.error || historiasQuery.error;

    if (!principalError) return;
    if (comercio || publicaciones.length > 0 || historias.length > 0) {
      setNoticeMessage(
        "No se pudo actualizar toda la información del espacio. Seguís viendo la última información disponible."
      );
      return;
    }

    setErrorMessage(
      principalError.message ||
        "Error desconocido cargando perfil del comercio."
    );
    setPerfilHydratado(true);
  }, [
    comercioQuery.error,
    publicacionesQuery.error,
    historiasQuery.error,
    comercio,
    publicaciones.length,
    historias.length,
  ]);

  useEffect(() => {
    let isCurrent = true;

    const puedeCargar = puedeCargarMetricasPrivadas({
      comercioId,
      estaAutenticado,
      comercioResuelto: comercioQuery.isSuccess,
      esPropietario: comercioQuery.data?.es_propietario,
      isEstadisticasOpen,
    });

    if (!puedeCargar) {
      setMetricasSociales(null);
      setComparacionMetricas(null);
      setAnalyticsEspacio(null);
      return () => {
        isCurrent = false;
      };
    }

    void loadDatosSecundarios(() => isCurrent);

    return () => {
      isCurrent = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    comercioId,
    estaAutenticado,
    comercioQuery.isSuccess,
    comercioQuery.data?.es_propietario,
    isEstadisticasOpen,
  ]);

  async function handleToggleLike(pubId) {
    if (usuarioDebeLoguearse()) return;

    if (isLikeLocked(pubId)) return;

    setLikeLock(pubId, true);

    const snapshot = publicaciones;

    setPublicaciones((prev) => optimisticToggleLike(prev, pubId));

    try {
      await toggleLikeMutation.mutateAsync(pubId);
    } catch {
      setPublicaciones(snapshot);
      setNoticeMessage(
        "No se pudo actualizar Me gusta. Intentá nuevamente."
      );
    } finally {
      setLikeLock(pubId, false);
    }
  }


    // =====================================================
  // ETAPA 60 — Seguir / dejar de seguir espacio
  // =====================================================
  async function handleToggleFollow() {
    if (usuarioDebeLoguearse()) return;

    const siguiendoActual = seguimientoQuery.data?.siguiendo;
    if (
      typeof siguiendoActual !== "boolean" ||
      toggleSeguimientoMutation.isPending
    ) {
      return;
    }

    try {
      await toggleSeguimientoMutation.mutateAsync({ siguiendoActual });
    } catch (error) {
      setErrorMessage(error.message || "Error al seguir/dejar de seguir.");
    }
  }

  async function handleToggleSave(pubId) {

    if (usuarioDebeLoguearse()) return;

    if (isSaveLocked(pubId)) return;

    setSaveLock(pubId, true);

    const current = publicaciones.find((p) => p.id === pubId);
    const estabaGuardada = Boolean(current?.guardada_by_me);
    const snapshot = publicaciones;

    setPublicaciones((prev) => optimisticToggleGuardado(prev, pubId));

    try {
      await toggleGuardadoMutation.mutateAsync({
        publicacionId: pubId,
        estabaGuardada,
      });
    } catch {
      setPublicaciones(snapshot);
      setNoticeMessage(
        "No se pudo actualizar el guardado. Intentá nuevamente."
      );
    } finally {
      setSaveLock(pubId, false);
    }
  }

  async function handleHistoriaVisible(historiaId) {
    if (typeof historiaId !== "number") return;

    if (ultimaHistoriaVistaMarcadaRef.current === historiaId) {
      return;
    }

    ultimaHistoriaVistaMarcadaRef.current = historiaId;

    try {
      await marcarHistoriaVista(historiaId);

      setHistorias((prev) =>
        prev.map((h) =>
          h.id === historiaId
            ? { ...h, vista_by_me: true }
            : h
        )
      );
    } catch {
      // silencioso
    }
  }

  function handleHistoriaDeleted(historiaId) {
    setHistorias((prev) =>
      prev.filter((historia) => historia.id !== historiaId)
    );
    setViewerHistorias((prev) =>
      prev.filter((historia) => historia.id !== historiaId)
    );
  }

  function handleOpenHistorias() {
    if (usuarioDebeLoguearse()) return;

    if (!historias.length) return;

    setViewerHistorias(historias);
    setViewerIsOpen(true);
  }

  function handleOpenDenunciaComercio() {
    if (usuarioDebeLoguearse()) return;
    setIsDenunciaComercioOpen(true);
  }

  async function handleHistoriaCreated() {
    await refreshHistorias();
  }

  function handleChangePublicacionForm(event) {
    const { name, value } = event.target;

    setPublicacionForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  }

  function handleSelectImagenPublicacion(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setImagenFile(file);
  }

  function handleCloseCrearPublicacion() {
    setIsCrearPublicacionOpen(false);

    setPublicacionForm({
      titulo: "",
      descripcion: "",
      imagen_url: "",
    });

    setImagenFile(null);
  }

  async function handleSubmitCrearPublicacion() {
    if (!publicacionForm.titulo.trim()) {
      setErrorMessage("El título de la publicación es obligatorio.");
      return;
    }

    try {
      setIsCreatingPublicacion(true);
      setErrorMessage("");

      let imagenUrlFinal = null;

      if (imagenFile) {
        try {
          const token = getAccessToken();

          if (!token) {
            throw new Error("No hay sesión activa.");
          }

          const data = await uploadImagen(imagenFile, token);

          imagenUrlFinal = data.url;
        } catch (error) {
          setErrorMessage(error.message || "Error subiendo la imagen.");
          return;
        }
      }

      await crearPublicacionDeComercio(comercioId, {
        titulo: publicacionForm.titulo,
        descripcion: publicacionForm.descripcion,
        imagen_url: imagenUrlFinal,
        seccion_id: null,
        is_activa: true,
      });

      handleCloseCrearPublicacion();
      await refreshPublicaciones();
    } catch (error) {
      setErrorMessage(error.message || "Error al crear la publicación.");
    } finally {
      setIsCreatingPublicacion(false);
    }
  }

  const tieneHistoriasPendientes = historias.some(
  (historia) => !historia?.vista_by_me
  );

  const hayDatosVisibles =
    Boolean(comercio) || publicaciones.length > 0 || historias.length > 0;

  const isInitialLoading =
    !hayDatosVisibles &&
    !perfilHydratado &&
    (comercioQuery.isLoading ||
      publicacionesQuery.isLoading ||
      historiasQuery.isLoading);

  const siguiendoConfirmado = seguimientoQuery.data?.siguiendo;
  const seguimientoDesconocido =
    estaAutenticado && typeof siguiendoConfirmado !== "boolean";
  const siguiendoVisible = siguiendoConfirmado === true;

  return (
    <div className="min-h-screen bg-canvas text-primary">
      <main className="mx-auto max-w-7xl px-0 py-4 sm:px-4 sm:py-6">

        <div className="mb-4 flex items-center justify-end gap-2">
          {!esComercioMio(comercio) && comercio?.id ? (
            <Button
              variant="secondary"
              onClick={handleOpenDenunciaComercio}
              aria-label="Denunciar espacio"
              className="h-6 min-h-6 w-6 min-w-6 shrink-0 rounded-full p-0 text-primary active:[transform:none]"
            >
              <span
                aria-hidden="true"
                className="inline-flex h-full w-full items-center justify-center text-[12.6px] leading-none text-primary"
              >
                ...
              </span>
            </Button>
          ) : null}

          <Button
            variant="ghost"
            onClick={() => navigate(-1)}
            className="min-h-6 cursor-pointer px-[7px] py-[4.2px] text-[9.8px] leading-[14px] active:[transform:none]"
          >
            <span>
            ← Volver
            </span>
          </Button>
        </div>
        
        {isInitialLoading && (
          <div className="space-y-4">
            <Skeleton className="h-40 rounded-3xl border border-border" />
            <div className="grid grid-cols-3 gap-2">
              <Skeleton className="aspect-square rounded-2xl border border-border" />
              <Skeleton className="aspect-square rounded-2xl border border-border" />
              <Skeleton className="aspect-square rounded-2xl border border-border" />
            </div>
          </div>
        )}

        {!isInitialLoading && errorMessage && !hayDatosVisibles && (
          <Alert className="p-5" variant="danger">
            <p className="font-semibold">Error</p>
            <p className="mt-2 break-words">{errorMessage}</p>
          </Alert>
        )}

        {!isInitialLoading && noticeMessage && hayDatosVisibles && (
          <Alert variant="warning" role="status" aria-live="polite" className="mb-4 flex items-center justify-between gap-3">
            <span>{noticeMessage}</span>
            <Button variant="ghost" onClick={() => setNoticeMessage("")} className="shrink-0 text-xs">
              Cerrar
            </Button>
          </Alert>
        )}

        {!isInitialLoading && (!errorMessage || hayDatosVisibles) && (
          <>
            <Surface as="section" className="relative p-4 pb-2 sm:p-6 sm:pb-2">
              
        {esComercioMio(comercio) && (
          <div className="absolute right-3 top-1 flex flex-col items-end gap-1">

            <div className="group relative">
              <span
                className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-border bg-surface-subtle text-base leading-none"
                aria-label={comercio?.is_activo === false ? "Espacio inactivo" : "Espacio activo"}
              >
                {comercio?.is_activo === false ? "🔴" : "🟢"}
              </span>

              <div className="pointer-events-none absolute right-10 top-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface-elevated px-2 py-1 text-[11px] text-primary opacity-0 shadow-elevation transition-opacity group-hover:opacity-100">
                {comercio?.is_activo === false ? "Inactivo" : "Activo"}
              </div>
            </div>

            <div className="group relative">
      <Button
        iconOnly
        aria-label="Editar espacio"
        variant="ghost"
        onClick={() => navigate(`/perfil?editarEspacioId=${comercio.id}`)}
        className="text-lg text-brand"
      >
        <span className="text-brand">
        ✏️
        </span>
      </Button>

              <div className="pointer-events-none absolute right-10 top-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface-elevated px-2 py-1 text-[11px] text-primary opacity-0 shadow-elevation transition-opacity group-hover:opacity-100">
                Editar
              </div>
            </div>

            <div className="group relative">
              <Button
                iconOnly
                variant="ghost"
                onClick={() => setAgendaComercio(comercio)}
                aria-label="Abrir agenda"
              >
                <span className="relative inline-flex h-6 w-5 flex-col overflow-hidden rounded-sm border border-border-strong bg-surface-elevated">
                  <span className="absolute -top-0.5 left-1 right-1 flex justify-between">
                    <span className="h-1 w-0.5 rounded-full bg-border-strong" />
                    <span className="h-1 w-0.5 rounded-full bg-border-strong" />
                    <span className="h-1 w-0.5 rounded-full bg-border-strong" />
                    <span className="h-1 w-0.5 rounded-full bg-border-strong" />
                  </span>
                  <span className="flex h-2 items-center justify-center bg-danger-surface pt-0.5 text-[3px] font-black leading-none tracking-[0.08em] text-danger-text">
                    MARZO
                  </span>
                  <span className="flex flex-1 items-center justify-center text-[10px] font-black leading-none text-primary">
                    11
                  </span>
                </span>
              </Button>

              <div className="pointer-events-none absolute right-10 top-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface-elevated px-2 py-1 text-[11px] text-primary opacity-0 shadow-elevation transition-opacity group-hover:opacity-100">
                Agenda
              </div>
            </div>

          </div>
        )}
              
          <div className="flex items-start justify-between gap-4">
            <div className="flex min-w-0 flex-1 items-start gap-4">
              <Button
              variant="ghost"
              onClick={handleOpenHistorias}
              aria-label={`Abrir historias de ${comercio?.nombre || "comercio"}`}
              className={`
                h-20
                min-h-20
                w-20
                p-0
                shrink-0
                overflow-hidden
                rounded-full
                bg-canvas
                sm:h-24
                sm:min-h-24
                sm:w-24
                transition
                ${
                  historias.length > 0
                    ? tieneHistoriasPendientes
                      ? "bg-gradient-to-tr from-brand via-interactive-primary to-warning-text p-[2px]"
                      : "border-4 border-border-strong"
                    : "border border-border"
                }
              `}
            >
            <div className="h-full w-full overflow-hidden rounded-full bg-canvas">
              {comercioImagenUrl ? (
                <img
                  src={comercioImagenUrl}
                  alt={comercio?.nombre || "Comercio"}
                  decoding="async"
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center text-2xl font-bold text-primary">
                  {(comercio?.nombre || "C").slice(0, 1).toUpperCase()}
                </div>
              )}
            </div>
              </Button>
                  
                <div className="min-w-0 flex-1 text-left">
                  <h1 className="text-2xl font-bold leading-tight text-primary sm:truncate">
                    {comercio?.nombre ?? "Comercio"}
                  </h1>
                  
                  {comercio?.descripcion ? (
                    <p className="mt-2 max-w-2xl break-words text-sm leading-6 text-secondary">
                      {comercio.descripcion}
                    </p>
                  ) : (
                    <p className="mt-2 text-sm text-muted">
                      Este comercio todavía no agregó descripción.
                    </p>
                  )}

              </div>
            </div>

            {!esComercioMio(comercio) && (
              <div className="flex shrink-0 flex-col items-center gap-2">
                <Button
                  variant={siguiendoVisible ? "secondary" : "primary"}
                  onClick={handleToggleFollow}
                  disabled={
                    seguimientoDesconocido || toggleSeguimientoMutation.isPending
                  }
                  className="min-h-6 rounded-xl px-[5.6px] py-[2.8px] text-[8.4px] leading-[11.2px] active:[transform:none]"
                >
                  {seguimientoDesconocido
                    ? "Comprobando..."
                    : siguiendoVisible
                    ? "Siguiendo"
                    : "+Seguir"}
                </Button>
              </div>
            )}
          </div>

              {/* INFO DEL ESPACIO */}
              <div className="mt-4 flex w-full flex-wrap items-end gap-x-4 gap-y-2">

                {/* WHATSAPP */}
                {comercio?.whatsapp && (
                  <a
                    href={`https://wa.me/${String(comercio.whatsapp).replace(/\D/g, "")}?text=Hola%2C%20te%20encontré%20en%20FeedGo%20y%20quiero%20consultarte`}
                    onClick={(event) => {
                      if (usuarioDebeLoguearse()) event.preventDefault();
                    }}
                    target="_blank"
                    rel="noreferrer"
                    className="interactive-bubble interactive-bubble--liquid group cursor-pointer rounded-xl px-2 py-1 text-xs font-semibold"
                  >
                    <span className="inline-flex items-center gap-1 text-green-400 group-hover:text-green-300">
                      <MessageCircle size={14} aria-hidden="true" />
                      WhatsApp
                    </span>
                    <InteractiveLiquidLayers />
                  </a>
                )}

                {/* INSTAGRAM */}
                {comercio?.instagram && (
                  <a
                    href={`https://instagram.com/${String(comercio.instagram).replace("@", "")}`}
                    onClick={(event) => {
                      if (usuarioDebeLoguearse()) event.preventDefault();
                    }}
                    target="_blank"
                    rel="noreferrer"
                    className="interactive-bubble interactive-bubble--liquid group cursor-pointer rounded-xl px-2 py-1 text-xs font-semibold"
                  >
                    <span className="inline-flex items-center gap-1 text-pink-400 group-hover:text-pink-300">
                      <Camera size={14} aria-hidden="true" />
                      Instagram
                    </span>
                    <InteractiveLiquidLayers />
                  </a>
                )}

                {/* MAPS */}
                {(comercio?.latitud && comercio?.longitud) || comercio?.maps_url ? (
                  <a
                    href={
                      comercio?.latitud && comercio?.longitud
                        ? `https://www.google.com/maps?q=${comercio.latitud},${comercio.longitud}`
                        : comercio.maps_url
                    }
                    onClick={(event) => {
                      if (usuarioDebeLoguearse()) event.preventDefault();
                    }}
                    target="_blank"
                    rel="noreferrer"
                    className="interactive-bubble interactive-bubble--liquid group cursor-pointer rounded-xl px-2 py-1 text-xs font-semibold"
                  >
                    <span className="inline-flex items-center gap-1 text-brand group-hover:text-brand-strong">
                    <MapPin size={14} aria-hidden="true" />
                    Cómo llegar
                    </span>
                    <InteractiveLiquidLayers />
                  </a>
                ) : null}

              </div>

              {puedoCrearHistoria && (
                <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2">
                  <Button
                    variant="ghost"
                    className="group cursor-pointer rounded-xl px-2 py-1 text-xs"
                    onClick={() => setIsCrearHistoriaOpen(true)}
                  >
                    <span className="inline-flex items-center gap-1 text-secondary group-hover:text-primary">
                      <PlusCircle size={14} aria-hidden="true" />
                      Historia
                    </span>
                  </Button>

                  <Button
                    variant="ghost"
                    className="group cursor-pointer rounded-xl px-2 py-1 text-xs"
                    onClick={() => setIsCrearPublicacionOpen(true)}
                  >
                    <span className="inline-flex items-center gap-1 text-secondary group-hover:text-primary">
                      <PlusCircle size={14} aria-hidden="true" />
                    Publicación
                    </span>
                  </Button>

                  <Button
                    variant="ghost"
                    className="group cursor-pointer rounded-xl px-2 py-1 text-xs"
                    onClick={() => setIsEstadisticasOpen(true)}
                  >
                    <span className="inline-flex items-center gap-1 text-secondary group-hover:text-primary">
                      <BarChart3 size={14} aria-hidden="true" />
                    Estadísticas
                    </span>
                  </Button>

                </div>
              )}

              <div className="mt-2 grid w-full grid-cols-[minmax(0,1fr)_auto] items-start gap-x-4">
                <div className="min-w-0">
                  {comercio?.ciudad && (
                    <p className="flex min-h-9 min-w-0 items-start gap-2 break-words py-1 text-xs leading-4 text-secondary">
                      <MapPin size={14} className="mt-1.5 shrink-0" aria-hidden="true" />
                      <span className="min-w-0 break-words pt-1.5">
                        {comercio?.direccion
                          ? `${comercio.direccion}, ${comercio.ciudad}`
                          : comercio.ciudad}
                        {comercio?.provincia && comercio?.direccion
                          ? `, ${comercio.provincia}`
                          : ""}
                      </span>
                    </p>
                  )}
                </div>

                <EstadoHorarioBadge
                  horarioAtencion={comercio?.horario_atencion}
                  variant="inline"
                  className="min-w-0 justify-self-end justify-end text-right leading-4"
                />
              </div>
            </Surface>

            <section className="mt-6">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-base font-semibold text-primary">
                  Publicaciones
                </h2>

                <span className="text-xs text-muted">
                  Vista en cuadrícula
                </span>
              </div>

              {publicaciones.length === 0 ? (
                <Surface className="p-5">
                  <p className="text-secondary">
                    Este comercio no tiene publicaciones todavía.
                  </p>
                </Surface>
              ) : (
                <div className="grid grid-cols-2 gap-0 sm:grid-cols-3 [&>*]:w-full">
                  {publicaciones.map((p) => (
                    <PublicacionCard
                      key={p.id}
                      pub={p}
                      headerRightBadgeText={comercio?.nombre}
                      isActingLike={Boolean(likeLocks[p.id])}
                      isActingSave={Boolean(saveLocks[p.id])}
                      onToggleLike={() => handleToggleLike(p.id)}
                      onToggleSave={() => handleToggleSave(p.id)}
                      compact
                      compactWholeCardLink
                    />
                  ))}
                </div>
              )}
            </section>

            {isEstadisticasOpen && (
              <ActiveLayer
                onClose={() => setIsEstadisticasOpen(false)}
                labelledBy="estadisticas-espacio-title"
                describedBy="estadisticas-espacio-description"
                closeOnBackdrop={false}
                className="px-4"
                contentClassName="w-full max-w-lg"
              >
                <Surface variant="elevated" className="max-h-[calc(100dvh-2rem)] overflow-y-auto p-6">
                  <div className="mb-5 flex items-start justify-between gap-4">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-brand">
                        FeedGo Analytics
                      </p>

                      <h3 id="estadisticas-espacio-title" className="mt-1 text-xl font-bold text-primary">
                        Estadísticas del espacio
                      </h3>

                      <p id="estadisticas-espacio-description" className="mt-2 text-sm leading-6 text-secondary">
                        Métricas reales calculadas desde la actividad del espacio.
                      </p>
                    </div>

                    <Button
                      iconOnly
                      aria-label="Cerrar estadísticas"
                      variant="ghost"
                      onClick={() => setIsEstadisticasOpen(false)}
                      className="text-sm"
                    >
                      ✕
                    </Button>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <Surface variant="subtle" className="p-4">
                      <p className="text-xs text-secondary">Seguidores</p>

                      <p className="mt-2 text-2xl font-bold text-primary">
                        {metricasSociales?.total_seguidores ?? comercio?.seguidores_count ?? 0}
                      </p>

                      <p className="mt-1 text-xs text-secondary">
                        {comparacionMetricas?.fecha_anterior
                          ? `${comparacionMetricas?.seguidores?.delta >= 0 ? "↑" : "↓"} ${comparacionMetricas?.seguidores?.delta ?? 0} vs período anterior`
                          : "Sin período anterior"}
                      </p>
                    </Surface>

                    <Surface variant="subtle" className="p-4">
                      <p className="text-xs text-secondary">Publicaciones</p>

                      <p className="mt-2 text-2xl font-bold text-primary">
                        {metricasSociales?.total_publicaciones ?? publicaciones.length}
                      </p>

                      <p className="mt-1 text-xs text-secondary">
                        {comparacionMetricas?.fecha_anterior
                          ? `${comparacionMetricas?.publicaciones?.delta >= 0 ? "↑" : "↓"} ${comparacionMetricas?.publicaciones?.delta ?? 0} vs período anterior`
                          : "Sin período anterior"}
                      </p>
                    </Surface>

                    <Surface variant="subtle" className="p-4">
                      <p className="text-xs text-secondary">Likes publicaciones</p>

                      <p className="mt-2 text-2xl font-bold text-primary">
                        {metricasSociales?.total_likes_publicaciones ?? 0}
                      </p>

                      <p className="mt-1 text-xs text-secondary">
                        {comparacionMetricas?.fecha_anterior
                          ? `${comparacionMetricas?.likes_publicaciones?.delta >= 0 ? "↑" : "↓"} ${comparacionMetricas?.likes_publicaciones?.delta ?? 0} vs período anterior`
                          : "Sin período anterior"}
                      </p>
                    </Surface>

                    <Surface variant="subtle" className="p-4">
                      <p className="text-xs text-secondary">Guardados</p>

                      <p className="mt-2 text-2xl font-bold text-primary">
                        {metricasSociales?.total_guardados_publicaciones ?? 0}
                      </p>

                      <p className="mt-1 text-xs text-secondary">
                        {comparacionMetricas?.fecha_anterior
                          ? `${comparacionMetricas?.guardados_publicaciones?.delta >= 0 ? "↑" : "↓"} ${comparacionMetricas?.guardados_publicaciones?.delta ?? 0} vs período anterior`
                          : "Sin período anterior"}
                      </p>
                    </Surface>

                    <Surface variant="subtle" className="p-4">
                      <p className="text-xs text-secondary">Vistas historias</p>

                      <p className="mt-2 text-2xl font-bold text-primary">
                        {metricasSociales?.total_vistas_historias ?? 0}
                      </p>

                      <p className="mt-1 text-xs text-secondary">
                        {comparacionMetricas?.fecha_anterior
                          ? `${comparacionMetricas?.vistas_historias?.delta >= 0 ? "↑" : "↓"} ${comparacionMetricas?.vistas_historias?.delta ?? 0} vs período anterior`
                          : "Sin período anterior"}
                      </p>
                    </Surface>

                    <Surface variant="subtle" className="p-4">
                      <p className="text-xs text-secondary">Likes historias</p>

                      <p className="mt-2 text-2xl font-bold text-primary">
                        {metricasSociales?.total_likes_historias ?? 0}
                      </p>

                      <p className="mt-1 text-xs text-secondary">
                        {comparacionMetricas?.fecha_anterior
                          ? `${comparacionMetricas?.likes_historias?.delta >= 0 ? "↑" : "↓"} ${comparacionMetricas?.likes_historias?.delta ?? 0} vs período anterior`
                          : "Sin período anterior"}
                      </p>
                    </Surface>
                  </div>

                  {analyticsEspacio?.insights?.length > 0 && (
                    <div className="mt-5 space-y-3">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-brand">
                          Insights automáticos
                        </p>
                      </div>

                      {analyticsEspacio.insights.map((insight, index) => (
                        <Surface
                          key={index}
                          variant="subtle"
                          className="p-4"
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-sm">
                              {insight.tipo === "positivo"
                                ? "🟢"
                                : insight.tipo === "alerta"
                                ? "🟠"
                                : "🔵"}
                            </span>

                            <p className="text-sm font-semibold text-primary">
                              {insight.titulo}
                            </p>
                          </div>

                          <p className="mt-2 text-sm leading-6 text-secondary">
                            {insight.descripcion}
                          </p>

                          <div className="mt-3 rounded-xl border border-border-subtle bg-canvas-subtle p-3">
                            <p className="text-xs font-medium uppercase tracking-wide text-muted">
                              Acción recomendada
                            </p>

                            <p className="mt-1 text-sm text-secondary">
                              {insight.accion_recomendada}
                            </p>
                          </div>
                        </Surface>
                      ))}
                    </div>
                  )}

                  <p className="mt-5 text-xs leading-5 text-muted">
                    Estos datos vienen del backend y se recalculan desde la base real.
                  </p>
                </Surface>
              </ActiveLayer>
            )}

            <CrearHistoriaModal
              isOpen={isCrearHistoriaOpen}
              comercioId={comercioId}
              onClose={() => setIsCrearHistoriaOpen(false)}
              onCreated={handleHistoriaCreated}
            />

            {isCrearPublicacionOpen && (
              <ActiveLayer
                onClose={handleCloseCrearPublicacion}
                labelledBy="crear-publicacion-title"
                describedBy="crear-publicacion-description"
                closeOnBackdrop={false}
                className="px-4"
                contentClassName="w-full max-w-lg"
              >
                <Surface variant="elevated" className="max-h-[calc(100dvh-2rem)] overflow-y-auto p-6">
                  <div className="mb-5">
                    <h3 id="crear-publicacion-title" className="text-lg font-semibold text-primary">
                      Crear publicación
                    </h3>
                    <p id="crear-publicacion-description" className="mt-1 text-sm text-secondary">
                      Completá los datos para publicar en este contenido.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label htmlFor="publicacion-titulo" className="mb-1 block text-sm font-medium text-secondary">
                        Título
                      </label>
                      <Input
                        id="publicacion-titulo"
                        type="text"
                        name="titulo"
                        value={publicacionForm.titulo}
                        onChange={handleChangePublicacionForm}
                        placeholder="Ej: Promo de la semana"
                        className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-primary outline-none placeholder:text-muted focus-visible:border-border-strong focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
                      />
                    </div>

                    <div>
                      <label htmlFor="publicacion-descripcion" className="mb-1 block text-sm font-medium text-secondary">
                        Descripción
                      </label>
                      <Textarea
                        id="publicacion-descripcion"
                        name="descripcion"
                        value={publicacionForm.descripcion}
                        onChange={handleChangePublicacionForm}
                        placeholder="Contá de qué trata esta publicación"
                        rows={4}
                        className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-primary outline-none placeholder:text-muted focus-visible:border-border-strong focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
                      />
                    </div>

                    <div>
                      <label htmlFor="publicacion-media" className="mb-1 block text-sm font-medium text-secondary">
                        Imagen o video
                      </label>

                      <Input
                        id="publicacion-media"
                        type="file"
                        accept="
                          image/jpeg,
                          image/png,
                          image/webp,
                          video/mp4,
                          video/webm,
                          video/ogg,
                          video/quicktime
                        "
                        capture="environment"
                        onChange={handleSelectImagenPublicacion}
                        className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-primary file:mr-3 file:rounded-lg file:border-0 file:bg-interactive-primary file:px-3 file:py-1 file:text-sm file:font-semibold file:text-interactive-on-primary"
                      />

                      {imagenFile ? (
                        <p className="mt-1 text-xs text-secondary">
                          Archivo seleccionado: {imagenFile.name}
                        </p>
                      ) : null}
                    </div>
                  </div>

                  <div className="mt-6 grid grid-cols-2 gap-3">
                    <Button
                      variant="secondary"
                      className="rounded-xl px-4 py-3 text-sm"
                      onClick={handleCloseCrearPublicacion}
                    >
                      Cancelar
                    </Button>

                    <Button
                      variant="primary"
                      disabled={isCreatingPublicacion}
                      className="rounded-xl px-4 py-3 text-sm"
                      onClick={handleSubmitCrearPublicacion}
                    >
                      {isCreatingPublicacion ? "Creando..." : "Crear publicación"}
                    </Button>
                  </div>
                </Surface>
              </ActiveLayer>
            )}
          </>
        )}
        <HistoriasViewer
          isOpen={viewerIsOpen}
          onClose={() => setViewerIsOpen(false)}
          onHistoriaVisible={handleHistoriaVisible}
          onHistoriaDeleted={handleHistoriaDeleted}
          historias={viewerHistorias}
          titulo={comercio?.nombre || "Historias"}
        />
        {agendaComercio ? (
          <AgendaPrivadaModal
            comercio={agendaComercio}
            onClose={() => setAgendaComercio(null)}
          />
        ) : null}
        <DenunciaModal
          isOpen={isDenunciaComercioOpen}
          onClose={() => setIsDenunciaComercioOpen(false)}
          recursoTipo={RECURSO_DENUNCIA_COMERCIO}
          recursoId={comercio?.id}
          titulo="Denunciar comercio"
        />
      </main>
    </div>
  );
}

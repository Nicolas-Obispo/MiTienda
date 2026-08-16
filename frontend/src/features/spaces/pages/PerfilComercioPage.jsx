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
  toggleSeguimientoEspacio,
  useSocialInteractions,
  useToggleGuardadoPublicacionMutation,
  useToggleLikePublicacionMutation,
} from "@features/social";

import {
  crearPublicacionDeComercio,
  useComercioDetalle,
  usePublicacionesComercio,
} from "@features/spaces";

import {
  marcarHistoriaVista,
  useHistoriasComercio,
} from "@features/stories";

import {
  usePublicacionesGuardadas,
} from "@features/posts";

import {
  obtenerEstadoSeguimiento,
} from "@features/spaces";

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

const seguimientoPerfilComercioCache = new Map();

export default function CommerceProfilePage() {
  const { id } = useParams();
  const comercioId = Number(id);
  const navigate = useNavigate();
  const {
    estaAutenticado,
    requireAuthentication: usuarioDebeLoguearse,
  } = useProtectedActionRedirect();
  const seguimientoCacheInicial = seguimientoPerfilComercioCache.get(comercioId);

  const [perfilHydratado, setPerfilHydratado] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const [comercio, setComercio] = useState(null);
  const [historias, setHistorias] = useState([]);
  const [viewerIsOpen, setViewerIsOpen] = useState(false);
  const [viewerHistorias, setViewerHistorias] = useState([]);
  const ultimaHistoriaVistaMarcadaRef = useRef(null);
  const seguidoresCountPrevioRef = useRef(
    typeof seguimientoCacheInicial?.seguidores_count === "number"
      ? seguimientoCacheInicial.seguidores_count
      : null
  );
  const [publicaciones, setPublicaciones] = useState([]);

  const redirectAnonymousDetail = useCallback(() => {
    navigate("/registro", {
      replace: true,
      state: { message: "Registrate para seguir explorando este espacio." },
    });
  }, [navigate]);

  useAnonymousDetailGate({
    enabled: !estaAutenticado,
    ready: Boolean(comercio),
    onExpire: redirectAnonymousDetail,
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

  const [siguiendo, setSiguiendo] = useState(() =>
    typeof seguimientoCacheInicial?.siguiendo === "boolean"
      ? seguimientoCacheInicial.siguiendo
      : false
  );
  const [seguimientoHydratado, setSeguimientoHydratado] = useState(() =>
    typeof seguimientoCacheInicial?.siguiendo === "boolean"
  );
  const [isLoadingFollow, setIsLoadingFollow] = useState(false);

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

  function guardarSeguimientoVisible(estadoSeguimiento) {
    if (!estadoSeguimiento || !comercioId || Number.isNaN(comercioId)) return;

    const siguienteEstado = {
      siguiendo: Boolean(estadoSeguimiento.siguiendo),
      seguidores_count: estadoSeguimiento.seguidores_count,
    };

    seguimientoPerfilComercioCache.set(comercioId, siguienteEstado);
    setSiguiendo(siguienteEstado.siguiendo);
    setSeguimientoHydratado(true);

    if (typeof siguienteEstado.seguidores_count === "number") {
      seguidoresCountPrevioRef.current = siguienteEstado.seguidores_count;
    } else if (siguienteEstado.seguidores_count === null) {
      seguidoresCountPrevioRef.current = null;
    }
  }

  async function loadDatosSecundarios() {
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

      // ETAPA 62
      setMetricasSociales(metricasData);
      setComparacionMetricas(comparacionData);
      setAnalyticsEspacio(analyticsData);

            // ETAPA 60 — Cargamos estado real de seguimiento solo si hay sesión.
      try {
        if (accessToken) {
          const estadoSeguimiento = await obtenerEstadoSeguimiento(comercioId);

          guardarSeguimientoVisible(estadoSeguimiento);

          setComercio((prev) =>
            prev
              ? {
                  ...prev,
                  seguidores_count: estadoSeguimiento.seguidores_count,
                }
              : prev
          );
        }
      } catch {
        // No rompemos la pantalla si falla el estado de seguimiento.
      }
    } catch {
      // No bloqueamos el perfil si fallan metricas, analytics o seguimiento.
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
      setErrorMessage(error.message || "Error refrescando publicaciones.");
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
    const seguimientoCacheado = seguimientoPerfilComercioCache.get(comercioId);

    if (!seguimientoCacheado) {
      setSiguiendo(false);
      setSeguimientoHydratado(false);
      return;
    }

    setSiguiendo(Boolean(seguimientoCacheado.siguiendo));
    setSeguimientoHydratado(true);

    if (typeof seguimientoCacheado.seguidores_count === "number") {
      seguidoresCountPrevioRef.current = seguimientoCacheado.seguidores_count;
    } else if (seguimientoCacheado.seguidores_count === null) {
      seguidoresCountPrevioRef.current = null;
    }
  }, [comercioId]);

  useEffect(() => {
    if (typeof comercio?.seguidores_count !== "number") return;
    if (
      comercio.seguidores_count === 0 &&
      seguidoresCountPrevioRef.current !== null
    ) {
      return;
    }

    seguidoresCountPrevioRef.current = comercio.seguidores_count;
  }, [comercio?.seguidores_count]);

  useEffect(() => {
    const principalError =
      comercioQuery.error || publicacionesQuery.error || historiasQuery.error;

    if (!principalError) return;
    if (comercio || publicaciones.length > 0 || historias.length > 0) return;

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
    loadDatosSecundarios();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [comercioId]);

  async function handleToggleLike(pubId) {
    if (usuarioDebeLoguearse()) return;

    if (isLikeLocked(pubId)) return;

    setLikeLock(pubId, true);

    const snapshot = publicaciones;

    setPublicaciones((prev) => optimisticToggleLike(prev, pubId));

    try {
      await toggleLikeMutation.mutateAsync(pubId);
    } catch (error) {
      setPublicaciones(snapshot);
      setErrorMessage(error.message || "Error al togglear like.");
    } finally {
      setLikeLock(pubId, false);
    }
  }


    // =====================================================
  // ETAPA 60 — Seguir / dejar de seguir espacio
  // =====================================================
  async function handleToggleFollow() {
    if (usuarioDebeLoguearse()) return;

    if (isLoadingFollow) return;

    try {
      setIsLoadingFollow(true);
      const siguiendoActual = seguimientoHydratado
        ? siguiendo
        : seguimientoPerfilComercioCache.get(comercioId)?.siguiendo ?? siguiendo;

      await toggleSeguimientoEspacio({
        comercioId,
        siguiendo: siguiendoActual,
      });

      setSiguiendo(!siguiendoActual);

      // Refrescamos estado y contador real desde backend.
      let estadoSeguimiento = null;

      try {
        estadoSeguimiento = await obtenerEstadoSeguimiento(comercioId);
      } catch (error) {
        if (siguiendoActual && error?.status === 404) {
          guardarSeguimientoVisible({
            siguiendo: false,
            seguidores_count: null,
          });

          setComercio((prev) =>
            prev
              ? {
                  ...prev,
                  seguidores_count: null,
                }
              : prev
          );

          return;
        }

        throw error;
      }

      guardarSeguimientoVisible(estadoSeguimiento);

      setComercio((prev) =>
        prev
          ? {
              ...prev,
              seguidores_count: estadoSeguimiento.seguidores_count,
            }
          : prev
      );
    } catch (error) {
      setErrorMessage(error.message || "Error al seguir/dejar de seguir.");
    } finally {
      setIsLoadingFollow(false);
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
    } catch (error) {
      setPublicaciones(snapshot);
      setErrorMessage(error.message || "Error al guardar/quitar guardado.");
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

  const publicacionesQueryItems = normalizarItems(publicacionesQuery.data);

  const publicacionesCountVisible =
    publicaciones.length > 0
      ? publicaciones.length
      : publicacionesQueryItems.length > 0
      ? publicacionesQueryItems.length
      : comercio?.publicaciones_count ?? comercio?.total_publicaciones ?? 0;

  const seguimientoCacheActual =
    seguimientoPerfilComercioCache.get(comercioId);

  const siguiendoVisible = seguimientoHydratado
    ? siguiendo
    : typeof seguimientoCacheActual?.siguiendo === "boolean"
    ? seguimientoCacheActual.siguiendo
    : siguiendo;

  const seguidoresCountDesdeComercio =
    typeof comercio?.seguidores_count === "number"
      ? comercio.seguidores_count
      : typeof comercioQuery.data?.seguidores_count === "number"
      ? comercioQuery.data.seguidores_count
      : null;

  const seguidoresCountVisible =
    seguidoresCountPrevioRef.current ??
    (typeof seguimientoCacheActual?.seguidores_count === "number"
      ? seguimientoCacheActual.seguidores_count
      : null) ??
    seguidoresCountDesdeComercio;

  const seguidoresCountLabel =
    typeof seguidoresCountVisible === "number"
      ? `${seguidoresCountVisible} seguidores`
      : "Seguidores no disponibles";

  return (
    <div className="min-h-screen bg-canvas text-primary">
      <main className="mx-auto max-w-5xl px-0 py-4 sm:px-4 sm:py-6">

        <div className="mb-4">
          <Button
            variant="ghost"
            onClick={() => navigate(-1)}
            className="cursor-pointer text-sm"
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

        {!isInitialLoading && errorMessage && (
          <Alert className="p-5" variant="danger">
            <p className="font-semibold">Error</p>
            <p className="mt-2 break-words">{errorMessage}</p>
          </Alert>
        )}

        {!isInitialLoading && !errorMessage && (
          <>
            <Surface as="section" className="relative p-4 sm:p-6">
              
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
              
              <div className="flex items-start justify-between">
  
            {/* IZQUIERDA (todo tu contenido actual) */}
            <div>
              {/* nombre, descripción, etc */}
            </div>

            {/* DERECHA (botón) */}
            {!esComercioMio(comercio) && (
              <Button
                variant={siguiendoVisible ? "secondary" : "primary"}
                onClick={handleToggleFollow}
                className="rounded-xl px-2 py-1 text-xs"
              >
                {siguiendoVisible ? "Siguiendo" : "+Seguir"}
              </Button>
            )}

          </div>

          <div className="flex items-start gap-4">
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

                  {comercio?.ciudad && (
                    <p className="mt-2 flex max-w-full items-start gap-2 break-words text-sm text-secondary">
                      <MapPin size={14} className="shrink-0" aria-hidden="true" />
                      {comercio?.direccion
                        ? `${comercio.direccion}, ${comercio.ciudad}`
                        : comercio.ciudad}
                      {comercio?.provincia && comercio?.direccion
                        ? `, ${comercio.provincia}`
                        : ""}
                    </p>
                  )}

                  <div className="mt-3 flex flex-wrap items-center gap-1">
                    
                    {/* PUBLICACIONES */}
                    <span className="max-w-full break-words rounded-full border border-border bg-surface-subtle px-3 py-1 text-xs">
                      {publicacionesCountVisible} publicaciones
                    </span>

                    {/* SEGUIDORES */}
                    <span className="max-w-full break-words rounded-full border border-border bg-surface-subtle px-3 py-1 text-xs">
                      {seguidoresCountLabel}
                    </span>

                  </div>

                </div>
              </div>

              {/* INFO DEL ESPACIO */}
              <div className="mt-4 flex w-full flex-wrap items-center gap-x-4 gap-y-2">

                {/* WHATSAPP */}
                {comercio?.whatsapp && (
                  <a
                    href={`https://wa.me/${String(comercio.whatsapp).replace(/\D/g, "")}?text=Hola%2C%20te%20encontré%20en%20MiPlaza%20y%20quiero%20consultarte`}
                    target="_blank"
                    rel="noreferrer"
                    className="interactive-bubble group cursor-pointer text-xs font-semibold"
                  >
                    <span className="inline-flex items-center gap-2 text-green-400 group-hover:text-green-300">
                      <MessageCircle size={14} aria-hidden="true" />
                      WhatsApp
                    </span>
                  </a>
                )}

                {/* INSTAGRAM */}
                {comercio?.instagram && (
                  <a
                    href={`https://instagram.com/${String(comercio.instagram).replace("@", "")}`}
                    target="_blank"
                    rel="noreferrer"
                    className="interactive-bubble group cursor-pointer text-xs font-semibold"
                  >
                    <span className="inline-flex items-center gap-2 text-pink-400 group-hover:text-pink-300">
                      <Camera size={14} aria-hidden="true" />
                      Instagram
                    </span>
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
                    target="_blank"
                    rel="noreferrer"
                    className="interactive-bubble group cursor-pointer text-xs font-semibold"
                  >
                    <span className="inline-flex items-center gap-2 text-brand group-hover:text-brand-strong">
                    <MapPin size={14} aria-hidden="true" />
                    Cómo llegar
                    </span>
                  </a>
                ) : null}

                <EstadoHorarioBadge
                  horarioAtencion={comercio?.horario_atencion}
                  variant="inline"
                  className="ml-auto justify-end"
                />

                {comercio?.id ? (
                  <Button
                    variant="ghost"
                    onClick={() => setIsDenunciaComercioOpen(true)}
                    className="group cursor-pointer text-xs"
                  >
                    <span className="inline-flex items-center gap-2 text-secondary group-hover:text-primary">
                      Denunciar
                    </span>
                  </Button>
                ) : null}

              </div>

              {puedoCrearHistoria && (
                <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2">
                  <Button
                    variant="ghost"
                    className="group cursor-pointer text-sm"
                    onClick={() => setIsCrearHistoriaOpen(true)}
                  >
                    <span className="inline-flex items-center gap-2 text-secondary group-hover:text-primary">
                      <PlusCircle size={16} aria-hidden="true" />
                      Historia
                    </span>
                  </Button>

                  <Button
                    variant="ghost"
                    className="group cursor-pointer text-sm"
                    onClick={() => setIsCrearPublicacionOpen(true)}
                  >
                    <span className="inline-flex items-center gap-2 text-secondary group-hover:text-primary">
                      <PlusCircle size={16} aria-hidden="true" />
                    Publicación
                    </span>
                  </Button>

                  <Button
                    variant="ghost"
                    className="group cursor-pointer text-sm"
                    onClick={() => setIsEstadisticasOpen(true)}
                  >
                    <span className="inline-flex items-center gap-2 text-secondary group-hover:text-primary">
                      <BarChart3 size={16} aria-hidden="true" />
                    Estadísticas
                    </span>
                  </Button>

                </div>
              )}
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
                <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3 sm:gap-2 md:gap-3">
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
                        MiPlaza Analytics
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

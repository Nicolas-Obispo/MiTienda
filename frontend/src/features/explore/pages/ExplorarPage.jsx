/**
 * ExplorarPage.jsx
 * ----------------
 * ETAPA 56 — Mejora visual (mobile first + grid)
 *
 * CAMBIOS:
 * - Grid responsive (tipo Instagram)
 * - Card visual centrada en imagen
 * - Nombre real del comercio
 * - Eliminamos lista en columna
 * - Base preparada para UX moderna
 *
 * ETAPA 61 — Mejora de exploración
 * - Se agrega selector Espacios / Publicaciones
 * - Espacios mantiene comportamiento existente
 * - Publicaciones reutiliza formato de grilla
 * - Se recuerda el último modo usado con localStorage
 * - NO se toca lógica de backend
 */

import React, { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  getExplorarEspaciosInfiniteQueryOptions,
  useExplorarEspacios,
  useExplorarPublicaciones,
} from "@features/explore";

import { useNavigate } from "react-router-dom";
import { useSearchSuggestions } from "@features/search/hooks/useSearchSuggestions";
import {
  Alert,
  Button,
  GeographicContextControls,
  getMediaUrlFromAny,
  Input,
  Skeleton,
  Surface,
  useGeographicContext,
} from "@shared";
import EstadoHorarioBadge from "@features/availability/components/EstadoHorarioBadge";

const HISTORIAL_BUSQUEDA_KEY = "miplaza_explorar_historial_busqueda";
const HISTORIAL_BUSQUEDA_MAX = 5;

function normalizarBusqueda(valor) {
  if (!valor) return null;
  const t = valor.trim();
  return t ? t : null;
}

function usarModoIA(q, modoExplorar) {
  return Boolean(q) && modoExplorar === "espacios";
}

function leerHistorialBusqueda() {
  try {
    const historial = JSON.parse(
      localStorage.getItem(HISTORIAL_BUSQUEDA_KEY) || "[]"
    );

    if (!Array.isArray(historial)) return [];

    return historial
      .map((item) => String(item || "").trim())
      .filter(Boolean)
      .slice(0, HISTORIAL_BUSQUEDA_MAX);
  } catch {
    return [];
  }
}

export default function ExplorarPage() {
  const [busqueda, setBusqueda] = useState("");
  const [busquedaSugerenciasDebounced, setBusquedaSugerenciasDebounced] =
    useState(null);
  const [buscadorActivo, setBuscadorActivo] = useState(false);
  const [historialBusqueda, setHistorialBusqueda] = useState(() =>
    leerHistorialBusqueda()
  );

  const [modoExplorar, setModoExplorar] = useState(() => {
    const modoGuardado = localStorage.getItem("miplaza_explorar_modo");

    if (modoGuardado === "publicaciones") return "publicaciones";
    return "espacios";
  });

  const [limit] = useState(20);

  const {
    context: geographicContext,
    distanceFresh,
    hasTerritory,
    queryContext,
    requestDeviceLocation,
    territoryFresh,
  } = useGeographicContext();
  const [searchScope, setSearchScope] = useState({
    scope: "local",
    expansion_km: null,
    territoryId: null,
  });
  const activeTerritoryId = queryContext
    ? `${queryContext.country_code}:${queryContext.province_code}:${queryContext.city_key}`
    : null;
  const effectiveSearchScope =
    searchScope.territoryId === activeTerritoryId &&
    (searchScope.scope !== "expanded" || queryContext?.lat !== null)
      ? searchScope
      : { scope: "local", expansion_km: null };

  const busquedaNormalizada = normalizarBusqueda(busqueda);
  const usarSmartSemantic = usarModoIA(busquedaNormalizada, modoExplorar);

  useEffect(() => {
    const timer = setTimeout(() => {
      setBusquedaSugerenciasDebounced(normalizarBusqueda(busqueda));
    }, 300);

    return () => clearTimeout(timer);
  }, [busqueda]);

  const queryClient = useQueryClient();

  const sugerenciasQuery = useSearchSuggestions({
    q: busquedaSugerenciasDebounced,
    limit: 5,
    enabled: modoExplorar === "espacios",
  });

  const espaciosQuery = useExplorarEspacios({
    q: busquedaNormalizada,
    smart: usarSmartSemantic ? false : usarModoIA(busquedaNormalizada, modoExplorar),
    smart_semantic: usarSmartSemantic,
    lat: queryContext?.lat ?? null,
    lng: queryContext?.lng ?? null,
    city_key: queryContext?.city_key ?? null,
    province_code: queryContext?.province_code ?? null,
    country_code: queryContext?.country_code ?? null,
    positionRevision: queryContext?.positionRevision ?? 0,
    scope: effectiveSearchScope.scope,
    expansion_km: effectiveSearchScope.expansion_km,
    limit,
    enabled: hasTerritory && modoExplorar === "espacios",
  });

  const publicacionesQuery = useExplorarPublicaciones({
    q: busquedaNormalizada,
    limit,
    offset: 0,
  });

  const espaciosQueryData = espaciosQuery.data?.pages
    ? espaciosQuery.data.pages.flatMap((pagina) =>
        Array.isArray(pagina) ? pagina : []
      )
    : [];

  const publicacionesQueryData = Array.isArray(publicacionesQuery.data)
  ? publicacionesQuery.data
  : [];

  const estaCargandoQuery =
    modoExplorar === "publicaciones"
      ? publicacionesQuery.isLoading || publicacionesQuery.isFetching
      : espaciosQuery.isLoading || espaciosQuery.isFetching;

  const error =
    modoExplorar === "publicaciones"
      ? publicacionesQuery.error?.message
      : espaciosQuery.error?.message;

  const navigate = useNavigate();

  function cambiarModoExplorar(nuevoModo) {
    setModoExplorar(nuevoModo);
    localStorage.setItem("miplaza_explorar_modo", nuevoModo);
  }

  function guardarEnHistorialBusqueda(valor) {
    const q = normalizarBusqueda(valor);
    if (!q) return;

    const historialActualizado = [
      q,
      ...historialBusqueda.filter(
        (item) => item.toLowerCase() !== q.toLowerCase()
      ),
    ].slice(0, HISTORIAL_BUSQUEDA_MAX);

    setHistorialBusqueda(historialActualizado);
    localStorage.setItem(
      HISTORIAL_BUSQUEDA_KEY,
      JSON.stringify(historialActualizado)
    );
  }

  function prefetchBusquedaEspacios(valor) {
    const q = normalizarBusqueda(valor);
    if (!q || !hasTerritory) return;

    const paramsBusqueda = {
      q,
      smart: false,
      smart_semantic: true,
      lat: queryContext?.lat ?? null,
      lng: queryContext?.lng ?? null,
      city_key: queryContext?.city_key ?? null,
      province_code: queryContext?.province_code ?? null,
      country_code: queryContext?.country_code ?? null,
      positionRevision: queryContext?.positionRevision ?? 0,
      scope: effectiveSearchScope.scope,
      expansion_km: effectiveSearchScope.expansion_km,
      radio_km: null,
      limit,
    };

    queryClient.prefetchInfiniteQuery(
      getExplorarEspaciosInfiniteQueryOptions(paramsBusqueda)
    );
  }

  async function confirmarBusqueda(valor) {
    const q = normalizarBusqueda(valor);
    if (!q) return;

    const needsRefresh =
      geographicContext.source === "device" && (!territoryFresh || !distanceFresh);
    if (needsRefresh) {
      await requestDeviceLocation({ needDistance: true });
    }

    setBusqueda(q);
    guardarEnHistorialBusqueda(q);
    if (!needsRefresh) prefetchBusquedaEspacios(q);
    setBuscadorActivo(false);
  }

  function manejarTeclaBuscador(event) {
    if (event.key === "Enter") {
      confirmarBusqueda(busqueda);
    }

    if (event.key === "Escape") {
      setBuscadorActivo(false);
    }
  }

  function getNombrePublicacion(publicacion) {
    return (
      publicacion?.titulo ||
      publicacion?.comercio_nombre ||
      publicacion?.nombre_comercio ||
      publicacion?.comercio?.nombre ||
      "Publicación"
    );
  }

  function getSubtituloPublicacion(publicacion) {
    return (
      publicacion?.comercio_nombre ||
      publicacion?.nombre_comercio ||
      publicacion?.comercio?.nombre ||
      publicacion?.descripcion ||
      "MiPlaza"
    );
  }

  function esVideo(url) {
  if (!url || typeof url !== "string") return false;

  return [".mp4", ".webm", ".ogg", ".mov"].some((ext) =>
    url.toLowerCase().includes(ext)
  );
  }

  function irAPerfilComercio(comercioId) {
    if (!comercioId) return;
    navigate(`/comercios/${comercioId}`);
  }

  function irADetallePublicacion(publicacionId) {
    if (!publicacionId) return;
    navigate(`/publicaciones/${publicacionId}`);
  }

  const qUI = busquedaNormalizada;
  const modoIAActivo = usarModoIA(qUI, modoExplorar);

  const publicacionesFiltradas = publicacionesQueryData;

  const itemsActuales =
    modoExplorar === "publicaciones"
      ? publicacionesFiltradas
      : espaciosQueryData;

  const sugerenciasBusqueda = Array.isArray(
    sugerenciasQuery.data?.suggestions
  )
    ? sugerenciasQuery.data.suggestions
    : [];

  const opcionesBuscador = busquedaNormalizada
    ? sugerenciasBusqueda.map((sugerencia) => ({
        key: `${sugerencia.type}-${sugerencia.id}`,
        label: sugerencia.label,
        meta: formatearTipoSugerencia(sugerencia.type),
        value: sugerencia.label,
      }))
    : historialBusqueda.map((item, index) => ({
        key: `historial-${item}-${index}`,
        label: item,
        meta: "Reciente",
        value: item,
      }));

  const mostrarPanelBuscador =
    modoExplorar === "espacios" && buscadorActivo && opcionesBuscador.length > 0;

  function formatearTipoSugerencia(type) {
    if (type === "rubro") return "Rubro";
    if (type === "categoria") return "Categoria";
    if (type === "subcategoria") return "Subcategoria";
    return "Sugerencia";
  }

  return (
    <div className="space-y-3 bg-canvas px-1 py-3 text-primary sm:space-y-4 sm:p-4">
      {/* HEADER */}
      <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl font-semibold">Explorar</h1>

        <div className="flex max-w-full flex-wrap items-center gap-2">
          <Button
            type="button"
            onClick={() => cambiarModoExplorar("espacios")}
            variant="secondary"
            aria-pressed={modoExplorar === "espacios"}
            className={`rounded-full px-3 py-1 text-xs ${
              modoExplorar === "espacios"
                ? "border-selected-border bg-selected-surface text-selected-text"
                : ""
            }`}
          >
            Espacios
          </Button>

          <Button
            type="button"
            onClick={() => cambiarModoExplorar("publicaciones")}
            variant="secondary"
            aria-pressed={modoExplorar === "publicaciones"}
            className={`rounded-full px-3 py-1 text-xs ${
              modoExplorar === "publicaciones"
                ? "border-selected-border bg-selected-surface text-selected-text"
                : ""
            }`}
          >
            Publicaciones
          </Button>

          {modoIAActivo && (
            <span className="rounded-full border border-selected-border bg-selected-surface px-3 py-1 text-xs text-selected-text">
              ✨ IA
            </span>
          )}
        </div>
      </div>

      {/* BUSCADOR */}
      <div className="relative">
        <Input
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          onFocus={() => setBuscadorActivo(true)}
          onBlur={() => {
            setTimeout(() => setBuscadorActivo(false), 120);
          }}
          onKeyDown={manejarTeclaBuscador}
          aria-label="Buscar en Explorar"
          placeholder={
            modoExplorar === "publicaciones"
              ? "Buscar publicaciones..."
              : "Buscar comercios..."
          }
          className="text-sm"
        />

        {mostrarPanelBuscador && (
          <Surface
            variant="elevated"
            className="absolute left-0 right-0 top-full z-20 mt-1 overflow-hidden"
          >
            {opcionesBuscador.map((opcion) => (
              <Button
                key={opcion.key}
                type="button"
                onMouseDown={(event) => {
                  event.preventDefault();
                  confirmarBusqueda(opcion.value);
                }}
                variant="ghost"
                className="flex w-full items-center justify-between gap-3 rounded-none px-3 py-2 text-left text-sm hover:bg-surface-subtle"
              >
                <span className="truncate font-medium">{opcion.label}</span>
                <span className="shrink-0 text-xs text-muted">
                  {opcion.meta}
                </span>
              </Button>
            ))}
          </Surface>
        )}
      </div>

      {modoExplorar === "espacios" && <GeographicContextControls />}

      {/* ERROR */}
      {error && (
        <Alert role="alert" variant="danger">
          {error}
        </Alert>
      )}

      {estaCargandoQuery && itemsActuales.length === 0 && hasTerritory && (
        <Surface variant="subtle" className="flex items-center gap-3 p-3">
          <Skeleton className="h-4 w-20 rounded-full" />
          <p className="text-sm text-secondary">Cargando...</p>
        </Surface>
      )}

      {/* GRID DE COMERCIOS */}
      {modoExplorar === "espacios" && (
        <div
          className="
            grid 
            grid-cols-3 
            sm:grid-cols-3 
            md:grid-cols-4 
            gap-1.5
            sm:gap-3
          "
        >
          {espaciosQueryData.map((c) => {
            const comercioImagenUrl = getMediaUrlFromAny(c);

            return (
              <Surface
                key={c.id}
                onClick={() => irAPerfilComercio(c.id)}
                className="group cursor-pointer overflow-hidden"
              >
                {/* IMAGEN */}
                <div className="aspect-square w-full overflow-hidden bg-surface-subtle">
                  {comercioImagenUrl ? (
                    <img
                      src={comercioImagenUrl}
                      alt={c.nombre || "Comercio"}
                      loading="lazy"
                      decoding="async"
                      className="w-full h-full object-cover group-hover:scale-105 transition"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center text-xs text-muted">
                      Sin imagen
                    </div>
                  )}
                </div>

                {/* INFO */}
                <div className="p-2">
                  <p className="text-sm font-medium truncate">
                    {c.nombre || "Comercio"}
                  </p>

                  <p className="truncate text-xs text-secondary">
                    {c.ciudad || "Ciudad"}
                  </p>

                  {typeof c.distancia_km === "number" && (
                    <p className="text-xs text-brand">
                      📍 {c.distancia_km < 1
                        ? `${Math.round(c.distancia_km * 1000)} m`
                        : `${c.distancia_km.toFixed(1)} km`}
                    </p>
                  )}
                  <EstadoHorarioBadge
                    horarioAtencion={c.horario_atencion}
                    compact
                    className="mt-1"
                  />
                </div>
              </Surface>
            );
          })}
        </div>
      )}

      {/* GRID DE PUBLICACIONES */}
      {modoExplorar === "publicaciones" && (
        <div
          className="
            grid 
            grid-cols-3 
            sm:grid-cols-3 
            md:grid-cols-4 
            gap-1.5
            sm:gap-3
          "
        >
          {publicacionesFiltradas.map((p) => {
            const publicacionImagenUrl = getMediaUrlFromAny(p);

            return (
              <Surface
                key={p.id}
                onClick={() => irADetallePublicacion(p.id)}
                className="group cursor-pointer overflow-hidden"
              >
                {/* IMAGEN */}
                <div className="aspect-square w-full overflow-hidden bg-surface-subtle">
                  {publicacionImagenUrl ? (
                    esVideo(publicacionImagenUrl) ? (
                      <video
                        src={publicacionImagenUrl}
                        autoPlay
                        muted
                        loop
                        playsInline
                        preload="metadata"
                        className="w-full h-full object-cover group-hover:scale-105 transition"
                      />
                    ) : (
                      <img
                        src={publicacionImagenUrl}
                        alt={getNombrePublicacion(p)}
                        loading="lazy"
                        decoding="async"
                        className="w-full h-full object-cover group-hover:scale-105 transition"
                      />
                    )
                  ) : (
                    <div className="flex h-full w-full items-center justify-center text-xs text-muted">
                      Sin imagen
                    </div>
                  )}
                </div>

                {/* INFO */}
                <div className="p-2">
                  <p className="text-sm font-medium truncate">
                    {getNombrePublicacion(p)}
                  </p>

                  <p className="truncate text-xs text-secondary">
                    {getSubtituloPublicacion(p)}
                  </p>
                </div>
              </Surface>
            );
          })}
        </div>
      )}

      {/* SIN RESULTADOS */}
      {!estaCargandoQuery && itemsActuales.length === 0 && !error && (
        <Surface variant="subtle" className="p-3">
          <p className="text-sm">
            {modoExplorar === "publicaciones"
              ? "No hay publicaciones para mostrar."
              : hasTerritory
                ? `No encontramos resultados en ${geographicContext.city}.`
                : "Elegí una ciudad o usá tu ubicación para buscar espacios."}
          </p>
          {modoExplorar === "espacios" && hasTerritory && queryContext?.lat !== null && effectiveSearchScope.scope === "local" && (
            <Button
              type="button"
              onClick={() => setSearchScope({ scope: "expanded", expansion_km: 50, territoryId: activeTerritoryId })}
              variant="secondary"
              className="mt-2 px-3 py-2 text-xs"
            >
              Ver opciones cercanas fuera de {geographicContext.city}
            </Button>
          )}
          {modoExplorar === "espacios" && hasTerritory && effectiveSearchScope.expansion_km === 50 && (
            <Button
              type="button"
              onClick={() => setSearchScope({ scope: "expanded", expansion_km: 100, territoryId: activeTerritoryId })}
              variant="secondary"
              className="mt-2 px-3 py-2 text-xs"
            >
              Ampliar búsqueda hasta 100 km
            </Button>
          )}
        </Surface>
      )}

        {/* PAGINACIÓN TANSTACK */}
    {modoExplorar === "espacios" && espaciosQueryData.length > 0 && (
      <div className="pt-2">
        {espaciosQuery.hasNextPage ? (
          <Button
            type="button"
            onClick={() => espaciosQuery.fetchNextPage()}
            disabled={espaciosQuery.isFetchingNextPage}
            variant="secondary"
            className="w-full px-4 py-2"
          >
            {espaciosQuery.isFetchingNextPage ? "Cargando..." : "Cargar más"}
          </Button>
        ) : (
          <p className="text-center text-sm text-secondary">
            No hay más resultados.
          </p>
        )}
      </div>
      )}

    </div>
  );
}

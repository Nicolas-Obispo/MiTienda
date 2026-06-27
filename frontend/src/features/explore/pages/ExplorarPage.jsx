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
import { queryKeys } from "@core/constants/queryKeys";
import {
  useExplorarEspacios,
  useExplorarPublicaciones,
} from "@features/explore";
import { listarComerciosActivos } from "@features/spaces";

import { useNavigate } from "react-router-dom";
import { useSearchSuggestions } from "@features/search/hooks/useSearchSuggestions";
import { getMediaUrlFromAny } from "@shared";

const HISTORIAL_BUSQUEDA_KEY = "miplaza_explorar_historial_busqueda";
const HISTORIAL_BUSQUEDA_MAX = 5;

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

  const [ubicacion, setUbicacion] = useState({
    lat: null,
    lng: null,
    lista: false,
    error: null,
  });

  useEffect(() => {
    if (!navigator.geolocation) {
      queueMicrotask(() => {
        setUbicacion((prev) => ({
          ...prev,
          lista: true,
          error: "Ubicación no disponible",
        }));
      });
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUbicacion({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          lista: true,
          error: null,
        });
      },
      () => {
        setUbicacion((prev) => ({
          ...prev,
          lista: true,
          error: "Ubicación no disponible",
        }));
      }
    );
  }, []);

  const busquedaNormalizada = _normalizarBusqueda(busqueda);
  const usarSmartSemantic = _usarModoIA(busquedaNormalizada);

  useEffect(() => {
    const timer = setTimeout(() => {
      setBusquedaSugerenciasDebounced(_normalizarBusqueda(busqueda));
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
    smart: usarSmartSemantic ? false : _usarModoIA(busquedaNormalizada),
    smart_semantic: usarSmartSemantic,
    lat: ubicacion.lista ? ubicacion.lat : null,
    lng: ubicacion.lista ? ubicacion.lng : null,
    limit,
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

  function _normalizarBusqueda(valor) {
    if (!valor) return null;
    const t = valor.trim();
    return t ? t : null;
  }

  function _usarModoIA(q) {
    return Boolean(q) && modoExplorar === "espacios";
  }

  function cambiarModoExplorar(nuevoModo) {
    setModoExplorar(nuevoModo);
    localStorage.setItem("miplaza_explorar_modo", nuevoModo);
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

  function guardarEnHistorialBusqueda(valor) {
    const q = _normalizarBusqueda(valor);
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
    const q = _normalizarBusqueda(valor);
    if (!q) return;

    const paramsBusqueda = {
      q,
      smart: false,
      smart_semantic: true,
      lat: ubicacion.lista ? ubicacion.lat : null,
      lng: ubicacion.lista ? ubicacion.lng : null,
      radio_km: null,
      limit,
    };

    queryClient.prefetchInfiniteQuery({
      queryKey: queryKeys.explore.spaces(paramsBusqueda),
      initialPageParam: 0,
      queryFn: ({ pageParam = 0 }) =>
        listarComerciosActivos({
          ...paramsBusqueda,
          offset: pageParam,
        }),
      getNextPageParam: (lastPage, allPages) => {
        const ultimaPagina = Array.isArray(lastPage) ? lastPage : [];

        if (ultimaPagina.length < limit) {
          return undefined;
        }

        return allPages.length * limit;
      },
      staleTime: 1000 * 30,
    });
  }

  function confirmarBusqueda(valor) {
    const q = _normalizarBusqueda(valor);
    if (!q) return;

    setBusqueda(q);
    guardarEnHistorialBusqueda(q);
    prefetchBusquedaEspacios(q);
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

  function publicacionCoincideConBusqueda(publicacion, q) {
    if (!q) return true;

    const texto = [
      publicacion?.titulo,
      publicacion?.descripcion,
      publicacion?.comercio_nombre,
      publicacion?.nombre_comercio,
      publicacion?.comercio?.nombre,
      publicacion?.comercio?.nombre_comercio,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

    return texto.includes(q.toLowerCase());
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
  const modoIAActivo = _usarModoIA(qUI);

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
    <div className="px-1 py-3 space-y-3 sm:p-4 sm:space-y-4">
      {/* HEADER */}
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">Explorar</h1>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => cambiarModoExplorar("espacios")}
            className={`rounded-full border px-3 py-1 text-xs font-semibold transition ${
              modoExplorar === "espacios"
                ? "border-white bg-white text-gray-950 shadow"
                : "border-gray-300 bg-transparent text-gray-700"
            }`}
          >
            Espacios
          </button>

          <button
            type="button"
            onClick={() => cambiarModoExplorar("publicaciones")}
            className={`rounded-full border px-3 py-1 text-xs font-semibold transition ${
              modoExplorar === "publicaciones"
                ? "border-white bg-white text-gray-950 shadow"
                : "border-gray-300 bg-transparent text-gray-700"
            }`}
          >
            Publicaciones
          </button>

          {modoIAActivo && (
            <span className="text-xs rounded-full border px-3 py-1">
              ✨ IA
            </span>
          )}
        </div>
      </div>

      {/* BUSCADOR */}
      <div className="relative">
        <input
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          onFocus={() => setBuscadorActivo(true)}
          onBlur={() => {
            setTimeout(() => setBuscadorActivo(false), 120);
          }}
          onKeyDown={manejarTeclaBuscador}
          placeholder={
            modoExplorar === "publicaciones"
              ? "Buscar publicaciones..."
              : "Buscar comercios..."
          }
          className="w-full rounded-xl border px-3 py-2"
        />

        {mostrarPanelBuscador && (
          <div className="absolute left-0 right-0 top-full z-20 mt-1 overflow-hidden rounded-xl border bg-white text-gray-950 shadow-lg">
            {opcionesBuscador.map((opcion) => (
              <button
                key={opcion.key}
                type="button"
                onMouseDown={(event) => {
                  event.preventDefault();
                  confirmarBusqueda(opcion.value);
                }}
                className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm hover:bg-gray-100"
              >
                <span className="truncate font-medium">{opcion.label}</span>
                <span className="shrink-0 text-xs text-gray-500">
                  {opcion.meta}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* ERROR */}
      {error && (
        <div className="rounded-xl border p-3">
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* LOADING INICIAL */}
      {modoExplorar === "espacios" && !ubicacion.lista && (
        <div className="rounded-xl border p-3">
          <p className="text-sm">Buscando ubicación...</p>
        </div>
      )}

      {estaCargandoQuery && itemsActuales.length === 0 && ubicacion.lista && (
        <div className="rounded-xl border p-3">
          <p className="text-sm">Cargando...</p>
        </div>
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
              <div
                key={c.id}
                onClick={() => irAPerfilComercio(c.id)}
                className="cursor-pointer group"
              >
                {/* IMAGEN */}
                <div className="w-full aspect-square rounded-xl overflow-hidden border bg-gray-100">
                  {comercioImagenUrl ? (
                    <img
                      src={comercioImagenUrl}
                      alt={c.nombre || "Comercio"}
                      loading="lazy"
                      decoding="async"
                      className="w-full h-full object-cover group-hover:scale-105 transition"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-xs">
                      Sin imagen
                    </div>
                  )}
                </div>

                {/* INFO */}
                <div className="mt-1 px-1">
                  <p className="text-sm font-medium truncate">
                    {c.nombre || "Comercio"}
                  </p>

                  <p className="text-xs opacity-70 truncate">
                    {c.ciudad || "Ciudad"}
                  </p>

                  {typeof c.distancia_km === "number" && (
                    <p className="text-xs text-orange-500">
                      📍 {c.distancia_km < 1
                        ? `${Math.round(c.distancia_km * 1000)} m`
                        : `${c.distancia_km.toFixed(1)} km`}
                    </p>
                  )}
                  {ubicacion.error && typeof c.distancia_km !== "number" && (
                    <p className="text-xs text-orange-500">
                      {ubicacion.error}
                    </p>
                  )}
                </div>
              </div>
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
              <div
                key={p.id}
                onClick={() => irADetallePublicacion(p.id)}
                className="cursor-pointer group"
              >
                {/* IMAGEN */}
                <div className="w-full aspect-square rounded-xl overflow-hidden border bg-gray-100">
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
                    <div className="w-full h-full flex items-center justify-center text-xs">
                      Sin imagen
                    </div>
                  )}
                </div>

                {/* INFO */}
                <div className="mt-1 px-1">
                  <p className="text-sm font-medium truncate">
                    {getNombrePublicacion(p)}
                  </p>

                  <p className="text-xs opacity-70 truncate">
                    {getSubtituloPublicacion(p)}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* SIN RESULTADOS */}
      {!estaCargandoQuery && itemsActuales.length === 0 && !error && (
        <div className="rounded-xl border p-3">
          <p className="text-sm">
            {modoExplorar === "publicaciones"
              ? "No hay publicaciones para mostrar."
              : "No hay comercios para mostrar."}
          </p>
        </div>
      )}

        {/* PAGINACIÓN TANSTACK */}
    {modoExplorar === "espacios" && espaciosQueryData.length > 0 && (
      <div className="pt-2">
        {espaciosQuery.hasNextPage ? (
          <button
            type="button"
            onClick={() => espaciosQuery.fetchNextPage()}
            disabled={espaciosQuery.isFetchingNextPage}
            className="w-full rounded-xl border px-4 py-2"
          >
            {espaciosQuery.isFetchingNextPage ? "Cargando..." : "Cargar más"}
          </button>
        ) : (
          <p className="text-sm opacity-70 text-center">
            No hay más resultados.
          </p>
        )}
      </div>
      )}

    </div>
  );
}

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
import {
  useExplorarEspacios,
  useExplorarPublicaciones,
} from "@features/explore";

import { useNavigate } from "react-router-dom";
import { getMediaUrlFromAny } from "@shared";

export default function ExplorarPage() {
  const [busqueda, setBusqueda] = useState("");

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

  const espaciosQuery = useExplorarEspacios({
    q: _normalizarBusqueda(busqueda),
    smart: _usarModoIA(_normalizarBusqueda(busqueda)),
    lat: ubicacion.lista ? ubicacion.lat : null,
    lng: ubicacion.lista ? ubicacion.lng : null,
    limit,
  });

  const publicacionesQuery = useExplorarPublicaciones({
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

  const qUI = _normalizarBusqueda(busqueda);
  const modoIAActivo = _usarModoIA(qUI);

  const publicacionesFiltradas = publicacionesQueryData.filter((publicacion) =>
    publicacionCoincideConBusqueda(publicacion, qUI)
  );

  const itemsActuales =
    modoExplorar === "publicaciones"
      ? publicacionesFiltradas
      : espaciosQueryData;

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
      <input
        value={busqueda}
        onChange={(e) => setBusqueda(e.target.value)}
        placeholder={
          modoExplorar === "publicaciones"
            ? "Buscar publicaciones..."
            : "Buscar comercios..."
        }
        className="w-full rounded-xl border px-3 py-2"
      />

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

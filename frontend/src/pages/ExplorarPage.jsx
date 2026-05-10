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

import React, { useEffect, useRef, useState } from "react";
import { listarComerciosActivos } from "../services/comercios_service";
import { fetchPublicacionesPublicas } from "../services/feed_service";
import { useNavigate } from "react-router-dom";
import { getMediaUrlFromAny } from "../utils/mediaUrl";

export default function ExplorarPage() {
  const [busqueda, setBusqueda] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  const [modoExplorar, setModoExplorar] = useState(() => {
    const modoGuardado = localStorage.getItem("miplaza_explorar_modo");

    if (modoGuardado === "publicaciones") return "publicaciones";
    return "espacios";
  });

  const [comercios, setComercios] = useState([]);
  const [publicaciones, setPublicaciones] = useState([]);

  const [limit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [hayMas, setHayMas] = useState(true);

  const navigate = useNavigate();
  const debounceRef = useRef(null);

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

  async function cargarPrimerPagina(qRaw) {
    setCargando(true);
    setError("");

    const q = _normalizarBusqueda(qRaw);
    const smart = _usarModoIA(q);

    try {
      if (modoExplorar === "publicaciones") {
        const data = await fetchPublicacionesPublicas({
          limit,
          offset: 0,
        });
        const lista = Array.isArray(data) ? data : [];

        setPublicaciones(lista);
        setHayMas(false);
        return;
      }

      const data = await listarComerciosActivos({
        q,
        smart,
        limit,
        offset: 0,
      });

      const lista = Array.isArray(data) ? data : [];

      setComercios(lista);
      setOffset(lista.length);
      setHayMas(lista.length === limit);
    } catch (e) {
      setError(
        e?.message ||
          (modoExplorar === "publicaciones"
            ? "Error al cargar publicaciones"
            : "Error al cargar comercios")
      );

      if (modoExplorar === "publicaciones") {
        setPublicaciones([]);
      } else {
        setComercios([]);
      }

      setOffset(0);
      setHayMas(false);
    } finally {
      setCargando(false);
    }
  }

  async function cargarMas() {
    if (cargando || !hayMas || modoExplorar === "publicaciones") return;

    setCargando(true);
    setError("");

    const q = _normalizarBusqueda(busqueda);
    const smart = _usarModoIA(q);

    try {
      const data = await listarComerciosActivos({
        q,
        smart,
        limit,
        offset,
      });

      const lista = Array.isArray(data) ? data : [];

      setComercios((prev) => [...prev, ...lista]);
      setOffset((prev) => prev + lista.length);
      setHayMas(lista.length === limit);
    } catch (e) {
      setError(e?.message || "Error al cargar más comercios");
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => {
    cargarPrimerPagina(null);
    // eslint-disable-next-line
  }, [modoExplorar]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    const q = _normalizarBusqueda(busqueda);

    if (!q) {
      debounceRef.current = setTimeout(() => {
        cargarPrimerPagina(null);
      }, 200);
      return;
    }

    debounceRef.current = setTimeout(() => {
      cargarPrimerPagina(q);
    }, 350);

    return () => clearTimeout(debounceRef.current);
    // eslint-disable-next-line
  }, [busqueda]);

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

  const publicacionesFiltradas = publicaciones.filter((publicacion) =>
    publicacionCoincideConBusqueda(publicacion, qUI)
  );

  const itemsActuales =
    modoExplorar === "publicaciones" ? publicacionesFiltradas : comercios;

  return (
    <div className="p-4 space-y-4">
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
      {cargando && itemsActuales.length === 0 && (
        <div className="rounded-xl border p-3">
          <p className="text-sm">Cargando...</p>
        </div>
      )}

      {/* GRID DE COMERCIOS */}
      {modoExplorar === "espacios" && (
        <div
          className="
            grid 
            grid-cols-2 
            sm:grid-cols-3 
            md:grid-cols-4 
            gap-3
          "
        >
          {comercios.map((c) => {
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
            grid-cols-2 
            sm:grid-cols-3 
            md:grid-cols-4 
            gap-3
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
                        className="w-full h-full object-cover group-hover:scale-105 transition"
                      />
                    ) : (
                      <img
                        src={publicacionImagenUrl}
                        alt={getNombrePublicacion(p)}
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
      {!cargando && itemsActuales.length === 0 && !error && (
        <div className="rounded-xl border p-3">
          <p className="text-sm">
            {modoExplorar === "publicaciones"
              ? "No hay publicaciones para mostrar."
              : "No hay comercios para mostrar."}
          </p>
        </div>
      )}

      {/* PAGINACIÓN */}
      {modoExplorar === "espacios" && (
        <div className="pt-2">
          {hayMas ? (
            <button
              onClick={cargarMas}
              disabled={cargando}
              className="w-full rounded-xl border px-4 py-2"
            >
              {cargando ? "Cargando..." : "Cargar más"}
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
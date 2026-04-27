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
 * NO se toca lógica de backend
 */

import React, { useEffect, useRef, useState } from "react";
import { listarComerciosActivos } from "../services/comercios_service";
import { useNavigate } from "react-router-dom";
import { getMediaUrlFromAny } from "../utils/mediaUrl";

export default function ExplorarPage() {
  const [busqueda, setBusqueda] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  const [comercios, setComercios] = useState([]);

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
    return Boolean(q);
  }

  async function cargarPrimerPagina(qRaw) {
    setCargando(true);
    setError("");

    const q = _normalizarBusqueda(qRaw);
    const smart = _usarModoIA(q);

    try {
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
      setError(e?.message || "Error al cargar comercios");
      setComercios([]);
      setOffset(0);
      setHayMas(false);
    } finally {
      setCargando(false);
    }
  }

  async function cargarMas() {
    if (cargando || !hayMas) return;

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
  }, []);

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

  const qUI = _normalizarBusqueda(busqueda);
  const modoIAActivo = _usarModoIA(qUI);

  return (
    <div className="p-4 space-y-4">
      {/* HEADER */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Explorar</h1>

        {modoIAActivo && (
          <span className="text-xs rounded-full border px-3 py-1">
            ✨ IA
          </span>
        )}
      </div>

      {/* BUSCADOR */}
      <input
        value={busqueda}
        onChange={(e) => setBusqueda(e.target.value)}
        placeholder="Buscar comercios..."
        className="w-full rounded-xl border px-3 py-2"
      />

      {/* ERROR */}
      {error && (
        <div className="rounded-xl border p-3">
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* LOADING INICIAL */}
      {cargando && comercios.length === 0 && (
        <div className="rounded-xl border p-3">
          <p className="text-sm">Cargando...</p>
        </div>
      )}

      {/* GRID DE COMERCIOS */}
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

      {/* SIN RESULTADOS */}
      {!cargando && comercios.length === 0 && !error && (
        <div className="rounded-xl border p-3">
          <p className="text-sm">No hay comercios para mostrar.</p>
        </div>
      )}

      {/* PAGINACIÓN */}
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
    </div>
  );
}
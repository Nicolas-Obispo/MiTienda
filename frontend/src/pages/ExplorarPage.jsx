/**
 * ExplorarPage.jsx
 * ----------------
 * ETAPA 48 — Explorar (Discovery de comercios activos)
 * ETAPA 50 — IA v1 (MVP):
 * - smart=true cuando hay búsqueda (q)
 * - Indicador visual: "✨ Modo IA"
 *
 * ETAPA 50.3 — UX:
 * - Search as you type (debounce)
 * - Reset automático al borrar el input
 *
 * Reglas de oro:
 * - El frontend no inventa estado
 * - Todo sale del backend (/comercios/activos)
 */

import React, { useEffect, useRef, useState } from "react";
import { listarComerciosActivos } from "../services/comercios_service";
import { useNavigate } from "react-router-dom";

export default function ExplorarPage() {
  // Estado UI
  const [busqueda, setBusqueda] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  // Datos
  const [comercios, setComercios] = useState([]);

  // Paginado MVP
  const [limit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [hayMas, setHayMas] = useState(true);

  const navigate = useNavigate();

  // Debounce timer
  const debounceRef = useRef(null);

  /**
   * _normalizarBusqueda
   * - Evita enviar strings vacíos al backend
   * - Devuelve null si no hay búsqueda real
   */
  function _normalizarBusqueda(valor) {
    if (!valor) return null;
    const t = valor.trim();
    return t ? t : null;
  }

  /**
   * _usarModoIA
   * - UX: solo activamos IA cuando hay búsqueda real (q)
   */
  function _usarModoIA(q) {
    return Boolean(q);
  }

  /**
   * cargarPrimerPagina
   * - Resetea lista y offset
   */
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

  /**
   * cargarMas
   * - Trae la siguiente página usando offset actual
   */
  async function cargarMas() {
    if (cargando) return;
    if (!hayMas) return;

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

  /**
   * useEffect inicial
   * Carga primera página sin filtro
   */
  useEffect(() => {
    cargarPrimerPagina(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /**
   * handleBuscar
   * - Se mantiene por compatibilidad UX (botón), pero ya no es necesario
   */
  async function handleBuscar(e) {
    e.preventDefault();
    await cargarPrimerPagina(busqueda);
  }

  /**
   * ETAPA 50.3 — Search as you type (debounce)
   * - Cuando cambia busqueda:
   *   - si está vacía -> resetea lista completa
   *   - si tiene texto -> busca automáticamente con debounce
   */
  useEffect(() => {
    // Cancelar timer anterior si existe
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    const q = _normalizarBusqueda(busqueda);

    // Si no hay búsqueda, volvemos a listar todo automáticamente
    if (!q) {
      debounceRef.current = setTimeout(() => {
        cargarPrimerPagina(null);
      }, 200); // rápido para sentir reset inmediato
      return () => {
        if (debounceRef.current) clearTimeout(debounceRef.current);
      };
    }

    // Si hay búsqueda, debounce para no spamear backend
    debounceRef.current = setTimeout(() => {
      cargarPrimerPagina(q);
    }, 350);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busqueda]);

  /**
   * irAPerfilComercio
   * Navega al perfil de comercio
   */
  function irAPerfilComercio(comercioId) {
    if (!comercioId) return;
    navigate(`/comercios/${comercioId}`);
  }

  const qUI = _normalizarBusqueda(busqueda);
  const modoIAActivo = _usarModoIA(qUI);

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">Explorar</h1>

        {modoIAActivo ? (
          <span className="text-xs rounded-full border px-3 py-1">
            ✨ Modo IA
          </span>
        ) : null}
      </div>

      <form onSubmit={handleBuscar} className="flex gap-2">
        <input
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          placeholder="Buscar comercios por nombre..."
          className="flex-1 rounded-xl border px-3 py-2"
        />
        <button
          type="submit"
          disabled={cargando}
          className="rounded-xl px-4 py-2 border"
          title="Opcional: también podés escribir y buscar automático"
        >
          Buscar
        </button>
      </form>

      {error ? (
        <div className="rounded-xl border p-3">
          <p className="text-sm">{error}</p>
        </div>
      ) : null}

      {cargando && comercios.length === 0 ? (
        <div className="rounded-xl border p-3">
          <p className="text-sm">Cargando...</p>
        </div>
      ) : null}

      <div className="space-y-2">
        {comercios.map((c) => (
          <button
            key={c.id}
            onClick={() => irAPerfilComercio(c.id)}
            className="w-full text-left rounded-2xl border p-3 hover:bg-black/5"
          >
            <div className="flex items-start gap-3">
              {c.portada_url ? (
                <img
                  src={c.portada_url}
                  alt={c.nombre}
                  className="h-14 w-14 rounded-xl object-cover border"
                />
              ) : (
                <div className="h-14 w-14 rounded-xl border flex items-center justify-center text-xs">
                  Sin foto
                </div>
              )}

              <div className="flex-1">
                <p className="font-medium">{c.nombre}</p>
                <p className="text-sm opacity-80">
                  {c.ciudad ? `${c.ciudad}` : "Ciudad no informada"}
                  {c.provincia ? `, ${c.provincia}` : ""}
                </p>
                {c.descripcion ? (
                  <p className="text-sm opacity-80 line-clamp-2">
                    {c.descripcion}
                  </p>
                ) : null}
              </div>
            </div>
          </button>
        ))}

        {!cargando && comercios.length === 0 && !error ? (
          <div className="rounded-xl border p-3">
            <p className="text-sm">No hay comercios para mostrar.</p>
          </div>
        ) : null}
      </div>

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
/**
 * ProfilePage.jsx
 * ----------------
 * ETAPA 39 (Perfil de usuario) - Guardados
 * ETAPA 45 (Orden UX navegación) - Admin: "Mis comercios" + acciones (Crear / Editar / Desactivar)
 *
 * Objetivo:
 * - Mantener: publicaciones guardadas del usuario (GET /publicaciones/guardadas)
 * - Agregar arriba: "Mis comercios" (GET /comercios/mis)
 * - Acciones admin:
 *   - Crear comercio (POST /comercios)
 *   - Editar comercio (PUT /comercios/{id})
 *   - Desactivar comercio (DELETE /comercios/{id})
 *
 * Regla de oro:
 * - El frontend NO inventa estado de negocio.
 * - Solo consume backend y renderiza.
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import PublicacionCard from "../components/PublicacionCard";
import {
  fetchPublicacionesGuardadas,
  toggleLikePublicacion,
  guardarPublicacion,
  quitarPublicacionGuardada,
} from "../services/feed_service";
import {
  getMisComercios,
  crearComercio,
  desactivarComercio,
  actualizarComercio,
  reactivarComercio,
} from "../services/comercios_service";

export default function ProfilePage() {
  // ==========================
  // Estado: Guardados
  // ==========================
  const [isLoading, setIsLoading] = useState(true);
  const [publicaciones, setPublicaciones] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");

  // Locks por publicación
  const [likeLocks, setLikeLocks] = useState({});
  const [saveLocks, setSaveLocks] = useState({});

  const likeLocksMemo = useMemo(() => likeLocks, [likeLocks]);
  const saveLocksMemo = useMemo(() => saveLocks, [saveLocks]);

  function setLock(setter, pubId, value) {
    setter((prev) => ({ ...prev, [pubId]: value }));
  }

  // ==========================
  // Estado: Mis comercios (admin)
  // ==========================
  const [isLoadingComercios, setIsLoadingComercios] = useState(true);
  const [misComercios, setMisComercios] = useState([]);
  const [comerciosErrorMessage, setComerciosErrorMessage] = useState("");

  // Locks / estado para acciones admin
  const [isCreatingComercio, setIsCreatingComercio] = useState(false);
  const [isActingComercioById, setIsActingComercioById] = useState({}); // { [id]: true/false }

  // Form crear/editar (simple, mínimo viable)
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingComercioId, setEditingComercioId] = useState(null);
  const [createErrorMessage, setCreateErrorMessage] = useState("");
  const [createForm, setCreateForm] = useState({
    nombre: "",
    descripcion: "",
    portada_url: "",
    rubro_id: 1,
    provincia: "",
    ciudad: "",
    direccion: "",
    whatsapp: "",
    instagram: "",
    maps_url: "",
  });

  function setComercioLock(comercioId, value) {
    setIsActingComercioById((prev) => ({ ...prev, [comercioId]: value }));
  }

  // --------------------------
  // Helpers form
  // --------------------------
  function handleResetForm() {
    // Resetea modo edición + form (evita quedar "pegado" en editar)
    setEditingComercioId(null);
    setCreateErrorMessage("");
    setCreateForm({
      nombre: "",
      descripcion: "",
      portada_url: "",
      rubro_id: 1,
      provincia: "",
      ciudad: "",
      direccion: "",
      whatsapp: "",
      instagram: "",
      maps_url: "",
    });
  }

  /**
   * Inicia edición de un comercio:
   * - Precarga el formulario con datos reales del item listado
   * - Abre el form en modo edición
   */
  function handleEditarComercio(comercio) {
    if (!comercio?.id) return;

    setCreateErrorMessage("");
    setEditingComercioId(comercio.id);
    setShowCreateForm(true);

    setCreateForm({
      nombre: comercio.nombre || "",
      descripcion: comercio.descripcion || "",
      portada_url: comercio.portada_url || "",
      rubro_id: comercio.rubro_id || 1,
      provincia: comercio.provincia || "",
      ciudad: comercio.ciudad || "",
      direccion: comercio.direccion || "",
      whatsapp: comercio.whatsapp || "",
      instagram: comercio.instagram || "",
      maps_url: comercio.maps_url || "",
    });
  }

  // --------------------------
  // Cargar guardados
  // --------------------------
  async function loadGuardadas() {
    try {
      setIsLoading(true);
      setErrorMessage("");

      const guardadasData = await fetchPublicacionesGuardadas();

      const guardadasItems = Array.isArray(guardadasData)
        ? guardadasData
        : guardadasData?.items || [];

      // Normalizamos para que todas queden como publicaciones “guardadas por mí”
      const normalized = guardadasItems
        .map((g) => {
          if (g && typeof g.id === "number") return g;
          if (g?.publicacion && typeof g.publicacion.id === "number")
            return g.publicacion;
          return null;
        })
        .filter(Boolean)
        .map((p) => ({
          ...p,
          guardada_by_me: true,
        }));

      setPublicaciones(normalized);
    } catch (error) {
      setErrorMessage(error.message || "Error desconocido cargando guardados.");
      setPublicaciones([]);
    } finally {
      setIsLoading(false);
    }
  }

  // --------------------------
  // Cargar mis comercios
  // --------------------------
  async function loadMisComercios() {
    try {
      setIsLoadingComercios(true);
      setComerciosErrorMessage("");

      const data = await getMisComercios();
      const items = Array.isArray(data) ? data : data?.items || [];
      setMisComercios(items);
    } catch (error) {
      setComerciosErrorMessage(
        error.message || "Error desconocido cargando tus comercios."
      );
      setMisComercios([]);
    } finally {
      setIsLoadingComercios(false);
    }
  }

  useEffect(() => {
    loadMisComercios();
    loadGuardadas();
  }, []);

  /**
   * Optimistic Like
   */
  async function handleToggleLike(pubId) {
    if (likeLocksMemo[pubId]) return;

    setLock(setLikeLocks, pubId, true);

    const snapshot = publicaciones;

    setPublicaciones((prev) =>
      prev.map((p) => {
        if (p.id !== pubId) return p;

        const nextLiked = !p.liked_by_me;
        const delta = nextLiked ? 1 : -1;

        const nextLikesCount = Math.max(0, (p.likes_count || 0) + delta);
        const nextInteraccionesCount = Math.max(
          0,
          (p.interacciones_count || 0) + delta
        );

        return {
          ...p,
          liked_by_me: nextLiked,
          likes_count: nextLikesCount,
          interacciones_count: nextInteraccionesCount,
        };
      })
    );

    try {
      await toggleLikePublicacion(pubId);
    } catch (error) {
      setPublicaciones(snapshot);
      setErrorMessage(error.message || "Error al togglear like.");
    } finally {
      setLock(setLikeLocks, pubId, false);
    }
  }

  /**
   * Optimistic Guardado
   */
  async function handleToggleSave(pubId) {
    if (saveLocksMemo[pubId]) return;

    setLock(setSaveLocks, pubId, true);

    const snapshot = publicaciones;

    const current = publicaciones.find((p) => p.id === pubId);
    const estabaGuardada = Boolean(current?.guardada_by_me);

    if (estabaGuardada) {
      setPublicaciones((prev) => prev.filter((p) => p.id !== pubId));
    } else {
      setPublicaciones((prev) =>
        prev.map((p) => {
          if (p.id !== pubId) return p;

          const nextGuardadosCount = Math.max(0, (p.guardados_count || 0) + 1);
          const nextInteraccionesCount = Math.max(
            0,
            (p.interacciones_count || 0) + 1
          );

          return {
            ...p,
            guardada_by_me: true,
            guardados_count: nextGuardadosCount,
            interacciones_count: nextInteraccionesCount,
          };
        })
      );
    }

    try {
      if (estabaGuardada) {
        await quitarPublicacionGuardada(pubId);
      } else {
        await guardarPublicacion(pubId);
      }
    } catch (error) {
      setPublicaciones(snapshot);
      setErrorMessage(error.message || "Error al guardar/quitar guardado.");
    } finally {
      setLock(setSaveLocks, pubId, false);
    }
  }

  // =====================================================
  // ETAPA 45 — Crear / Editar comercio
  // =====================================================
  function handleCreateInputChange(e) {
    const { name, value } = e.target;

    if (name === "rubro_id") {
      setCreateForm((prev) => ({ ...prev, [name]: Number(value) }));
      return;
    }

    setCreateForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleCrearComercioSubmit(e) {
    e.preventDefault();

    try {
      setCreateErrorMessage("");
      setIsCreatingComercio(true);

      if (!createForm.nombre.trim()) throw new Error("El nombre es obligatorio.");
      if (!createForm.provincia.trim() || !createForm.ciudad.trim()) {
        throw new Error("Provincia y ciudad son obligatorias.");
      }

      // Payload limpio: strings vacíos -> null donde aplica
      const payload = {
        ...createForm,
        direccion: createForm.direccion?.trim() ? createForm.direccion.trim() : null,
        whatsapp: createForm.whatsapp?.trim() ? createForm.whatsapp.trim() : null,
        instagram: createForm.instagram?.trim() ? createForm.instagram.trim() : null,
        maps_url: createForm.maps_url?.trim() ? createForm.maps_url.trim() : null,
        portada_url: createForm.portada_url?.trim() ? createForm.portada_url.trim() : null,
        descripcion: createForm.descripcion?.trim() ? createForm.descripcion.trim() : "",
      };

      // ✅ Si estamos editando, hacemos PUT. Si no, POST.
      if (editingComercioId) {
        await actualizarComercio(editingComercioId, payload);
      } else {
        await crearComercio(payload);
      }

      // Refrescamos desde backend (estado real)
      await loadMisComercios();

      // Cerramos form y reseteamos
      setShowCreateForm(false);
      handleResetForm();
    } catch (error) {
      setCreateErrorMessage(error.message || "Error procesando el comercio.");
    } finally {
      setIsCreatingComercio(false);
    }
  }

  // =====================================================
  // ETAPA 45 — Desactivar comercio
  // =====================================================
  async function handleDesactivarComercio(comercioId) {
    if (!comercioId) return;
    if (isActingComercioById[comercioId]) return;

    const ok = window.confirm(
      "¿Seguro que querés desactivar este comercio? (Se puede reactivar en una etapa futura)"
    );
    if (!ok) return;

    try {
      setComerciosErrorMessage("");
      setComercioLock(comercioId, true);

      await desactivarComercio(comercioId);

      // Refrescamos desde backend (estado real)
      await loadMisComercios();
    } catch (error) {
      setComerciosErrorMessage(error.message || "Error desactivando el comercio.");
    } finally {
      setComercioLock(comercioId, false);
    }
  }
      // =====================================================
    // ETAPA 45 — Acciones admin: Reactivar comercio
    // =====================================================
  async function handleReactivarComercio(comercioId) {
    if (!comercioId) return;
    if (isActingComercioById[comercioId]) return;

    const ok = window.confirm("¿Querés reactivar este comercio?");
    if (!ok) return;

    try {
      setComerciosErrorMessage("");
      setComercioLock(comercioId, true);

      await reactivarComercio(comercioId);

      // Refrescamos desde backend (estado real)
      await loadMisComercios();
    } catch (error) {
      setComerciosErrorMessage(error.message || "Error reactivando el comercio.");
    } finally {
      setComercioLock(comercioId, false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <main className="mx-auto max-w-3xl px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-xl sm:text-2xl font-bold text-white">Mi Perfil</h1>
          <p className="mt-1 text-sm text-gray-400">
            Admin (mis comercios) + mis publicaciones guardadas.
          </p>
        </div>

        {/* ===================================================== */}
        {/* Sección: Mis comercios (admin) */}
        {/* ===================================================== */}
        <div className="mb-8">
          <div className="flex items-end justify-between gap-3">
            <h2 className="text-lg font-semibold">Mis comercios</h2>

            <button
              type="button"
              onClick={() => {
                setCreateErrorMessage("");
                setShowCreateForm((prev) => {
                  const next = !prev;

                  // Si lo abrimos para crear, aseguramos modo "crear"
                  if (next) handleResetForm();

                  // Si lo cerramos, limpiamos también
                  if (!next) handleResetForm();

                  return next;
                });
              }}
              className="rounded-xl border border-gray-800 bg-gray-950 px-4 py-2 text-sm hover:border-gray-700"
            >
              {showCreateForm ? "Cerrar" : "Crear comercio"}
            </button>
          </div>

          {/* Form crear/editar */}
          {showCreateForm && (
            <div className="mt-4 rounded-2xl border border-gray-800 bg-gray-950 p-5">
              <p className="font-semibold">
                {editingComercioId ? "Editar comercio" : "Nuevo comercio"}
              </p>

              <p className="mt-1 text-sm text-gray-400">
                Versión simple (ETAPA 45). Luego lo mejoramos con UI dedicada.
              </p>

              {createErrorMessage && (
                <div className="mt-3 rounded-xl border border-red-900 bg-red-950/40 p-4">
                  <p className="font-semibold text-red-200">Error</p>
                  <p className="mt-2 text-red-100 break-words">{createErrorMessage}</p>
                </div>
              )}

              <form onSubmit={handleCrearComercioSubmit} className="mt-4 space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-gray-400">Nombre *</label>
                    <input
                      name="nombre"
                      value={createForm.nombre}
                      onChange={handleCreateInputChange}
                      className="mt-1 w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm"
                      placeholder="Ej: Comercio Test"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-gray-400">Rubro ID *</label>
                    <input
                      name="rubro_id"
                      type="number"
                      value={createForm.rubro_id}
                      onChange={handleCreateInputChange}
                      className="mt-1 w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm"
                      min={1}
                    />
                  </div>

                  <div>
                    <label className="text-xs text-gray-400">Provincia *</label>
                    <input
                      name="provincia"
                      value={createForm.provincia}
                      onChange={handleCreateInputChange}
                      className="mt-1 w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm"
                      placeholder="Ej: Santa Fe"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-gray-400">Ciudad *</label>
                    <input
                      name="ciudad"
                      value={createForm.ciudad}
                      onChange={handleCreateInputChange}
                      className="mt-1 w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm"
                      placeholder="Ej: Rafaela"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs text-gray-400">Descripción</label>
                  <textarea
                    name="descripcion"
                    value={createForm.descripcion}
                    onChange={handleCreateInputChange}
                    className="mt-1 w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm"
                    rows={3}
                    placeholder="Breve descripción..."
                  />
                </div>

                <div>
                  <label className="text-xs text-gray-400">Portada URL</label>
                  <input
                    name="portada_url"
                    value={createForm.portada_url}
                    onChange={handleCreateInputChange}
                    className="mt-1 w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm"
                    placeholder="https://..."
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-gray-400">WhatsApp</label>
                    <input
                      name="whatsapp"
                      value={createForm.whatsapp}
                      onChange={handleCreateInputChange}
                      className="mt-1 w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm"
                      placeholder="+54..."
                    />
                  </div>

                  <div>
                    <label className="text-xs text-gray-400">Instagram</label>
                    <input
                      name="instagram"
                      value={createForm.instagram}
                      onChange={handleCreateInputChange}
                      className="mt-1 w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm"
                      placeholder="@mi_comercio"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-gray-400">Dirección</label>
                    <input
                      name="direccion"
                      value={createForm.direccion}
                      onChange={handleCreateInputChange}
                      className="mt-1 w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm"
                      placeholder="Calle 123"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-gray-400">Maps URL</label>
                    <input
                      name="maps_url"
                      value={createForm.maps_url}
                      onChange={handleCreateInputChange}
                      className="mt-1 w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm"
                      placeholder="https://maps..."
                    />
                  </div>
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <button
                    type="submit"
                    disabled={isCreatingComercio}
                    className="rounded-xl bg-white text-black px-4 py-2 text-sm font-semibold disabled:opacity-60"
                  >
                    {isCreatingComercio
                      ? "Procesando..."
                      : editingComercioId
                      ? "Guardar cambios"
                      : "Crear"}
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setShowCreateForm(false);
                      handleResetForm();
                    }}
                    className="rounded-xl border border-gray-800 bg-gray-950 px-4 py-2 text-sm hover:border-gray-700"
                  >
                    Cancelar
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Loading */}
          {isLoadingComercios && (
            <div className="mt-3 space-y-2">
              <div className="h-16 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
              <div className="h-16 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
            </div>
          )}

          {/* Error */}
          {!isLoadingComercios && comerciosErrorMessage && (
            <div className="mt-3 rounded-2xl border border-red-900 bg-red-950/40 p-5">
              <p className="font-semibold text-red-200">Error (Mis comercios)</p>
              <p className="mt-2 text-red-100 break-words">{comerciosErrorMessage}</p>
            </div>
          )}

          {/* Empty */}
          {!isLoadingComercios && !comerciosErrorMessage && misComercios.length === 0 && (
            <div className="mt-3 rounded-2xl border border-gray-800 bg-gray-950 p-6 text-center">
              <p className="text-gray-200 font-semibold">Todavía no tenés comercios</p>
              <p className="mt-2 text-gray-400 text-sm">
                Creá uno con el botón “Crear comercio”.
              </p>
            </div>
          )}

          {/* OK */}
          {!isLoadingComercios && !comerciosErrorMessage && misComercios.length > 0 && (
            <div className="mt-3 space-y-3">
              {misComercios.map((c) => {
                const isActing = Boolean(isActingComercioById[c.id]);

                return (
                  <div
                    key={c.id}
                    className="rounded-2xl border border-gray-800 bg-gray-950 p-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <Link
                        to={`/comercios/${c.id}`}
                        className="block hover:opacity-90"
                      >
                        <p className="font-semibold text-white">{c.nombre}</p>
                        <p className="mt-1 text-sm text-gray-400">
                          {(c.ciudad || "Ciudad") + ", " + (c.provincia || "Provincia")}
                        </p>
                        <p className="mt-2 text-xs text-gray-500">
                          {c.activo ? "Activo" : "Inactivo"} · ID {c.id}
                        </p>
                      </Link>
                      
                      {/* Acciones admin */}
                      <div className="flex flex-col items-end gap-2">
                        <button
                          type="button"
                          onClick={() => handleEditarComercio(c)}
                          disabled={isActing}
                          className="rounded-xl border border-gray-800 bg-gray-900 px-3 py-2 text-xs hover:border-gray-700 disabled:opacity-50"
                          title="Editar comercio"
                        >
                          Editar
                        </button>

                        {c.activo ? (
                          <button
                            type="button"
                            onClick={() => handleDesactivarComercio(c.id)}
                            disabled={isActing}
                            className="rounded-xl border border-gray-800 bg-gray-900 px-3 py-2 text-xs hover:border-gray-700 disabled:opacity-50"
                            title="Desactivar comercio"
                          >
                            {isActing ? "Procesando..." : "Desactivar"}
                          </button>
                        ) : (
                          <button
                            type="button"
                            onClick={() => handleReactivarComercio(c.id)}
                            disabled={isActing}
                            className="rounded-xl border border-gray-800 bg-gray-900 px-3 py-2 text-xs hover:border-gray-700 disabled:opacity-50"
                            title="Reactivar comercio"
                          >
                            {isActing ? "Procesando..." : "Activar"}
                          </button>
                        )}
                      </div>

                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* ===================================================== */}
        {/* Sección: Guardados (lo existente) */}
        {/* ===================================================== */}

        {/* Estado: Loading */}
        {isLoading && (
          <div className="space-y-3">
            <div className="h-28 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
            <div className="h-28 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
            <div className="h-28 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
          </div>
        )}

        {/* Estado: Error */}
        {!isLoading && errorMessage && (
          <div className="rounded-2xl border border-red-900 bg-red-950/40 p-5">
            <p className="font-semibold text-red-200">Error</p>
            <p className="mt-2 text-red-100 break-words">{errorMessage}</p>

            <p className="mt-3 text-sm text-gray-200">
              Si ves <b>401</b>, verificá que exista{" "}
              <code className="bg-gray-800 px-1 rounded">access_token</code> en
              localStorage.
            </p>
          </div>
        )}

        {/* Estado: Vacío */}
        {!isLoading && !errorMessage && publicaciones.length === 0 && (
          <div className="rounded-2xl border border-gray-800 bg-gray-950 p-6 text-center">
            <p className="text-gray-200 font-semibold">No tenés guardados</p>
            <p className="mt-2 text-gray-400 text-sm">
              Guardá publicaciones desde el Feed o Ranking y van a aparecer acá.
            </p>
          </div>
        )}

        {/* Estado: OK */}
        {!isLoading && !errorMessage && publicaciones.length > 0 && (
          <div className="space-y-4">
            {publicaciones.map((p) => (
              <PublicacionCard
                key={p.id}
                pub={p}
                isActingLike={Boolean(likeLocksMemo[p.id])}
                isActingSave={Boolean(saveLocksMemo[p.id])}
                onToggleLike={() => handleToggleLike(p.id)}
                onToggleSave={() => handleToggleSave(p.id)}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

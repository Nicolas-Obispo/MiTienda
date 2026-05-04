/**
 * ProfilePage.jsx
 * ----------------
 * ETAPA 39 (Perfil de usuario) - Guardados
 * ETAPA 45 (Orden UX navegación) - Admin: espacios publicadores + acciones (Crear / Editar / Desactivar)
 * ETAPA 49 (Avatar usuario) - Subida real + drag & drop + persistencia en BD
 * ETAPA 49 (Portada espacio) - Upload real + drag & drop + botón "Seleccionar imagen"
 * ETAPA 59.1 (Corrección conceptual) - "Mi perfil" como pantalla general del usuario.
 *
 * Regla de oro:
 * - El frontend NO inventa estado de negocio.
 * - Solo consume backend y renderiza.
 *
 * Decisión de producto:
 * - Usuario = cuenta de acceso.
 * - Mi perfil = pantalla personal del usuario dentro de MiPlaza.
 * - Tus espacios = negocios, servicios o perfiles públicos que ese usuario administra.
 * - Backend mantiene "comercios" por compatibilidad técnica.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
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
  // =====================================================
  // Helpers generales (token + base URL)
  // =====================================================
  function getToken() {
    return (
      localStorage.getItem("access_token") ||
      localStorage.getItem("token") ||
      ""
    );
  }

  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  // =====================================================
  // Estado: Perfil personal del usuario
  // =====================================================
  const [usuarioMe, setUsuarioMe] = useState(null);
  const [isLoadingMe, setIsLoadingMe] = useState(true);
  const [avatarErrorMessage, setAvatarErrorMessage] = useState("");
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
  const [isDragOverAvatar, setIsDragOverAvatar] = useState(false);

  const fileInputRef = useRef(null);

  // =====================================================
  // Estado: Portada de espacio
  // =====================================================
  const [isUploadingPortada, setIsUploadingPortada] = useState(false);
  const [isDragOverPortada, setIsDragOverPortada] = useState(false);
  const [portadaErrorMessage, setPortadaErrorMessage] = useState("");

  const portadaFileInputRef = useRef(null);

  async function loadUsuarioMe() {
    try {
      setIsLoadingMe(true);
      setAvatarErrorMessage("");

      const token = getToken();
      if (!token) {
        setUsuarioMe(null);
        return;
      }

      const resp = await fetch(`${API_BASE_URL}/usuarios/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!resp.ok) {
        throw new Error(`No se pudo cargar tu perfil (status ${resp.status}).`);
      }

      const data = await resp.json();
      setUsuarioMe(data);
    } catch (error) {
      setUsuarioMe(null);
      setAvatarErrorMessage(
        error.message || "Error desconocido cargando tu perfil."
      );
    } finally {
      setIsLoadingMe(false);
    }
  }

  async function uploadMedia(file) {
    const token = getToken();
    if (!token) throw new Error("No hay sesión activa (token).");

    const formData = new FormData();
    formData.append("file", file);

    const resp = await fetch(`${API_BASE_URL}/media/upload`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(
        `Error subiendo imagen (status ${resp.status}): ${
          text || "sin detalle"
        }`
      );
    }

    const data = await resp.json();
    if (!data?.url) throw new Error("Upload ok pero no vino url.");
    return data.url;
  }

  async function updateUsuarioAvatar(avatarUrl) {
    const token = getToken();
    if (!token) throw new Error("No hay sesión activa (token).");

    const resp = await fetch(`${API_BASE_URL}/usuarios/me/avatar`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ avatar_url: avatarUrl }),
    });

    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(
        `Error guardando avatar (status ${resp.status}): ${
          text || "sin detalle"
        }`
      );
    }

    return await resp.json();
  }

  function isValidImageFile(file) {
    if (!file) return false;
    const allowed = ["image/jpeg", "image/png", "image/webp"];
    return allowed.includes(file.type);
  }

  async function handleAvatarFile(file) {
    try {
      setAvatarErrorMessage("");

      if (!file) return;
      if (!isValidImageFile(file)) {
        throw new Error("Formato inválido. Usá JPG, PNG o WEBP.");
      }

      setIsUploadingAvatar(true);

      const url = await uploadMedia(file);
      const updatedUser = await updateUsuarioAvatar(url);

      setUsuarioMe(updatedUser);
    } catch (error) {
      setAvatarErrorMessage(
        error.message || "Error desconocido actualizando el avatar."
      );
    } finally {
      setIsUploadingAvatar(false);
      setIsDragOverAvatar(false);

      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  function handleAvatarInputChange(e) {
    const file = e.target.files?.[0];
    handleAvatarFile(file);
  }

  function handleAvatarClick() {
    if (isUploadingAvatar) return;
    fileInputRef.current?.click();
  }

  function handleAvatarDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    if (isUploadingAvatar) return;
    setIsDragOverAvatar(true);
  }

  function handleAvatarDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOverAvatar(false);
  }

  function handleAvatarDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    if (isUploadingAvatar) return;

    const file = e.dataTransfer?.files?.[0];
    handleAvatarFile(file);
  }

  // =====================================================
  // Portada de espacio
  // =====================================================
  function handlePortadaClick() {
    if (isUploadingPortada) return;
    portadaFileInputRef.current?.click();
  }

  function handlePortadaDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    if (isUploadingPortada) return;
    setIsDragOverPortada(true);
  }

  function handlePortadaDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOverPortada(false);
  }

  async function handlePortadaFile(file) {
    try {
      setPortadaErrorMessage("");

      if (!file) return;
      if (!isValidImageFile(file)) {
        throw new Error("Formato inválido. Usá JPG, PNG o WEBP.");
      }

      setIsUploadingPortada(true);

      const url = await uploadMedia(file);

      setCreateForm((prev) => ({
        ...prev,
        portada_url: url,
      }));
    } catch (error) {
      setPortadaErrorMessage(
        error.message || "Error desconocido subiendo la portada."
      );
    } finally {
      setIsUploadingPortada(false);
      setIsDragOverPortada(false);

      if (portadaFileInputRef.current) portadaFileInputRef.current.value = "";
    }
  }

  function handlePortadaInputChange(e) {
    const file = e.target.files?.[0];
    handlePortadaFile(file);
  }

  function handlePortadaDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    if (isUploadingPortada) return;

    const file = e.dataTransfer?.files?.[0];
    handlePortadaFile(file);
  }

  // ==========================================================
  // Estado: Publicaciones guardadas
  // ==========================================================
  const [isLoading, setIsLoading] = useState(true);
  const [publicaciones, setPublicaciones] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");

  const [likeLocks, setLikeLocks] = useState({});
  const [saveLocks, setSaveLocks] = useState({});

  const likeLocksMemo = useMemo(() => likeLocks, [likeLocks]);
  const saveLocksMemo = useMemo(() => saveLocks, [saveLocks]);

  function setLock(setter, pubId, value) {
    setter((prev) => ({ ...prev, [pubId]: value }));
  }

  // ==========================================================
  // Estado: Espacios administrados
  // ==========================================================
  const [isLoadingComercios, setIsLoadingComercios] = useState(true);
  const [misComercios, setMisComercios] = useState([]);
  const [comerciosErrorMessage, setComerciosErrorMessage] = useState("");

  const [isCreatingComercio, setIsCreatingComercio] = useState(false);
  const [isActingComercioById, setIsActingComercioById] = useState({});

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

  function handleResetForm() {
    setEditingComercioId(null);
    setCreateErrorMessage("");
    setPortadaErrorMessage("");
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

  function handleEditarComercio(comercio) {
    if (!comercio?.id) return;

    setCreateErrorMessage("");
    setPortadaErrorMessage("");
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

  async function loadGuardadas() {
    try {
      setIsLoading(true);
      setErrorMessage("");

      const guardadas = await fetchPublicacionesGuardadas();

      setPublicaciones(Array.isArray(guardadas) ? guardadas : []);
    } catch (error) {
      setErrorMessage(
        error.message || "Error desconocido cargando guardados."
      );
      setPublicaciones([]);
    } finally {
      setIsLoading(false);
    }
  }

  async function loadMisComercios() {
    try {
      setIsLoadingComercios(true);
      setComerciosErrorMessage("");

      const data = await getMisComercios();
      const items = Array.isArray(data) ? data : data?.items || [];
      setMisComercios(items);
    } catch (error) {
      setComerciosErrorMessage(
        error.message || "Error desconocido cargando tus espacios."
      );
      setMisComercios([]);
    } finally {
      setIsLoadingComercios(false);
    }
  }

  useEffect(() => {
    loadUsuarioMe();
    loadMisComercios();
    loadGuardadas();
  }, []);

  async function handleToggleLike(pubId) {
    if (likeLocksMemo[pubId]) return;

    setLock(setLikeLocks, pubId, true);

    const snapshot = publicaciones;

    setPublicaciones((prev) =>
      prev.map((p) => {
        if (p.id !== pubId) return p;

        const nextLiked = !p.liked_by_me;
        const delta = nextLiked ? 1 : -1;

        return {
          ...p,
          liked_by_me: nextLiked,
          likes_count: Math.max(0, (p.likes_count || 0) + delta),
          interacciones_count: Math.max(
            0,
            (p.interacciones_count || 0) + delta
          ),
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

          return {
            ...p,
            guardada_by_me: true,
            guardados_count: Math.max(0, (p.guardados_count || 0) + 1),
            interacciones_count: Math.max(
              0,
              (p.interacciones_count || 0) + 1
            ),
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
  // Crear / Editar espacio
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

      if (!createForm.nombre.trim()) {
        throw new Error("El nombre es obligatorio.");
      }

      if (!createForm.provincia.trim() || !createForm.ciudad.trim()) {
        throw new Error("Provincia y ciudad son obligatorias.");
      }

      const payload = {
        ...createForm,
        direccion: createForm.direccion?.trim()
          ? createForm.direccion.trim()
          : null,
        whatsapp: createForm.whatsapp?.trim()
          ? createForm.whatsapp.trim()
          : null,
        instagram: createForm.instagram?.trim()
          ? createForm.instagram.trim()
          : null,
        maps_url: createForm.maps_url?.trim()
          ? createForm.maps_url.trim()
          : null,
        portada_url: createForm.portada_url?.trim()
          ? createForm.portada_url.trim()
          : null,
        descripcion: createForm.descripcion?.trim()
          ? createForm.descripcion.trim()
          : "",
      };

      if (editingComercioId) {
        await actualizarComercio(editingComercioId, payload);
      } else {
        await crearComercio(payload);
      }

      await loadMisComercios();

      setShowCreateForm(false);
      handleResetForm();
    } catch (error) {
      setCreateErrorMessage(error.message || "Error procesando tu espacio.");
    } finally {
      setIsCreatingComercio(false);
    }
  }

  async function handleDesactivarComercio(comercioId) {
    if (!comercioId) return;
    if (isActingComercioById[comercioId]) return;

    const ok = window.confirm(
      "¿Seguro que querés desactivar este espacio? Podrás reactivarlo más adelante."
    );
    if (!ok) return;

    try {
      setComerciosErrorMessage("");
      setComercioLock(comercioId, true);

      await desactivarComercio(comercioId);
      await loadMisComercios();
    } catch (error) {
      setComerciosErrorMessage(
        error.message || "Error desactivando el espacio."
      );
    } finally {
      setComercioLock(comercioId, false);
    }
  }

  async function handleReactivarComercio(comercioId) {
    if (!comercioId) return;
    if (isActingComercioById[comercioId]) return;

    const ok = window.confirm("¿Querés reactivar este espacio?");
    if (!ok) return;

    try {
      setComerciosErrorMessage("");
      setComercioLock(comercioId, true);

      await reactivarComercio(comercioId);
      await loadMisComercios();
    } catch (error) {
      setComerciosErrorMessage(
        error.message || "Error reactivando el espacio."
      );
    } finally {
      setComercioLock(comercioId, false);
    }
  }

  const avatarUrl = usuarioMe?.avatar_url || "";

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <main className="mx-auto max-w-3xl px-4 py-8">
        {/* ===================================================== */}
        {/* Header: Mi perfil */}
        {/* ===================================================== */}
        <section className="mb-6">
          <h1 className="text-xl sm:text-2xl font-bold text-white">
            Mi perfil
          </h1>

          <p className="mt-1 text-sm text-gray-400">
            Gestioná tu actividad, tus espacios y tus publicaciones guardadas.
          </p>

          {/* Perfil personal */}
          <div className="mt-4 rounded-2xl border border-gray-800 bg-gray-950 p-4">
            <div className="flex items-center gap-4">
              <div
                role="button"
                tabIndex={0}
                onClick={handleAvatarClick}
                onDragOver={handleAvatarDragOver}
                onDragLeave={handleAvatarDragLeave}
                onDrop={handleAvatarDrop}
                className={[
                  "relative h-16 w-16 rounded-full border overflow-hidden",
                  "flex items-center justify-center",
                  isDragOverAvatar ? "border-green-400" : "border-gray-700",
                  "bg-gray-900",
                  isUploadingAvatar
                    ? "opacity-70 cursor-not-allowed"
                    : "cursor-pointer",
                ].join(" ")}
                title="Click para elegir imagen o arrastrá una foto acá"
              >
                {avatarUrl ? (
                  <img
                    src={avatarUrl}
                    alt="Foto de perfil"
                    className="h-full w-full object-cover"
                    draggable={false}
                  />
                ) : (
                  <span className="text-xs text-gray-300">Sin foto</span>
                )}

                {isUploadingAvatar && (
                  <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                    <span className="text-xs">Subiendo...</span>
                  </div>
                )}
              </div>

              <div className="flex-1">
                <p className="font-semibold">Perfil personal</p>

                <p className="mt-1 text-sm text-gray-400">
                  Este es tu perfil dentro de MiPlaza. Podés explorar,
                  guardar publicaciones, seguir espacios y también administrar
                  tus propios espacios.
                </p>

                <button
                  type="button"
                  onClick={handleAvatarClick}
                  disabled={isUploadingAvatar}
                  className="mt-2 rounded-xl bg-white text-black px-3 py-2 text-xs font-semibold disabled:opacity-60"
                >
                  {isUploadingAvatar ? "Subiendo..." : "Cambiar foto"}
                </button>

                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handleAvatarInputChange}
                  className="hidden"
                />

                <p className="mt-2 text-xs text-gray-500">
                  {isLoadingMe
                    ? "Cargando usuario..."
                    : usuarioMe?.email
                    ? `Sesión: ${usuarioMe.email}`
                    : "No se pudo cargar el usuario."}
                </p>

                {avatarErrorMessage && (
                  <div className="mt-3 rounded-xl border border-red-900 bg-red-950/40 p-3">
                    <p className="text-sm text-red-100 break-words">
                      {avatarErrorMessage}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* ===================================================== */}
        {/* Sección: Tus espacios */}
        {/* ===================================================== */}
        <section className="mb-8">
          <div className="flex items-end justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">Tus espacios</h2>
              <p className="mt-1 text-sm text-gray-400">
                Estos son los espacios publicos que administrás.
              </p>
            </div>

            <button
              type="button"
              onClick={() => {
                setCreateErrorMessage("");
                setShowCreateForm((prev) => {
                  const next = !prev;

                  if (next) handleResetForm();
                  if (!next) handleResetForm();

                  return next;
                });
              }}
              className="rounded-xl border border-gray-800 bg-gray-950 px-4 py-2 text-sm hover:border-gray-700"
            >
              {showCreateForm ? "Cerrar" : "Crear espacio"}
            </button>
          </div>

          {showCreateForm && (
            <div className="mt-4 rounded-2xl border border-gray-800 bg-gray-950 p-5">
              <p className="font-semibold">
                {editingComercioId ? "Editar espacio" : "Crear espacio"}
              </p>

              <p className="mt-1 text-sm text-gray-400">
                Creá un espacio para mostrar un negocio, servicio, profesión o
                emprendimiento.
              </p>

              {createErrorMessage && (
                <div className="mt-3 rounded-xl border border-red-900 bg-red-950/40 p-4">
                  <p className="font-semibold text-red-200">Error</p>
                  <p className="mt-2 text-red-100 break-words">
                    {createErrorMessage}
                  </p>
                </div>
              )}

              <form onSubmit={handleCrearComercioSubmit} className="mt-4 space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-gray-400">
                      Nombre del espacio *
                    </label>
                    <input
                      name="nombre"
                      value={createForm.nombre}
                      onChange={handleCreateInputChange}
                      className="mt-1 w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm"
                      placeholder="Ej: Kiosco Centro, Estudio Jurídico, Ferretería..."
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
                    placeholder="Contá brevemente qué ofrece este espacio..."
                  />
                </div>

                <div>
                  <label className="text-xs text-gray-400">Portada</label>

                  <div className="mt-2 flex items-center gap-3">
                    <div
                      role="button"
                      tabIndex={0}
                      onClick={handlePortadaClick}
                      onDragOver={handlePortadaDragOver}
                      onDragLeave={handlePortadaDragLeave}
                      onDrop={handlePortadaDrop}
                      className={[
                        "relative h-14 w-14 rounded-xl border overflow-hidden",
                        "flex items-center justify-center",
                        isDragOverPortada ? "border-green-400" : "border-gray-700",
                        "bg-gray-900",
                        isUploadingPortada
                          ? "opacity-70 cursor-not-allowed"
                          : "cursor-pointer",
                      ].join(" ")}
                      title="Click para elegir imagen o arrastrá una foto acá"
                    >
                      {createForm.portada_url ? (
                        <img
                          src={createForm.portada_url}
                          alt="Portada del espacio"
                          className="h-full w-full object-cover"
                          draggable={false}
                        />
                      ) : (
                        <span className="text-[10px] text-gray-300 text-center px-1">
                          Sin portada
                        </span>
                      )}

                      {isUploadingPortada && (
                        <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                          <span className="text-[10px]">Subiendo...</span>
                        </div>
                      )}
                    </div>

                    <div
                      role="button"
                      tabIndex={0}
                      onClick={handlePortadaClick}
                      className="flex-1 cursor-pointer select-none"
                      title="Click para seleccionar imagen"
                    >
                      <p className="text-sm text-gray-300">
                        Click o arrastrar para subir. Formatos: JPG / PNG /
                        WEBP.
                      </p>

                      <button
                        type="button"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          handlePortadaClick();
                        }}
                        disabled={isUploadingPortada}
                        className="mt-2 rounded-xl bg-white text-black px-3 py-2 text-xs font-semibold disabled:opacity-60"
                      >
                        {isUploadingPortada ? "Subiendo..." : "Seleccionar imagen"}
                      </button>

                      <input
                        ref={portadaFileInputRef}
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        onChange={handlePortadaInputChange}
                        className="hidden"
                      />

                      {portadaErrorMessage && (
                        <p className="mt-2 text-xs text-red-200 break-words">
                          {portadaErrorMessage}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="mt-3">
                    <label className="text-xs text-gray-500">
                      Portada URL opcional
                    </label>
                    <input
                      name="portada_url"
                      value={createForm.portada_url}
                      onChange={handleCreateInputChange}
                      className="mt-1 w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm"
                      placeholder="https://... o /uploads/..."
                    />
                  </div>
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
                      placeholder="@tu_espacio"
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

          {isLoadingComercios && (
            <div className="mt-3 space-y-2">
              <div className="h-16 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
              <div className="h-16 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
            </div>
          )}

          {!isLoadingComercios && comerciosErrorMessage && (
            <div className="mt-3 rounded-2xl border border-red-900 bg-red-950/40 p-5">
              <p className="font-semibold text-red-200">Error</p>
              <p className="mt-2 text-red-100 break-words">
                {comerciosErrorMessage}
              </p>
            </div>
          )}

          {!isLoadingComercios &&
            !comerciosErrorMessage &&
            misComercios.length === 0 && (
              <div className="mt-3 rounded-2xl border border-purple-900 bg-purple-950/30 p-6 text-center">
                <p className="text-lg font-bold text-purple-100">
                  Todavía no creaste espacios
                </p>

                <p className="mt-2 text-sm leading-6 text-purple-100/80">
                  Podés usar MiPlaza solo para explorar, guardar publicaciones e
                  interactuar. Cuando quieras mostrar un negocio, servicio o
                  profesión, creá tu primer espacio.
                </p>

                <button
                  type="button"
                  onClick={() => {
                    setCreateErrorMessage("");
                    handleResetForm();
                    setShowCreateForm(true);
                  }}
                  className="mt-4 rounded-xl bg-purple-600 px-4 py-2 text-sm font-semibold text-white hover:bg-purple-500"
                >
                  Crear espacio
                </button>
              </div>
            )}

          {!isLoadingComercios &&
            !comerciosErrorMessage &&
            misComercios.length > 0 && (
                <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
                  {misComercios.map((c) => {
                    const isActing = Boolean(isActingComercioById[c.id]);

                    return (
                      <div
                        key={c.id}
                        className="relative overflow-hidden rounded-2xl border border-gray-800 bg-gray-950"
                      >
                        {/* PORTADA */}
                        <Link to={`/comercios/${c.id}`}>
                          <div className="aspect-square bg-gray-800">
                            {c.portada_url ? (
                              <img
                                src={c.portada_url}
                                alt="Portada del espacio"
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-xs text-gray-400">
                                Sin portada
                              </div>
                            )}
                          </div>
                        </Link>

                        {/* NOMBRE */}
                        <div className="p-2">
                          <p className="truncate text-xs font-semibold text-white">
                            {c.nombre}
                          </p>
                        </div>

                        {/* BADGE ESTADO */}
                        <span className="absolute top-2 left-2 rounded-full bg-black/70 px-2 py-0.5 text-[10px]">
                          {c.activo ? "🟢Activo" : "🔴Pausado"}
                        </span>

                        {/* ACCIONES */}
                        <div className="absolute top-2 right-2 flex flex-col gap-1">
                          <button
                            onClick={() => handleEditarComercio(c)}
                            disabled={isActing}
                            className="bg-black/70 text-[10px] px-2 py-1 rounded"
                          >
                            Editar
                          </button>

                          {c.activo ? (
                            <button
                              onClick={() => handleDesactivarComercio(c.id)}
                              disabled={isActing}
                              className="bg-black/70 text-[10px] px-2 py-1 rounded"
                            >
                              {isActing ? "..." : "Pausar"}
                            </button>
                          ) : (
                            <button
                              onClick={() => handleReactivarComercio(c.id)}
                              disabled={isActing}
                              className="bg-black/70 text-[10px] px-2 py-1 rounded"
                            >
                              {isActing ? "..." : "Activar"}
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}
        </section>

        {/* ===================================================== */}
        {/* Sección: Publicaciones guardadas */}
        {/* ===================================================== */}
        <section>
          <div className="mb-3">
            <h2 className="text-lg font-semibold">Publicaciones guardadas</h2>
            <p className="mt-1 text-sm text-gray-400">
              Contenido que guardaste desde Feed, Ranking o Explorador.
            </p>
          </div>

          {isLoading && (
            <div className="space-y-3">
              <div className="h-28 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
              <div className="h-28 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
              <div className="h-28 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
            </div>
          )}

          {!isLoading && errorMessage && (
            <div className="rounded-2xl border border-red-900 bg-red-950/40 p-5">
              <p className="font-semibold text-red-200">Error</p>
              <p className="mt-2 text-red-100 break-words">{errorMessage}</p>

              <p className="mt-3 text-sm text-gray-200">
                Si ves <b>401</b>, verificá que exista{" "}
                <code className="bg-gray-800 px-1 rounded">access_token</code>{" "}
                en localStorage.
              </p>
            </div>
          )}

          {!isLoading && !errorMessage && publicaciones.length === 0 && (
            <div className="rounded-2xl border border-gray-800 bg-gray-950 p-6 text-center">
              <p className="text-gray-200 font-semibold">
                No tenés publicaciones guardadas
              </p>
              <p className="mt-2 text-gray-400 text-sm">
                Guardá publicaciones desde el Feed o Ranking y van a aparecer
                acá.
              </p>
            </div>
          )}

          {!isLoading && !errorMessage && publicaciones.length > 0 && (
            <div className="space-y-4">
              <div
                className="
                  grid
                  grid-cols-3
                  sm:grid-cols-3
                  md:grid-cols-4
                  gap-1
                "
              >
                {publicaciones.map((p) => (
                  <div
                    key={p.id}
                    className="relative aspect-square bg-gray-800 overflow-hidden"
                  >
                    {p.imagen_url ? (
                      <img
                        src={p.imagen_url}
                        alt=""
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-xs text-gray-400">
                        Sin imagen
                      </div>
                    )}

                    <div className="absolute inset-0 bg-black/40 opacity-0 hover:opacity-100 transition flex items-center justify-center">
                      <div className="text-xs text-white text-center">
                        <p>❤️ {p.likes_count || 0}</p>
                        <p>💾 {p.guardados_count || 0}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
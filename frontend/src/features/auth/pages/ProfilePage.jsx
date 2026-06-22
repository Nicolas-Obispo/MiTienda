/**
 * ProfilePage.jsx
 * ----------------
 * ETAPA 72.9 (Perfil de usuario) - Edicion de perfil y espacios administrados
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
 * - Mi perfil = pantalla personal del usuario dentro de FeedGo!.
 * - Tus espacios = negocios, servicios o perfiles públicos que ese usuario administra.
 * - Backend mantiene "comercios" por compatibilidad técnica.
 */

import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { httpPut } from "@core";
import { queryKeys } from "@core/constants/queryKeys";
import {
  getMediaUrlFromAny,
  uploadImagen,
  LocationPicker,
} from "@shared";
import { actualizarPerfilUsuario, getMe, useAuth } from "@features/auth";
import { cambiarModoUsuario } from "@features/auth/services/usuarioService";
import { useQueryClient } from "@tanstack/react-query";

import {
  crearComercio,
  desactivarComercio,
  actualizarComercio,
  reactivarComercio,
  useMisComercios,
} from "@features/spaces";

const COLOR_FONDO_PRESETS = [
  { nombre: "Negro/default", valor: "#111827" },
  { nombre: "Gris oscuro", valor: "#1F2937" },
];

const COLOR_FONDO_DEFAULT = "#111827";

function normalizeColorFondo(colorFondo) {
  const color = String(colorFondo || "").trim().toUpperCase();
  const isAllowed = COLOR_FONDO_PRESETS.some(
    (preset) => preset.valor.toUpperCase() === color
  );

  return isAllowed ? color : COLOR_FONDO_DEFAULT;
}

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


  // =====================================================
  // Estado: Perfil personal del usuario
  // =====================================================
  const [usuarioMe, setUsuarioMe] = useState(null);
  const [isLoadingMe, setIsLoadingMe] = useState(true);
  const [avatarErrorMessage, setAvatarErrorMessage] = useState("");
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
  const [showPerfilForm, setShowPerfilForm] = useState(false);
  const [showColorFondoOptions, setShowColorFondoOptions] = useState(false);
  const [isSavingPerfil, setIsSavingPerfil] = useState(false);
  const [perfilErrorMessage, setPerfilErrorMessage] = useState("");
  const [perfilSuccessMessage, setPerfilSuccessMessage] = useState("");
  const [perfilForm, setPerfilForm] = useState({
    provincia: "",
    ciudad: "",
    color_fondo: COLOR_FONDO_DEFAULT,
  });

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

      const data = await getMe(token);

      setUsuarioMe(data);
      setPerfilForm({
        provincia: data?.provincia || "",
        ciudad: data?.ciudad || "",
        color_fondo: normalizeColorFondo(data?.color_fondo),
      });
    } catch (error) {
      setUsuarioMe(null);
      setAvatarErrorMessage(
        error.message || "Error desconocido cargando tu perfil."
      );
    } finally {
      setIsLoadingMe(false);
    }
  }

  async function activarModoPublicador() {
    try {
      const token = getToken();

      if (!token) {
        throw new Error("No hay sesión activa.");
      }

      const usuarioActualizado =
        await cambiarModoUsuario(token, "publicador");

      setUsuarioMe(usuarioActualizado);
    } catch (error) {
      alert(
        error?.message ||
        "No se pudo activar el modo publicador."
      );
    }
  }

  function abrirEdicionPerfil() {
    setPerfilErrorMessage("");
    setPerfilSuccessMessage("");
    setShowColorFondoOptions(false);
    setPerfilForm({
      provincia: usuarioMe?.provincia || "",
      ciudad: usuarioMe?.ciudad || "",
      color_fondo: normalizeColorFondo(usuarioMe?.color_fondo),
    });
    setShowPerfilForm(true);
  }

  function cancelarEdicionPerfil() {
    setPerfilErrorMessage("");
    setPerfilSuccessMessage("");
    setShowColorFondoOptions(false);
    setPerfilForm({
      provincia: usuarioMe?.provincia || "",
      ciudad: usuarioMe?.ciudad || "",
      color_fondo: normalizeColorFondo(usuarioMe?.color_fondo),
    });
    setShowPerfilForm(false);
  }

  function handlePerfilFormChange(e) {
    const { name, value } = e.target;

    setPerfilForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  }

  async function handlePerfilSubmit(e) {
    e.preventDefault();

    try {
      setIsSavingPerfil(true);
      setPerfilErrorMessage("");
      setPerfilSuccessMessage("");

      const token = getToken();

      if (!token) {
        throw new Error("No hay sesion activa.");
      }

      const payload = {
        provincia: perfilForm.provincia.trim(),
        ciudad: perfilForm.ciudad.trim(),
        color_fondo: normalizeColorFondo(perfilForm.color_fondo),
      };

      const usuarioActualizado = await actualizarPerfilUsuario(token, payload);

      setUsuarioMe(usuarioActualizado);
      await refrescarUsuario?.();
      setPerfilForm({
        provincia: usuarioActualizado?.provincia || "",
        ciudad: usuarioActualizado?.ciudad || "",
        color_fondo: normalizeColorFondo(usuarioActualizado?.color_fondo),
      });
      setShowColorFondoOptions(false);
      setShowPerfilForm(false);
      setPerfilSuccessMessage("Perfil actualizado");
    } catch (error) {
      setPerfilErrorMessage(
        error.message || "No se pudo actualizar el perfil."
      );
      setPerfilSuccessMessage("");
    } finally {
      setIsSavingPerfil(false);
    }
  }

  async function uploadMedia(file) {
    const token = getToken();

    if (!token) {
      throw new Error("No hay sesión activa (token).");
    }

    const data = await uploadImagen(file, token);

    if (!data?.url) {
      throw new Error("Upload ok pero no vino url.");
    }

    return data.url;
  }

  async function updateUsuarioAvatar(avatarUrl) {
    const token = getToken();

    if (!token) {
      throw new Error("No hay sesión activa (token).");
    }

    return httpPut(
      "/usuarios/me/avatar",
      {
        avatar_url: avatarUrl,
      },
      token
    );
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
  // Estado: Espacios administrados
  // ==========================================================
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { logout, refrescarUsuario } = useAuth();
  const [comerciosErrorMessage, setComerciosErrorMessage] = useState("");
  const {
    data: misComercios = [],
    isLoading: isLoadingComercios,
    error: misComerciosError,
  } = useMisComercios({
    enabled: Boolean(getToken()),
  });
  const comerciosQueryErrorMessage = misComerciosError
    ? misComerciosError.message || "Error desconocido cargando tus espacios."
    : "";
  const comerciosErrorVisible =
    comerciosErrorMessage || comerciosQueryErrorMessage;

  const [isCreatingComercio, setIsCreatingComercio] = useState(false);
  const [isActingComercioById, setIsActingComercioById] = useState({});

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showActivarEspacioInfo, setShowActivarEspacioInfo] = useState(false);
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
    latitud: null,
    longitud: null,
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
      latitud: null,
      longitud: null,
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
      portada_url: getMediaUrlFromAny(comercio) || "",
      rubro_id: comercio.rubro_id || 1,
      provincia: comercio.provincia || "",
      ciudad: comercio.ciudad || "",
      direccion: comercio.direccion || "",
      whatsapp: comercio.whatsapp || "",
      instagram: comercio.instagram || "",
      maps_url: comercio.maps_url || "",
      latitud: comercio.latitud ?? null,
      longitud: comercio.longitud ?? null,
    });
  }

  async function manejarLogout() {
    await logout();
    navigate("/login");
  }

  useEffect(() => {
    loadUsuarioMe();
  }, []);

  useEffect(() => {
    if (!perfilSuccessMessage) return undefined;

    const timeoutId = window.setTimeout(() => {
      setPerfilSuccessMessage("");
    }, 3000);

    return () => window.clearTimeout(timeoutId);
  }, [perfilSuccessMessage]);

  useEffect(() => {
    const editarEspacioId = Number(searchParams.get("editarEspacioId"));

    if (!editarEspacioId || misComercios.length === 0) return;

    const comercioParaEditar = misComercios.find(
      (c) => Number(c.id) === editarEspacioId
    );

    if (!comercioParaEditar) return;

    handleEditarComercio(comercioParaEditar);
  }, [searchParams, misComercios]);

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
          latitud:
            createForm.latitud !== null && createForm.latitud !== ""
              ? Number(createForm.latitud)
              : null,
          longitud:
            createForm.longitud !== null && createForm.longitud !== ""
              ? Number(createForm.longitud)
              : null,
      };

      if (editingComercioId) {
        await actualizarComercio(editingComercioId, payload);
        await queryClient.invalidateQueries({
          queryKey: queryKeys.spaces.mis(),
        });
        await queryClient.invalidateQueries({
          queryKey: queryKeys.spaces.detalle(editingComercioId),
        });

        setShowCreateForm(false);
        handleResetForm();

        navigate(`/comercios/${editingComercioId}`);
        return;
      }

      await crearComercio(payload);
      await queryClient.invalidateQueries({
        queryKey: queryKeys.spaces.mis(),
      });

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
      await queryClient.invalidateQueries({
        queryKey: queryKeys.spaces.mis(),
      });
      queryClient.invalidateQueries({ queryKey: ["explore", "spaces"] });
      await queryClient.invalidateQueries({
        queryKey: queryKeys.spaces.detalle(comercioId),
      });
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
      await queryClient.invalidateQueries({
        queryKey: queryKeys.spaces.mis(),
      });
      queryClient.invalidateQueries({ queryKey: ["explore", "spaces"] });
      await queryClient.invalidateQueries({
        queryKey: queryKeys.spaces.detalle(comercioId),
      });
    } catch (error) {
      setComerciosErrorMessage(
        error.message || "Error reactivando el espacio."
      );
    } finally {
      setComercioLock(comercioId, false);
    }
  }

  const avatarUrl = usuarioMe?.avatar_url || "";
  const esModoPublicador = usuarioMe?.modo_activo === "publicador";
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

          {!showPerfilForm && (
          <p className="mt-1 text-sm text-gray-400">
            Gestioná tu actividad, tus espacios y tus publicaciones guardadas.
          </p>
          )}

          {perfilSuccessMessage && (
            <div className="mt-4 flex items-center gap-2 rounded-xl border border-green-800 bg-green-950/50 px-4 py-3 text-sm font-semibold text-green-100">
              <span aria-hidden="true">✓</span>
              <span>{perfilSuccessMessage}</span>
            </div>
          )}

          {/* Perfil personal */}
          {!showPerfilForm && (
          <div className="mt-4 rounded-2xl border border-gray-800 bg-gray-950 p-4">
            <div className="flex items-center gap-4">
              <div
                className={[
                  "relative h-16 w-16 rounded-full border overflow-hidden",
                  "flex items-center justify-center",
                  "border-gray-700 bg-gray-900",
                ].join(" ")}
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

              </div>

              <div className="flex-1">
                <p className="font-semibold">Perfil personal</p>

                <p className="mt-1 text-sm text-gray-400">
                  Este es tu perfil dentro de FeedGo!. Podés explorar,
                  guardar publicaciones, seguir espacios y también administrar
                  tus propios espacios.
                </p>

                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    onClick={abrirEdicionPerfil}
                    disabled={isLoadingMe || !usuarioMe || showPerfilForm}
                    className="rounded-xl border border-gray-700 bg-gray-900 px-3 py-2 text-xs font-semibold text-gray-200 hover:bg-gray-800 disabled:opacity-60"
                  >
                    Editar perfil
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setCreateErrorMessage("");
                      handleResetForm();
                      setShowActivarEspacioInfo(misComercios.length === 0);
                      setShowCreateForm(misComercios.length > 0);
                    }}
                    className="rounded-xl bg-orange-500 px-3 py-2 text-xs font-semibold text-white hover:bg-orange-400"
                  >
                    Crear nuevo espacio
                  </button>
                </div>

                <p className="mt-2 text-xs text-gray-500">
                  {isLoadingMe
                    ? "Cargando usuario..."
                    : usuarioMe?.email
                    ? `Sesión: ${usuarioMe.email}`
                    : "No se pudo cargar el usuario."}
                </p>

                <button
                  type="button"
                  onClick={manejarLogout}
                  className="mt-2 rounded-xl border border-gray-700 bg-gray-900 px-3 py-2 text-xs font-semibold text-gray-200 hover:bg-gray-800"
                >
                  Cerrar sesión
                </button>

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
          )}
        </section>

        {showPerfilForm && (
          <section className="mb-8 rounded-2xl border border-gray-800 bg-gray-950 p-4">
            <form onSubmit={handlePerfilSubmit} className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="relative h-32 w-32 shrink-0 overflow-hidden rounded-full border border-gray-700 bg-gray-900">
                  {avatarUrl ? (
                    <img
                      src={avatarUrl}
                      alt="Foto de perfil"
                      className="h-full w-full object-cover"
                      draggable={false}
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center px-1 text-center text-xs text-gray-300">
                      Sin foto
                    </div>
                  )}
                </div>

                <p className="min-w-0 flex-1 truncate text-sm text-gray-200">
                  {usuarioMe?.email || "Usuario sin correo"}
                </p>
              </div>

              <div>
                <button
                  type="button"
                  onClick={handleAvatarClick}
                  disabled={isUploadingAvatar || isSavingPerfil}
                  className="rounded-xl bg-white px-3 py-2 text-xs font-semibold text-black transition-all hover:bg-gray-100 hover:shadow-md disabled:opacity-60"
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
              </div>

              <div>
                <span className="text-xs font-medium text-gray-400">
                  Color de fondo
                </span>

                <div className="relative mt-2">
                  <button
                    type="button"
                    onClick={() =>
                      setShowColorFondoOptions((isOpen) => !isOpen)
                    }
                    disabled={isSavingPerfil}
                    className="rounded-xl border border-gray-700 bg-gray-900 px-3 py-2 text-xs font-semibold text-gray-200 hover:bg-gray-800 disabled:opacity-60"
                    aria-expanded={showColorFondoOptions}
                  >
                    Color de fondo
                  </button>

                  {showColorFondoOptions && (
                    <div className="absolute left-0 z-20 mt-2 w-64 overflow-hidden rounded-xl border border-gray-800 bg-gray-950 shadow-xl">
                      {COLOR_FONDO_PRESETS.map((color) => {
                        const isSelected =
                          normalizeColorFondo(perfilForm.color_fondo).toLowerCase() ===
                          color.valor.toLowerCase();

                        return (
                          <button
                            key={color.nombre}
                            type="button"
                            onClick={() => {
                              setPerfilForm((prev) => ({
                                ...prev,
                                color_fondo: color.valor,
                              }));
                              setShowColorFondoOptions(false);
                            }}
                            disabled={isSavingPerfil}
                            className={[
                              "flex w-full items-center gap-3 px-3 py-2 text-left text-sm",
                              isSelected
                                ? "bg-orange-500/20 text-white"
                                : "text-gray-200 hover:bg-gray-900",
                              "disabled:opacity-60",
                            ].join(" ")}
                            aria-pressed={isSelected}
                          >
                            <span
                              className="h-5 w-5 rounded-full border border-gray-600"
                              style={{ backgroundColor: color.valor }}
                              aria-hidden="true"
                            />
                            <span>{color.nombre}</span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>

              <label className="block">
                <span className="text-xs font-medium text-gray-400">
                  Provincia
                </span>
                <input
                  type="text"
                  name="provincia"
                  value={perfilForm.provincia}
                  onChange={handlePerfilFormChange}
                  disabled={isSavingPerfil}
                  className="mt-1 w-full rounded-xl border border-gray-800 bg-gray-900 px-3 py-2 text-sm text-white outline-none focus:border-orange-500 disabled:opacity-60"
                  placeholder="Provincia"
                />
              </label>

              <label className="block">
                <span className="text-xs font-medium text-gray-400">
                  Ciudad
                </span>
                <input
                  type="text"
                  name="ciudad"
                  value={perfilForm.ciudad}
                  onChange={handlePerfilFormChange}
                  disabled={isSavingPerfil}
                  className="mt-1 w-full rounded-xl border border-gray-800 bg-gray-900 px-3 py-2 text-sm text-white outline-none focus:border-orange-500 disabled:opacity-60"
                  placeholder="Ciudad"
                />
              </label>

              <div className="flex flex-wrap gap-2">
                <button
                  type="submit"
                  disabled={isSavingPerfil}
                  className="rounded-xl bg-orange-500 px-3 py-2 text-xs font-semibold text-white hover:bg-orange-400 disabled:opacity-60"
                >
                  {isSavingPerfil ? "Guardando..." : "Guardar"}
                </button>

                <button
                  type="button"
                  onClick={cancelarEdicionPerfil}
                  disabled={isSavingPerfil}
                  className="rounded-xl border border-gray-700 bg-gray-900 px-3 py-2 text-xs font-semibold text-gray-200 hover:bg-gray-800 disabled:opacity-60"
                >
                  Cancelar
                </button>
              </div>
            </form>

            {perfilErrorMessage && (
              <p className="mt-3 text-xs text-red-300">
                {perfilErrorMessage}
              </p>
            )}
          </section>
        )}

        {!showPerfilForm && showActivarEspacioInfo && (
        <div className="mt-3 rounded-2xl border border-purple-900 bg-purple-950/30 p-6 text-center">
          <p className="text-lg font-bold text-purple-100">
            Creá tu espacio en FeedGo!
          </p>

          <p className="mt-2 text-sm leading-6 text-purple-100/80">
            Un espacio es tu perfil público dentro de FeedGo!. Puede representar
            un negocio, emprendimiento, servicio, profesión o proyecto personal.
            Desde allí vas a poder publicar contenido, compartir historias,
            mostrar información de contacto y construir tu presencia dentro de
            la comunidad.
          </p>

          <button
            type="button"
              onClick={async () => {
                if (!esModoPublicador) {
                  await activarModoPublicador();
                }

                setShowActivarEspacioInfo(false); // ocultar explicación

                setCreateErrorMessage("");
                handleResetForm();

                setShowCreateForm(true); // mostrar formulario
              }}
            className="mt-4 rounded-xl bg-orange-500 px-4 py-2 text-sm font-semibold text-white hover:bg-orange-400"
          >
            Iniciar espacio
          </button>
        </div>
        )}




        {/* ===================================================== */}
        {/* Sección: Tus espacios */}
        {/* ===================================================== */}
        {!showPerfilForm && (esModoPublicador || showCreateForm) && (
          <section className="mb-8">
            {misComercios.length > 0 && (
              <div className="flex items-end justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold">Tus espacios</h2>
                  <p className="mt-1 text-sm text-gray-400">
                    Estos son los espacios públicos que administrás.
                  </p>
                </div>
              </div>
            )}

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
                          "relative h-26 w-26 rounded-2xl border overflow-hidden",
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
                          Elege una imagen que represente claramente tu espacio.
                        </p>

                        <p className="mt-1 text-xs text-gray-500">
                          Recomendamos utilizar el logo de tu negocio, el nombre de tu emprendimiento,
                          una imagen de tu marca o una foto que ayude a los usuarios a identificar tu
                          actividad de forma rápida.
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
                  </div>

                  <div>
                    <label className="text-xs text-gray-400">
                      Ubicación del espacio
                    </label>

                    <div className="mt-2">
                      <LocationPicker
                        direccion={createForm.direccion}
                        ciudad={createForm.ciudad}
                        provincia={createForm.provincia}
                        latitud={createForm.latitud}
                        longitud={createForm.longitud}
                        onChange={({ latitud, longitud }) => {
                          setCreateForm((prev) => ({
                            ...prev,
                            latitud,
                            longitud,
                          }));
                        }}
                      />
                    </div>

                    <p className="mt-1 text-xs text-gray-500">
                      Buscá la dirección, mové el pin y guardá la ubicación exacta.
                    </p>
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

            {isLoadingComercios && misComercios.length === 0 && (
              <div className="mt-3 space-y-2">
                <div className="h-16 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
                <div className="h-16 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
              </div>
            )}

            {comerciosErrorVisible && misComercios.length === 0 && (
              <div className="mt-3 rounded-2xl border border-red-900 bg-red-950/40 p-5">
                <p className="font-semibold text-red-200">Error</p>
                <p className="mt-2 text-red-100 break-words">
                  {comerciosErrorVisible}
                </p>
              </div>
            )}



            {(!isLoadingComercios || misComercios.length > 0) &&
              !(comerciosErrorVisible && misComercios.length === 0) &&
              misComercios.length > 0 && (
                  <div className="mt-3 grid grid-cols-3 gap-1.5 sm:grid-cols-3 sm:gap-3">
                    {misComercios.map((c) => {
                      const isActing = Boolean(isActingComercioById[c.id]);
                      const imagenUrl = getMediaUrlFromAny(c);

                      return (
                        <div
                          key={c.id}
                          className="relative overflow-hidden rounded-2xl border border-gray-800 bg-gray-950"
                        >
                          {/* PORTADA */}
                          <Link to={`/comercios/${c.id}`}>
                            <div className="aspect-square bg-gray-800">
                              {imagenUrl ? (
                                <img
                                  src={imagenUrl}
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
        )}

      </main>
    </div>
  );
}

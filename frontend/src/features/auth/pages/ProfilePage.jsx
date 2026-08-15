/**
 * ProfilePage.jsx
 * ----------------
 * ETAPA 72.9 (Perfil de usuario) - Edicion de perfil y espacios administrados
 * ETAPA 45 (Orden UX navegación) - Admin: espacios publicadores + acciones (Crear / Editar / Desactivar)
 * ETAPA 49 (Avatar usuario) - Subida real + drag & drop + persistencia en BD
 * ETAPA 49 (Portada espacio) - Upload real + drag & drop + botón "Seleccionar imagen"
 * ETAPA 59.1 (Corrección conceptual) - Mi cuenta como pantalla general del usuario.
 *
 * Regla de oro:
 * - El frontend NO inventa estado de negocio.
 * - Solo consume backend y renderiza.
 *
 * Decisión de producto:
 * - Usuario = cuenta de acceso.
 * - Perfil administrador = cuenta de acceso y administración dentro de FeedGo!.
 * - Mis espacios = negocios, servicios o perfiles públicos que ese usuario administra.
 * - Backend mantiene "comercios" por compatibilidad técnica.
 */

import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { httpPut } from "@core";
import { queryKeys } from "@core/constants/queryKeys";
import {
  Alert,
  Button,
  FormControl,
  getMediaUrlFromAny,
  Input,
  uploadImagen,
  LocationPicker,
  Select,
  Skeleton,
  Surface,
  Textarea,
} from "@shared";
import { invalidateLocationAfterAddressEdit } from "@shared/components/locationPickerState";
import { actualizarPerfilUsuario, getMe, useAuth } from "@features/auth";
import { cambiarModoUsuario } from "@features/auth/services/usuarioService";
import { useQueryClient } from "@tanstack/react-query";
import AgendaGeneralModal from "@features/agenda/components/AgendaGeneralModal";
import AgendaPrivadaModal from "@features/agenda/components/AgendaPrivadaModal";
import EstadoHorarioBadge from "@features/availability/components/EstadoHorarioBadge";
import HorariosAtencionEditor from "@features/availability/components/HorariosAtencionEditor";
import AppearanceSelector from "@features/auth/components/AppearanceSelector";

import {
  crearComercio,
  desactivarComercio,
  actualizarComercio,
  reactivarComercio,
  useMisComercios,
  useRubroEspecialidades,
  useRubros,
} from "@features/spaces";

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
  // Estado: Mi cuenta del usuario
  // =====================================================
  const [usuarioMe, setUsuarioMe] = useState(null);
  const [isLoadingMe, setIsLoadingMe] = useState(true);
  const [avatarErrorMessage, setAvatarErrorMessage] = useState("");
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
  const [showPerfilForm, setShowPerfilForm] = useState(false);
  const [showAppearanceOptions, setShowAppearanceOptions] = useState(false);
  const [isSavingPerfil, setIsSavingPerfil] = useState(false);
  const [perfilErrorMessage, setPerfilErrorMessage] = useState("");
  const [perfilSuccessMessage, setPerfilSuccessMessage] = useState("");
  const [perfilForm, setPerfilForm] = useState({
    provincia: "",
    ciudad: "",
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
    setShowAppearanceOptions(false);
    setPerfilForm({
      provincia: usuarioMe?.provincia || "",
      ciudad: usuarioMe?.ciudad || "",
    });
    setShowPerfilForm(true);
  }

  function cancelarEdicionPerfil() {
    setPerfilErrorMessage("");
    setPerfilSuccessMessage("");
    setShowAppearanceOptions(false);
    setPerfilForm({
      provincia: usuarioMe?.provincia || "",
      ciudad: usuarioMe?.ciudad || "",
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
      };

      const usuarioActualizado = await actualizarPerfilUsuario(token, payload);

      setUsuarioMe(usuarioActualizado);
      await refrescarUsuario?.();
      setPerfilForm({
        provincia: usuarioActualizado?.provincia || "",
        ciudad: usuarioActualizado?.ciudad || "",
      });
      setShowAppearanceOptions(false);
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
  const {
    data: rubros = [],
    isLoading: isLoadingRubros,
  } = useRubros();

  const [isCreatingComercio, setIsCreatingComercio] = useState(false);
  const [isActingComercioById, setIsActingComercioById] = useState({});
  const [isAgendaGeneralOpen, setIsAgendaGeneralOpen] = useState(false);
  const [agendaComercio, setAgendaComercio] = useState(null);
  const [horariosEditorComercio, setHorariosEditorComercio] = useState(null);

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showActivarEspacioInfo, setShowActivarEspacioInfo] = useState(false);
  const [editingComercioId, setEditingComercioId] = useState(null);
  const [createErrorMessage, setCreateErrorMessage] = useState("");
  const [createForm, setCreateForm] = useState({
    nombre: "",
    descripcion: "",
    portada_url: "",
    rubro_id: 1,
    especialidad_ids: [],
    provincia: "",
    ciudad: "",
    direccion: "",
    whatsapp: "",
    instagram: "",
    maps_url: "",
    latitud: null,
    longitud: null,
    mostrar_direccion_publicamente: true,
  });
  const {
    data: especialidadesRubro = [],
    isLoading: isLoadingEspecialidades,
  } = useRubroEspecialidades(createForm.rubro_id);

  function setComercioLock(comercioId, value) {
    setIsActingComercioById((prev) => ({ ...prev, [comercioId]: value }));
  }

  function handleResetForm() {
    setEditingComercioId(null);
    setCreateErrorMessage("");
    setPortadaErrorMessage("");
    setHorariosEditorComercio(null);
    setCreateForm({
      nombre: "",
      descripcion: "",
      portada_url: "",
      rubro_id: 1,
      especialidad_ids: [],
      provincia: "",
      ciudad: "",
      direccion: "",
      whatsapp: "",
      instagram: "",
      maps_url: "",
      latitud: null,
      longitud: null,
      mostrar_direccion_publicamente: true,
    });
  }

  function handleEditarComercio(comercio) {
    if (!comercio?.id) return;

    setCreateErrorMessage("");
    setPortadaErrorMessage("");
    setHorariosEditorComercio(null);
    setEditingComercioId(comercio.id);
    setShowCreateForm(true);

    setCreateForm({
      nombre: comercio.nombre || "",
      descripcion: comercio.descripcion || "",
      portada_url: getMediaUrlFromAny(comercio) || "",
      rubro_id: comercio.rubro_id || 1,
      especialidad_ids: comercio.especialidad_ids || [],
      provincia: comercio.provincia || "",
      ciudad: comercio.ciudad || "",
      direccion: comercio.direccion || "",
      whatsapp: comercio.whatsapp || "",
      instagram: comercio.instagram || "",
      maps_url: comercio.maps_url || "",
      latitud: comercio.latitud ?? null,
      longitud: comercio.longitud ?? null,
      mostrar_direccion_publicamente:
        comercio.mostrar_direccion_publicamente !== false,
    });
  }

  function abrirEditorHorariosDesdeFormulario() {
    if (!editingComercioId) return;

    const comercioEditando = misComercios.find(
      (comercio) => Number(comercio.id) === Number(editingComercioId)
    );

    if (!comercioEditando) return;

    setHorariosEditorComercio(comercioEditando);
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
      const rubroId = Number(value);
      setCreateForm((prev) => ({
        ...prev,
        [name]: rubroId,
        especialidad_ids: [],
      }));
      return;
    }

    if (name === "direccion") {
      setCreateForm((prev) =>
        invalidateLocationAfterAddressEdit(prev, value)
      );
      return;
    }

    setCreateForm((prev) => ({ ...prev, [name]: value }));
  }

  function handleEspecialidadesChange(event) {
    const especialidadId = Number(event.target.value);
    event.target.value = "";

    if (!especialidadId) return;

    setCreateForm((prev) => {
      const especialidadesActuales = prev.especialidad_ids.map(Number);

      if (especialidadesActuales.includes(especialidadId)) {
        return prev;
      }

      return {
        ...prev,
        especialidad_ids: [...especialidadesActuales, especialidadId],
      };
    });
  }

  function handleQuitarEspecialidad(especialidadId) {
    const especialidadIdNumerico = Number(especialidadId);

    setCreateForm((prev) => {
      const especialidadesActuales = prev.especialidad_ids.map(Number);

      return {
        ...prev,
        especialidad_ids: especialidadesActuales.filter(
          (id) => id !== especialidadIdNumerico
        ),
      };
    });
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

      if (
        !createForm.direccion.trim() ||
        createForm.latitud === null ||
        createForm.longitud === null
      ) {
        throw new Error("Confirmá una ubicación completa antes de guardar.");
      }

      if (!Number(createForm.rubro_id)) {
        throw new Error("El rubro es obligatorio.");
      }

      const payload = {
        ...createForm,
        rubro_id: Number(createForm.rubro_id),
        especialidad_ids: createForm.especialidad_ids
          .map(Number)
          .filter(Boolean),
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

      delete payload.rubro_secundario_ids;

      if (editingComercioId) {
        await actualizarComercio(editingComercioId, payload);
        await queryClient.invalidateQueries({
          queryKey: queryKeys.spaces.mis(),
        });
        await queryClient.invalidateQueries({
          queryKey: queryKeys.spaces.detalle(editingComercioId),
        });
        await queryClient.invalidateQueries({ queryKey: queryKeys.explore.all });
        await queryClient.invalidateQueries({ queryKey: ["spaces", "seguidos"] });

        setShowCreateForm(false);
        handleResetForm();

        navigate(`/comercios/${editingComercioId}`);
        return;
      }

      await crearComercio(payload);
      await queryClient.invalidateQueries({
        queryKey: queryKeys.spaces.mis(),
      });
      await queryClient.invalidateQueries({ queryKey: queryKeys.explore.all });
      await queryClient.invalidateQueries({ queryKey: ["spaces", "seguidos"] });

      setShowCreateForm(false);
      handleResetForm();
    } catch (error) {
      setCreateErrorMessage(error.message || "Error procesando el espacio.");
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
    <div className="min-h-screen bg-canvas text-primary">
      <main className="mx-auto max-w-3xl px-4 py-8">
        {/* ===================================================== */}
        {/* Header: Perfil administrador */}
        {/* ===================================================== */}
        <section className="mb-6">
          <h1 className="text-xl font-bold text-primary sm:text-2xl">
            Perfil administrador
          </h1>

          {!showPerfilForm && (
          <p className="mt-1 text-sm text-secondary">
            Gestioná tu cuenta, tus espacios y tus publicaciones guardadas.
          </p>
          )}

          {perfilSuccessMessage && (
            <Alert variant="success" className="mt-4 flex items-center gap-2 font-semibold">
              <span aria-hidden="true">✓</span>
              <span>{perfilSuccessMessage}</span>
            </Alert>
          )}

          {/* Mi cuenta */}
          {!showPerfilForm && (
          <Surface as="section" className="mt-4 p-4" aria-labelledby="mi-cuenta-title">
            <div className="flex items-center gap-4">
              <div
                className={[
                  "relative h-16 w-16 shrink-0 rounded-full border overflow-hidden",
                  "flex items-center justify-center",
                  "border-border-strong bg-surface-subtle",
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
                  <span className="text-xs text-secondary">Sin foto</span>
                )}

              </div>

              <div className="min-w-0 flex-1">
                <h2 id="mi-cuenta-title" className="font-semibold text-primary">Mi cuenta</h2>

                <p className="mt-1 text-sm text-secondary">
                  Esta cuenta puede explorar, guardar publicaciones, seguir
                  espacios y administrar uno o varios espacios propios o de
                  clientes.
                </p>

                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <Button
                    type="button"
                    onClick={abrirEdicionPerfil}
                    disabled={isLoadingMe || !usuarioMe || showPerfilForm}
                    variant="secondary"
                    className="px-3 py-2 text-xs leading-4"
                  >
                    <span>Editar perfil</span>
                  </Button>

                  <Button
                    type="button"
                    onClick={() => {
                      setCreateErrorMessage("");
                      handleResetForm();
                      setShowActivarEspacioInfo(misComercios.length === 0);
                      setShowCreateForm(misComercios.length > 0);
                    }}
                    variant="primary"
                    className="px-3 py-2 text-xs leading-4"
                  >
                    <span>Crear nuevo espacio</span>
                  </Button>

                  <Button
                    type="button"
                    onClick={() => setIsAgendaGeneralOpen(true)}
                    disabled={misComercios.length === 0}
                    variant="secondary"
                    className="px-3 py-2 text-xs leading-4"
                  >
                    <span>Agenda general</span>
                  </Button>
                </div>

                <p className="mt-2 break-all text-xs text-muted">
                  {isLoadingMe
                    ? "Cargando usuario..."
                    : usuarioMe?.email
                    ? `Sesión: ${usuarioMe.email}`
                    : "No se pudo cargar el usuario."}
                </p>

                <Button
                  type="button"
                  onClick={manejarLogout}
                  variant="danger"
                  className="mt-2 px-3 py-2 text-xs leading-4"
                >
                  <span>Cerrar sesión</span>
                </Button>

                {avatarErrorMessage && (
                  <Alert variant="danger" role="alert" className="mt-3 p-3">
                    <p className="break-words">
                      {avatarErrorMessage}
                    </p>
                  </Alert>
                )}
              </div>
            </div>
          </Surface>
          )}
        </section>

        {showPerfilForm && (
          <Surface as="section" variant="elevated" className="mb-8 p-4">
            <form onSubmit={handlePerfilSubmit} className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="relative h-32 w-32 shrink-0 overflow-hidden rounded-full border border-border bg-surface-subtle">
                  {avatarUrl ? (
                    <img
                      src={avatarUrl}
                      alt="Foto de perfil"
                      className="h-full w-full object-cover"
                      draggable={false}
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center px-1 text-center text-xs text-secondary">
                      Sin foto
                    </div>
                  )}
                </div>

                <p className="min-w-0 flex-1 truncate text-sm text-secondary">
                  {usuarioMe?.email || "Usuario sin correo"}
                </p>
              </div>

              <div>
                <Button
                  type="button"
                  onClick={handleAvatarClick}
                  disabled={isUploadingAvatar || isSavingPerfil}
                  variant="secondary"
                  className="px-3 py-2 text-xs"
                >
                  {isUploadingAvatar ? "Subiendo..." : "Cambiar foto"}
                </Button>

                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handleAvatarInputChange}
                  className="hidden"
                />
              </div>

              <div>
                <Button
                  type="button"
                  onClick={() =>
                    setShowAppearanceOptions((isOpen) => !isOpen)
                  }
                  disabled={isSavingPerfil}
                  variant="secondary"
                  className="px-3 py-2 text-xs"
                  aria-expanded={showAppearanceOptions}
                  aria-controls="perfil-apariencia-options"
                >
                  Color de fondo
                </Button>

                {showAppearanceOptions && (
                  <Surface
                    id="perfil-apariencia-options"
                    variant="subtle"
                    className="mt-2 p-3"
                  >
                    <AppearanceSelector />
                  </Surface>
                )}
              </div>

              <FormControl label="Provincia" labelFor="perfil-provincia">
                <Input
                  id="perfil-provincia"
                  type="text"
                  name="provincia"
                  value={perfilForm.provincia}
                  onChange={handlePerfilFormChange}
                  disabled={isSavingPerfil}
                  className="text-sm"
                  placeholder="Provincia"
                />
              </FormControl>

              <FormControl label="Ciudad" labelFor="perfil-ciudad">
                <Input
                  id="perfil-ciudad"
                  type="text"
                  name="ciudad"
                  value={perfilForm.ciudad}
                  onChange={handlePerfilFormChange}
                  disabled={isSavingPerfil}
                  className="text-sm"
                  placeholder="Ciudad"
                />
              </FormControl>

              <div className="flex flex-wrap gap-2">
                <Button
                  type="submit"
                  disabled={isSavingPerfil}
                  variant="secondary"
                  className="px-3 py-2 text-xs"
                >
                  {isSavingPerfil ? "Guardando..." : "Guardar"}
                </Button>

                <Button
                  type="button"
                  onClick={cancelarEdicionPerfil}
                  disabled={isSavingPerfil}
                  variant="secondary"
                  className="px-3 py-2 text-xs"
                >
                  Cancelar
                </Button>
              </div>
            </form>

            {perfilErrorMessage && (
              <Alert role="alert" variant="danger" className="mt-3 text-xs">
                {perfilErrorMessage}
              </Alert>
            )}
          </Surface>
        )}

        {!showPerfilForm && showActivarEspacioInfo && (
        <Surface variant="subtle" className="mt-3 p-6 text-center">
          <p className="text-lg font-bold text-primary">
            Creá o administrá espacios en FeedGo!
          </p>

          <p className="mt-2 text-sm leading-6 text-secondary">
            Un espacio es un perfil público dentro de FeedGo!. Puede
            representar un negocio, emprendimiento, servicio, profesión,
            franquicia, cliente o proyecto. Desde esta cuenta vas a poder
            publicar contenido, compartir historias, mostrar información de
            contacto y construir presencia dentro de la comunidad.
          </p>

          <Button
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
            variant="primary"
            className="mt-4 px-4 py-2 text-sm"
          >
            Crear primer espacio
          </Button>
        </Surface>
        )}




        {/* ===================================================== */}
        {/* Sección: Mis espacios */}
        {/* ===================================================== */}
        {!showPerfilForm && (esModoPublicador || showCreateForm) && (
          <section className="mb-8">
            {misComercios.length > 0 && (
              <div className="flex items-end justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold">Mis espacios</h2>
                  <p className="mt-1 text-sm text-secondary">
                    Estos son los espacios públicos que administrás desde esta
                    cuenta.
                  </p>
                </div>
              </div>
            )}

            {showCreateForm && (
              <Surface as="section" variant="elevated" className="mt-4 p-5">
                <p className="font-semibold">
                  {editingComercioId ? "Editar espacio" : "Crear espacio"}
                </p>

                <p className="mt-1 text-sm text-secondary">
                  Creá un espacio para mostrar un negocio, servicio,
                  profesión, emprendimiento o cliente administrado.
                </p>

                {createErrorMessage && (
                  <Alert variant="danger" role="alert" className="mt-3 p-4">
                    <p className="font-semibold">Error</p>
                    <p className="mt-2 break-words">
                      {createErrorMessage}
                    </p>
                  </Alert>
                )}

                <form onSubmit={handleCrearComercioSubmit} className="mt-4 space-y-3">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label htmlFor="espacio-nombre" className="text-xs text-secondary">
                        Nombre del espacio *
                      </label>
                      <Input
                        id="espacio-nombre"
                        name="nombre"
                        value={createForm.nombre}
                        onChange={handleCreateInputChange}
                        className="mt-1 text-sm"
                        placeholder="Ej: Kiosco Centro, Estudio Jurídico, Ferretería..."
                      />
                    </div>

                    <div>
                      <label htmlFor="espacio-rubro" className="text-xs text-secondary">Rubro *</label>
                      <Select
                        id="espacio-rubro"
                        name="rubro_id"
                        value={createForm.rubro_id}
                        onChange={handleCreateInputChange}
                        disabled={isLoadingRubros || rubros.length === 0}
                        className="mt-1 text-sm"
                      >
                        {rubros.length === 0 ? (
                          <option value={createForm.rubro_id}>
                            {isLoadingRubros ? "Cargando rubros..." : "Sin rubros disponibles"}
                          </option>
                        ) : (
                          rubros.map((rubro) => (
                            <option key={rubro.id} value={rubro.id}>
                              {rubro.nombre}
                            </option>
                          ))
                        )}
                      </Select>
                    </div>

                    <Surface variant="subtle" className="sm:col-span-2 rounded-xl p-3">
                      <label htmlFor="espacio-especialidad" className="text-xs font-semibold text-secondary">
                        Especialidades
                      </label>
                      <p className="mt-1 text-xs text-muted">
                        Opcional. Selecciona especialidades reales del rubro
                        principal.
                      </p>

                      <Select
                        id="espacio-especialidad"
                        value=""
                        onChange={handleEspecialidadesChange}
                        disabled={
                          isLoadingEspecialidades ||
                          especialidadesRubro.length === 0 ||
                          especialidadesRubro.every((especialidad) =>
                            createForm.especialidad_ids
                              .map(Number)
                              .includes(Number(especialidad.id))
                          )
                        }
                        className="mt-3 text-sm"
                      >
                        <option value="">
                          {isLoadingEspecialidades
                            ? "Cargando especialidades..."
                            : especialidadesRubro.length === 0
                            ? "Sin especialidades disponibles"
                            : "Agregar especialidad..."}
                        </option>

                        {especialidadesRubro
                          .filter(
                            (especialidad) =>
                              !createForm.especialidad_ids
                                .map(Number)
                                .includes(Number(especialidad.id))
                          )
                          .map((especialidad) => (
                          <option
                            key={especialidad.id}
                            value={especialidad.id}
                          >
                            {especialidad.nombre}
                          </option>
                        ))}
                      </Select>

                      {createForm.especialidad_ids.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {createForm.especialidad_ids
                            .map(Number)
                            .map((especialidadId) => {
                              const especialidad = especialidadesRubro.find(
                                (item) => Number(item.id) === especialidadId
                              );

                              if (!especialidad) return null;

                              return (
                                <span
                                  key={especialidadId}
                                  className="inline-flex items-center gap-2 rounded-full border border-selected-border bg-selected-surface px-3 py-1 text-xs font-semibold text-selected-text"
                                >
                                  {especialidad.nombre}
                                  <Button
                                    type="button"
                                    onClick={() =>
                                      handleQuitarEspecialidad(especialidadId)
                                    }
                                    variant="ghost"
                                    iconOnly
                                    className="!h-6 !min-h-6 !w-6 text-selected-text"
                                    aria-label={`Quitar ${especialidad.nombre}`}
                                  >
                                    x
                                  </Button>
                                </span>
                              );
                            })}
                        </div>
                      )}
                    </Surface>

                    <div>
                      <label htmlFor="espacio-provincia" className="text-xs text-secondary">Provincia *</label>
                      <Input
                        id="espacio-provincia"
                        name="provincia"
                        value={createForm.provincia}
                        onChange={handleCreateInputChange}
                        className="mt-1 text-sm"
                        placeholder="Ej: Santa Fe"
                      />
                    </div>

                    <div>
                      <label htmlFor="espacio-ciudad" className="text-xs text-secondary">Ciudad *</label>
                      <Input
                        id="espacio-ciudad"
                        name="ciudad"
                        value={createForm.ciudad}
                        onChange={handleCreateInputChange}
                        className="mt-1 text-sm"
                        placeholder="Ej: Rafaela"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="espacio-descripcion" className="text-xs text-secondary">Descripción</label>
                    <Textarea
                      id="espacio-descripcion"
                      name="descripcion"
                      value={createForm.descripcion}
                      onChange={handleCreateInputChange}
                      className="mt-1 text-sm"
                      rows={3}
                      placeholder="Contá brevemente qué ofrece este espacio..."
                    />
                  </div>

                  <div>
                    <span className="text-xs text-secondary">Portada</span>

                    <div className="mt-2 flex items-center gap-3">
                      <button
                        type="button"
                        aria-label="Seleccionar portada del espacio"
                        disabled={isUploadingPortada}
                        onClick={handlePortadaClick}
                        onDragOver={handlePortadaDragOver}
                        onDragLeave={handlePortadaDragLeave}
                        onDrop={handlePortadaDrop}
                        className={[
                          "relative h-26 w-26 rounded-2xl border overflow-hidden",
                          "flex items-center justify-center",
                          isDragOverPortada ? "border-success-border" : "border-border-strong",
                          "bg-surface-subtle focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring",
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
                          <span className="text-[10px] text-secondary text-center px-1">
                            Sin portada
                          </span>
                        )}

                        {isUploadingPortada && (
                          <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                            <span className="text-[10px]">Subiendo...</span>
                          </div>
                        )}
                      </button>

                      <div
                        className="flex-1"
                      >
                        <p className="text-sm text-secondary">
                          Elegí una imagen que represente claramente este espacio.
                        </p>

                        <p className="mt-1 text-xs text-muted">
                          Recomendamos utilizar el logo del negocio, el nombre
                          del emprendimiento, una imagen de marca o una foto
                          que ayude a los usuarios a identificar la actividad
                          de forma rápida.
                        </p>

                        <Button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            handlePortadaClick();
                          }}
                          disabled={isUploadingPortada}
                          variant="secondary"
                          className="mt-2 px-3 py-2 text-xs"
                        >
                          {isUploadingPortada ? "Subiendo..." : "Seleccionar imagen"}
                        </Button>

                        <input
                          ref={portadaFileInputRef}
                          type="file"
                          accept="image/jpeg,image/png,image/webp"
                          onChange={handlePortadaInputChange}
                          className="hidden"
                        />

                        {portadaErrorMessage && (
                          <p className="mt-2 text-xs text-danger-text break-words" role="alert">
                            {portadaErrorMessage}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label htmlFor="espacio-whatsapp" className="text-xs text-secondary">WhatsApp</label>
                      <Input
                        id="espacio-whatsapp"
                        name="whatsapp"
                        value={createForm.whatsapp}
                        onChange={handleCreateInputChange}
                        className="mt-1 text-sm"
                        placeholder="+54..."
                      />
                    </div>

                    <div>
                      <label htmlFor="espacio-instagram" className="text-xs text-secondary">Instagram</label>
                      <Input
                        id="espacio-instagram"
                        name="instagram"
                        value={createForm.instagram}
                        onChange={handleCreateInputChange}
                        className="mt-1 text-sm"
                        placeholder="@tu_espacio"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">

                    <div>
                      <label htmlFor="espacio-direccion" className="text-xs text-secondary">Dirección</label>
                      <Input
                        id="espacio-direccion"
                        name="direccion"
                        value={createForm.direccion}
                        onChange={handleCreateInputChange}
                        className="mt-1 text-sm"
                        placeholder="Calle 123"
                      />
                    </div>
                  </div>

                  <div className={horariosEditorComercio ? "hidden" : undefined}>
                    <p className="text-xs text-secondary">
                      Ubicación del espacio
                    </p>

                    <div className="mt-2">
                      <LocationPicker
                        direccion={createForm.direccion}
                        ciudad={createForm.ciudad}
                        provincia={createForm.provincia}
                        latitud={createForm.latitud}
                        longitud={createForm.longitud}
                        onConfirm={({ direccion, latitud, longitud }) => {
                          setCreateForm((prev) => ({
                            ...prev,
                            direccion,
                            latitud,
                            longitud,
                          }));
                        }}
                      />
                    </div>

                    <p className="mt-1 text-xs text-muted">
                      Buscá la dirección, mové el pin y guardá la ubicación exacta.
                    </p>

                    <Surface variant="subtle" className="mt-4 rounded-xl p-3">
                      <label className="flex cursor-pointer items-start gap-3 text-sm text-primary">
                        <input
                          type="checkbox"
                          checked={createForm.mostrar_direccion_publicamente}
                          onChange={(event) =>
                            setCreateForm((previous) => ({
                              ...previous,
                              mostrar_direccion_publicamente: event.target.checked,
                            }))
                          }
                          className="mt-1 h-4 w-4 rounded border-border-strong bg-surface text-interactive-primary focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
                        />
                        <span>
                          <span className="block font-semibold">Mostrar mi dirección públicamente</span>
                          <span className="mt-1 block text-xs leading-5 text-secondary">
                            FeedGo usa la ubicación del espacio para incluirlo en búsquedas locales.
                            Si no atendés al público allí, podés mantener privada la dirección:
                            las personas verán solamente tu ciudad.
                          </span>
                        </span>
                      </label>
                    </Surface>
                  </div>

                  {editingComercioId ? (
                    <Surface variant="subtle" className="rounded-xl p-3">
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                        <div className="min-w-0">
                          <p className="text-xs font-semibold text-secondary">
                            Horarios de atención
                          </p>
                          <p className="mt-1 text-xs text-muted">
                            Administrá las franjas semanales de este espacio.
                          </p>
                        </div>

                        <Button
                          type="button"
                          onClick={abrirEditorHorariosDesdeFormulario}
                          variant="secondary"
                          className="min-h-10 px-3 py-2 text-sm"
                        >
                          Horarios de atención
                        </Button>
                      </div>
                    </Surface>
                  ) : null}

                  <div className="flex items-center gap-3 pt-2">
                    <Button
                      type="submit"
                      disabled={isCreatingComercio}
                      variant="primary"
                      className="px-4 py-2 text-sm"
                    >
                      {isCreatingComercio
                        ? "Procesando..."
                        : editingComercioId
                        ? "Guardar cambios"
                        : "Crear"}
                    </Button>

                    <Button
                      type="button"
                      onClick={() => {
                        setShowCreateForm(false);
                        handleResetForm();
                      }}
                      variant="secondary"
                      className="px-4 py-2 text-sm"
                    >
                      Cancelar
                    </Button>
                  </div>
                </form>
              </Surface>
            )}

            {isLoadingComercios && misComercios.length === 0 && (
              <div className="mt-3 space-y-2">
                <Skeleton className="h-16 rounded-2xl border border-border" />
                <Skeleton className="h-16 rounded-2xl border border-border" />
              </div>
            )}

            {comerciosErrorVisible && misComercios.length === 0 && (
              <Alert variant="danger" role="alert" className="mt-3 p-5">
                <p className="font-semibold">Error</p>
                <p className="mt-2 break-words">
                  {comerciosErrorVisible}
                </p>
              </Alert>
            )}



            {(!isLoadingComercios || misComercios.length > 0) &&
              !(comerciosErrorVisible && misComercios.length === 0) &&
              misComercios.length > 0 && (
                  <div className="mt-3 grid grid-cols-3 gap-1.5 sm:grid-cols-3 sm:gap-3">
                    {misComercios.map((c) => {
                      const isActing = Boolean(isActingComercioById[c.id]);
                      const imagenUrl = getMediaUrlFromAny(c);

                      return (
                        <Surface
                          key={c.id}
                          className="relative overflow-hidden rounded-2xl"
                        >
                          {/* PORTADA */}
                          <Link to={`/comercios/${c.id}`}>
                            <div className="aspect-square bg-surface-subtle">
                              {imagenUrl ? (
                                <img
                                  src={imagenUrl}
                                  alt="Portada del espacio"
                                  className="w-full h-full object-cover"
                                />
                              ) : (
                                <div className="w-full h-full flex items-center justify-center text-xs text-muted">
                                  Sin portada
                                </div>
                              )}
                            </div>
                          </Link>

                          {/* NOMBRE */}
                          <div className="p-2">
                            <p className="truncate text-xs font-semibold text-primary">
                              {c.nombre}
                            </p>

                            <EstadoHorarioBadge
                              horarioAtencion={c.horario_atencion}
                              compact
                              className="mt-1"
                            />
                          </div>

                          {/* BADGE ESTADO */}
                          <span className="absolute top-2 left-2 rounded-full bg-black/70 px-2 py-0.5 text-[10px]">
                            {c.activo ? "🟢Activo" : "🔴Pausado"}
                          </span>

                          {/* ACCIONES */}
                          <div className="absolute top-2 right-2 flex flex-col gap-1">
                            <Button
                              onClick={() => handleEditarComercio(c)}
                              disabled={isActing}
                              variant="secondary"
                              className="px-2 py-1 text-[10px]"
                            >
                              <span>Editar</span>
                            </Button>

                            <Button
                              type="button"
                              onClick={() => setAgendaComercio(c)}
                              disabled={isActing}
                              variant="secondary"
                              className="px-2 py-1 text-[10px]"
                            >
                              <span>Agenda</span>
                            </Button>

                            {c.activo ? (
                              <Button
                                onClick={() => handleDesactivarComercio(c.id)}
                                disabled={isActing}
                                variant="warning"
                                className="px-2 py-1 text-[10px]"
                              >
                                <span>{isActing ? "..." : "Pausar"}</span>
                              </Button>
                            ) : (
                              <Button
                                onClick={() => handleReactivarComercio(c.id)}
                                disabled={isActing}
                                variant="success"
                                className="px-2 py-1 text-[10px]"
                              >
                                {isActing ? "..." : "Activar"}
                              </Button>
                            )}
                          </div>
                        </Surface>
                      );
                    })}
                </div>
              )}

            {horariosEditorComercio ? (
              <HorariosAtencionEditor
                comercio={horariosEditorComercio}
                onClose={() => setHorariosEditorComercio(null)}
              />
            ) : null}

            {agendaComercio ? (
              <AgendaPrivadaModal
                comercio={agendaComercio}
                onClose={() => setAgendaComercio(null)}
              />
            ) : null}

          </section>
        )}

        {isAgendaGeneralOpen ? (
          <AgendaGeneralModal
            comercios={misComercios}
            onClose={() => setIsAgendaGeneralOpen(false)}
          />
        ) : null}
      </main>
    </div>
  );
}

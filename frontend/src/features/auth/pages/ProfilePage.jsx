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
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { Bell } from "lucide-react";
import { ActiveLayer } from "@core";
import { httpPut } from "@core";
import { queryKeys } from "@core/constants/queryKeys";
import {
  Alert,
  Button,
  FormControl,
  getMediaUrlFromAny,
  Input,
  PasswordInput,
  uploadImagen,
  LocationPicker,
  Select,
  Skeleton,
  Surface,
  Textarea,
} from "@shared";
import { invalidateLocationAfterAddressEdit } from "@shared/components/locationPickerState";
import {
  actualizarPerfilUsuario,
  addPasswordCredential,
  reauthenticateWithPassword,
  startGoogleLinkAuthorization,
  startGoogleReauthentication,
  unlinkGoogleIdentity,
  useAuth,
  useCommercialCapabilityRemediation,
  useGoogleIdentityAvailability,
} from "@features/auth";
import { getInternalReturnTo } from "@core/navigation/internalReturnTo";
import { cambiarModoUsuario } from "@features/auth/services/usuarioService";
import { useQueryClient } from "@tanstack/react-query";
import AgendaGeneralModal from "@features/agenda/components/AgendaGeneralModal";
import AgendaPrivadaModal from "@features/agenda/components/AgendaPrivadaModal";
import EstadoHorarioBadge from "@features/availability/components/EstadoHorarioBadge";
import HorariosAtencionEditor from "@features/availability/components/HorariosAtencionEditor";
import { useReemplazarHorariosAtencionMutation } from "@features/availability/hooks/useHorariosAtencion";
import {
  crearComercioConHorariosDraft,
  reintentarHorariosDeComercio,
} from "@features/availability/services/horarios_draft_flow";
import AppearanceSelector from "@features/auth/components/AppearanceSelector";
import CambiarPasswordForm from "@features/auth/components/CambiarPasswordForm";
import {
  evaluarPasswordRegistro,
  passwordRegistroValida,
} from "@features/auth/services/registrationValidation";

import {
  crearComercio,
  desactivarComercio,
  actualizarComercio,
  reactivarComercio,
  useMisComercios,
  useRubroEspecialidades,
  useRubros,
} from "@features/spaces";

const CAMPOS_PERFIL_FALTANTES = {
  provincia: "Agregá tu provincia.",
  ciudad: "Agregá tu ciudad.",
  fecha_nacimiento: "Agregá tu fecha de nacimiento.",
  telefono: "Agregá tu teléfono.",
  email_verificado: "Verificá tu correo electrónico.",
};

const PENDIENTES_COMERCIALES = {
  perfil_incompleto: "Completá los datos de tu perfil.",
  aceptaciones_legales_pendientes: "Revisá las aceptaciones requeridas.",
  mayoria_edad_requerida: "Necesitás ser mayor de edad para esta función.",
};

const PENDING_ASTERISK_CLASS = "ml-1 text-[1.1em] font-bold text-danger-text";
const PERSONAL_PENDING_FIELDS = [
  "email_verificado",
  "fecha_nacimiento",
  "telefono",
  "provincia",
  "ciudad",
];

const AUTHENTICATION_METHOD_LABELS = {
  password: "Contraseña",
  google: "Google",
};

function PendingAsterisk() {
  return <span aria-hidden="true" className={PENDING_ASTERISK_CLASS}>*</span>;
}

export default function ProfilePage() {
  // =====================================================
  // Estado: Mi cuenta del usuario
  // =====================================================
  const [avatarErrorMessage, setAvatarErrorMessage] = useState("");
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
  const [showPerfilForm, setShowPerfilForm] = useState(false);
  const [perfilSection, setPerfilSection] = useState(null);
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [showAccountPendingPanel, setShowAccountPendingPanel] = useState(false);
  const [isSavingPerfil, setIsSavingPerfil] = useState(false);
  const [perfilErrorMessage, setPerfilErrorMessage] = useState("");
  const [perfilSuccessMessage, setPerfilSuccessMessage] = useState("");
  const [securityErrorMessage, setSecurityErrorMessage] = useState("");
  const [securityStatusMessage, setSecurityStatusMessage] = useState("");
  const [securityConfirmation, setSecurityConfirmation] = useState(null);
  const [isSecurityActionPending, setIsSecurityActionPending] = useState(false);
  const [addPasswordForm, setAddPasswordForm] = useState({ password: "", confirmation: "" });
  const [showReauthentication, setShowReauthentication] = useState(false);
  const [reauthenticationPassword, setReauthenticationPassword] = useState("");
  const [isReauthenticating, setIsReauthenticating] = useState(false);
  const [remediationTarget, setRemediationTarget] = useState(null);
  const [perfilForm, setPerfilForm] = useState({
    provincia: "",
    ciudad: "",
    fecha_nacimiento: "",
    telefono_e164: "",
  });

  const fileInputRef = useRef(null);
  const accountPendingPanelCloseRef = useRef(null);
  const securityActionInFlightRef = useRef(false);

  // =====================================================
  // Estado: Portada de espacio
  // =====================================================
  const [isUploadingPortada, setIsUploadingPortada] = useState(false);
  const [isDragOverPortada, setIsDragOverPortada] = useState(false);
  const [portadaErrorMessage, setPortadaErrorMessage] = useState("");

  const portadaFileInputRef = useRef(null);

  async function activarModoPublicador() {
    try {
      const token = accessToken;

      if (!token) {
        throw new Error("No hay sesión activa.");
      }

      await cambiarModoUsuario(token, "publicador");

      await refrescarUsuario();
    } catch (error) {
      alert(
        error?.message ||
        "No se pudo activar el modo publicador."
      );
    }
  }

  function abrirEdicionPerfil(target = null) {
    setShowAccountPendingPanel(false);
    setPerfilErrorMessage("");
    setPerfilSuccessMessage("");
    setShowPasswordForm(false);
    setPerfilSection(target ? "datos" : "menu");
    setPerfilForm({
      provincia: usuario?.provincia || "",
      ciudad: usuario?.ciudad || "",
      fecha_nacimiento: usuario?.fecha_nacimiento || "",
      telefono_e164: usuario?.telefono_e164 || "",
    });
    setShowPerfilForm(true);
    setRemediationTarget(target);
  }

  function cancelarEdicionPerfil() {
    setPerfilErrorMessage("");
    setPerfilSuccessMessage("");
    setPerfilForm({
      provincia: usuario?.provincia || "",
      ciudad: usuario?.ciudad || "",
      fecha_nacimiento: usuario?.fecha_nacimiento || "",
      telefono_e164: usuario?.telefono_e164 || "",
    });
    setShowPerfilForm(false);
    setPerfilSection(null);
    setRemediationTarget(null);
  }

  function volverAlMenuEdicion() {
    setPerfilErrorMessage("");
    setShowPasswordForm(false);
    setPerfilForm({
      provincia: usuario?.provincia || "",
      ciudad: usuario?.ciudad || "",
      fecha_nacimiento: usuario?.fecha_nacimiento || "",
      telefono_e164: usuario?.telefono_e164 || "",
    });
    setPerfilSection("menu");
    setRemediationTarget(null);
  }

  function cerrarPanelPendientesCuenta() {
    setShowAccountPendingPanel(false);
  }

  function completarCambioPassword() {
    setShowPasswordForm(false);
    setPerfilSection("menu");
    setPerfilSuccessMessage("Listo, tu contraseña fue actualizada.");
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

      const token = accessToken;

      if (!token) {
        throw new Error("No hay sesion activa.");
      }

      const payload = {
        provincia: perfilForm.provincia.trim(),
        ciudad: perfilForm.ciudad.trim(),
        fecha_nacimiento: perfilForm.fecha_nacimiento || null,
        telefono_e164: perfilForm.telefono_e164.trim() || null,
      };

      await actualizarPerfilUsuario(token, payload);

      const usuarioRefrescado = await refrescarUsuario();
      setPerfilForm({
        provincia: usuarioRefrescado?.provincia || "",
        ciudad: usuarioRefrescado?.ciudad || "",
        fecha_nacimiento: usuarioRefrescado?.fecha_nacimiento || "",
        telefono_e164: usuarioRefrescado?.telefono_e164 || "",
      });
      setPerfilSection("menu");
      setPerfilSuccessMessage("Perfil actualizado");
    } catch (error) {
      const mensaje =
        error?.status === 409
          ? "Este teléfono ya está registrado. Probá con otro."
          : error?.status === 422
            ? "Revisá los datos ingresados e intentá nuevamente."
            : "No pudimos actualizar tus datos ahora. Intentá nuevamente.";
      setPerfilErrorMessage(mensaje);
      setPerfilSuccessMessage("");
    } finally {
      setIsSavingPerfil(false);
    }
  }

  async function uploadMedia(file) {
    const token = accessToken;

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
    const token = accessToken;

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
      await updateUsuarioAvatar(url);

      await refrescarUsuario();
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
  const location = useLocation();
  const queryClient = useQueryClient();
  const reemplazarHorariosMutation = useReemplazarHorariosAtencionMutation();
  const navigate = useNavigate();
  const {
    accessToken,
    isCargandoUsuario: isLoadingMe,
    login,
    logout,
    refrescarUsuario,
    usuario,
  } = useAuth();
  const { isAvailable: googleIdentityAvailable } = useGoogleIdentityAvailability();
  const camposPerfilFaltantes = Array.isArray(usuario?.campos_perfil_faltantes)
    ? usuario.campos_perfil_faltantes
    : [];
  const pendientesComerciales = Array.isArray(usuario?.pendientes_comerciales)
    ? usuario.pendientes_comerciales
    : [];
  const {
    intentarAccionComercial,
    manejarErrorCapability,
  } = useCommercialCapabilityRemediation();
  const [comerciosErrorMessage, setComerciosErrorMessage] = useState("");
  const {
    data: misComercios = [],
    isLoading: isLoadingComercios,
    error: misComerciosError,
  } = useMisComercios({
    enabled: Boolean(accessToken),
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
  const [horariosDraft, setHorariosDraft] = useState([]);
  const [horariosDraftConfigurado, setHorariosDraftConfigurado] = useState(false);
  const [comercioCreadoPendienteHorarios, setComercioCreadoPendienteHorarios] =
    useState(null);

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
    setHorariosDraft([]);
    setHorariosDraftConfigurado(false);
    setComercioCreadoPendienteHorarios(null);
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

  async function handleEditarComercio(comercio) {
    if (!comercio?.id) return;
    if (!(await intentarAccionComercial("puede_administrar_espacios"))) return;

    setCreateErrorMessage("");
    setPortadaErrorMessage("");
    setHorariosEditorComercio(null);
    setHorariosDraft([]);
    setHorariosDraftConfigurado(false);
    setComercioCreadoPendienteHorarios(null);
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

  async function abrirEditorHorariosDesdeFormulario() {
    if (editingComercioId && !(await intentarAccionComercial("puede_administrar_espacios"))) {
      return;
    }
    if (!editingComercioId) {
      setHorariosEditorComercio({
        nombre: createForm.nombre || "Nuevo espacio",
      });
      return;
    }

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

  function iniciarRemediationPerfil(campo) {
    const returnTo = getInternalReturnTo(searchParams.get("returnTo"), "/perfil");
    if (campo === "email_verificado") {
      navigate("/verificar-email", { state: { returnTo } });
      return;
    }

    abrirEdicionPerfil(campo);
  }

  useEffect(() => {
    if (!location.state?.resetProfileEditor) return;
    setPerfilErrorMessage("");
    setPerfilSuccessMessage("");
    setShowPasswordForm(false);
    setShowPerfilForm(false);
    setPerfilSection(null);
    setRemediationTarget(null);
  }, [location.key, location.state?.resetProfileEditor]);

  useEffect(() => {
    if (!perfilSuccessMessage) return undefined;

    const timeoutId = window.setTimeout(() => {
      setPerfilSuccessMessage("");
    }, 3000);

    return () => window.clearTimeout(timeoutId);
  }, [perfilSuccessMessage]);

  useEffect(() => {
    if (!showPerfilForm || showPasswordForm || !remediationTarget) return;

    const inputByTarget = {
      provincia: "perfil-provincia",
      ciudad: "perfil-ciudad",
      fecha_nacimiento: "perfil-fecha-nacimiento",
      telefono: "perfil-telefono",
    };
    const inputId = inputByTarget[remediationTarget];
    if (inputId) {
      document.getElementById(inputId)?.focus();
    }
    setRemediationTarget(null);
  }, [remediationTarget, showPasswordForm, showPerfilForm]);

  useEffect(() => {
    if (searchParams.get("remediation") !== "commercial" || !usuario) return;

    const campo = camposPerfilFaltantes[0];
    const returnTo = getInternalReturnTo(searchParams.get("returnTo"), "/perfil");
    navigate("/perfil", { replace: true });

    if (campo) {
      if (campo === "email_verificado") {
        navigate("/verificar-email", { state: { returnTo } });
      } else {
        abrirEdicionPerfil(campo);
      }
      return;
    }

    if (pendientesComerciales.includes("aceptaciones_legales_pendientes")) {
      setPerfilSuccessMessage("Todavía no hay una pantalla para revisar estas aceptaciones.");
    } else if (pendientesComerciales.includes("mayoria_edad_requerida")) {
      setPerfilSuccessMessage("Necesitás ser mayor de edad para usar esta función.");
    }
  }, [camposPerfilFaltantes, navigate, pendientesComerciales, searchParams, usuario]);

  useEffect(() => {
    if (searchParams.get("security") !== "access" || !usuario) return;
    navigate("/perfil", { replace: true });
    setShowAccountPendingPanel(false);
    setShowPasswordForm(false);
    setShowPerfilForm(true);
    setPerfilSection("security");
    setRemediationTarget(null);
  }, [navigate, searchParams, usuario]);

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

    const capability = editingComercioId
      ? "puede_administrar_espacios"
      : "puede_crear_espacio";
    if (!(await intentarAccionComercial(capability))) return;

    try {
      setCreateErrorMessage("");
      setIsCreatingComercio(true);

      if (comercioCreadoPendienteHorarios) {
        try {
          await reintentarHorariosDeComercio({
            guardarHorarios: (variables) =>
              reemplazarHorariosMutation.mutateAsync(variables),
            comercioId: comercioCreadoPendienteHorarios.id,
            franjas: horariosDraft,
          });
          setShowCreateForm(false);
          handleResetForm();
        } catch {
          setCreateErrorMessage(
            "El espacio fue creado, pero no se pudieron guardar sus horarios."
          );
        }
        return;
      }

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

      const { comercio: comercioCreado, horariosError } =
        await crearComercioConHorariosDraft({
          crear: crearComercio,
          guardarHorarios: (variables) =>
            reemplazarHorariosMutation.mutateAsync(variables),
          payload,
          horariosConfigurados: horariosDraftConfigurado,
          franjas: horariosDraft,
        });
      await queryClient.invalidateQueries({
        queryKey: queryKeys.spaces.mis(),
      });
      await queryClient.invalidateQueries({ queryKey: queryKeys.explore.all });
      await queryClient.invalidateQueries({ queryKey: ["spaces", "seguidos"] });

      if (horariosError) {
        setComercioCreadoPendienteHorarios(comercioCreado);
        setCreateErrorMessage(
          "El espacio fue creado, pero no se pudieron guardar sus horarios."
        );
        return;
      }

      setShowCreateForm(false);
      handleResetForm();
    } catch (error) {
      if (await manejarErrorCapability(error)) return;
      setCreateErrorMessage(error.message || "Error procesando el espacio.");
    } finally {
      setIsCreatingComercio(false);
    }
  }

  async function handleDesactivarComercio(comercioId) {
    if (!comercioId) return;
    if (isActingComercioById[comercioId]) return;
    if (!(await intentarAccionComercial("puede_administrar_espacios"))) return;

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
      if (await manejarErrorCapability(error)) return;
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
    if (!(await intentarAccionComercial("puede_administrar_espacios"))) return;

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
      if (await manejarErrorCapability(error)) return;
      setComerciosErrorMessage(
        error.message || "Error reactivando el espacio."
      );
    } finally {
      setComercioLock(comercioId, false);
    }
  }

  async function abrirAgendaComercio(comercio) {
    if (!(await intentarAccionComercial("puede_administrar_espacios"))) return;
    setAgendaComercio(comercio);
  }

  async function abrirAgendaGeneral() {
    if (!(await intentarAccionComercial("puede_administrar_espacios"))) return;
    setIsAgendaGeneralOpen(true);
  }

  const avatarUrl = usuario?.avatar_url || "";
  const authenticationMethods = usuario?.authentication_methods || {};
  const hasPassword = authenticationMethods.has_password === true;
  const googleLinked = authenticationMethods.google_linked === true;
  const usableAuthenticationMethods = Array.isArray(authenticationMethods.usable_methods)
    ? authenticationMethods.usable_methods
    : [];
  const canUnlinkGoogle = authenticationMethods.can_unlink_google === true;
  const canReauthenticateWithPassword = usableAuthenticationMethods.includes("password");
  const canReauthenticateWithGoogle =
    usableAuthenticationMethods.includes("google") && googleIdentityAvailable;
  const addPasswordRequirements = evaluarPasswordRegistro(addPasswordForm.password);
  const addPasswordIsValid = passwordRegistroValida(addPasswordForm.password);

  function clearSecurityFeedback() {
    setSecurityErrorMessage("");
    setSecurityStatusMessage("");
  }

  function requestRecentReauthentication() {
    setAddPasswordForm({ password: "", confirmation: "" });
    setSecurityConfirmation(null);
    setReauthenticationPassword("");
    setShowReauthentication(true);
    setSecurityStatusMessage(
      "Para continuar, confirma nuevamente uno de tus metodos de acceso."
    );
  }

  function handleSecurityOperationError(error) {
    if (error?.status === 403 && error?.code === "recent_reauthentication_required") {
      requestRecentReauthentication();
      return true;
    }
    if (error?.status === 401) {
      void refrescarUsuario();
      setSecurityErrorMessage("Tu sesion ya no esta activa. Inicia sesion nuevamente.");
      return true;
    }
    return false;
  }

  async function refreshSecurityMethods() {
    const refreshed = await refrescarUsuario();
    return Boolean(refreshed);
  }

  async function handleAddPassword(event) {
    event.preventDefault();
    clearSecurityFeedback();
    if (
      !accessToken ||
      !addPasswordIsValid ||
      addPasswordForm.password !== addPasswordForm.confirmation ||
      isSecurityActionPending ||
      securityActionInFlightRef.current
    ) {
      return;
    }

    securityActionInFlightRef.current = true;
    setIsSecurityActionPending(true);
    try {
      await addPasswordCredential(accessToken, { newPassword: addPasswordForm.password });
      setAddPasswordForm({ password: "", confirmation: "" });
      if (await refreshSecurityMethods()) {
        setSecurityStatusMessage("Listo, configuraste tu contrasena.");
      }
    } catch (error) {
      setAddPasswordForm({ password: "", confirmation: "" });
      if (!handleSecurityOperationError(error)) {
        setSecurityErrorMessage("No pudimos agregar la contrasena. Intenta nuevamente.");
      }
    } finally {
      securityActionInFlightRef.current = false;
      setIsSecurityActionPending(false);
    }
  }

  async function startGoogleLink() {
    if (
      !accessToken ||
      !googleIdentityAvailable ||
      googleLinked ||
      securityActionInFlightRef.current
    ) {
      return;
    }
    securityActionInFlightRef.current = true;
    setIsSecurityActionPending(true);
    clearSecurityFeedback();
    try {
      const result = await startGoogleLinkAuthorization(accessToken, { returnTo: "/perfil?security=access" });
      if (typeof result?.authorization_url !== "string") throw new Error("authorization_url_missing");
      window.location.assign(result.authorization_url);
    } catch (error) {
      securityActionInFlightRef.current = false;
      if (!handleSecurityOperationError(error)) {
        setSecurityErrorMessage("No pudimos iniciar la vinculacion con Google.");
      }
      setIsSecurityActionPending(false);
    }
  }

  async function confirmUnlinkGoogle() {
    if (!accessToken || !canUnlinkGoogle || securityActionInFlightRef.current) return;
    securityActionInFlightRef.current = true;
    setIsSecurityActionPending(true);
    clearSecurityFeedback();
    try {
      await unlinkGoogleIdentity(accessToken);
      setSecurityConfirmation(null);
      if (await refreshSecurityMethods()) {
        setSecurityStatusMessage("Google fue desvinculada de tu cuenta.");
      }
    } catch (error) {
      if (!handleSecurityOperationError(error)) {
        setSecurityErrorMessage(
          error?.code === "cannot_remove_last_authentication_method"
            ? "No podes desvincular Google porque es tu unico metodo de acceso."
            : "No pudimos desvincular Google. Intenta nuevamente."
        );
      }
    } finally {
      securityActionInFlightRef.current = false;
      setIsSecurityActionPending(false);
    }
  }

  async function submitPasswordReauthentication(event) {
    event.preventDefault();
    if (
      !accessToken ||
      !reauthenticationPassword ||
      isReauthenticating ||
      securityActionInFlightRef.current
    ) return;
    clearSecurityFeedback();
    securityActionInFlightRef.current = true;
    setIsReauthenticating(true);
    try {
      const result = await reauthenticateWithPassword(accessToken, {
        currentPassword: reauthenticationPassword,
      });
      if (typeof result?.token !== "string") throw new Error("reauthentication_token_missing");
      login(result.token);
      setReauthenticationPassword("");
      setShowReauthentication(false);
      setSecurityStatusMessage(
        "Reautenticacion completada. Confirma nuevamente la operacion que querias realizar."
      );
    } catch {
      setReauthenticationPassword("");
      setSecurityErrorMessage("No pudimos confirmar tu contrasena. Intenta nuevamente.");
    } finally {
      securityActionInFlightRef.current = false;
      setIsReauthenticating(false);
    }
  }

  async function beginGoogleReauthentication() {
    if (!accessToken || !canReauthenticateWithGoogle || securityActionInFlightRef.current) return;
    securityActionInFlightRef.current = true;
    setIsReauthenticating(true);
    clearSecurityFeedback();
    try {
      const result = await startGoogleReauthentication(accessToken, { returnTo: "/perfil?security=access" });
      if (typeof result?.authorization_url !== "string") throw new Error("authorization_url_missing");
      window.location.assign(result.authorization_url);
    } catch {
      securityActionInFlightRef.current = false;
      setIsReauthenticating(false);
      setSecurityErrorMessage("No pudimos iniciar la reautenticacion con Google.");
    }
  }
  const esModoPublicador = usuario?.modo_activo === "publicador";
  const perfilCompleto = usuario?.perfil_completo === true;
  const capacidadesComerciales = usuario?.capabilities || {};
  const tienePendientesCuenta = Boolean(
    usuario &&
      (!perfilCompleto ||
        camposPerfilFaltantes.length > 0 ||
        pendientesComerciales.length > 0 ||
        Object.values(capacidadesComerciales).some((capability) => capability === false))
  );
  const esCampoPerfilFaltante = (campo) => camposPerfilFaltantes.includes(campo);
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
          <Surface as="section" className="relative mt-4 p-4" aria-labelledby="mi-cuenta-title">
            <Button
              type="button"
              iconOnly
              aria-label={
                tienePendientesCuenta
                  ? "Ver pendientes de la cuenta: tenés pendientes"
                  : "Ver pendientes de la cuenta"
              }
              aria-expanded={showAccountPendingPanel}
              aria-controls="perfil-pendientes-panel"
              onClick={() => setShowAccountPendingPanel(true)}
              variant="secondary"
              className="absolute right-3 top-3 !h-8 !min-h-8 !w-8 !bg-transparent hover:!bg-surface-subtle"
            >
              <span aria-hidden="true" className="relative flex h-6 w-6 items-center justify-center">
                <Bell size={13} strokeWidth={2.25} />
                {tienePendientesCuenta && (
                  <span className="absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full bg-danger-text ring-2 ring-surface" />
                )}
              </span>
            </Button>
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
                <div className="flex min-w-0 flex-wrap items-baseline gap-x-2 gap-y-1 pr-10">
                  <h2 id="mi-cuenta-title" className="font-semibold text-primary">Mi cuenta</h2>
                  {usuario?.email && (
                    <span className="min-w-0 break-all text-sm text-secondary">{usuario.email}</span>
                  )}
                </div>

                <p className="mt-1 text-sm text-secondary">
                  Esta cuenta puede explorar, guardar publicaciones, seguir
                  espacios y administrar uno o varios espacios propios o de
                  clientes.
                </p>

                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <Button
                    type="button"
                    onClick={() => abrirEdicionPerfil()}
                    disabled={isLoadingMe || !usuario || showPerfilForm}
                    variant="secondary"
                    className="px-3 py-2 text-xs leading-4"
                  >
                    <span>
                      Editar perfil
                      {!perfilCompleto && (
                        <>
                          <PendingAsterisk />
                          <span className="sr-only">: tenés datos pendientes</span>
                        </>
                      )}
                    </span>
                  </Button>

                  <Button
                    type="button"
                    onClick={async () => {
                      if (!(await intentarAccionComercial("puede_crear_espacio"))) return;
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
                    onClick={abrirAgendaGeneral}
                    disabled={misComercios.length === 0}
                    variant="secondary"
                    className="px-3 py-2 text-xs leading-4"
                  >
                    <span>Agenda general</span>
                  </Button>
                </div>

                {isLoadingMe && <p className="mt-2 text-xs text-muted">Cargando usuario...</p>}

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

          {!showPerfilForm && showAccountPendingPanel && usuario && (
            <ActiveLayer
              onClose={cerrarPanelPendientesCuenta}
              labelledBy="perfil-pendientes-title"
              describedBy="perfil-pendientes-description"
              initialFocusRef={accountPendingPanelCloseRef}
              contentClassName="w-full max-w-md px-4 py-6"
            >
              <Surface
                id="perfil-pendientes-panel"
                className="space-y-4 p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 id="perfil-pendientes-title" className="font-semibold text-primary">
                      Estado del perfil
                    </h2>
                    <p id="perfil-pendientes-description" className="mt-1 text-sm text-secondary" role="status">
                      {perfilCompleto ? "Perfil completo" : "Perfil incompleto"}
                    </p>
                  </div>
                  <Button
                    ref={accountPendingPanelCloseRef}
                    type="button"
                    onClick={cerrarPanelPendientesCuenta}
                    variant="secondary"
                    className="px-3 py-2 text-xs"
                  >
                    Cerrar
                  </Button>
                </div>

                {!perfilCompleto && (
                  <div className="space-y-2">
                    <p className="text-sm text-secondary">
                      Completá estos datos para preparar tu perfil.
                    </p>
                    <ul className="space-y-2" aria-label="Datos pendientes del perfil">
                      {camposPerfilFaltantes.map((campo) => (
                        <li
                          key={campo}
                          className="flex flex-wrap items-center justify-between gap-2 text-sm text-secondary"
                        >
                          <span>{CAMPOS_PERFIL_FALTANTES[campo]}</span>
                          <Button
                            type="button"
                            onClick={() => iniciarRemediationPerfil(campo)}
                            variant="secondary"
                            className="px-3 py-2 text-xs"
                          >
                            {campo === "email_verificado" ? "Verificar" : "Completar"}
                          </Button>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="space-y-2">
                  <h3 className="text-sm font-semibold text-primary">
                    Funciones comerciales
                  </h3>
                  <ul className="space-y-1 text-sm text-secondary">
                    <li>
                      Crear espacios: {capacidadesComerciales.puede_crear_espacio ? "disponible" : "todavía no disponible"}
                    </li>
                    <li>
                      Administrar espacios: {capacidadesComerciales.puede_administrar_espacios ? "disponible" : "todavía no disponible"}
                    </li>
                    <li>
                      Publicar en espacios: {capacidadesComerciales.puede_publicar_en_espacios ? "disponible" : "todavía no disponible"}
                    </li>
                  </ul>
                </div>

                {pendientesComerciales.length > 0 && (
                  <ul className="space-y-1 text-sm text-secondary" aria-label="Pendientes comerciales">
                    {pendientesComerciales.map((pendiente) => (
                      <li key={pendiente}>{PENDIENTES_COMERCIALES[pendiente]}</li>
                    ))}
                  </ul>
                )}
              </Surface>
            </ActiveLayer>
          )}
        </section>

        {showPerfilForm && (
          <Surface as="section" variant="elevated" className="mb-8 p-4">
            {perfilSection === "menu" ? (
              <section className="space-y-3" aria-labelledby="editar-perfil-menu-title">
                <div className="flex items-center justify-between gap-3">
                  <h2 id="editar-perfil-menu-title" className="text-lg font-semibold text-primary">
                    Editar perfil
                  </h2>
                  <Button type="button" onClick={cancelarEdicionPerfil} variant="secondary" className="px-3 py-2 text-xs">
                    Volver
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button type="button" onClick={() => setPerfilSection("datos")} variant="secondary" className="px-3 py-2 text-xs">
                    Datos personales
                    {PERSONAL_PENDING_FIELDS.some(esCampoPerfilFaltante) && <PendingAsterisk />}
                  </Button>
                  <Button type="button" onClick={() => setPerfilSection("foto")} variant="secondary" className="px-3 py-2 text-xs">
                    Cambiar foto
                  </Button>
                  <Button type="button" onClick={() => { setShowPasswordForm(hasPassword); setPerfilSection("security"); }} variant="secondary" className="px-3 py-2 text-xs">
                    Seguridad y acceso
                  </Button>
                  <Button type="button" onClick={() => setPerfilSection("fondo")} variant="secondary" className="px-3 py-2 text-xs">
                    Cambiar fondo
                  </Button>
                </div>
              </section>
            ) : perfilSection === "foto" ? (
              <section className="space-y-4" aria-labelledby="perfil-foto-title">
                <h2 id="perfil-foto-title" className="text-lg font-semibold text-primary">Cambiar foto</h2>
                <div className="flex items-center gap-3">
                  <div className="relative h-32 w-32 shrink-0 overflow-hidden rounded-full border border-border bg-surface-subtle">
                    {avatarUrl ? <img src={avatarUrl} alt="Foto de perfil" className="h-full w-full object-cover" draggable={false} /> : <span className="flex h-full w-full items-center justify-center text-xs text-secondary">Sin foto</span>}
                  </div>
                  <div>
                    <Button type="button" onClick={handleAvatarClick} disabled={isUploadingAvatar} variant="secondary" className="px-3 py-2 text-xs">
                      {isUploadingAvatar ? "Subiendo..." : "Seleccionar imagen"}
                    </Button>
                    <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp" onChange={handleAvatarInputChange} className="hidden" />
                  </div>
                </div>
                {avatarErrorMessage && <Alert variant="danger" role="alert">{avatarErrorMessage}</Alert>}
                <div className="flex flex-wrap gap-2">
                  <Button type="button" onClick={volverAlMenuEdicion} variant="secondary" className="px-3 py-2 text-xs">Aplicar</Button>
                  <Button type="button" onClick={volverAlMenuEdicion} variant="secondary" className="px-3 py-2 text-xs">Cancelar</Button>
                </div>
              </section>
            ) : perfilSection === "fondo" ? (
              <section className="space-y-4" aria-labelledby="perfil-fondo-title">
                <h2 id="perfil-fondo-title" className="text-lg font-semibold text-primary">Cambiar fondo</h2>
                <AppearanceSelector />
                <div className="flex flex-wrap gap-2">
                  <Button type="button" onClick={volverAlMenuEdicion} variant="secondary" className="px-3 py-2 text-xs">Aplicar</Button>
                  <Button type="button" onClick={volverAlMenuEdicion} variant="secondary" className="px-3 py-2 text-xs">Cancelar</Button>
                </div>
              </section>
            ) : perfilSection === "security" ? (
              <section className="space-y-4" aria-labelledby="perfil-security-title">
                <div>
                  <h2 id="perfil-security-title" className="text-lg font-semibold">Seguridad y acceso</h2>
                  <p className="mt-1 text-sm text-secondary">
                    Revisá los métodos disponibles para acceder a tu cuenta.
                  </p>
                </div>

                <dl className="space-y-2 rounded-xl border border-border p-3 text-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <dt className="font-medium text-primary">Contraseña</dt>
                    <dd className="text-secondary">{hasPassword ? "Configurada" : "No configurada"}</dd>
                  </div>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <dt className="font-medium text-primary">Google</dt>
                    <dd className="text-secondary">{googleLinked ? "Vinculada" : "No vinculada"}</dd>
                  </div>
                </dl>

                <section className="space-y-2" aria-labelledby="metodos-acceso-title">
                  <h3 id="metodos-acceso-title" className="text-base font-semibold">Métodos disponibles</h3>
                  {usableAuthenticationMethods.length > 0 ? (
                    <ul className="list-disc space-y-1 pl-5 text-sm text-secondary">
                      {usableAuthenticationMethods.map((method) => (
                        <li key={method}>{AUTHENTICATION_METHOD_LABELS[method] || "Método de acceso"}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-secondary">No hay métodos de acceso disponibles para mostrar.</p>
                  )}
                </section>

                {securityErrorMessage && (
                  <Alert role="alert" variant="danger">{securityErrorMessage}</Alert>
                )}
                {securityStatusMessage && (
                  <Alert role="status" variant="success">{securityStatusMessage}</Alert>
                )}

                {showReauthentication && (
                  <section className="space-y-3 rounded-xl border border-border p-3" aria-labelledby="reauthentication-title">
                    <div>
                      <h3 id="reauthentication-title" className="text-base font-semibold">Confirmar acceso</h3>
                      <p className="mt-1 text-sm text-secondary">
                        Volve a demostrar control de uno de tus metodos de acceso antes de continuar.
                      </p>
                    </div>
                    {canReauthenticateWithPassword && (
                      <form onSubmit={submitPasswordReauthentication} className="space-y-2">
                        <FormControl label="Contrasena actual" labelFor="security-reauth-password">
                          <PasswordInput
                            id="security-reauth-password"
                            autoComplete="current-password"
                            value={reauthenticationPassword}
                            onChange={(event) => setReauthenticationPassword(event.target.value)}
                            required
                          />
                        </FormControl>
                        <Button type="submit" disabled={isReauthenticating} variant="secondary" className="px-3 py-2 text-xs">
                          {isReauthenticating ? "Confirmando..." : "Confirmar con contrasena"}
                        </Button>
                      </form>
                    )}
                    {canReauthenticateWithGoogle && (
                      <Button
                        type="button"
                        onClick={beginGoogleReauthentication}
                        disabled={isReauthenticating}
                        variant="secondary"
                        className="px-3 py-2 text-xs"
                      >
                        Continuar con Google
                      </Button>
                    )}
                    <Button
                      type="button"
                      onClick={() => { setReauthenticationPassword(""); setShowReauthentication(false); }}
                      disabled={isReauthenticating}
                      variant="secondary"
                      className="px-3 py-2 text-xs"
                    >
                      Cancelar
                    </Button>
                  </section>
                )}

                {hasPassword ? (
                  <section className="space-y-3" aria-labelledby="cambiar-password-title">
                    <h3 id="cambiar-password-title" className="text-base font-semibold">Cambiar contraseña</h3>
                    <CambiarPasswordForm onCancel={volverAlMenuEdicion} onSuccess={completarCambioPassword} />
                  </section>
                ) : (
                  <section className="space-y-3" aria-labelledby="agregar-password-title">
                    <h3 id="agregar-password-title" className="text-base font-semibold">Contraseña</h3>
                    <p className="text-sm text-secondary">Todavía no configuraste una contraseña.</p>
                    <form onSubmit={handleAddPassword} className="space-y-3">
                      <FormControl label="Nueva contraseña" labelFor="add-password-new">
                        <PasswordInput
                          id="add-password-new"
                          autoComplete="new-password"
                          value={addPasswordForm.password}
                          onChange={(event) => setAddPasswordForm((current) => ({ ...current, password: event.target.value }))}
                          required
                        />
                        <p className="mt-1 text-xs text-secondary">
                          {addPasswordRequirements.longitud && addPasswordRequirements.mayuscula && addPasswordRequirements.minuscula && addPasswordRequirements.numero && addPasswordRequirements.sinEspacios
                            ? "La contraseña cumple los requisitos."
                            : "Usá al menos 8 caracteres, mayúscula, minúscula, número y sin espacios."}
                        </p>
                      </FormControl>
                      <FormControl
                        label="Confirmar nueva contraseña"
                        labelFor="add-password-confirmation"
                        error={addPasswordForm.confirmation && addPasswordForm.confirmation !== addPasswordForm.password ? "Las contraseñas no coinciden." : null}
                      >
                        <PasswordInput
                          id="add-password-confirmation"
                          autoComplete="new-password"
                          value={addPasswordForm.confirmation}
                          onChange={(event) => setAddPasswordForm((current) => ({ ...current, confirmation: event.target.value }))}
                          required
                        />
                      </FormControl>
                      <Button
                        type="submit"
                        disabled={isSecurityActionPending || !addPasswordIsValid || addPasswordForm.password !== addPasswordForm.confirmation}
                        variant="secondary"
                        className="px-3 py-2 text-xs"
                      >
                        {isSecurityActionPending ? "Guardando..." : "Agregar contraseña"}
                      </Button>
                    </form>
                  </section>
                )}

                <section className="space-y-2" aria-labelledby="google-access-title">
                  <h3 id="google-access-title" className="text-base font-semibold">Google</h3>
                  {googleLinked ? (
                    <>
                      {!googleIdentityAvailable && (
                        <p className="text-sm text-secondary">Google está vinculada, pero no está disponible actualmente.</p>
                      )}
                      {canUnlinkGoogle && (
                        <Button type="button" onClick={() => setSecurityConfirmation("unlink-google")} disabled={isSecurityActionPending} variant="secondary" className="px-3 py-2 text-xs">
                          Desvincular Google
                        </Button>
                      )}
                    </>
                  ) : googleIdentityAvailable ? (
                    <Button type="button" onClick={() => setSecurityConfirmation("link-google")} disabled={isSecurityActionPending} variant="secondary" className="px-3 py-2 text-xs">
                      Vincular Google
                    </Button>
                  ) : null}
                </section>
                {securityConfirmation && (
                  <section className="space-y-3 rounded-xl border border-border p-3" aria-labelledby="security-confirmation-title">
                    <h3 id="security-confirmation-title" className="text-base font-semibold">
                      {securityConfirmation === "link-google" ? "Vincular Google" : "Desvincular Google"}
                    </h3>
                    <p className="text-sm text-secondary">
                      {securityConfirmation === "link-google"
                        ? "Vas a continuar con Google para vincular este método de acceso a tu cuenta FeedGo."
                        : "Vas a quitar Google como método de acceso de esta cuenta."}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <Button
                        type="button"
                        onClick={securityConfirmation === "link-google" ? startGoogleLink : confirmUnlinkGoogle}
                        disabled={isSecurityActionPending}
                        variant="secondary"
                        className="px-3 py-2 text-xs"
                      >
                        {isSecurityActionPending ? "Procesando..." : "Confirmar"}
                      </Button>
                      <Button type="button" onClick={() => setSecurityConfirmation(null)} disabled={isSecurityActionPending} variant="secondary" className="px-3 py-2 text-xs">
                        Cancelar
                      </Button>
                    </div>
                  </section>
                )}
              </section>
            ) : (
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
                  {usuario?.email || "Usuario sin correo"}
                </p>
              </div>

              <section
                className="space-y-3 rounded-xl border border-border p-3"
                aria-labelledby="datos-personales-title"
              >
                <div>
                  <h2
                    id="datos-personales-title"
                    className="text-base font-semibold text-primary"
                  >
                    Datos personales
                  </h2>
                  <p className="mt-1 text-xs text-secondary">
                    Estos datos son privados y sólo se usan para tu cuenta.
                  </p>
                </div>

                <div className="space-y-1.5">
                  <p className="text-sm font-medium text-secondary">
                    Correo electrónico
                    {esCampoPerfilFaltante("email_verificado") && (
                      <PendingAsterisk />
                    )}
                  </p>
                  <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border bg-surface-subtle px-3 py-2 text-sm text-primary">
                    <span className="min-w-0 break-all">{usuario?.email || "Correo no disponible"}</span>
                    {esCampoPerfilFaltante("email_verificado") ? (
                      <Button
                        type="button"
                        onClick={() => iniciarRemediationPerfil("email_verificado")}
                        variant="secondary"
                        className="px-3 py-2 text-xs"
                      >
                        Verificar
                      </Button>
                    ) : (
                      <span className="text-xs text-success-text">Verificado</span>
                    )}
                  </div>
                </div>

                <FormControl
                  label={
                    <>
                      Fecha de nacimiento
                      {esCampoPerfilFaltante("fecha_nacimiento") && (
                        <PendingAsterisk />
                      )}
                    </>
                  }
                  labelFor="perfil-fecha-nacimiento"
                >
                  <Input
                    id="perfil-fecha-nacimiento"
                    type="date"
                    name="fecha_nacimiento"
                    value={perfilForm.fecha_nacimiento}
                    onChange={handlePerfilFormChange}
                    disabled={isSavingPerfil}
                    className="box-border min-w-0 max-w-full text-sm"
                  />
                </FormControl>

                <FormControl
                  label={
                    <>
                      Teléfono
                      {esCampoPerfilFaltante("telefono") && (
                        <PendingAsterisk />
                      )}
                    </>
                  }
                  labelFor="perfil-telefono"
                >
                  <Input
                    id="perfil-telefono"
                    type="tel"
                    name="telefono_e164"
                    value={perfilForm.telefono_e164}
                    onChange={handlePerfilFormChange}
                    disabled={isSavingPerfil || Boolean(usuario?.telefono_verified_at)}
                    className="text-sm"
                    placeholder="Ingresá tu teléfono"
                    autoComplete="tel"
                  />
                </FormControl>
                <p className="text-xs text-secondary" role="status">
                  {usuario?.telefono_e164 && !usuario?.telefono_verified_at
                    ? "Este teléfono todavía no está verificado."
                    : "El teléfono es un dato requerido del perfil."}
                </p>

                <FormControl
                  label={
                    <>
                      Provincia
                      {esCampoPerfilFaltante("provincia") && (
                        <PendingAsterisk />
                      )}
                    </>
                  }
                  labelFor="perfil-provincia"
                >
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

                <FormControl
                  label={
                    <>
                      Ciudad
                      {esCampoPerfilFaltante("ciudad") && (
                        <PendingAsterisk />
                      )}
                    </>
                  }
                  labelFor="perfil-ciudad"
                >
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
              </section>

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
                  onClick={volverAlMenuEdicion}
                  disabled={isSavingPerfil}
                  variant="secondary"
                  className="px-3 py-2 text-xs"
                >
                  Cancelar
                </Button>
              </div>
            </form>
            )}

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
        {!showPerfilForm && (
          <section className="mb-8">
            <div className="flex items-end justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold">Mis espacios</h2>
                <p className="mt-1 text-sm text-secondary">
                  Estos son los espacios públicos que administrás desde esta
                  cuenta.
                </p>
              </div>
            </div>

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

                      <div className="flex-1">
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

                  <Surface variant="subtle" className="rounded-xl p-3">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                      <div className="min-w-0">
                        <p className="text-xs font-semibold text-secondary">
                          Horarios de atención
                        </p>
                        <p className="mt-1 text-xs text-muted">
                          {editingComercioId
                            ? "Administrá las franjas semanales de este espacio."
                            : horariosDraftConfigurado
                              ? `${horariosDraft.length} franjas configuradas.`
                              : "Configurá las franjas semanales antes de crear el espacio."}
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

                  <div className="flex items-center gap-3 pt-2">
                    <Button
                      type="submit"
                      disabled={isCreatingComercio}
                      variant="primary"
                      className="px-4 py-2 text-sm"
                    >
                      {isCreatingComercio
                        ? "Procesando..."
                        : comercioCreadoPendienteHorarios
                        ? "Reintentar horarios"
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
                          <span className="absolute top-2 left-2 rounded-full bg-black/70 px-2 py-0.5 text-[10px] text-interactive-on-primary">
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
                              onClick={() => abrirAgendaComercio(c)}
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
                mode={editingComercioId ? "persisted" : "draft"}
                initialFranjas={horariosDraft}
                onSaveDraft={(franjas) => {
                  setHorariosDraft(franjas);
                  setHorariosDraftConfigurado(true);
                }}
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

/**
 * PerfilComercioPage.jsx
 * -----------------------
 * ETAPA 58
 * - Perfil de comercio mantiene vista tipo perfil/Instagram
 * - Publicaciones del comercio en cuadrícula
 * - Feed principal queda vertical, pero el comercio queda como galería
 */

import { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

import PublicacionCard from "../components/PublicacionCard";
import CrearHistoriaModal from "../components/CrearHistoriaModal";
import { MessageCircle, Camera, MapPin } from "lucide-react";
import { getMediaUrlFromAny } from "../utils/mediaUrl";

import {
  getComercioById,
  getHistoriasDeComercio,
  getPublicacionesDeComercio,
  crearPublicacionDeComercio,
} from "../services/comercios_service";

import {
  fetchPublicacionesGuardadas,
  toggleLikePublicacion,
  guardarPublicacion,
  quitarPublicacionGuardada,
} from "../services/feed_service";

import { useAuth } from "../context/useAuth";

export default function CommerceProfilePage() {
  const { id } = useParams();
  const comercioId = Number(id);
  const navigate = useNavigate();
  const { usuario, user } = useAuth();
  const usuarioActivo = usuario || user || null;

  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  const [comercio, setComercio] = useState(null);
  const [historias, setHistorias] = useState([]);
  const [publicaciones, setPublicaciones] = useState([]);

  const [isCrearHistoriaOpen, setIsCrearHistoriaOpen] = useState(false);
  const [isCrearPublicacionOpen, setIsCrearPublicacionOpen] = useState(false);

  const [publicacionForm, setPublicacionForm] = useState({
    titulo: "",
    descripcion: "",
    imagen_url: "",
  });

  const [imagenFile, setImagenFile] = useState(null);
  const [isCreatingPublicacion, setIsCreatingPublicacion] = useState(false);

  const [likeLocks, setLikeLocks] = useState({});
  const [saveLocks, setSaveLocks] = useState({});

  const likeLocksMemo = useMemo(() => likeLocks, [likeLocks]);
  const saveLocksMemo = useMemo(() => saveLocks, [saveLocks]);

  function setLock(setter, pubId, value) {
    setter((prev) => ({ ...prev, [pubId]: value }));
  }

  function esComercioMio(comercioData, userData) {
    if (!comercioData || !userData) return false;

    const comercioOwner =
      comercioData.owner_user_id ??
      comercioData.usuario_id ??
      comercioData.propietario_id ??
      null;

    const userId = userData.id ?? userData.user_id ?? userData.usuario_id ?? null;

    if (comercioOwner == null || userId == null) return false;

    return Number(comercioOwner) === Number(userId);
  }

  const puedoCrearHistoria = esComercioMio(comercio, usuarioActivo);
  const comercioImagenUrl = getMediaUrlFromAny(comercio);

  function getAccessToken() {
    return localStorage.getItem("access_token");
  }

  async function loadAll() {
    if (!comercioId || Number.isNaN(comercioId)) {
      setErrorMessage("ID de comercio inválido.");
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setErrorMessage("");

      const token = getAccessToken();

      const [comercioData, publicacionesData, historiasData, guardadasData] =
        await Promise.all([
          getComercioById(comercioId),
          getPublicacionesDeComercio(comercioId),
          getHistoriasDeComercio(comercioId),
          token ? fetchPublicacionesGuardadas() : Promise.resolve([]),
        ]);

      const pubs = Array.isArray(publicacionesData)
        ? publicacionesData
        : publicacionesData?.items || [];

      const hist = Array.isArray(historiasData)
        ? historiasData
        : historiasData?.items || [];

      const guardadasItems = Array.isArray(guardadasData)
        ? guardadasData
        : guardadasData?.items || [];

      const guardadasSet = new Set(
        guardadasItems
          .map((g) => g?.id ?? g?.publicacion_id)
          .filter((pid) => typeof pid === "number")
      );

      const mergedPubs = pubs.map((p) => ({
        ...p,
        guardada_by_me: Boolean(p.guardada_by_me) || guardadasSet.has(p.id),
      }));

      setComercio(comercioData);
      setHistorias(hist);
      setPublicaciones(mergedPubs);
    } catch (error) {
      setErrorMessage(
        error.message || "Error desconocido cargando perfil del comercio."
      );
      setComercio(null);
      setHistorias([]);
      setPublicaciones([]);
    } finally {
      setIsLoading(false);
    }
  }

  async function refreshHistorias() {
    if (!comercioId || Number.isNaN(comercioId)) return;

    try {
      const historiasData = await getHistoriasDeComercio(comercioId);

      const hist = Array.isArray(historiasData)
        ? historiasData
        : historiasData?.items || [];

      setHistorias(hist);
    } catch (error) {
      setErrorMessage(error.message || "Error refrescando historias.");
    }
  }

  async function refreshPublicaciones() {
    if (!comercioId || Number.isNaN(comercioId)) return;

    try {
      const token = getAccessToken();

      const [publicacionesData, guardadasData] = await Promise.all([
        getPublicacionesDeComercio(comercioId),
        token ? fetchPublicacionesGuardadas() : Promise.resolve([]),
      ]);

      const pubs = Array.isArray(publicacionesData)
        ? publicacionesData
        : publicacionesData?.items || [];

      const guardadasItems = Array.isArray(guardadasData)
        ? guardadasData
        : guardadasData?.items || [];

      const guardadasSet = new Set(
        guardadasItems
          .map((g) => g?.id ?? g?.publicacion_id)
          .filter((pid) => typeof pid === "number")
      );

      const mergedPubs = pubs.map((p) => ({
        ...p,
        guardada_by_me: Boolean(p.guardada_by_me) || guardadasSet.has(p.id),
      }));

      setPublicaciones(mergedPubs);
    } catch (error) {
      setErrorMessage(error.message || "Error refrescando publicaciones.");
    }
  }

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [comercioId]);

  function usuarioDebeLoguearse() {
  const token = localStorage.getItem("access_token");

  if (!token) {
    navigate("/login", {
      replace: false,
      state: {
        message:
          "Para poder interactuar con la app, debes iniciá sesión.",
      },
    });

    return true;
  }

  return false;
}

  async function handleToggleLike(pubId) {
    if (usuarioDebeLoguearse()) return;

    if (likeLocksMemo[pubId]) return;

    setLock(setLikeLocks, pubId, true);
    const snapshot = publicaciones;

    setPublicaciones((prev) =>
      prev.map((p) => {
        if (p.id !== pubId) return p;

        const nextLiked = !Boolean(p.liked_by_me);
        const delta = nextLiked ? 1 : -1;

        return {
          ...p,
          liked_by_me: nextLiked,
          likes_count: Math.max(0, (p.likes_count || 0) + delta),
          interacciones_count: Math.max(0, (p.interacciones_count || 0) + delta),
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

    if (usuarioDebeLoguearse()) return;

    if (saveLocksMemo[pubId]) return;

    setLock(setSaveLocks, pubId, true);
    const snapshot = publicaciones;

    const current = publicaciones.find((p) => p.id === pubId);
    const estabaGuardada = Boolean(current?.guardada_by_me);

    setPublicaciones((prev) =>
      prev.map((p) => {
        if (p.id !== pubId) return p;

        const nextSaved = !Boolean(p.guardada_by_me);
        const delta = nextSaved ? 1 : -1;

        return {
          ...p,
          guardada_by_me: nextSaved,
          guardados_count: Math.max(0, (p.guardados_count || 0) + delta),
          interacciones_count: Math.max(0, (p.interacciones_count || 0) + delta),
        };
      })
    );

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

  async function handleHistoriaCreated() {
    await refreshHistorias();
  }

  function handleChangePublicacionForm(event) {
    const { name, value } = event.target;

    setPublicacionForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  }

  function handleSelectImagenPublicacion(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setImagenFile(file);
  }

  function handleCloseCrearPublicacion() {
    setIsCrearPublicacionOpen(false);

    setPublicacionForm({
      titulo: "",
      descripcion: "",
      imagen_url: "",
    });

    setImagenFile(null);
  }

  async function handleSubmitCrearPublicacion() {
    if (!publicacionForm.titulo.trim()) {
      setErrorMessage("El título de la publicación es obligatorio.");
      return;
    }

    try {
      setIsCreatingPublicacion(true);
      setErrorMessage("");

      let imagenUrlFinal = null;

      if (imagenFile) {
        const formData = new FormData();
        formData.append("file", imagenFile);

        try {
          const response = await fetch("http://127.0.0.1:8000/media/upload", {
            method: "POST",
            headers: {
              Authorization: `Bearer ${localStorage.getItem("access_token")}`,
            },
            body: formData,
          });

          if (!response.ok) {
            throw new Error("Error al subir la imagen");
          }

          const data = await response.json();
          imagenUrlFinal = data.url;
        } catch (error) {
          setErrorMessage(error.message || "Error subiendo la imagen.");
          return;
        }
      }

      await crearPublicacionDeComercio(comercioId, {
        titulo: publicacionForm.titulo,
        descripcion: publicacionForm.descripcion,
        imagen_url: imagenUrlFinal,
        seccion_id: null,
        is_activa: true,
      });

      handleCloseCrearPublicacion();
      await refreshPublicaciones();
    } catch (error) {
      setErrorMessage(error.message || "Error al crear la publicación.");
    } finally {
      setIsCreatingPublicacion(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <main className="mx-auto max-w-5xl px-4 py-6">
        {isLoading && (
          <div className="space-y-4">
            <div className="h-40 rounded-3xl border border-gray-800 bg-gray-900 animate-pulse" />
            <div className="grid grid-cols-3 gap-2">
              <div className="aspect-square rounded-2xl border border-gray-800 bg-gray-900 animate-pulse" />
              <div className="aspect-square rounded-2xl border border-gray-800 bg-gray-900 animate-pulse" />
              <div className="aspect-square rounded-2xl border border-gray-800 bg-gray-900 animate-pulse" />
            </div>
          </div>
        )}

        {!isLoading && errorMessage && (
          <div className="rounded-2xl border border-red-900 bg-red-950/40 p-5">
            <p className="font-semibold text-red-200">Error</p>
            <p className="mt-2 text-red-100 break-words">{errorMessage}</p>
          </div>
        )}

        {!isLoading && !errorMessage && (
          <>
            <section className="relative rounded-3xl border border-gray-800 bg-gray-900 p-5 sm:p-6">
              <span className="absolute right-6 top-6 rounded-full border border-gray-700 bg-gray-950 px-3 py-1 text-xs text-gray-300">
                {comercio?.is_activo ? "Activo" : "Inactivo"}
              </span>
              <div className="flex items-start gap-4">
                <div className="h-20 w-20 shrink-0 overflow-hidden rounded-full border border-gray-700 bg-gray-950 sm:h-24 sm:w-24">
                  {comercioImagenUrl ? (
                    <img
                      src={comercioImagenUrl}
                      alt={comercio?.nombre || "Comercio"}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center text-2xl font-bold text-white">
                      {(comercio?.nombre || "C").slice(0, 1).toUpperCase()}
                    </div>
                  )}
                </div>

                <div className="min-w-0 flex-1">
                  <h1 className="truncate text-2xl font-bold text-white">
                    {comercio?.nombre ?? "Comercio"}
                  </h1>

                  {comercio?.descripcion ? (
                    <p className="mt-2 max-w-2xl text-sm leading-6 text-gray-300">
                      {comercio.descripcion}
                    </p>
                  ) : (
                    <p className="mt-2 text-sm text-gray-500">
                      Este comercio todavía no agregó descripción.
                    </p>
                  )}

                  <div className="mt-4 flex items-center justify-between">
                    
                    {/* IZQUIERDA */}
                    <div className="flex flex-wrap items-center gap-3 text-sm text-gray-300">

                      {/* PUBLICACIONES */}
                      <span className="rounded-full border border-gray-700 bg-gray-950 px-3 py-1">
                        {publicaciones.length} publicaciones
                      </span>

                      {/* SEGUIDORES */}
                      <span className="rounded-full border border-gray-700 bg-gray-950 px-3 py-1">
                        {comercio?.seguidores_count ?? 0} seguidores
                      </span>

                    </div>

                  </div>

                  {/* INFO DEL ESPACIO */}
                  <div className="mt-5 flex flex-wrap items-center gap-3 text-sm">

                    {/* WHATSAPP */}
                    {comercio?.whatsapp && (
                      <a
                        href={`https://wa.me/${String(comercio.whatsapp).replace(/\D/g, "")}?text=Hola%2C%20te%20encontré%20en%20MiPlaza%20y%20quiero%20consultarte`}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-2 rounded-full border border-gray-700 bg-gray-950 px-4 py-2 text-xs font-semibold text-green-400 hover:bg-gray-900"
                      >
                        <MessageCircle size={14} />
                        WhatsApp
                      </a>
                    )}

                    {/* INSTAGRAM */}
                    {comercio?.instagram && (
                      <a
                        href={`https://instagram.com/${String(comercio.instagram).replace("@", "")}`}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-2 rounded-full border border-gray-700 bg-gray-950 px-4 py-2 text-xs font-semibold text-pink-400 hover:bg-gray-900"
                      >
                        <Camera size={14} />
                        Instagram
                      </a>
                    )}

                    {/* MAPS */}
                    {comercio?.maps_url && (
                      <a
                        href={comercio.maps_url}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-2 rounded-full border border-gray-700 bg-gray-950 px-4 py-2 text-xs font-semibold text-blue-400 hover:bg-gray-900"
                      >
                        <MapPin size={14} />
                        Cómo llegar
                      </a>
                    )}

                  </div>
                </div>
              </div>

              {puedoCrearHistoria && (
                <div className="mt-5 flex flex-wrap gap-3">
                  <button
                    type="button"
                    className="rounded-xl bg-white px-4 py-2 text-sm font-semibold text-gray-900 hover:opacity-90"
                    onClick={() => setIsCrearHistoriaOpen(true)}
                  >
                    + Historia
                  </button>

                  <button
                    type="button"
                    className="rounded-xl bg-white px-4 py-2 text-sm font-semibold text-gray-900 hover:opacity-90"
                    onClick={() => setIsCrearPublicacionOpen(true)}
                  >
                    + Publicación
                  </button>

                  <button
                    type="button"
                     className="rounded-xl bg-white px-4 py-2 text-sm font-semibold text-gray-900 hover:opacity-90"
                  >
                    Estadísticas
                  </button>

                </div>
              )}
            </section>

            <section className="mt-6">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-base font-semibold text-white">
                  Publicaciones
                </h2>

                <span className="text-xs text-gray-500">
                  Vista en cuadrícula
                </span>
              </div>

              {publicaciones.length === 0 ? (
                <div className="rounded-2xl border border-gray-800 bg-gray-900 p-5">
                  <p className="text-gray-300">
                    Este comercio no tiene publicaciones todavía.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:gap-3">
                  {publicaciones.map((p) => (
                    <PublicacionCard
                      key={p.id}
                      pub={p}
                      headerRightBadgeText="Comercio"
                      isActingLike={Boolean(likeLocksMemo[p.id])}
                      isActingSave={Boolean(saveLocksMemo[p.id])}
                      onToggleLike={() => handleToggleLike(p.id)}
                      onToggleSave={() => handleToggleSave(p.id)}
                      compact
                    />
                  ))}
                </div>
              )}
            </section>

            <CrearHistoriaModal
              isOpen={isCrearHistoriaOpen}
              comercioId={comercioId}
              onClose={() => setIsCrearHistoriaOpen(false)}
              onCreated={handleHistoriaCreated}
            />

            {isCrearPublicacionOpen && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
                <div className="w-full max-w-lg rounded-2xl border border-gray-700 bg-gray-900 p-6">
                  <div className="mb-5">
                    <h3 className="text-lg font-semibold text-white">
                      Crear publicación
                    </h3>
                    <p className="mt-1 text-sm text-gray-400">
                      Completá los datos para publicar en este contenido.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="mb-1 block text-sm font-medium text-gray-200">
                        Título
                      </label>
                      <input
                        type="text"
                        name="titulo"
                        value={publicacionForm.titulo}
                        onChange={handleChangePublicacionForm}
                        placeholder="Ej: Promo de la semana"
                        className="w-full rounded-xl border border-gray-700 bg-gray-950 px-4 py-3 text-sm text-white outline-none placeholder:text-gray-500 focus:border-white"
                      />
                    </div>

                    <div>
                      <label className="mb-1 block text-sm font-medium text-gray-200">
                        Descripción
                      </label>
                      <textarea
                        name="descripcion"
                        value={publicacionForm.descripcion}
                        onChange={handleChangePublicacionForm}
                        placeholder="Contá de qué trata esta publicación"
                        rows={4}
                        className="w-full rounded-xl border border-gray-700 bg-gray-950 px-4 py-3 text-sm text-white outline-none placeholder:text-gray-500 focus:border-white"
                      />
                    </div>

                    <div>
                      <label className="mb-1 block text-sm font-medium text-gray-200">
                        Imagen
                      </label>
                      <input
                        type="file"
                        accept="image/*"
                        capture="environment"
                        onChange={handleSelectImagenPublicacion}
                        className="w-full rounded-xl border border-gray-700 bg-gray-950 px-4 py-3 text-sm text-white file:mr-3 file:rounded-lg file:border-0 file:bg-white file:px-3 file:py-1 file:text-sm file:font-semibold file:text-black"
                      />

                      {imagenFile ? (
                        <p className="mt-1 text-xs text-gray-400">
                          Imagen seleccionada: {imagenFile.name}
                        </p>
                      ) : null}
                    </div>
                  </div>

                  <div className="mt-6 grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      className="rounded-xl border border-gray-700 bg-gray-950 px-4 py-3 text-sm font-semibold text-white hover:bg-gray-800"
                      onClick={handleCloseCrearPublicacion}
                    >
                      Cancelar
                    </button>

                    <button
                      type="button"
                      disabled={isCreatingPublicacion}
                      className="rounded-xl bg-white px-4 py-3 text-sm font-semibold text-gray-900 hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                      onClick={handleSubmitCrearPublicacion}
                    >
                      {isCreatingPublicacion ? "Creando..." : "Crear publicación"}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
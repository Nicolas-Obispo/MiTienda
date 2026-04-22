/**
 * PerfilComercioPage.jsx
 * -----------------------
 * ETAPA 40 — Perfil de comercio (40.1 UI + 40.2 Data básica)
 * ETAPA 42 — Crear historia desde UI (solo dueño)
 */

import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import PublicacionCard from "../components/PublicacionCard";
import CrearHistoriaModal from "../components/CrearHistoriaModal";
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

  const { usuario, user } = useAuth();
  const usuarioActivo = usuario || user || null;

  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  const [comercio, setComercio] = useState(null);
  const [historias, setHistorias] = useState([]);
  const [publicaciones, setPublicaciones] = useState([]);

  // Modal crear historia (ETAPA 42)
  const [isCrearHistoriaOpen, setIsCrearHistoriaOpen] = useState(false);

  // Modal crear publicación (ETAPA 57)
  const [isCrearPublicacionOpen, setIsCrearPublicacionOpen] = useState(false);

  /*
  ====================================================
  FORMULARIO CREAR PUBLICACIÓN
  - Estado local del modal
  - En el próximo paso lo conectamos al backend real
  ====================================================
  */
  const [publicacionForm, setPublicacionForm] = useState({
    titulo: "",
    descripcion: "",
    imagen_url: "",
  });

  /*
  ====================================================
  ARCHIVO DE IMAGEN SELECCIONADO
  - Guarda la imagen real (no URL)
  ====================================================
  */
  const [imagenFile, setImagenFile] = useState(null);

  const [isCreatingPublicacion, setIsCreatingPublicacion] = useState(false);

  // Locks por publicación (like/guardar)
  const [likeLocks, setLikeLocks] = useState({});
  const [saveLocks, setSaveLocks] = useState({});

  const likeLocksMemo = useMemo(() => likeLocks, [likeLocks]);
  const saveLocksMemo = useMemo(() => saveLocks, [saveLocks]);

  function setLock(setter, pubId, value) {
    setter((prev) => ({ ...prev, [pubId]: value }));
  }

  // ✅ Determina si el comercio es “mío”
  // Intentamos campos comunes: owner_user_id / usuario_id / propietario_id
  function esComercioMio(comercioData, userData) {
    if (!comercioData || !userData) return false;

    const comercioOwner =
      comercioData.owner_user_id ??
      comercioData.usuario_id ??
      comercioData.propietario_id ??
      null;

    const userId =
      userData.id ?? userData.user_id ?? userData.usuario_id ?? null;

    if (comercioOwner == null || userId == null) return false;

    return Number(comercioOwner) === Number(userId);
  }

  const puedoCrearHistoria = esComercioMio(comercio, usuarioActivo);

  async function loadAll() {
    if (!comercioId || Number.isNaN(comercioId)) {
      setErrorMessage("ID de comercio inválido.");
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setErrorMessage("");

      const [comercioData, publicacionesData, historiasData, guardadasData] =
        await Promise.all([
          getComercioById(comercioId),
          getPublicacionesDeComercio(comercioId),
          getHistoriasDeComercio(comercioId),
          fetchPublicacionesGuardadas(),
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
          .map((g) => g?.publicacion_id)
          .filter((pid) => typeof pid === "number")
      );

      const mergedPubs = pubs.map((p) => ({
        ...p,
        guardada_by_me: guardadasSet.has(p.id),
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

    /*
  ====================================================
  REFRESH DE PUBLICACIONES
  - Se usa después de crear una publicación nueva
  - Mantiene sincronizada la UI con backend
  ====================================================
  */
  async function refreshPublicaciones() {
    if (!comercioId || Number.isNaN(comercioId)) return;

    try {
      const [publicacionesData, guardadasData] = await Promise.all([
        getPublicacionesDeComercio(comercioId),
        fetchPublicacionesGuardadas(),
      ]);

      const pubs = Array.isArray(publicacionesData)
        ? publicacionesData
        : publicacionesData?.items || [];

      const guardadasItems = Array.isArray(guardadasData)
        ? guardadasData
        : guardadasData?.items || [];

      const guardadasSet = new Set(
        guardadasItems
          .map((g) => g?.publicacion_id)
          .filter((pid) => typeof pid === "number")
      );

      const mergedPubs = pubs.map((p) => ({
        ...p,
        guardada_by_me: guardadasSet.has(p.id),
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

  async function handleToggleLike(pubId) {
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

    /*
  ====================================================
  HELPERS DEL MODAL CREAR PUBLICACIÓN
  ====================================================
  */
  function handleChangePublicacionForm(event) {
    const { name, value } = event.target;

    setPublicacionForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  }

    /*
  ====================================================
  SELECCIÓN DE IMAGEN
  - Guarda archivo en memoria
  ====================================================
  */
  function handleSelectImagenPublicacion(event) {
    const file = event.target.files?.[0];

    if (!file) return;

    setImagenFile(file);
  }

  function handleCloseCrearPublicacion() {
    /*
    -----------------------------------------------
    Cerramos modal y limpiamos formulario
    -----------------------------------------------
    */
    setIsCrearPublicacionOpen(false);

    setPublicacionForm({
      titulo: "",
      descripcion: "",
      imagen_url: "",
    });
  }

    /*
  ====================================================
  SUBMIT CREAR PUBLICACIÓN
  - Conecta el modal con el backend real
  - Usa el endpoint que ya funciona en Swagger
  ====================================================
  */
  async function handleSubmitCrearPublicacion() {
    /*
    -----------------------------------------------
    Validación mínima de frontend
    -----------------------------------------------
    */
    if (!publicacionForm.titulo.trim()) {
      setErrorMessage("El título de la publicación es obligatorio.");
      return;
    }

    try {
      setIsCreatingPublicacion(true);
      setErrorMessage("");

      /*
      ====================================================
      UPLOAD DE IMAGEN (si existe)
      ====================================================
      */
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

          // ⚠️ Validación importante
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

      /*
      -----------------------------------------------
      Crear publicación real en backend
      -----------------------------------------------
      */
      await crearPublicacionDeComercio(comercioId, {
        titulo: publicacionForm.titulo,
        descripcion: publicacionForm.descripcion,
        imagen_url: imagenUrlFinal,
        seccion_id: null,
        is_activa: true,
      });

      /*
      -----------------------------------------------
      Limpiar estado de imagen
      -----------------------------------------------
      */
      setImagenFile(null);

      /*
      -----------------------------------------------
      Cerrar modal + limpiar form
      -----------------------------------------------
      */
      handleCloseCrearPublicacion();

      /*
      -----------------------------------------------
      Refrescar publicaciones (clave)
      -----------------------------------------------
      */
      await refreshPublicaciones();

    } catch (error) {
      setErrorMessage(error.message || "Error al crear la publicación.");
    } finally {
      setIsCreatingPublicacion(false);
    }
  }
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <main className="mx-auto max-w-3xl px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-xl sm:text-2xl font-bold text-white">
            Perfil de comercio
          </h1>
          <p className="mt-1 text-sm text-gray-400">
            Comercio ID:{" "}
            <span className="text-gray-200 font-semibold">{id}</span>
          </p>
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="space-y-3">
            <div className="h-24 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
            <div className="h-28 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
            <div className="h-28 rounded-2xl border border-gray-800 bg-gray-950 animate-pulse" />
          </div>
        )}

        {/* Error */}
        {!isLoading && errorMessage && (
          <div className="rounded-2xl border border-red-900 bg-red-950/40 p-5">
            <p className="font-semibold text-red-200">Error</p>
            <p className="mt-2 text-red-100 break-words">{errorMessage}</p>
          </div>
        )}

        {/* Contenido */}
        {!isLoading && !errorMessage && (
          <>
            {/* Card Comercio */}
            <section className="rounded-2xl border border-gray-800 bg-gray-950 p-5">
              <h2 className="text-lg font-semibold text-white">
                {comercio?.nombre ?? "Comercio"}
              </h2>

              <div className="mt-2 text-sm text-gray-300 space-y-1">
                {comercio?.descripcion && (
                  <p className="text-gray-200">{comercio.descripcion}</p>
                )}

                <p className="text-gray-400">
                  Estado:{" "}
                  <span className="text-gray-200 font-semibold">
                    {comercio?.is_activo ? "Activo" : "Inactivo"}
                  </span>
                </p>

                {/* Debug suave para que veas si el backend manda owner */}
                {(comercio?.owner_user_id ??
                  comercio?.usuario_id ??
                  comercio?.propietario_id) != null ? (
                  <p className="text-xs text-gray-500">
                    Owner:{" "}
                    {String(
                      comercio?.owner_user_id ??
                        comercio?.usuario_id ??
                        comercio?.propietario_id
                    )}
                  </p>
                ) : null}
              </div>
            </section>

            {/* Historias */}
            <section className="mt-6">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-semibold text-white">Historias</h3>

                {/* ✅ Botón crear historia SOLO si es mío */}
                {puedoCrearHistoria ? (
                  <button
                    type="button"
                    className="rounded-xl bg-white px-3 py-2 text-sm font-semibold text-gray-900 hover:opacity-90"
                    onClick={() => setIsCrearHistoriaOpen(true)}
                  >
                    + Historia
                  </button>
                ) : (
                  <span className="text-xs text-white/60">
                    (Solo el dueño puede publicar historias)
                  </span>
                )}
              </div>

              {historias.length === 0 ? (
                <div className="mt-3 rounded-2xl border border-gray-800 bg-gray-950 p-5">
                  <p className="text-gray-300">No hay historias todavía.</p>
                </div>
              ) : (
                <div className="mt-3 space-y-2">
                  {historias.map((h) => (
                    <div
                      key={h.id}
                      className="rounded-2xl border border-gray-800 bg-gray-950 p-4"
                    >
                      <p className="text-sm text-gray-200 font-semibold">
                        Historia #{h.id}
                      </p>

                      {h.media_url ? (
                        <p className="mt-1 text-sm text-gray-300 break-words">
                          {h.media_url}
                        </p>
                      ) : (
                        <p className="mt-1 text-sm text-gray-500">
                          (Sin media_url)
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Publicaciones */}
            <section className="mt-6">

              {/* 
              ============================================
              HEADER PUBLICACIONES
              - Título + botón crear publicación
              - Igual lógica que historias
              ============================================
              */}
              <div className="flex items-center justify-between">
                <h3 className="text-base font-semibold text-white">
                  Publicaciones
                </h3>

                {/* Botón crear publicación SOLO si es mi comercio */}
                {puedoCrearHistoria ? (
                  <button
                    type="button"
                    className="rounded-xl bg-white px-3 py-2 text-sm font-semibold text-gray-900 hover:opacity-90"
                    onClick={() => setIsCrearPublicacionOpen(true)}
                  >
                    + Publicación
                  </button>
                ) : null}
              </div>

              {publicaciones.length === 0 ? (
                <div className="mt-3 rounded-2xl border border-gray-800 bg-gray-950 p-5">
                  <p className="text-gray-300">
                    Este comercio no tiene publicaciones todavía.
                  </p>
                </div>
              ) : (
                <div className="mt-3 space-y-4">
                  {publicaciones.map((p) => (
                    <PublicacionCard
                      key={p.id}
                      pub={p}
                      headerRightBadgeText="Comercio"
                      isActingLike={Boolean(likeLocksMemo[p.id])}
                      isActingSave={Boolean(saveLocksMemo[p.id])}
                      onToggleLike={() => handleToggleLike(p.id)}
                      onToggleSave={() => handleToggleSave(p.id)}
                    />
                  ))}
                </div>
              )}
            </section>

            {/* Modal Crear Historia */}
            <CrearHistoriaModal
              isOpen={isCrearHistoriaOpen}
              comercioId={comercioId}
              onClose={() => setIsCrearHistoriaOpen(false)}
              onCreated={handleHistoriaCreated}
            />
            {/* 
            ====================================================
            MODAL CREAR PUBLICACIÓN
            - Formulario visual real
            - Todavía NO conectado al backend
            - Próximo paso: submit real
            ====================================================
            */}
            {isCrearPublicacionOpen && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
                <div className="w-full max-w-lg rounded-2xl border border-gray-700 bg-gray-900 p-6">

                  {/* Header del modal */}
                  <div className="mb-5">
                    <h3 className="text-lg font-semibold text-white">
                      Crear publicación
                    </h3>
                    <p className="mt-1 text-sm text-gray-400">
                      Completá los datos para publicar contenido en este comercio.
                    </p>
                  </div>

                  {/* Formulario */}
                  <div className="space-y-4">

                    {/* Campo título */}
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

                    {/* Campo descripción */}
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

                    {/* Campo imagen_url */}
                    <div>
                      <label className="mb-1 block text-sm font-medium text-gray-200">
                        URL de imagen
                      </label>
                      <input
                        type="file"
                        accept="image/*"
                        capture="environment"
                        onChange={handleSelectImagenPublicacion}
                        className="w-full rounded-xl border border-gray-700 bg-gray-950 px-4 py-3 text-sm text-white file:mr-3 file:rounded-lg file:border-0 file:bg-white file:px-3 file:py-1 file:text-sm file:font-semibold file:text-black"
                      />
                      <p className="mt-1 text-xs text-gray-500">
                        En el próximo paso lo conectamos con el guardado real en backend.
                      </p>
                    </div>
                  </div>

                  {/* Footer del modal */}
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

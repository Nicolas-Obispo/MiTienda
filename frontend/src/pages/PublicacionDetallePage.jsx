import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { httpGet } from "../services/http_service";
import InteraccionButton from "../components/InteraccionButton";
import {
  toggleLikePublicacion,
  guardarPublicacion,
  quitarPublicacionGuardada,
} from "../services/feed_service";
export default function PublicacionDetallePage() {
  /*
  ====================================================
  PARAMS
  - ID de la publicación desde la URL
  ====================================================
  */
  const { id } = useParams();

  /*
  ====================================================
  ESTADOS PRINCIPALES
  ====================================================
  */
  const [isLoading, setIsLoading] = useState(true);
  const [publicacion, setPublicacion] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  /*
  ====================================================
  ESTADOS DE INTERACCIÓN
  - liked: estado visual del corazón
  - guardada: estado visual del guardado
  - locks: evita doble click mientras se procesa
  ====================================================
  */
  const [liked, setLiked] = useState(false);
  const [guardada, setGuardada] = useState(false);
  const [isActingLike, setIsActingLike] = useState(false);
  const [isActingSave, setIsActingSave] = useState(false);

  /*
  ====================================================
  HELPERS DE NORMALIZACIÓN
  ====================================================
  */
  function getNombreComercio(pub) {
    return (
      pub?.comercio_nombre ||
      pub?.nombre_comercio ||
      pub?.comercio?.nombre ||
      (typeof pub?.comercio_id === "number"
        ? `Comercio #${pub.comercio_id}`
        : "Comercio")
    );
  }

  function getMediaUrl(pub) {
    return (
      pub?.imagen_url ||
      pub?.media_url ||
      pub?.foto_url ||
      pub?.portada_url ||
      pub?.thumbnail_url ||
      ""
    );
  }

  function esVideo(url) {
    if (!url || typeof url !== "string") return false;

    return [".mp4", ".webm", ".ogg", ".mov"].some((ext) =>
      url.toLowerCase().includes(ext)
    );
  }

  /*
  ====================================================
  CARGA DE DETALLE
  - IMPORTANTE: acá sí mandamos token para que backend
    devuelva liked_by_me y guardada_by_me reales
  ====================================================
  */
  async function loadPublicacion() {
    try {
      setIsLoading(true);
      setErrorMessage("");

      const token = localStorage.getItem("access_token");
      const data = await httpGet(`/publicaciones/${id}`, token);

      setPublicacion(data);

      /*
      -----------------------------------------------
      Sincronizamos estado visual inicial desde backend
      -----------------------------------------------
      */
      setLiked(Boolean(data?.liked_by_me));
      setGuardada(Boolean(data?.guardada_by_me));
    } catch (error) {
      setPublicacion(null);
      setErrorMessage(
        error?.message || "Error desconocido cargando la publicación."
      );
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadPublicacion();
  }, [id]);

  /*
  ====================================================
  TOGGLE LIKE
  - Reutiliza el mismo service real que ya funciona
    en feed/ranking/perfil
  ====================================================
  */
  async function handleToggleLike() {
    if (isActingLike || !publicacion) return;

    setIsActingLike(true);
    const snapshot = publicacion;
    const snapshotLiked = liked;

    /*
    -----------------------------------------------
    Optimistic UI
    -----------------------------------------------
    */
    const nextLiked = !liked;
    const delta = nextLiked ? 1 : -1;

    setLiked(nextLiked);
    setPublicacion((prev) => ({
      ...prev,
      liked_by_me: nextLiked,
      likes_count: Math.max(0, (prev?.likes_count || 0) + delta),
      interacciones_count: Math.max(
        0,
        (prev?.interacciones_count || 0) + delta
      ),
    }));

    try {
      await toggleLikePublicacion(Number(id));
    } catch (error) {
      /*
      -----------------------------------------------
      Rollback si falla
      -----------------------------------------------
      */
      setLiked(snapshotLiked);
      setPublicacion(snapshot);
      setErrorMessage(error?.message || "Error al dar like.");
    } finally {
      setIsActingLike(false);
    }
  }

  /*
  ====================================================
  TOGGLE GUARDAR
  - Reutiliza services reales existentes
  ====================================================
  */
  async function handleToggleGuardar() {
    if (isActingSave || !publicacion) return;

    setIsActingSave(true);
    const snapshot = publicacion;
    const snapshotGuardada = guardada;

    /*
    -----------------------------------------------
    Optimistic UI
    -----------------------------------------------
    */
    const nextGuardada = !guardada;
    const delta = nextGuardada ? 1 : -1;

    setGuardada(nextGuardada);
    setPublicacion((prev) => ({
      ...prev,
      guardada_by_me: nextGuardada,
      guardados_count: Math.max(0, (prev?.guardados_count || 0) + delta),
      interacciones_count: Math.max(
        0,
        (prev?.interacciones_count || 0) + delta
      ),
    }));

    try {
      if (guardada) {
        await quitarPublicacionGuardada(Number(id));
      } else {
        await guardarPublicacion(Number(id));
      }
    } catch (error) {
      /*
      -----------------------------------------------
      Rollback si falla
      -----------------------------------------------
      */
      setGuardada(snapshotGuardada);
      setPublicacion(snapshot);
      setErrorMessage(error?.message || "Error al guardar.");
    } finally {
      setIsActingSave(false);
    }
  }

  /*
  ====================================================
  DATOS DERIVADOS
  ====================================================
  */
  const mediaUrl = getMediaUrl(publicacion);
  const mediaEsVideo = esVideo(mediaUrl);
  const nombreComercio = getNombreComercio(publicacion);
  const comercioId =
    typeof publicacion?.comercio_id === "number" ? publicacion.comercio_id : null;

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <main className="mx-auto max-w-3xl px-4 py-6">
        {/* ========================= LOADING ========================= */}
        {isLoading && (
          <div className="space-y-3">
            <div className="h-10 animate-pulse rounded-xl border border-gray-800 bg-gray-950" />
            <div className="aspect-square animate-pulse rounded-2xl border border-gray-800 bg-gray-950" />
            <div className="h-20 animate-pulse rounded-2xl border border-gray-800 bg-gray-950" />
          </div>
        )}

        {/* ========================= ERROR ========================= */}
        {!isLoading && errorMessage && (
          <div className="rounded-2xl border border-red-900 bg-red-950/40 p-5">
            <p className="font-semibold text-red-200">Error</p>
            <p className="mt-2 break-words text-red-100">{errorMessage}</p>
          </div>
        )}

        {/* ========================= CONTENIDO ========================= */}
        {!isLoading && !errorMessage && publicacion && (
          <article className="overflow-hidden rounded-2xl border border-gray-800 bg-gray-950">
            {/* ================= HEADER ================= */}
            <header className="flex items-center justify-between p-4">
              {/* IZQUIERDA: nombre comercio */}
              <p className="text-lg font-semibold text-white">
                {nombreComercio}
              </p>

              {/* DERECHA: botón comercio */}
              {comercioId && (
                <Link
                  to={`/comercios/${comercioId}`}
                  className="rounded-full border border-gray-700 px-3 py-1 text-xs text-white hover:bg-gray-800"
                >
                  Ver comercio
                </Link>
              )}
            </header>

            {/* ================= MEDIA ================= */}
            <div className="bg-black">
              {mediaUrl ? (
                mediaEsVideo ? (
                  <video
                    src={mediaUrl}
                    controls
                    playsInline
                    className="w-full max-h-[80vh] object-cover"
                  />
                ) : (
                  <img
                    src={mediaUrl}
                    alt={publicacion?.titulo || nombreComercio}
                    className="w-full max-h-[80vh] object-cover"
                  />
                )
              ) : (
                <div className="flex aspect-square items-center justify-center text-gray-500">
                  Sin imagen
                </div>
              )}
            </div>

            {/* ================= INFO ================= */}
            <div className="space-y-4 p-4">
              {/* TÍTULO PROTAGONISTA */}
              {publicacion?.titulo && (
                <h2 className="text-xl font-bold text-white">
                  {publicacion.titulo}
                </h2>
              )}

              {/* DESCRIPCIÓN */}
              {publicacion?.descripcion && (
                <p className="text-gray-300">{publicacion.descripcion}</p>
              )}

              {/* ACCIONES */}
              <div className="flex gap-3">

                <InteraccionButton
                  type="like"
                  active={liked}
                  onClick={handleToggleLike}
                  disabled={isActingLike}
                  label={liked ? "Te gusta" : "Me gusta"}
                />

                <InteraccionButton
                  type="guardar"
                  active={guardada}
                  onClick={handleToggleGuardar}
                  disabled={isActingSave}
                  label={guardada ? "Guardada" : "Guardar"}
                />

              </div>

              {/* MÉTRICAS */}
              <div className="flex gap-4 text-sm text-gray-400">
                <span>❤️ {publicacion?.likes_count ?? 0}</span>
                <span>⭐ {publicacion?.guardados_count ?? 0}</span>
                <span>🔥 {publicacion?.interacciones_count ?? 0}</span>
              </div>
            </div>
          </article>
        )}
      </main>
    </div>
  );
}
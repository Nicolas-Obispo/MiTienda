import { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { httpGet } from "@core";
import { InteraccionButton } from "@shared";
import { useAuth } from "@features/auth";
import { getMediaUrlFromAny } from "@shared";
import {
  toggleLikePublicacion,
  guardarPublicacion,
  quitarPublicacionGuardada,
} from "@features/posts";

export default function PublicacionDetallePage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const { usuario, user } = useAuth();
  const usuarioActivo = usuario || user || null;

  const [isLoading, setIsLoading] = useState(true);
  const [publicacion, setPublicacion] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  const [liked, setLiked] = useState(false);
  const [guardada, setGuardada] = useState(false);
  const [isActingLike, setIsActingLike] = useState(false);
  const [isActingSave, setIsActingSave] = useState(false);
  const [esDuenoComercio, setEsDuenoComercio] = useState(false);

  const [mostrarConfirmacionEliminar, setMostrarConfirmacionEliminar] =
    useState(false);
  const [isDeletingPublicacion, setIsDeletingPublicacion] = useState(false);

  function usuarioDebeLoguearse() {
    const token = localStorage.getItem("access_token");

    if (!token) {
      navigate("/login", {
        state: {
          message: "Para poder interactuar con la app, debes iniciar sesión.",
        },
      });

      return true;
    }

    return false;
  }

  function getNombreComercio(pub) {
    return (
      pub?.comercio_nombre ||
      pub?.nombre_comercio ||
      pub?.comercio?.nombre ||
      pub?.comercio?.nombre_comercio ||
      pub?.comercio?.razon_social ||
      "Comercio"
    );
  }

  function esPublicacionMia(pub, userData) {
    if (!pub || !userData) return false;

    const owner =
      pub.owner_user_id ??
      pub.usuario_id ??
      pub.user_id ??
      null;

    const userId =
      userData.id ??
      userData.user_id ??
      userData.usuario_id ??
      null;

    if (owner == null || userId == null) return false;

    return Number(owner) === Number(userId);
  }

  function getMediaUrl(pub) {
    return getMediaUrlFromAny(pub);
  }

  function esVideo(url) {
    if (!url || typeof url !== "string") return false;

    return [".mp4", ".webm", ".ogg", ".mov"].some((ext) =>
      url.toLowerCase().includes(ext)
    );
  }

  async function loadPublicacion() {
    try {
      setIsLoading(true);
      setErrorMessage("");

      const token = localStorage.getItem("access_token");
      const data = await httpGet(`/publicaciones/${id}`, token);

      // 🔥 NUEVO: verificar si el comercio es mío
      if (data?.comercio_id && usuarioActivo) {
        try {
          const comercioData = await httpGet(
            `/comercios/${data.comercio_id}`,
            token
          );

          const owner =
            comercioData.owner_user_id ??
            comercioData.usuario_id ??
            comercioData.propietario_id ??
            null;

          const userId =
            usuarioActivo.id ??
            usuarioActivo.user_id ??
            usuarioActivo.usuario_id ??
            null;

          setEsDuenoComercio(
            owner != null && userId != null && Number(owner) === Number(userId)
          );
        } catch {
          setEsDuenoComercio(false);
        }
      }

      console.log("DATA PUBLICACION DETALLE:", data);

      setPublicacion(data);
      setLiked(Boolean(data?.liked_by_me));
      setGuardada(Boolean(data?.guardada_by_me));
    } catch (error) {
      setPublicacion(null);

      const mensaje = error?.message || "";

      const publicacionNoDisponible =
        mensaje.includes("404") ||
        mensaje.toLowerCase().includes("not found") ||
        mensaje.toLowerCase().includes("no encontrada") ||
        mensaje.toLowerCase().includes("no existe");

      if (publicacionNoDisponible) {
        setErrorMessage(
          "Lo siento, esta publicación ya no está disponible..."
        );
      } else {
        setErrorMessage(mensaje || "Error cargando la publicación.");
      }
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadPublicacion();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleToggleLike() {
    if (usuarioDebeLoguearse()) return;
    if (isActingLike || !publicacion) return;

    setIsActingLike(true);

    const snapshot = publicacion;
    const snapshotLiked = liked;

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
      setLiked(snapshotLiked);
      setPublicacion(snapshot);
      setErrorMessage(error?.message || "Error al dar like.");
    } finally {
      setIsActingLike(false);
    }
  }

  async function handleToggleGuardar() {
    if (usuarioDebeLoguearse()) return;
    if (isActingSave || !publicacion) return;

    setIsActingSave(true);

    const snapshot = publicacion;
    const snapshotGuardada = guardada;

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
      setGuardada(snapshotGuardada);
      setPublicacion(snapshot);
      setErrorMessage(error?.message || "Error al guardar.");
    } finally {
      setIsActingSave(false);
    }
  }

  function handleEliminarPublicacion() {
    if (!publicacion) return;

    setMostrarConfirmacionEliminar(true);
  }

  function handleCancelarEliminarPublicacion() {
    if (isDeletingPublicacion) return;

    setMostrarConfirmacionEliminar(false);
  }

  async function handleConfirmarEliminarPublicacion() {
    if (!publicacion || isDeletingPublicacion) return;

    try {
      setIsDeletingPublicacion(true);

      const token = localStorage.getItem("access_token");

      const response = await fetch(
        `http://127.0.0.1:8000/publicaciones/${publicacion.id}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Error al eliminar la publicación");
      }

      if (comercioId) {
        navigate(`/comercios/${comercioId}`, { replace: true });
      } else {
        navigate("/feed", { replace: true });
      }
    } catch (error) {
      setErrorMessage(error.message || "Error eliminando la publicación.");
      setMostrarConfirmacionEliminar(false);
    } finally {
      setIsDeletingPublicacion(false);
    }
  }

  const mediaUrl = getMediaUrl(publicacion);
  const mediaEsVideo = esVideo(mediaUrl);
  const nombreComercio = getNombreComercio(publicacion);
  const comercioId =
    typeof publicacion?.comercio_id === "number"
      ? publicacion.comercio_id
      : null;

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <main className="mx-auto max-w-3xl px-4 py-6">
        {isLoading && (
          <div className="space-y-3">
            <div className="h-10 animate-pulse rounded-xl border border-gray-800 bg-gray-950" />
            <div className="aspect-square animate-pulse rounded-2xl border border-gray-800 bg-gray-950" />
            <div className="h-20 animate-pulse rounded-2xl border border-gray-800 bg-gray-950" />
          </div>
        )}

        {!isLoading && errorMessage && (
          <div className="rounded-2xl border border-gray-800 bg-gray-950 p-8 text-center">
            <div className="flex flex-col items-center justify-center gap-3">
              <span className="text-4xl">😅</span>

              <p className="text-sm text-gray-300 break-words">
                {errorMessage}
              </p>
            </div>
          </div>
        )}

        {!isLoading && !errorMessage && publicacion && (
          <article className="overflow-hidden rounded-2xl border border-gray-800 bg-gray-950">
            <header className="flex items-center justify-between gap-3 p-4">
              <p className="truncate text-lg font-semibold text-white">
                {nombreComercio}
              </p>

              {comercioId && (
                <Link
                  to={`/comercios/${comercioId}`}
                  className="shrink-0 rounded-full border border-gray-700 px-3 py-1 text-xs font-semibold text-white hover:bg-gray-800"
                >
                  Ver perfil
                </Link>
              )}
            </header>

            <div className="bg-black">
              {mediaUrl ? (
                mediaEsVideo ? (
                  <video
                    key={mediaUrl}
                    src={mediaUrl}
                    autoPlay
                    muted
                    loop
                    playsInline
                    controls
                    className="max-h-[80vh] w-full object-contain"
                  />
                ) : (
                  <img
                    src={mediaUrl}
                    alt={publicacion?.titulo || nombreComercio}
                    className="max-h-[80vh] w-full object-contain"
                  />
                )
              ) : (
                <div className="flex aspect-square items-center justify-center text-gray-500">
                  Sin imagen
                </div>
              )}
            </div>

            <div className="space-y-4 p-4">
              {publicacion?.titulo && (
                <h2 className="text-xl font-bold text-white">
                  {publicacion.titulo}
                </h2>
              )}

              {publicacion?.descripcion && (
                <p className="text-gray-300">{publicacion.descripcion}</p>
              )}

              <div className="flex flex-wrap gap-3">
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

              <div className="flex items-center justify-between text-sm text-gray-400">
                <div className="flex flex-wrap gap-4">
                  <span>❤️ {publicacion?.likes_count ?? 0}</span>
                  <span>⭐ {publicacion?.guardados_count ?? 0}</span>
                  <span>🔥 {publicacion?.interacciones_count ?? 0}</span>
                </div>

                {esDuenoComercio && (
                  <button
                    type="button"
                    onClick={handleEliminarPublicacion}
                    className="rounded-full border border-white-800 bg-950/40 px-3 py-1 text-xs font-semibold text-r-300 hover:bg-red-900/40"
                    title="Eliminar publicación"
                  >
                    🗑️
                  </button>
                )}
              </div>
            </div>
          </article>
        )}
      </main>

      {mostrarConfirmacionEliminar && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
          <div className="w-full max-w-sm rounded-2xl border border-gray-800 bg-gray-950 p-5 shadow-xl">
            <p className="text-lg font-semibold text-white">
              Eliminar publicación
            </p>

            <p className="mt-2 text-sm text-gray-300">
              ¿Seguro que querés eliminar esta publicación?
            </p>

            <div className="mt-5 flex justify-end gap-3">
              <button
                type="button"
                onClick={handleCancelarEliminarPublicacion}
                disabled={isDeletingPublicacion}
                className="rounded-full border border-gray-700 px-4 py-2 text-sm font-semibold text-white hover:bg-gray-800 disabled:opacity-60"
              >
                Cancelar
              </button>

              <button
                type="button"
                onClick={handleConfirmarEliminarPublicacion}
                disabled={isDeletingPublicacion}
                className="rounded-full border border-red-800 bg-red-950/40 px-4 py-2 text-sm font-semibold text-red-200 hover:bg-red-900/40 disabled:opacity-60"
              >
                {isDeletingPublicacion ? "Eliminando..." : "Eliminar"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

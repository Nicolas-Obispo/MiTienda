import { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { httpGet } from "../services/http_service";
import InteraccionButton from "../components/InteraccionButton";
import {
  toggleLikePublicacion,
  guardarPublicacion,
  quitarPublicacionGuardada,
} from "../services/feed_service";

export default function PublicacionDetallePage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [isLoading, setIsLoading] = useState(true);
  const [publicacion, setPublicacion] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  const [liked, setLiked] = useState(false);
  const [guardada, setGuardada] = useState(false);
  const [isActingLike, setIsActingLike] = useState(false);
  const [isActingSave, setIsActingSave] = useState(false);

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

  function getMediaUrl(pub) {
    return (
      pub?.imagen_url ||
      pub?.media_url ||
      pub?.foto_url ||
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

  async function loadPublicacion() {
    try {
      setIsLoading(true);
      setErrorMessage("");

      const token = localStorage.getItem("access_token");
      const data = await httpGet(`/publicaciones/${id}`, token);

      console.log("DATA PUBLICACION DETALLE:", data);

      setPublicacion(data);
      setLiked(Boolean(data?.liked_by_me));
      setGuardada(Boolean(data?.guardada_by_me));
    } catch (error) {
      setPublicacion(null);
      setErrorMessage(error?.message || "Error cargando la publicación.");
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
          <div className="rounded-2xl border border-red-900 bg-red-950/40 p-5">
            <p className="font-semibold text-red-200">Error</p>
            <p className="mt-2 break-words text-red-100">{errorMessage}</p>
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
                    src={mediaUrl}
                    controls
                    playsInline
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

              <div className="flex flex-wrap gap-4 text-sm text-gray-400">
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
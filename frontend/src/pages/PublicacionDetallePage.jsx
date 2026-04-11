import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { httpGet } from "../services/http_service";

export default function PublicacionDetallePage() {
  const { id } = useParams();

  const [isLoading, setIsLoading] = useState(true);
  const [publicacion, setPublicacion] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

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

  async function loadPublicacion() {
    try {
      setIsLoading(true);
      setErrorMessage("");

      const data = await httpGet(`/publicaciones/${id}`);
      setPublicacion(data);
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const mediaUrl = getMediaUrl(publicacion);
  const mediaEsVideo = esVideo(mediaUrl);
  const nombreComercio = getNombreComercio(publicacion);
  const comercioId =
    typeof publicacion?.comercio_id === "number" ? publicacion.comercio_id : null;

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <main className="mx-auto max-w-3xl px-4 py-6">
        {isLoading && (
          <div className="space-y-3">
            <div className="h-10 w-40 rounded-xl bg-gray-950 border border-gray-800 animate-pulse" />
            <div className="aspect-square rounded-2xl bg-gray-950 border border-gray-800 animate-pulse" />
            <div className="h-20 rounded-2xl bg-gray-950 border border-gray-800 animate-pulse" />
          </div>
        )}

        {!isLoading && errorMessage && (
          <div className="rounded-2xl border border-red-900 bg-red-950/40 p-5">
            <p className="font-semibold text-red-200">Error</p>
            <p className="mt-2 text-red-100 break-words">{errorMessage}</p>
          </div>
        )}

        {!isLoading && !errorMessage && publicacion && (
          <article className="overflow-hidden rounded-2xl border border-gray-800 bg-gray-950">
            <header className="flex items-center justify-between gap-3 p-4">
              <div className="min-w-0">
                <p className="text-lg font-semibold text-white truncate">
                  {nombreComercio}
                </p>

                <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-gray-400">
                  {comercioId ? (
                    <Link
                      to={`/comercios/${comercioId}`}
                      className="inline-flex items-center rounded-md border border-gray-800 bg-gray-900 px-2 py-0.5 text-gray-300 hover:bg-gray-800 hover:text-white"
                    >
                      Ver comercio
                    </Link>
                  ) : null}

                  {publicacion?.titulo ? (
                    <span className="truncate text-gray-500">
                      {publicacion.titulo}
                    </span>
                  ) : null}
                </div>
              </div>
            </header>

            <div className="border-y border-gray-800 bg-black">
              {mediaUrl ? (
                mediaEsVideo ? (
                  <video
                    src={mediaUrl}
                    controls
                    playsInline
                    className="h-auto max-h-[80vh] w-full object-cover"
                  />
                ) : (
                  <img
                    src={mediaUrl}
                    alt={publicacion?.titulo || nombreComercio}
                    className="h-auto max-h-[80vh] w-full object-cover"
                  />
                )
              ) : (
                <div className="flex aspect-square w-full items-center justify-center bg-gray-900 text-sm text-gray-500">
                  Sin imagen
                </div>
              )}
            </div>

            <div className="p-4">
              {publicacion?.descripcion ? (
                <p className="text-sm sm:text-base text-gray-200 leading-relaxed">
                  {publicacion.descripcion}
                </p>
              ) : (
                <p className="text-sm italic text-gray-500">Sin descripción.</p>
              )}

              <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-gray-300">
                <span>👍 {publicacion?.likes_count ?? 0}</span>
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
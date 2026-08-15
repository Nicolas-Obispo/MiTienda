import { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import {
  Alert,
  Button,
  InteraccionButton,
  Skeleton,
  Surface,
  getMediaUrlFromAny,
} from "@shared";
import { usePublicacionDetalle } from "@features/posts";
import {
  useToggleGuardadoPublicacionMutation,
  useToggleLikePublicacionMutation,
} from "@features/social";
import { httpDelete } from "@core/services/http_service";
import { ActiveLayer } from "@core";
import DenunciaModal from "@features/moderation/components/DenunciaModal";
import { RECURSO_DENUNCIA_PUBLICACION } from "@features/moderation/constants/denuncias";

export default function PublicacionDetallePage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const {
    data: publicacionQuery,
    isLoading,
    error: publicacionError,
  } = usePublicacionDetalle(id);

  const likeMutation = useToggleLikePublicacionMutation();
  const guardadoMutation = useToggleGuardadoPublicacionMutation();

  const [publicacion, setPublicacion] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  const [liked, setLiked] = useState(false);
  const [guardada, setGuardada] = useState(false);
  const [isActingLike, setIsActingLike] = useState(false);
  const [isActingSave, setIsActingSave] = useState(false);
  const [esDuenoComercio] = useState(false);

  const [mostrarConfirmacionEliminar, setMostrarConfirmacionEliminar] =
    useState(false);
  const [isDeletingPublicacion, setIsDeletingPublicacion] = useState(false);
  const [isDenunciaOpen, setIsDenunciaOpen] = useState(false);

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
    return getMediaUrlFromAny(pub);
  }

  function esVideo(url) {
    if (!url || typeof url !== "string") return false;

    return [".mp4", ".webm", ".ogg", ".mov"].some((ext) =>
      url.toLowerCase().includes(ext)
    );
  }

  useEffect(() => {
    if (!publicacionQuery) return;

    setPublicacion(publicacionQuery);
    setLiked(Boolean(publicacionQuery?.liked_by_me));
    setGuardada(Boolean(publicacionQuery?.guardada_by_me));
    setErrorMessage("");
  }, [publicacionQuery]);

  useEffect(() => {
    if (!publicacionError) return;

    const mensaje = publicacionError?.message || "";

    const publicacionNoDisponible =
      mensaje.includes("404") ||
      mensaje.toLowerCase().includes("not found") ||
      mensaje.toLowerCase().includes("no encontrada") ||
      mensaje.toLowerCase().includes("no existe");

    if (publicacionNoDisponible) {
      setErrorMessage("Lo siento, esta publicación ya no está disponible...");
    } else {
      setErrorMessage(mensaje || "Error cargando la publicación.");
    }
  }, [publicacionError]);

  async function handleToggleLike() {
    if (usuarioDebeLoguearse()) return;
    if (isActingLike || !publicacion) return;

    setIsActingLike(true);

    const snapshotLiked = liked;

    setLiked((prev) => !prev);

    try {
      await likeMutation.mutateAsync(Number(id));
    } catch (error) {
      setLiked(snapshotLiked);
      setErrorMessage(error?.message || "Error al dar like.");
    } finally {
      setIsActingLike(false);
    }
  }

  async function handleToggleGuardar() {
    if (usuarioDebeLoguearse()) return;
    if (isActingSave || !publicacion) return;

    setIsActingSave(true);

    const snapshotGuardada = guardada;

    setGuardada((prev) => !prev);

    try {
      await guardadoMutation.mutateAsync({
        publicacionId: Number(id),
        estabaGuardada: snapshotGuardada,
      });
    } catch (error) {
      setGuardada(snapshotGuardada);
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

      await httpDelete(`/publicaciones/${publicacion.id}`, token);

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

  const publicacionVisible = publicacionQuery ?? publicacion;

  const mediaUrl = getMediaUrl(publicacionVisible);
  const mediaEsVideo = esVideo(mediaUrl);
  const nombreComercio = getNombreComercio(publicacionVisible);
  const comercioId =
    typeof publicacionVisible?.comercio_id === "number"
      ? publicacionVisible.comercio_id
      : null;

  return (
    <div className="min-h-screen bg-canvas text-primary">
      <main className="mx-auto max-w-3xl px-4 py-6">
        {isLoading && !publicacionVisible && (
          <div className="space-y-3">
            <Skeleton className="h-10 rounded-xl" />
            <Skeleton className="aspect-square rounded-2xl" />
            <Skeleton className="h-20 rounded-2xl" />
          </div>
        )}

        {errorMessage && !publicacionVisible && (
          <Alert variant="danger" role="alert" className="p-8 text-center">
            <div className="flex flex-col items-center justify-center gap-3">
              <span className="text-4xl">😅</span>

              <p className="break-words text-sm">
                {errorMessage}
              </p>
            </div>
          </Alert>
        )}

        {publicacionVisible && (
          <Surface as="article" className="overflow-hidden">
            <header className="flex items-center justify-between gap-3 p-4">
              <p className="truncate text-lg font-semibold text-primary">
                {nombreComercio}
              </p>

              {comercioId && (
                <Link
                  to={`/comercios/${comercioId}`}
                  className="interactive-bubble interactive-bubble--secondary shrink-0 text-xs font-semibold"
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
                    alt={publicacionVisible?.titulo || nombreComercio}
                    className="max-h-[80vh] w-full object-contain"
                  />
                )
              ) : (
                <div className="flex aspect-square items-center justify-center bg-surface-subtle text-muted">
                  Sin imagen
                </div>
              )}
            </div>

            <div className="space-y-4 p-4">
              {publicacionVisible?.titulo && (
                <h2 className="text-xl font-bold text-primary">
                  {publicacionVisible.titulo}
                </h2>
              )}

              {publicacionVisible?.descripcion && (
                <p className="text-secondary">
                  {publicacionVisible.descripcion}
                </p>
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

                <Button
                  type="button"
                  onClick={() => setIsDenunciaOpen(true)}
                  variant="secondary"
                  className="text-sm"
                >
                  Denunciar
                </Button>
              </div>

              <div className="flex items-center justify-between text-sm text-muted">
                <div className="flex flex-wrap gap-4">
                  <span>❤️ {publicacionVisible?.likes_count ?? 0}</span>
                  <span>⭐ {publicacionVisible?.guardados_count ?? 0}</span>
                  <span>
                    🔥 {publicacionVisible?.interacciones_count ?? 0}
                  </span>
                </div>

                {esDuenoComercio && (
                  <Button
                    type="button"
                    onClick={handleEliminarPublicacion}
                    variant="danger"
                    className="px-3 py-1 text-xs"
                    aria-label="Eliminar publicacion"
                    title="Eliminar publicación"
                  >
                    🗑️
                  </Button>
                )}
              </div>
            </div>
          </Surface>
        )}
      </main>

      {mostrarConfirmacionEliminar && (
        <ActiveLayer
          onClose={handleCancelarEliminarPublicacion}
          closeOnBackdrop={!isDeletingPublicacion}
          closeOnEscape={!isDeletingPublicacion}
          labelledBy="eliminar-publicacion-title"
          contentClassName="mx-4 w-full max-w-sm"
        >
          <Surface variant="elevated" className="p-5">
            <p
              id="eliminar-publicacion-title"
              className="text-lg font-semibold text-primary"
            >
              Eliminar publicación
            </p>

            <p className="mt-2 text-sm text-secondary">
              ¿Seguro que querés eliminar esta publicación?
            </p>

            <div className="mt-5 flex justify-end gap-3">
              <Button
                type="button"
                onClick={handleCancelarEliminarPublicacion}
                disabled={isDeletingPublicacion}
                variant="secondary"
                className="px-4 py-2 text-sm"
              >
                Cancelar
              </Button>

              <Button
                type="button"
                onClick={handleConfirmarEliminarPublicacion}
                disabled={isDeletingPublicacion}
                variant="danger"
                className="px-4 py-2 text-sm"
              >
                {isDeletingPublicacion ? "Eliminando..." : "Eliminar"}
              </Button>
            </div>
          </Surface>
        </ActiveLayer>
      )}

      <DenunciaModal
        isOpen={isDenunciaOpen}
        onClose={() => setIsDenunciaOpen(false)}
        recursoTipo={RECURSO_DENUNCIA_PUBLICACION}
        recursoId={publicacionVisible?.id}
        titulo="Denunciar publicacion"
      />
    </div>
  );
}

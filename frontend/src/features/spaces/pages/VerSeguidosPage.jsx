import { useState } from "react";
import { Link } from "react-router-dom";
import { usePublicacionesGuardadas } from "@features/posts";
import { useMisEspaciosSeguidos } from "@features/spaces";
import {
  Alert,
  Button,
  GeographicContextControls,
  Surface,
  getMediaUrlFromAny,
  useGeographicContext,
} from "@shared";

export default function VerSeguidosPage() {
  const [vistaActiva, setVistaActiva] = useState("espacios");

  const { queryContext } = useGeographicContext();

  const {
    data: espaciosData = [],
    isLoading: cargando,
    isFetching: fetchingEspacios,
    error: espaciosError,
  } = useMisEspaciosSeguidos({
    lat: queryContext?.lat ?? null,
    lng: queryContext?.lng ?? null,
    positionRevision: queryContext?.positionRevision ?? 0,
    enabled: vistaActiva === "espacios",
  });

  const espacios = Array.isArray(espaciosData) ? espaciosData : [];
  const espaciosErrorMessage = espaciosError
    ? espaciosError.message || "Error desconocido cargando espacios seguidos."
    : "";

  const {
    data: publicacionesGuardadasData = [],
    isLoading: cargandoGuardadas,
    error: guardadasError,
  } = usePublicacionesGuardadas({
    enabled: vistaActiva === "guardadas",
  });

  const publicacionesGuardadas = Array.isArray(publicacionesGuardadasData)
    ? publicacionesGuardadasData
    : [];

  const guardadasErrorMessage = guardadasError
    ? guardadasError.message || "Error desconocido cargando publicaciones guardadas."
    : "";

  return (
    <div className="space-y-4 bg-canvas text-primary">
      <h1 className="text-xl font-semibold text-primary">Seguidos</h1>

      <div className="flex flex-wrap gap-2">
        <Button
          variant="secondary"
          aria-pressed={vistaActiva === "espacios"}
          onClick={() => setVistaActiva("espacios")}
          className={[
            "rounded-xl border px-3 py-2 text-xs font-semibold",
            vistaActiva === "espacios"
              ? "border-selected-border bg-selected-surface text-selected-text"
              : "border-border bg-surface-subtle text-secondary hover:bg-surface",
          ].join(" ")}
        >
          Espacios seguidos
        </Button>

        <Button
          variant="secondary"
          aria-pressed={vistaActiva === "guardadas"}
          onClick={() => setVistaActiva("guardadas")}
          className={[
            "rounded-xl border px-3 py-2 text-xs font-semibold",
            vistaActiva === "guardadas"
              ? "border-selected-border bg-selected-surface text-selected-text"
              : "border-border bg-surface-subtle text-secondary hover:bg-surface",
          ].join(" ")}
        >
          Publicaciones guardadas
        </Button>
      </div>

      {vistaActiva === "espacios" && <GeographicContextControls />}

      {vistaActiva === "espacios" && cargando && espacios.length === 0 && (
        <p className="text-center text-muted">Cargando...</p>
      )}

      {vistaActiva === "espacios" &&
        espaciosErrorMessage &&
        espacios.length === 0 && (
          <Alert variant="danger" role="alert" className="p-5">
            <p className="font-semibold">Error</p>
            <p className="mt-2 break-words">
              {espaciosErrorMessage}
            </p>
          </Alert>
        )}

      {vistaActiva === "espacios" &&
        !cargando &&
        !fetchingEspacios &&
        !espaciosErrorMessage &&
        espacios.length === 0 && (
        <p className="text-muted">Todavia no seguis ningun espacio.</p>
      )}

      {vistaActiva === "espacios" &&
        espacios.map((c) => {
          const imagenUrl = getMediaUrlFromAny(c);

          return (
            <Surface
              as={Link}
              to={`/comercios/${c.id}`}
              key={c.id}
              className="flex items-center gap-4 rounded-xl p-3 transition-colors hover:bg-surface-subtle"
            >
              <div className="h-16 w-16 shrink-0 overflow-hidden rounded-lg bg-surface-subtle">
                {imagenUrl ? (
                  <img
                    src={imagenUrl}
                    alt={c.nombre}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center text-xs text-muted">
                    Sin imagen
                  </div>
                )}
              </div>

              <div className="min-w-0 flex-1">
                <h2 className="break-words text-sm font-semibold text-primary">
                  {c.nombre}
                </h2>
                <p className="text-xs text-secondary line-clamp-2">
                  {c.descripcion || "Sin descripcion"}
                </p>
                {c.ciudad && <p className="break-words text-xs text-muted">{c.ciudad}</p>}
                {typeof c.distancia_km === "number" && (
                  <p className="mt-1 text-xs text-interactive-primary">
                    Estas a{" "}
                    {c.distancia_km < 1
                      ? `${Math.round(c.distancia_km * 1000)} m`
                      : `${c.distancia_km.toFixed(1)} km`}
                  </p>
                )}
              </div>
            </Surface>
          );
        })}

      {vistaActiva === "guardadas" && cargandoGuardadas && (
        <p className="text-center text-muted">Cargando...</p>
      )}

      {vistaActiva === "guardadas" &&
        !cargandoGuardadas &&
        guardadasErrorMessage && (
          <Alert variant="danger" role="alert" className="p-5">
            <p className="font-semibold">Error</p>
            <p className="mt-2 break-words">
              {guardadasErrorMessage}
            </p>
          </Alert>
        )}

      {vistaActiva === "guardadas" &&
        !cargandoGuardadas &&
        !guardadasErrorMessage &&
        publicacionesGuardadas.length === 0 && (
          <p className="text-muted">No tenes publicaciones guardadas.</p>
        )}

      {vistaActiva === "guardadas" &&
        !cargandoGuardadas &&
        !guardadasErrorMessage &&
        publicacionesGuardadas.length > 0 && (
          <div className="grid grid-cols-3 gap-1 sm:grid-cols-3 md:grid-cols-4">
            {publicacionesGuardadas.map((p) => {
              const publicacionImagenUrl = getMediaUrlFromAny(p);

              return (
                <Link
                  key={p.id}
                  to={`/publicaciones/${p.id}`}
                  className="relative aspect-square overflow-hidden bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring"
                >
                  {publicacionImagenUrl ? (
                    <img
                      src={publicacionImagenUrl}
                      alt=""
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center text-xs text-muted">
                      Sin imagen
                    </div>
                  )}

                  <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition hover:opacity-100">
                    <div className="text-center text-xs text-white">
                      <p>Likes {p.likes_count || 0}</p>
                      <p>Guardados {p.guardados_count || 0}</p>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
    </div>
  );
}

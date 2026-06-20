import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { usePublicacionesGuardadas } from "@features/posts";
import { obtenerMisEspaciosSeguidos } from "@features/spaces";
import { getMediaUrlFromAny } from "@shared";

export default function VerSeguidosPage() {
  const [vistaActiva, setVistaActiva] = useState("espacios");
  const [espacios, setEspacios] = useState([]);
  const [cargando, setCargando] = useState(true);

  const [ubicacion, setUbicacion] = useState({
    lat: null,
    lng: null,
    lista: false,
    error: null,
  });

  useEffect(() => {
    if (!navigator.geolocation) {
      queueMicrotask(() => {
        setUbicacion((prev) => ({
          ...prev,
          lista: true,
          error: "Ubicacion no disponible",
        }));
      });
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUbicacion({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          lista: true,
          error: null,
        });
      },
      () => {
        setUbicacion((prev) => ({
          ...prev,
          lista: true,
          error: "Ubicacion no disponible",
        }));
      }
    );
  }, []);

  useEffect(() => {
    let cancelado = false;

    async function cargar() {
      try {
        setCargando(true);

        const data = await obtenerMisEspaciosSeguidos({
          lat: ubicacion.lat,
          lng: ubicacion.lng,
        });

        if (cancelado) return;
        setEspacios(data);
      } catch {
        // Error esperado de carga: la pantalla conserva el estado actual.
      } finally {
        if (!cancelado) {
          setCargando(false);
        }
      }
    }

    cargar();

    return () => {
      cancelado = true;
    };
  }, [ubicacion.lat, ubicacion.lng]);

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
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Seguidos</h1>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setVistaActiva("espacios")}
          className={[
            "rounded-xl border px-3 py-2 text-xs font-semibold",
            vistaActiva === "espacios"
              ? "border-white bg-white text-gray-950"
              : "border-gray-800 bg-gray-950 text-gray-300 hover:bg-gray-900",
          ].join(" ")}
        >
          Espacios seguidos
        </button>

        <button
          type="button"
          onClick={() => setVistaActiva("guardadas")}
          className={[
            "rounded-xl border px-3 py-2 text-xs font-semibold",
            vistaActiva === "guardadas"
              ? "border-white bg-white text-gray-950"
              : "border-gray-800 bg-gray-950 text-gray-300 hover:bg-gray-900",
          ].join(" ")}
        >
          Publicaciones guardadas
        </button>
      </div>

      {vistaActiva === "espacios" && cargando && espacios.length === 0 && (
        <p className="text-center text-gray-400">Cargando...</p>
      )}

      {vistaActiva === "espacios" && !cargando && espacios.length === 0 && (
        <p className="text-gray-400">Todavia no seguis ningun espacio.</p>
      )}

      {vistaActiva === "espacios" &&
        espacios.map((c) => {
          const imagenUrl = getMediaUrlFromAny(c);

          return (
            <Link
              to={`/comercios/${c.id}`}
              key={c.id}
              className="flex items-center gap-4 rounded-xl border border-gray-800 bg-gray-950 p-3 hover:bg-gray-900"
            >
              <div className="h-16 w-16 overflow-hidden rounded-lg bg-gray-800">
                {imagenUrl ? (
                  <img
                    src={imagenUrl}
                    alt={c.nombre}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center text-xs text-gray-400">
                    Sin imagen
                  </div>
                )}
              </div>

              <div className="flex-1">
                <h2 className="text-sm font-semibold text-white">
                  {c.nombre}
                </h2>
                <p className="text-xs text-gray-400 line-clamp-2">
                  {c.descripcion || "Sin descripcion"}
                </p>
                {typeof c.distancia_km === "number" && (
                  <p className="mt-1 text-xs text-orange-500">
                    Estas a{" "}
                    {c.distancia_km < 1
                      ? `${Math.round(c.distancia_km * 1000)} m`
                      : `${c.distancia_km.toFixed(1)} km`}
                  </p>
                )}
                {!ubicacion.lista && typeof c.distancia_km !== "number" && (
                  <p className="mt-1 text-xs text-orange-500">
                    Buscando ubicacion...
                  </p>
                )}
                {ubicacion.error && typeof c.distancia_km !== "number" && (
                  <p className="mt-1 text-xs text-orange-500">
                    {ubicacion.error}
                  </p>
                )}
              </div>
            </Link>
          );
        })}

      {vistaActiva === "guardadas" && cargandoGuardadas && (
        <p className="text-center text-gray-400">Cargando...</p>
      )}

      {vistaActiva === "guardadas" &&
        !cargandoGuardadas &&
        guardadasErrorMessage && (
          <div className="rounded-2xl border border-red-900 bg-red-950/40 p-5">
            <p className="font-semibold text-red-200">Error</p>
            <p className="mt-2 text-red-100 break-words">
              {guardadasErrorMessage}
            </p>
          </div>
        )}

      {vistaActiva === "guardadas" &&
        !cargandoGuardadas &&
        !guardadasErrorMessage &&
        publicacionesGuardadas.length === 0 && (
          <p className="text-gray-400">No tenes publicaciones guardadas.</p>
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
                  className="relative aspect-square overflow-hidden bg-gray-800"
                >
                  {publicacionImagenUrl ? (
                    <img
                      src={publicacionImagenUrl}
                      alt=""
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center text-xs text-gray-400">
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

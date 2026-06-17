import { useEffect, useState } from "react";
import { obtenerMisEspaciosSeguidos } from "@features/spaces";
import { Link } from "react-router-dom";
import { getMediaUrlFromAny } from "@shared";

export default function VerSeguidosPage() {
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
          error: "Ubicación no disponible",
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
          error: "Ubicación no disponible",
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
  if (cargando && espacios.length === 0) {
    return <p className="text-center text-gray-400">Cargando...</p>;
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Espacios que seguís</h1>

      {espacios.length === 0 && (
        <p className="text-gray-400">
          Todavía no seguís ningún espacio.
        </p>
      )}

      {espacios.map((c) => {
        const imagenUrl = getMediaUrlFromAny(c);

        return (
          <Link
            to={`/comercios/${c.id}`}
            key={c.id}
            className="flex items-center gap-4 rounded-xl border border-gray-800 bg-gray-950 p-3 hover:bg-gray-900"
          >
            {/* IMAGEN IZQUIERDA */}
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

            {/* TEXTO DERECHA */}
            <div className="flex-1">
              <h2 className="text-sm font-semibold text-white">
                {c.nombre}
              </h2>
              <p className="text-xs text-gray-400 line-clamp-2">
                {c.descripcion || "Sin descripción"}
              </p>
              {typeof c.distancia_km === "number" && (
                <p className="text-xs text-orange-500 mt-1">
                  📍 Estás a {c.distancia_km < 1
                    ? `${Math.round(c.distancia_km * 1000)} m`
                    : `${c.distancia_km.toFixed(1)} km`}
                </p>
              )}
              {!ubicacion.lista && typeof c.distancia_km !== "number" && (
                <p className="text-xs text-orange-500 mt-1">
                  Buscando ubicación...
                </p>
              )}
              {ubicacion.error && typeof c.distancia_km !== "number" && (
                <p className="text-xs text-orange-500 mt-1">
                  {ubicacion.error}
                </p>
              )}
            </div>
          </Link>
        );
      })}
    </div>
  );
}

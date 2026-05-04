import { useEffect, useState } from "react";
import { obtenerMisEspaciosSeguidos } from "../services/seguidores_service";
import { Link } from "react-router-dom";

export default function VerSeguidosPage() {
  const [espacios, setEspacios] = useState([]);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    async function cargar() {
      try {
        const data = await obtenerMisEspaciosSeguidos();
        setEspacios(data);
      } catch (e) {
        console.error(e);
      } finally {
        setCargando(false);
      }
    }

    cargar();
  }, []);

  if (cargando) {
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

      {espacios.map((c) => (
        <Link
          to={`/comercios/${c.id}`}
          key={c.id}
          className="flex items-center gap-4 rounded-xl border border-gray-800 bg-gray-950 p-3 hover:bg-gray-900"
        >
          {/* IMAGEN IZQUIERDA */}
          <div className="h-16 w-16 overflow-hidden rounded-lg bg-gray-800">
            {c.imagen_url ? (
              <img
                src={c.imagen_url}
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
          </div>
        </Link>
      ))}
    </div>
  );
}
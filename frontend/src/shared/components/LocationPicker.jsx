import { useEffect, useState } from "react";
import {
  MapContainer,
  Marker,
  TileLayer,
  useMap,
  useMapEvents,
} from "react-leaflet";
import L from "leaflet";

delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

function DraggableMarker({ position, onChange }) {
  useMapEvents({
    click(e) {
      onChange(e.latlng.lat, e.latlng.lng);
    },
  });

  return (
    <Marker
      draggable
      position={position}
      eventHandlers={{
        dragend(e) {
          const marker = e.target;
          const nextPosition = marker.getLatLng();
          onChange(nextPosition.lat, nextPosition.lng);
        },
      }}
    />
  );
}

function MapPositionUpdater({ position }) {
  const map = useMap();

  useEffect(() => {
    map.setView(position);
  }, [map, position]);

  return null;
}

export default function LocationPicker({
  direccion = "",
  ciudad = "",
  provincia = "",
  latitud = null,
  longitud = null,
  onChange,
}) {
  const defaultPosition = [-31.2503, -61.4867]; // Rafaela
  const initialPosition =
    latitud !== null && longitud !== null
      ? [Number(latitud), Number(longitud)]
      : defaultPosition;

  const [query, setQuery] = useState("");
  const [position, setPosition] = useState(initialPosition);
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const initialQuery = [direccion, ciudad, provincia, "Argentina"]
      .filter(Boolean)
      .join(", ");

    setQuery(initialQuery);
  }, [direccion, ciudad, provincia]);

  function updatePosition(lat, lng) {
    const nextLat = Number(lat);
    const nextLng = Number(lng);

    setPosition([nextLat, nextLng]);
    onChange?.({
      latitud: nextLat,
      longitud: nextLng,
    });
  }

  async function handleBuscar() {
    if (!query.trim()) return;

    try {
      setIsSearching(true);
      setErrorMessage("");
      setSearchResults([]);

      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=5&countrycodes=ar&q=${encodeURIComponent(
          query
        )}`
      );

      const data = await response.json();

      if (!Array.isArray(data) || data.length === 0) {
        setErrorMessage("No se encontró la dirección.");
        return;
      }

      setSearchResults(data);
      updatePosition(data[0].lat, data[0].lon);
    } catch (error) {
      console.error(error);
      setErrorMessage("No se pudo buscar la dirección.");
    } finally {
      setIsSearching(false);
    }
  }

  function handleSelectResult(result) {
    setQuery(result.display_name || query);
    updatePosition(result.lat, result.lon);
  }

  function handleUsarUbicacionActual() {
    if (!navigator.geolocation) {
      setErrorMessage("Tu navegador no permite usar ubicación actual.");
      return;
    }

    setErrorMessage("");

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        updatePosition(pos.coords.latitude, pos.coords.longitude);
      },
      () => {
        setErrorMessage("No se pudo obtener tu ubicación actual.");
      }
    );
  }

  return (
    <div className="rounded-xl border border-gray-800 p-4">
      <div className="flex flex-col gap-2 sm:flex-row">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar dirección..."
          className="flex-1 rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm"
        />

        <button
          type="button"
          onClick={handleBuscar}
          disabled={isSearching}
          className="rounded-xl bg-orange-500 px-3 py-2 text-sm font-semibold text-white hover:bg-orange-600 disabled:opacity-60"
        >
          {isSearching ? "Buscando..." : "Buscar"}
        </button>

        <button
          type="button"
          onClick={handleUsarUbicacionActual}
          className="rounded-xl border border-gray-700 px-3 py-2 text-sm font-semibold text-white hover:bg-gray-800"
        >
          Usar mi ubicación
        </button>
      </div>

      {errorMessage && (
        <p className="mt-2 text-xs text-red-400">{errorMessage}</p>
      )}

      {searchResults.length > 0 && (
        <div className="mt-2 overflow-hidden rounded-xl border border-gray-800">
          {searchResults.map((result) => (
            <button
              key={result.place_id}
              type="button"
              onClick={() => handleSelectResult(result)}
              className="block w-full border-b border-gray-800 px-3 py-2 text-left text-xs text-gray-300 last:border-b-0 hover:bg-gray-900"
            >
              {result.display_name}
            </button>
          ))}
        </div>
      )}

      <div className="mt-3 h-72 overflow-hidden rounded-xl border border-gray-800">
        <MapContainer
          center={position}
          zoom={16}
          scrollWheelZoom={false}
          className="h-full w-full"
        >
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <MapPositionUpdater position={position} />
          <DraggableMarker position={position} onChange={updatePosition} />
        </MapContainer>
      </div>

      <p className="mt-2 text-xs text-gray-500">
        Lat: {position[0].toFixed(6)} / Lng: {position[1].toFixed(6)}
      </p>
    </div>
  );
}

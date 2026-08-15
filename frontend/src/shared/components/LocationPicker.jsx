import { useEffect, useRef, useState } from "react";
import {
  MapContainer,
  Marker,
  TileLayer,
  useMap,
  useMapEvents,
} from "react-leaflet";
import L from "leaflet";
import {
  buscarDirecciones,
  proponerDireccion,
} from "@shared/services/geocoding_service";
import { Alert, Button, Input, Surface } from "./primitives";

import {
  acceptDraftAddress,
  applyAddressProposal,
  canConfirmLocation,
  confirmLocation,
  createLocationDraft,
  isCurrentOperation,
  selectCoordinates,
  selectSearchResult,
  updateDraftAddress,
} from "./locationPickerState";

delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

function MapInteraction({ draft, onSelectCoordinates }) {
  useMapEvents({
    click(event) {
      onSelectCoordinates(event.latlng.lat, event.latlng.lng, "map");
    },
  });

  if (draft.latitude === null || draft.longitude === null) return null;

  return (
    <Marker
      draggable
      position={draft.position}
      eventHandlers={{
        dragend(event) {
          const nextPosition = event.target.getLatLng();
          onSelectCoordinates(nextPosition.lat, nextPosition.lng, "drag");
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
  onConfirm,
}) {
  const [isOpen, setIsOpen] = useState(true);
  const [draft, setDraft] = useState(() =>
    createLocationDraft({ direccion, latitud, longitud })
  );
  const [query, setQuery] = useState(direccion || "");
  const [searchResults, setSearchResults] = useState([]);
  const [asyncState, setAsyncState] = useState("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [attribution, setAttribution] = useState(null);
  const operationRevisionRef = useRef(0);
  const searchControllerRef = useRef(null);

  useEffect(() => {
    setDraft(createLocationDraft({ direccion, latitud, longitud }));
    setQuery(direccion || "");
  }, [direccion, latitud, longitud]);

  function invalidatePendingOperations() {
    operationRevisionRef.current += 1;
    searchControllerRef.current?.abort();
    searchControllerRef.current = null;
  }

  function resetFromCanonical() {
    setDraft(createLocationDraft({ direccion, latitud, longitud }));
    setQuery(direccion || "");
    setSearchResults([]);
    setAsyncState("idle");
    setErrorMessage("");
    setAttribution(null);
  }

  function handleOpen() {
    invalidatePendingOperations();
    resetFromCanonical();
    setIsOpen(true);
  }

  function handleCancel() {
    invalidatePendingOperations();
    resetFromCanonical();
    setIsOpen(false);
  }

  function handleQueryChange(event) {
    const nextQuery = event.target.value;
    invalidatePendingOperations();
    setQuery(nextQuery);
    setDraft((current) => updateDraftAddress(current, nextQuery));
    setSearchResults([]);
    setAsyncState("idle");
    setErrorMessage("");
  }

  async function handleSearch() {
    const addressQuery = query.trim();
    if (!addressQuery) return;

    invalidatePendingOperations();
    const operationRevision = operationRevisionRef.current;
    const controller = new AbortController();
    searchControllerRef.current = controller;

    try {
      setAsyncState("searching");
      setErrorMessage("");
      setSearchResults([]);
      setAttribution(null);

      const data = await buscarDirecciones(
        {
          query: addressQuery,
          ciudad,
          provincia,
          limit: 5,
        },
        { signal: controller.signal }
      );

      if (!isCurrentOperation(operationRevisionRef.current, operationRevision)) {
        return;
      }
      const alternatives = data?.alternativas;
      if (!Array.isArray(alternatives) || alternatives.length === 0) {
        setAsyncState("error");
        setErrorMessage("No se encontró la dirección.");
        return;
      }

      setSearchResults(alternatives);
      setAttribution(data?.attribution || null);
      setAsyncState("success");
    } catch (error) {
      if (error?.name === "AbortError") return;
      if (!isCurrentOperation(operationRevisionRef.current, operationRevision)) {
        return;
      }
      setAsyncState("error");
      setErrorMessage("No se pudo buscar la dirección.");
    } finally {
      if (isCurrentOperation(operationRevisionRef.current, operationRevision)) {
        searchControllerRef.current = null;
      }
    }
  }

  function handleSelectResult(result) {
    invalidatePendingOperations();
    const nextDraft = selectSearchResult(draft, result);
    setDraft(nextDraft);
    setQuery(nextDraft.address);
    setSearchResults([]);
    setAsyncState("success");
    setErrorMessage("");
  }

  async function handleSelectCoordinates(latitude, longitude, source) {
    invalidatePendingOperations();
    const operationRevision = operationRevisionRef.current;
    const controller = new AbortController();
    searchControllerRef.current = controller;
    setDraft((current) => selectCoordinates(current, latitude, longitude, source));
    setSearchResults([]);
    setAsyncState("searching");
    setErrorMessage("");
    setAttribution(null);

    try {
      const data = await proponerDireccion(
        { latitud: Number(latitude), longitud: Number(longitude) },
        { signal: controller.signal }
      );
      if (!isCurrentOperation(operationRevisionRef.current, operationRevision)) {
        return;
      }

      const proposal = data?.propuesta;
      if (!proposal) {
        setAsyncState("error");
        setErrorMessage(
          "No encontramos una dirección para este punto. Elegí una alternativa o revisá la dirección escrita."
        );
        return;
      }

      setDraft((current) => applyAddressProposal(current, {
        direccion: proposal.label,
        latitud: proposal.latitud,
        longitud: proposal.longitud,
        precision: proposal.precision,
        confidence: proposal.confidence,
      }));
      setQuery(proposal.label);
      setAttribution(data?.attribution || null);
      setAsyncState("success");
    } catch (error) {
      if (error?.name === "AbortError") return;
      if (!isCurrentOperation(operationRevisionRef.current, operationRevision)) {
        return;
      }
      setAsyncState("error");
      setErrorMessage(
        "No pudimos proponer una dirección para este punto. Revisá la dirección antes de confirmar."
      );
    } finally {
      if (isCurrentOperation(operationRevisionRef.current, operationRevision)) {
        searchControllerRef.current = null;
      }
    }
  }

  function handleUseCurrentLocation() {
    if (!navigator.geolocation) {
      setAsyncState("error");
      setErrorMessage("Tu navegador no permite usar ubicación actual.");
      return;
    }

    invalidatePendingOperations();
    const operationRevision = operationRevisionRef.current;
    setAsyncState("searching");
    setErrorMessage("");

    navigator.geolocation.getCurrentPosition(
      (position) => {
        if (!isCurrentOperation(operationRevisionRef.current, operationRevision)) {
          return;
        }
        handleSelectCoordinates(
          position.coords.latitude,
          position.coords.longitude,
          "device"
        );
      },
      () => {
        if (!isCurrentOperation(operationRevisionRef.current, operationRevision)) {
          return;
        }
        setAsyncState("error");
        setErrorMessage("No se pudo obtener tu ubicación actual.");
      }
    );
  }

  function handleAcceptWrittenAddress() {
    setDraft((current) => acceptDraftAddress(current));
  }

  function handleConfirm() {
    const confirmedLocation = confirmLocation(draft);
    if (!confirmedLocation) return;

    invalidatePendingOperations();
    onConfirm?.(confirmedLocation);
    setIsOpen(false);
  }

  if (!isOpen) {
    const hasCanonicalLocation =
      direccion && latitud !== null && longitud !== null;

    return (
      <Surface className="rounded-xl p-4">
        <p className="text-sm text-secondary">
          {hasCanonicalLocation
            ? `Ubicación confirmada: ${direccion}`
            : "Sin ubicación confirmada."}
        </p>
        <Button
          type="button"
          onClick={handleOpen}
          variant="secondary"
          className="mt-3 px-3 py-2 text-sm"
        >
          {hasCanonicalLocation ? "Editar ubicación" : "Seleccionar ubicación"}
        </Button>
      </Surface>
    );
  }

  return (
    <Surface className="rounded-xl p-4">
      <div className="flex flex-col gap-2 sm:flex-row">
        <Input
          value={query}
          onChange={handleQueryChange}
          placeholder="Buscar dirección..."
          aria-label="Dirección para buscar o confirmar"
          className="flex-1 text-sm"
        />

        <Button
          type="button"
          onClick={handleSearch}
          disabled={asyncState === "searching"}
          variant="primary"
          className="px-3 py-2 text-sm"
        >
          {asyncState === "searching" ? "Buscando..." : "Buscar"}
        </Button>

        <Button
          type="button"
          onClick={handleUseCurrentLocation}
          disabled={asyncState === "searching"}
          variant="secondary"
          className="px-3 py-2 text-sm"
        >
          Usar mi ubicación
        </Button>
      </div>

      {errorMessage && (
        <Alert variant="danger" role="alert" className="mt-2 p-3 text-xs">
          {errorMessage}
        </Alert>
      )}

      {searchResults.length > 0 && (
        <div className="mt-2 overflow-hidden rounded-xl border border-border">
          {searchResults.map((result) => (
            <Button
              key={`${result.latitud}:${result.longitud}:${result.label}`}
              type="button"
              onClick={() => handleSelectResult(result)}
              variant="ghost"
              className="block w-full rounded-none border-b border-border px-3 py-2 text-left text-xs text-secondary last:border-b-0 hover:bg-surface-subtle"
            >
              {result.label}
            </Button>
          ))}
        </div>
      )}

      <div className="mt-3 h-72 overflow-hidden rounded-xl border border-border">
        <MapContainer
          center={draft.position}
          zoom={16}
          scrollWheelZoom={false}
          className="h-full w-full"
        >
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <MapPositionUpdater position={draft.position} />
          <MapInteraction
            draft={draft}
            onSelectCoordinates={handleSelectCoordinates}
          />
        </MapContainer>
      </div>

      {draft.latitude !== null && draft.longitude !== null ? (
        <p className="mt-2 text-xs text-muted">
          Lat: {draft.latitude.toFixed(6)} / Lng: {draft.longitude.toFixed(6)}
        </p>
      ) : (
        <p className="mt-2 text-xs text-muted">
          El centro inicial del mapa es solo una referencia.
        </p>
      )}

      {draft.coherent && draft.precision !== "address" && (
        <p className="mt-2 text-xs text-warning-text">
          La dirección propuesta puede ser aproximada. Revisala antes de confirmar.
        </p>
      )}

      {attribution?.url && attribution?.label && (
        <a
          href={attribution.url}
          target="_blank"
          rel="noreferrer"
          className="mt-2 inline-block text-xs text-secondary underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
        >
          {attribution.label}
        </a>
      )}

      {!draft.coherent && draft.latitude !== null && draft.longitude !== null && (
        <Alert variant="warning" className="mt-3 p-3">
          <p className="text-xs">
            El punto cambió. Revisá la dirección antes de confirmar.
          </p>
          <Button
            type="button"
            onClick={handleAcceptWrittenAddress}
            disabled={!draft.address.trim()}
            variant="warning"
            className="mt-2 px-3 py-1.5 text-xs"
          >
            Usar esta dirección para el punto seleccionado
          </Button>
        </Alert>
      )}

      <div className="mt-4 flex flex-wrap justify-end gap-2">
        <Button
          type="button"
          onClick={handleCancel}
          variant="secondary"
          className="px-3 py-2 text-sm"
        >
          Cancelar
        </Button>
        <Button
          type="button"
          onClick={handleConfirm}
          disabled={!canConfirmLocation(draft)}
          variant="primary"
          className="px-3 py-2 text-sm"
        >
          Confirmar ubicación
        </Button>
      </div>
    </Surface>
  );
}

export const LOCATION_REFERENCE_POSITION = [-31.2503, -61.4867];

function finiteCoordinate(value) {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

export function createLocationDraft({
  direccion = "",
  latitud = null,
  longitud = null,
} = {}) {
  const latitude = finiteCoordinate(latitud);
  const longitude = finiteCoordinate(longitud);
  const hasCoordinates = latitude !== null && longitude !== null;
  const address = String(direccion || "").trim();
  const coherent = hasCoordinates && Boolean(address);

  return {
    mode: coherent ? "confirmed" : hasCoordinates ? "selected" : "reference",
    address,
    latitude,
    longitude,
    position: hasCoordinates
      ? [latitude, longitude]
      : LOCATION_REFERENCE_POSITION,
    coherent,
    source: coherent ? "canonical" : "reference",
    precision: coherent ? "address" : "unknown",
    confidence: null,
  };
}

export function selectSearchResult(draft, result) {
  const latitude = finiteCoordinate(result?.latitud);
  const longitude = finiteCoordinate(result?.longitud);
  const address = String(result?.label || "").trim();

  if (latitude === null || longitude === null || !address) return draft;

  return {
    ...draft,
    mode: "selected",
    address,
    latitude,
    longitude,
    position: [latitude, longitude],
    coherent: true,
    source: "search",
    precision: result.precision || "unknown",
    confidence: result.confidence ?? null,
  };
}

export function selectCoordinates(draft, latitudeValue, longitudeValue, source) {
  const latitude = finiteCoordinate(latitudeValue);
  const longitude = finiteCoordinate(longitudeValue);
  if (latitude === null || longitude === null) return draft;

  return {
    ...draft,
    mode: "selected",
    latitude,
    longitude,
    position: [latitude, longitude],
    coherent: false,
    source,
    precision: "unknown",
    confidence: null,
  };
}

export function updateDraftAddress(draft, addressValue) {
  const address = String(addressValue || "");
  if (address === draft.address) return draft;

  return {
    ...draft,
    mode:
      draft.latitude !== null && draft.longitude !== null
        ? "selected"
        : "empty",
    address,
    coherent: false,
    source: "manual",
  };
}

export function acceptDraftAddress(draft) {
  const address = draft.address.trim();
  const hasCoordinates = draft.latitude !== null && draft.longitude !== null;
  if (!address || !hasCoordinates) return draft;

  return {
    ...draft,
    mode: "selected",
    address,
    coherent: true,
    source: "manual_review",
    precision: "unknown",
    confidence: null,
  };
}

export function applyAddressProposal(draft, proposal) {
  const proposedLatitude = finiteCoordinate(proposal?.latitud);
  const proposedLongitude = finiteCoordinate(proposal?.longitud);
  const proposedAddress = String(proposal?.direccion || "").trim();
  const matchesCurrentPoint =
    proposedLatitude === draft.latitude && proposedLongitude === draft.longitude;

  if (!matchesCurrentPoint || !proposedAddress) return draft;

  return {
    ...draft,
    mode: "selected",
    address: proposedAddress,
    coherent: true,
    source: "address_proposal",
    precision: proposal.precision || "unknown",
    confidence: proposal.confidence ?? null,
  };
}

export function canConfirmLocation(draft) {
  return Boolean(
    draft.coherent &&
      draft.address.trim() &&
      draft.latitude !== null &&
      draft.longitude !== null
  );
}

export function confirmLocation(draft) {
  if (!canConfirmLocation(draft)) return null;

  return {
    direccion: draft.address.trim(),
    latitud: draft.latitude,
    longitud: draft.longitude,
  };
}

export function invalidateLocationAfterAddressEdit(location, nextAddress) {
  if (String(location.direccion || "") === String(nextAddress || "")) {
    return location;
  }

  return {
    ...location,
    direccion: nextAddress,
    latitud: null,
    longitud: null,
  };
}

export function isCurrentOperation(currentRevision, operationRevision) {
  return currentRevision === operationRevision;
}

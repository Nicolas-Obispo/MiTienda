import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { resolverTerritorio } from "@shared/services/geocoding_service";
import { GeographicContext } from "@shared/location/GeographicContextCore";
import {
  acceptDevicePosition,
  acquirePosition,
  createManualContext,
  EMPTY_GEOGRAPHIC_CONTEXT,
  FAST_POSITION_OPTIONS,
  geographicQueryContext,
  geolocationErrorState,
  isDistanceFresh,
  isTerritoryFresh,
} from "@shared/location/geographicContextState";

function readPosition(options) {
  return new Promise((resolve, reject) => {
    if (!globalThis.navigator?.geolocation) {
      reject(Object.assign(new Error("Geolocalización no disponible."), { code: "unavailable" }));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => resolve({
        lat: position.coords.latitude,
        lng: position.coords.longitude,
        accuracy: position.coords.accuracy,
        capturedAt: position.timestamp || Date.now(),
      }),
      reject,
      options
    );
  });
}

function permissionError(error) {
  if (error?.code === 1) return "Permiso de ubicación rechazado.";
  if (error?.code === 3) return "La ubicación no respondió a tiempo.";
  return error?.message || "No pudimos obtener tu ubicación.";
}

export function GeographicContextProvider({ children }) {
  const [context, setContext] = useState(EMPTY_GEOGRAPHIC_CONTEXT);
  const [permissionState, setPermissionState] = useState("idle");
  const [error, setError] = useState(null);
  const requestRevision = useRef(0);

  const requestDeviceLocation = useCallback(async ({ needDistance = true, force = false } = {}) => {
    const revision = ++requestRevision.current;
    setPermissionState("requesting");
    setError(null);
    try {
      const reading = await acquirePosition(readPosition, { needDistance });
      const territory = await resolverTerritorio({ latitud: reading.lat, longitud: reading.lng });
      if (revision !== requestRevision.current) return null;
      let accepted;
      setContext((previous) => {
        accepted = acceptDevicePosition(previous, reading, territory, { force });
        return accepted;
      });
      setPermissionState("granted");
      return accepted;
    } catch (requestError) {
      if (revision !== requestRevision.current) return null;
      setPermissionState(geolocationErrorState(requestError));
      setError(permissionError(requestError));
      return null;
    }
  }, []);

  const selectManualTerritory = useCallback((selection) => {
    requestRevision.current += 1;
    setContext((previous) => ({
      ...createManualContext(selection),
      positionRevision: (previous?.positionRevision || 0) + 1,
    }));
    setPermissionState("manual");
    setError(null);
  }, []);

  useEffect(() => {
    function refreshAfterForeground() {
      if (
        document.visibilityState === "visible" &&
        context.source === "device" &&
        !isTerritoryFresh(context)
      ) {
        requestDeviceLocation({ needDistance: true });
      }
    }
    document.addEventListener("visibilitychange", refreshAfterForeground);
    return () => document.removeEventListener("visibilitychange", refreshAfterForeground);
  }, [context, requestDeviceLocation]);

  const value = useMemo(() => ({
    context,
    permissionState,
    error,
    hasTerritory: Boolean(context.cityKey && context.provinceCode && context.countryCode),
    queryContext: geographicQueryContext(context),
    territoryFresh: isTerritoryFresh(context),
    distanceFresh: isDistanceFresh(context),
    requestDeviceLocation,
    selectManualTerritory,
  }), [context, permissionState, error, requestDeviceLocation, selectManualTerritory]);

  return <GeographicContext.Provider value={value}>{children}</GeographicContext.Provider>;
}

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
  const contextRef = useRef(EMPTY_GEOGRAPHIC_CONTEXT);
  const activeRequestRef = useRef(null);
  const automaticAttemptRef = useRef(null);
  const identityRef = useRef("anonymous");
  const profileTerritoryRef = useRef(null);
  const permissionStatusRef = useRef(null);
  const browserPermissionRef = useRef("unknown");
  const [browserPermission, setBrowserPermission] = useState("unknown");
  const [identityRevision, setIdentityRevision] = useState(0);

  const replaceContext = useCallback((nextContext) => {
    contextRef.current = nextContext;
    setContext(nextContext);
  }, []);

  const applyProfileFallback = useCallback(() => {
    const profile = profileTerritoryRef.current;
    if (!profile?.city || !profile?.province) {
      replaceContext(EMPTY_GEOGRAPHIC_CONTEXT);
      return null;
    }
    const fallback = createManualContext({ ...profile, source: "profile_fallback" });
    replaceContext(fallback);
    setPermissionState("denied");
    setError(null);
    return fallback;
  }, [replaceContext]);

  const requestDeviceLocation = useCallback(async ({ needDistance = true, force = false } = {}) => {
    if (activeRequestRef.current) return activeRequestRef.current;
    const revision = ++requestRevision.current;
    setPermissionState("requesting");
    setError(null);
    const request = (async () => { try {
      const reading = await acquirePosition(readPosition, { needDistance });
      const territory = await resolverTerritorio({ latitud: reading.lat, longitud: reading.lng });
      if (revision !== requestRevision.current) return null;
      let accepted;
      setContext((previous) => {
        accepted = acceptDevicePosition(previous, reading, territory, { force });
        contextRef.current = accepted;
        return accepted;
      });
      browserPermissionRef.current = "granted";
      setBrowserPermission("granted");
      setPermissionState("granted");
      return accepted;
    } catch (requestError) {
      if (revision !== requestRevision.current) return null;
      if (requestError?.code === 1) {
        browserPermissionRef.current = "denied";
        setBrowserPermission("denied");
        return applyProfileFallback();
      }
      setPermissionState(geolocationErrorState(requestError));
      setError(permissionError(requestError));
      return null;
    } finally {
      if (activeRequestRef.current === request) activeRequestRef.current = null;
    } })();
    activeRequestRef.current = request;
    return request;
  }, [applyProfileFallback]);

  const reconcileIdentity = useCallback(({ identityKey, profileTerritory = null }) => {
    profileTerritoryRef.current = profileTerritory;
    if (identityRef.current === identityKey) return;
    identityRef.current = identityKey;
    if (contextRef.current.source === "device" || activeRequestRef.current) return;
    setIdentityRevision((current) => current + 1);
    requestRevision.current += 1;
    automaticAttemptRef.current = null;
    activeRequestRef.current = null;
    replaceContext(EMPTY_GEOGRAPHIC_CONTEXT);
    setPermissionState("idle");
    setError(null);
    if (browserPermissionRef.current === "denied") applyProfileFallback();
  }, [applyProfileFallback, replaceContext]);

  const ensureAutomaticContext = useCallback(async () => {
    if (
      isTerritoryFresh(contextRef.current) ||
      (contextRef.current.source !== "device" && contextRef.current.cityKey)
    ) return contextRef.current;
    const attemptKey = `${identityRef.current || "anonymous"}:${identityRevision}:${browserPermission}`;
    if (automaticAttemptRef.current === attemptKey) return activeRequestRef.current;
    automaticAttemptRef.current = attemptKey;

    let permission = browserPermission;
    if (globalThis.navigator?.permissions?.query) {
      try {
        const status = await navigator.permissions.query({ name: "geolocation" });
        permissionStatusRef.current = status;
        permission = status.state;
        setBrowserPermission(status.state);
      } catch {
        permission = "unsupported";
      }
    }
    if (permission === "denied") return applyProfileFallback();
    return requestDeviceLocation({ needDistance: true });
  }, [applyProfileFallback, browserPermission, identityRevision, requestDeviceLocation]);

  const selectManualTerritory = useCallback((selection) => {
    requestRevision.current += 1;
    setContext((previous) => {
      const next = {
      ...createManualContext(selection),
      positionRevision: (previous?.positionRevision || 0) + 1,
      };
      contextRef.current = next;
      return next;
    });
    setPermissionState("manual");
    setError(null);
  }, []);

  useEffect(() => {
    if (!globalThis.navigator?.permissions?.query) return undefined;
    let disposed = false;
    let status;
    const handleChange = () => {
      if (disposed) return;
      browserPermissionRef.current = status.state;
      setBrowserPermission(status.state);
      automaticAttemptRef.current = null;
      if (status.state === "denied" && contextRef.current.source === "device") {
        requestRevision.current += 1;
        applyProfileFallback();
      }
    };
    navigator.permissions.query({ name: "geolocation" }).then((nextStatus) => {
      if (disposed) return;
      status = nextStatus;
      permissionStatusRef.current = status;
      browserPermissionRef.current = status.state;
      setBrowserPermission(status.state);
      status.addEventListener?.("change", handleChange);
    }).catch(() => {
      browserPermissionRef.current = "unsupported";
      setBrowserPermission("unsupported");
    });
    return () => {
      disposed = true;
      status?.removeEventListener?.("change", handleChange);
    };
  }, [applyProfileFallback]);

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
    browserPermission,
    ensureAutomaticContext,
    reconcileIdentity,
    requestDeviceLocation,
    selectManualTerritory,
  }), [browserPermission, context, permissionState, error, ensureAutomaticContext, reconcileIdentity, requestDeviceLocation, selectManualTerritory]);

  return <GeographicContext.Provider value={value}>{children}</GeographicContext.Provider>;
}

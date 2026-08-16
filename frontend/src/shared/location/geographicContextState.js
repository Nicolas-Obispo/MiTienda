export const TERRITORY_MAX_AGE_MS = 5 * 60 * 1000;
export const TERRITORY_MAX_ACCURACY_M = 1000;
export const DISTANCE_MAX_AGE_MS = 60 * 1000;
export const DISTANCE_MAX_ACCURACY_M = 100;

export const FAST_POSITION_OPTIONS = Object.freeze({
  maximumAge: 60 * 1000,
  timeout: 3000,
  enableHighAccuracy: false,
});

export const PRECISE_POSITION_OPTIONS = Object.freeze({
  maximumAge: 0,
  timeout: 8000,
  enableHighAccuracy: true,
});

export const EMPTY_GEOGRAPHIC_CONTEXT = Object.freeze({
  source: null,
  country: null,
  province: null,
  city: null,
  countryCode: null,
  provinceCode: null,
  cityKey: null,
  lat: null,
  lng: null,
  accuracy: null,
  capturedAt: null,
  positionRevision: 0,
  attribution: null,
});

function finite(value) {
  return typeof value === "number" && Number.isFinite(value);
}

export function positionAge(context, now = Date.now()) {
  return finite(context?.capturedAt) ? Math.max(0, now - context.capturedAt) : Infinity;
}

export function isTerritoryFresh(context, now = Date.now()) {
  return Boolean(
    context?.cityKey &&
      context?.provinceCode &&
      context?.countryCode &&
      finite(context?.accuracy) &&
      context.accuracy <= TERRITORY_MAX_ACCURACY_M &&
      positionAge(context, now) <= TERRITORY_MAX_AGE_MS
  );
}

export function isDistanceFresh(context, now = Date.now()) {
  return Boolean(
    finite(context?.lat) &&
      finite(context?.lng) &&
      finite(context?.accuracy) &&
      context.accuracy <= DISTANCE_MAX_ACCURACY_M &&
      positionAge(context, now) <= DISTANCE_MAX_AGE_MS
  );
}

export function distanceMeters(left, right) {
  if (![left?.lat, left?.lng, right?.lat, right?.lng].every(finite)) return Infinity;
  const radians = (degrees) => (degrees * Math.PI) / 180;
  const earthRadiusM = 6371000;
  const deltaLat = radians(right.lat - left.lat);
  const deltaLng = radians(right.lng - left.lng);
  const a =
    Math.sin(deltaLat / 2) ** 2 +
    Math.cos(radians(left.lat)) *
      Math.cos(radians(right.lat)) *
      Math.sin(deltaLng / 2) ** 2;
  return earthRadiusM * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export function territoryIdentity(context) {
  if (!context?.cityKey || !context?.provinceCode || !context?.countryCode) return null;
  return `${context.countryCode}:${context.provinceCode}:${context.cityKey}`;
}

export function isSignificantDisplacement(previous, next) {
  if (!finite(previous?.accuracy) || !finite(next?.accuracy)) return true;
  const threshold = Math.max(50, previous.accuracy + next.accuracy);
  return distanceMeters(previous, next) >= threshold;
}

export function acceptDevicePosition(previous, reading, territory, { now = Date.now(), force = false } = {}) {
  const next = {
    source: "device",
    country: territory.country,
    province: territory.province,
    city: territory.city,
    countryCode: territory.country_code,
    provinceCode: territory.province_code,
    cityKey: territory.city_key,
    lat: reading.lat,
    lng: reading.lng,
    accuracy: reading.accuracy,
    capturedAt: reading.capturedAt ?? now,
    positionRevision: previous?.positionRevision || 0,
    attribution: territory.attribution || null,
  };
  const territoryChanged = territoryIdentity(previous) !== territoryIdentity(next);
  const previousDistanceExpired = !isDistanceFresh(previous, now);
  if (
    !previous?.source ||
    force ||
    territoryChanged ||
    isSignificantDisplacement(previous, next) ||
    previousDistanceExpired
  ) {
    next.positionRevision += 1;
  }
  return next;
}

export function createManualContext({ city, province, provinceCode = null, source = "manual" }) {
  const cleanCity = String(city || "").trim();
  const cleanProvince = String(province || "").trim();
  if (!cleanCity || !cleanProvince) throw new Error("Ciudad y provincia son obligatorias.");
  return {
    ...EMPTY_GEOGRAPHIC_CONTEXT,
    source,
    country: "Argentina",
    province: cleanProvince,
    city: cleanCity,
    countryCode: "AR",
    provinceCode: provinceCode || cleanProvince,
    cityKey: cleanCity,
    positionRevision: 1,
  };
}

export function geographicQueryContext(context, now = Date.now()) {
  if (!territoryIdentity(context)) return null;
  const includePosition = context.source === "device" && isDistanceFresh(context, now);
  return {
    city_key: context.cityKey,
    province_code: context.provinceCode,
    country_code: context.countryCode,
    positionRevision: context.positionRevision,
    lat: includePosition ? context.lat : null,
    lng: includePosition ? context.lng : null,
  };
}

export async function acquirePosition(read, { needDistance = true } = {}) {
  let quick;
  try {
    quick = await read(FAST_POSITION_OPTIONS);
  } catch (error) {
    if (error?.code !== 3) throw error;
    return read(PRECISE_POSITION_OPTIONS);
  }
  const needsRefinement =
    quick.accuracy > TERRITORY_MAX_ACCURACY_M ||
    (needDistance && quick.accuracy > DISTANCE_MAX_ACCURACY_M);
  if (!needsRefinement) return quick;
  try {
    return await read(PRECISE_POSITION_OPTIONS);
  } catch (error) {
    if (quick.accuracy > TERRITORY_MAX_ACCURACY_M) throw error;
    return quick;
  }
}

export function geolocationErrorState(error) {
  if (error?.code === 1) return "denied";
  if (error?.code === "unavailable") return "unavailable";
  return "error";
}

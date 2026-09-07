/**
 * Acepta sólo destinos relativos dentro de FeedGo. Nunca interpreta ni
 * persiste datos sensibles: se usa exclusivamente como navegación de retorno.
 */
export function getInternalReturnTo(value, fallback = "/feed") {
  if (typeof value !== "string") return fallback;
  if (!value.startsWith("/") || value.startsWith("//") || value.includes("\\")) {
    return fallback;
  }

  try {
    const internalOrigin = "https://feedgo.internal";
    const url = new URL(value, internalOrigin);
    if (url.origin !== internalOrigin) return fallback;

    // El retorno conserva contexto navegable, nunca secretos ni datos privados.
    // Los fragmentos se descartan porque los flujos de identidad transportan
    // allí tokens de un solo uso.
    const sensitiveParam =
      /(^|_)(token|otp|code|codigo|password|contrasena|email|correo|phone|telefono|dob|fecha_nacimiento)(_|$)/i;
    for (const key of [...url.searchParams.keys()]) {
      if (sensitiveParam.test(key)) url.searchParams.delete(key);
    }

    const search = url.searchParams.toString();
    return `${url.pathname}${search ? `?${search}` : ""}`;
  } catch {
    return fallback;
  }
}

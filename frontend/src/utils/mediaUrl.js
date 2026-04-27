export function getMediaUrlFromAny(source) {
  const rawUrl =
    source?.imagen_url ||
    source?.media_url ||
    source?.foto_url ||
    source?.thumbnail_url ||
    source?.thumbnailUrl || // 🔥 FIX historias (camelCase del backend)
    source?.portada_url ||
    source?.logo_url ||
    "";

  if (!rawUrl || typeof rawUrl !== "string") return "";

  const apiBaseUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

  // 🔁 Reemplazo de localhost → IP real (clave para iPhone)
  if (rawUrl.startsWith("http://127.0.0.1:8000")) {
    return rawUrl.replace("http://127.0.0.1:8000", apiBaseUrl);
  }

  if (rawUrl.startsWith("http://localhost:8000")) {
    return rawUrl.replace("http://localhost:8000", apiBaseUrl);
  }

  // 🔁 Soporte rutas relativas
  if (rawUrl.startsWith("/uploads/")) {
    return `${apiBaseUrl}${rawUrl}`;
  }

  return rawUrl;
}
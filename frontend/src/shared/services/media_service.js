// frontend/src/services/media_service.js
// Service de infraestructura para subir archivos (MVP: imágenes) al backend.
// Regla de oro: el frontend NO inventa estado. Solo envía el archivo y recibe una URL.

// Usamos la misma base URL que http_service.js para mantener consistencia.
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

/**
 * Sube una imagen al backend usando multipart/form-data.
 * Devuelve: { url: "http://..." }
 *
 * @param {File} file - Archivo elegido por el usuario (input type="file")
 * @param {string|null} token - JWT (si existe) para Authorization Bearer
 */
export async function uploadImagen(file, token = null) {
  if (!file) {
    throw new Error("No se seleccionó ningún archivo.");
  }

  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/media/upload`, {
    method: "POST",
    // IMPORTANTE:
    // - NO seteamos Content-Type para multipart.
    // - El browser arma el boundary.
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: formData,
  });

  if (!response.ok) {
    // El backend puede devolver detail en texto/JSON
    const text = await response.text();
    throw new Error(`HTTP ${response.status} - ${text}`);
  }

  return response.json(); // { url }
}

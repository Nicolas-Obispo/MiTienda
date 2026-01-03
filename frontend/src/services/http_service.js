/**
 * http_service.js
 * ----------------
 * Capa HTTP (infraestructura) del Frontend.
 *
 * RESPONSABILIDAD:
 * - Centralizar llamadas fetch al backend.
 * - Manejar headers comunes (JSON + Authorization).
 * - Manejar errores HTTP de forma consistente.
 *
 * IMPORTANTE:
 * - Acá NO va lógica de negocio (eso vive en "services" específicos por feature).
 * - Este archivo SOLO sabe "cómo pegarle al backend".
 */

/**
 * Base URL del backend.
 * Vite expone variables de entorno con el prefijo VITE_*
 * Ej: VITE_API_BASE_URL=http://127.0.0.1:8000
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

/**
 * buildHeaders
 * Construye headers estándar para requests JSON.
 *
 * @param {string|null} token - JWT (si existe) para Authorization Bearer
 * @returns {object} headers listos para fetch
 */
function buildHeaders(token) {
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

/**
 * httpGet
 * Request GET genérico.
 *
 * @param {string} path - Ruta del backend, ej: "/feed/publicaciones"
 * @param {string|null} token - JWT opcional
 * @returns {Promise<any>} JSON parseado
 */
export async function httpGet(path, token = null) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    headers: buildHeaders(token),
  });

  // Si el backend responde error, leemos texto para tener mensaje útil
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status} - ${errorText}`);
  }

  return response.json();
}

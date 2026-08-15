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
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export class HttpError extends Error {
  constructor(status, message) {
    super(`HTTP ${status} - ${message}`);
    this.name = "HttpError";
    this.status = status;
    this.publicMessage = message;
  }
}

const DEFAULT_ERROR_MESSAGES = {
  400: "Solicitud inválida.",
  401: "No autenticado.",
  403: "No autorizado.",
  404: "Recurso no encontrado.",
  409: "No se pudo completar la operación por un conflicto.",
  413: "Archivo demasiado grande.",
  422: "Payload inválido.",
};

function safeErrorMessage(status) {
  return DEFAULT_ERROR_MESSAGES[status] || "No se pudo completar la operación.";
}

async function throwHttpError(response) {
  try {
    await response.text();
  } catch {
    // El cuerpo del error no se muestra al usuario ni se propaga.
  }

  throw new HttpError(response.status, safeErrorMessage(response.status));
}

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

  // Si el backend responde error, no propagamos el cuerpo crudo.
  if (!response.ok) {
    await throwHttpError(response);
  }

  return response.json();
}


/**
 * httpPost
 * Request POST genérico.
 *
 * @param {string} path - Ruta del backend
 * @param {object|null} body - Body JSON
 * @param {string|null} token - JWT opcional
 * @returns {Promise<any>} JSON parseado
 */
export async function httpPost(path, body = null, token = null, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: buildHeaders(token),
    body: body ? JSON.stringify(body) : null,
    signal: options.signal,
  });

  if (!response.ok) {
    await throwHttpError(response);
  }

  // Algunos endpoints devuelven texto simple
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

/**
 * httpDelete
 * Request DELETE genérico.
 *
 * @param {string} path - Ruta del backend
 * @param {string|null} token - JWT opcional
 * @returns {Promise<any>} respuesta vacía o texto
 */
export async function httpDelete(path, token = null) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "DELETE",
    headers: buildHeaders(token),
  });

  if (!response.ok) {
    await throwHttpError(response);
  }

  // DELETE suele devolver 204 No Content
  return null;
}

/**
 * httpPut
 * Request PUT genérico.
 *
 * @param {string} path - Ruta del backend
 * @param {object|null} body - Body JSON
 * @param {string|null} token - JWT opcional
 * @returns {Promise<any>} JSON parseado
 */
export async function httpPut(path, body = null, token = null) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PUT",
    headers: buildHeaders(token),
    body: body ? JSON.stringify(body) : null,
  });

  if (!response.ok) {
    await throwHttpError(response);
  }

  // PUT normalmente devuelve JSON
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

/**
 * httpPatch
 * Request PATCH generico.
 *
 * @param {string} path - Ruta del backend
 * @param {object|null} body - Body JSON
 * @param {string|null} token - JWT opcional
 * @returns {Promise<any>} JSON parseado
 */
export async function httpPatch(path, body = null, token = null) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PATCH",
    headers: buildHeaders(token),
    body: body ? JSON.stringify(body) : null,
  });

  if (!response.ok) {
    await throwHttpError(response);
  }

  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

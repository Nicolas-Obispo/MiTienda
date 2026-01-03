/**
 * feed_service.js
 * ----------------
 * Service de negocio del Feed (Frontend).
 *
 * RESPONSABILIDAD:
 * - Exponer funciones claras para obtener el feed desde el backend.
 * - No renderiza UI (eso es responsabilidad de pages/components).
 *
 * Usa:
 * - http_service.js (infraestructura HTTP)
 */

import { httpGet } from "./http_service";

/**
 * getAccessToken
 * Obtiene el token JWT desde localStorage.
 *
 * Nota:
 * - En esta etapa todavía no estamos haciendo el login completo desde UI.
 * - Por ahora, si el usuario se loguea por Swagger, puede pegar el token en localStorage.
 *
 * @returns {string} token o string vacío si no existe
 */
function getAccessToken() {
  return localStorage.getItem("access_token") || "";
}

/**
 * fetchFeedPublicaciones
 * Llama al backend para traer el feed personalizado del usuario autenticado.
 *
 * Backend:
 * - GET /feed/publicaciones
 *
 * @returns {Promise<Array>} Lista de publicaciones del feed
 */
export async function fetchFeedPublicaciones() {
  const token = getAccessToken();

  // Si no hay token, el backend normalmente devolverá 401.
  // Dejamos que la UI maneje el error (ej: mostrar "tenés que loguearte").
  return httpGet("/feed/publicaciones", token);
}

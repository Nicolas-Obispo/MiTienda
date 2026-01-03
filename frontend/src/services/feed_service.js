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

import { httpPost, httpDelete } from "./http_service";

/**
 * toggleLikePublicacion
 * Da o quita like a una publicación (toggle).
 *
 * Backend:
 * - POST /likes/publicaciones/{publicacion_id}
 *
 * @param {number} publicacionId
 * @returns {Promise<any>}
 */
export async function toggleLikePublicacion(publicacionId) {
  const token = getAccessToken();

  return httpPost(
    `/likes/publicaciones/${publicacionId}`,
    null,
    token
  );
}

/**
 * guardarPublicacion
 * Guarda una publicación para el usuario autenticado.
 *
 * Backend:
 * - POST /publicaciones/guardadas
 *
 * @param {number} publicacionId
 * @returns {Promise<any>}
 */
export async function guardarPublicacion(publicacionId) {
  const token = getAccessToken();

  return httpPost(
    "/publicaciones/guardadas",
    { publicacion_id: publicacionId },
    token
  );
}

/**
 * quitarPublicacionGuardada
 * Quita una publicación de los guardados del usuario.
 *
 * Backend:
 * - DELETE /publicaciones/guardadas/{publicacion_id}
 *
 * @param {number} publicacionId
 * @returns {Promise<any>}
 */
export async function quitarPublicacionGuardada(publicacionId) {
  const token = getAccessToken();

  return httpDelete(
    `/publicaciones/guardadas/${publicacionId}`,
    token
  );
}

/**
 * fetchPublicacionesGuardadas
 * Trae las publicaciones guardadas del usuario autenticado.
 *
 * Backend:
 * - GET /publicaciones/guardadas
 *
 * @returns {Promise<Array>} Lista de guardados (ej: [{ publicacion_id, created_at }])
 */
export async function fetchPublicacionesGuardadas() {
  const token = getAccessToken();
  return httpGet("/publicaciones/guardadas", token);
}

/**
 * fetchRankingPublicaciones
 * Trae el ranking de publicaciones ordenadas por score (likes + recencia).
 *
 * Backend:
 * - GET /ranking/publicaciones
 *
 * @returns {Promise<Array>} Lista de publicaciones rankeadas
 */
export async function fetchRankingPublicaciones() {
  const token = getAccessToken();
  return httpGet("/ranking/publicaciones", token);
}

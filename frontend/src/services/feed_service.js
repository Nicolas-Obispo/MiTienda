/**
 * feed_service.js
 * ----------------
 * Service de negocio del Feed (Frontend).
 *
 * RESPONSABILIDAD:
 * - Exponer funciones claras para obtener feed, ranking y guardados.
 * - Centralizar normalización de respuestas sin romper pantallas existentes.
 *
 * ETAPA 56:
 * - Compatibilidad real entre Feed, Ranking y Perfil
 * - Normalización segura de guardados
 */

import { httpGet, httpPost, httpDelete } from "./http_service";

/**
 * getAccessToken
 * Obtiene el token JWT desde localStorage.
 *
 * @returns {string} token o string vacío si no existe
 */
function getAccessToken() {
  return localStorage.getItem("access_token") || "";
}

/**
 * normalizarListaRespuesta
 * Convierte distintas formas de respuesta del backend en una lista.
 */
function normalizarListaRespuesta(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.data)) return data.data;
  if (Array.isArray(data?.resultados)) return data.resultados;
  return [];
}

/**
 * normalizarPublicacionGuardada
 * Convierte distintas variantes del backend en una publicación usable por la UI.
 *
 * IMPORTANTE:
 * - `id` final SIEMPRE debe ser el id de la publicación
 * - `publicacion_id` también se conserva para compatibilidad
 */
function normalizarPublicacionGuardada(item) {
  if (!item || typeof item !== "object") return null;

  // Caso 1: viene anidada en "publicacion"
  if (item.publicacion && typeof item.publicacion.id === "number") {
    return {
      ...item.publicacion,
      id: item.publicacion.id,
      publicacion_id: item.publicacion.id,
      guardada_by_me: true,
      created_at: item.created_at ?? item.publicacion.created_at,
    };
  }

  // Caso 2: viene anidada en "publicacion_data"
  if (item.publicacion_data && typeof item.publicacion_data.id === "number") {
    return {
      ...item.publicacion_data,
      id: item.publicacion_data.id,
      publicacion_id: item.publicacion_data.id,
      guardada_by_me: true,
      created_at: item.created_at ?? item.publicacion_data.created_at,
    };
  }

  // Caso 3: viene plana pero con publicacion_id
  if (typeof item.publicacion_id === "number") {
    return {
      ...item,
      id: item.publicacion_id,
      publicacion_id: item.publicacion_id,
      guardada_by_me: true,
    };
  }

  // Caso 4: ya viene como publicación directa real
  if (typeof item.id === "number") {
    return {
      ...item,
      id: item.id,
      publicacion_id: item.id,
      guardada_by_me: true,
    };
  }

  return null;
}

/**
 * fetchFeedPublicaciones
 * Backend:
 * - GET /feed/publicaciones
 */
export async function fetchFeedPublicaciones() {
  const token = getAccessToken();
  const data = await httpGet("/feed/publicaciones", token);
  return normalizarListaRespuesta(data);
}

/**
 * toggleLikePublicacion
 * Backend:
 * - POST /likes/publicaciones/{publicacion_id}
 */
export async function toggleLikePublicacion(publicacionId) {
  const token = getAccessToken();
  return httpPost(`/likes/publicaciones/${publicacionId}`, null, token);
}

/**
 * guardarPublicacion
 * Backend:
 * - POST /publicaciones/guardadas
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
 * Backend:
 * - DELETE /publicaciones/guardadas/{publicacion_id}
 */
export async function quitarPublicacionGuardada(publicacionId) {
  const token = getAccessToken();
  return httpDelete(`/publicaciones/guardadas/${publicacionId}`, token);
}

/**
 * fetchPublicacionesGuardadas
 * Backend:
 * - GET /publicaciones/guardadas
 *
 * Devuelve publicaciones listas para UI:
 * - id = id de publicación
 * - publicacion_id = id de publicación
 * - guardada_by_me = true
 */
export async function fetchPublicacionesGuardadas() {
  const token = getAccessToken();
  const data = await httpGet("/publicaciones/guardadas", token);

  const lista = normalizarListaRespuesta(data);

  return lista.map(normalizarPublicacionGuardada).filter(Boolean);
}

/**
 * fetchRankingPublicaciones
 * Backend:
 * - GET /ranking/publicaciones
 */
export async function fetchRankingPublicaciones() {
  const token = getAccessToken();
  const data = await httpGet("/ranking/publicaciones", token);
  return normalizarListaRespuesta(data);
}
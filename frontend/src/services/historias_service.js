/**
 * historias_service.js
 * -------------------------------------------------------
 * Service de Historias (MiPlaza).
 *
 * Responsabilidad:
 * - Centralizar llamadas HTTP relacionadas a Historias.
 * - Delegar autenticación a http_service (como el resto del proyecto).
 *
 * Backend real confirmado:
 * - GET /historias/comercios/{comercio_id}
 */

import { httpGet, httpPost } from "./http_service";

/**
 * fetchHistoriasPorComercio
 * Trae las historias activas y no expiradas de un comercio.
 *
 * Backend:
 * - GET /historias/comercios/{comercio_id}
 *
 * @param {number} comercioId - ID del comercio
 * @returns {Promise<Array>}
 */
export async function fetchHistoriasPorComercio(comercioId) {
  if (!comercioId) {
    throw new Error("fetchHistoriasPorComercio: comercioId es requerido");
  }

  return httpGet(`/historias/comercios/${comercioId}`);
}

/**
 * crearHistoria
 * Crea una historia para un comercio.
 *
 * Backend:
 * - POST /historias/comercios/{comercio_id}
 *
 * @param {number} comercioId - ID del comercio
 * @param {object} historiaPayload
 * @param {string} historiaPayload.media_url - URL del contenido (requerido)
 * @param {string} [historiaPayload.expira_en] - ISO datetime (opcional)
 * @param {number|null} [historiaPayload.publicacion_id] - ID publicación (opcional)
 * @param {boolean} [historiaPayload.is_activa] - default true
 * @returns {Promise<object>}
 */
export async function crearHistoria(comercioId, historiaPayload) {
  if (!comercioId) {
    throw new Error("crearHistoria: comercioId es requerido");
  }
  if (!historiaPayload?.media_url) {
    throw new Error("crearHistoria: media_url es requerido");
  }

  const endpoint = `/historias/comercios/${comercioId}`;

  // Mandamos exactamente lo que espera el backend (JSON)
  return httpPost(endpoint, {
    media_url: historiaPayload.media_url,
    expira_en: historiaPayload.expira_en,
    publicacion_id: historiaPayload.publicacion_id ?? null,
    is_activa: historiaPayload.is_activa ?? true,
  });
}

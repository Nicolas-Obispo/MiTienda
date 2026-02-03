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

import { httpGet } from "./http_service";

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

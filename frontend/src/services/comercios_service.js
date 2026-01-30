/**
 * comercios_service.js
 * --------------------
 * ETAPA 40 — Perfil de comercio
 *
 * Responsabilidad:
 * - Llamadas HTTP relacionadas a comercios y su perfil
 *
 * Endpoints reales (Swagger):
 * - GET /comercios/{comercio_id}
 * - GET /publicaciones/comercios/{comercio_id}
 * - GET /historias/comercios/{comercio_id}
 */

import { httpGet } from "./http_service";

/**
 * getComercioById
 * Obtiene un comercio por ID.
 */
export async function getComercioById(comercioId) {
  if (!comercioId) throw new Error("comercioId es requerido");
  return httpGet(`/comercios/${comercioId}`);
}

/**
 * getPublicacionesDeComercio
 * Lista publicaciones por comercio.
 */
export async function getPublicacionesDeComercio(comercioId) {
  if (!comercioId) throw new Error("comercioId es requerido");
  return httpGet(`/publicaciones/comercios/${comercioId}`);
}

/**
 * getHistoriasDeComercio
 * Lista historias por comercio.
 */
export async function getHistoriasDeComercio(comercioId) {
  if (!comercioId) throw new Error("comercioId es requerido");
  return httpGet(`/historias/comercios/${comercioId}`);
}

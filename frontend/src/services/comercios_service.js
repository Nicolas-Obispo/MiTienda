/**
 * comercios_service.js
 * --------------------
 * ETAPA 40 — Perfil de comercio
 * ETAPA 45 — Admin (mis comercios)
 *
 * Responsabilidad:
 * - Llamadas HTTP relacionadas a comercios y su perfil
 *
 * Endpoints reales (Swagger):
 * - GET /comercios/{comercio_id}
 * - GET /publicaciones/comercios/{comercio_id}
 * - GET /historias/comercios/{comercio_id}
 *
 * ETAPA 45 (admin):
 * - GET /comercios/mis
 * - POST /comercios
 * - DELETE /comercios/{comercio_id}
 */

import { httpGet, httpPost, httpDelete, httpPut } from "./http_service";

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

/**
 * getMisComercios
 * ----------------
 * ETAPA 45
 * Obtiene los comercios del usuario logueado.
 *
 * Requiere JWT válido.
 * Endpoint: GET /comercios/mis
 */
export async function getMisComercios() {
  // Leemos el token exactamente como lo usa el sistema actual
  const token = localStorage.getItem("access_token");

  if (!token) {
    throw new Error("No hay sesión activa.");
  }

  return httpGet("/comercios/mis", token);
}

/**
 * crearComercio
 * -------------
 * ETAPA 45
 * Crea un comercio para el usuario logueado.
 *
 * Requiere JWT válido.
 * Endpoint: POST /comercios
 */
export async function crearComercio(payload) {
  const token = localStorage.getItem("access_token");
  if (!token) throw new Error("No hay sesión activa.");

  if (!payload || typeof payload !== "object") {
    throw new Error("payload es requerido");
  }

  return httpPost("/comercios", payload, token);
}

/**
 * desactivarComercio
 * ------------------
 * ETAPA 45
 * Desactiva un comercio (soft delete).
 *
 * Requiere JWT válido.
 * Endpoint: DELETE /comercios/{comercio_id}
 */
export async function desactivarComercio(comercioId) {
  const token = localStorage.getItem("access_token");
  if (!token) throw new Error("No hay sesión activa.");

  if (!comercioId) throw new Error("comercioId es requerido");

  return httpDelete(`/comercios/${comercioId}`, token);
}

/**
 * actualizarComercio
 * ------------------
 * ETAPA 45
 * Edita un comercio del usuario logueado.
 *
 * Requiere JWT válido.
 * Endpoint: PUT /comercios/{comercio_id}
 */
export async function actualizarComercio(comercioId, payload) {
  const token = localStorage.getItem("access_token");
  if (!token) throw new Error("No hay sesión activa.");

  if (!comercioId) throw new Error("comercioId es requerido");
  if (!payload || typeof payload !== "object") {
    throw new Error("payload es requerido");
  }

  return httpPut(`/comercios/${comercioId}`, payload, token);
}

/**
 * reactivarComercio
 * -----------------
 * ETAPA 45
 * Reactiva un comercio (revierte soft delete).
 *
 * Requiere JWT válido.
 * Endpoint: POST /comercios/{comercio_id}/reactivar
 */
export async function reactivarComercio(comercioId) {
  const token = localStorage.getItem("access_token");
  if (!token) throw new Error("No hay sesión activa.");

  if (!comercioId) throw new Error("comercioId es requerido");

  // POST sin body
  return httpPost(`/comercios/${comercioId}/reactivar`, null, token);
}

/**
 * comercios_service.js
 * --------------------
 * ETAPA 40 — Perfil de comercio
 * ETAPA 45 — Admin (mis comercios)
 * ETAPA 48 — Explorar (comercios activos)
 * ETAPA 50 — IA v1 (smart search)
 *
 * Responsabilidad:
 * - Llamadas HTTP relacionadas a comercios y su perfil
 *
 * ETAPA 50:
 * - GET /comercios/activos?q=&smart=&limit=&offset=
 */

import { httpGet, httpPost, httpDelete, httpPut } from "./http_service";

/**
 * getComercioById
 */
export async function getComercioById(comercioId) {
  if (!comercioId) throw new Error("comercioId es requerido");
  return httpGet(`/comercios/${comercioId}`);
}

/**
 * getPublicacionesDeComercio
 */
export async function getPublicacionesDeComercio(comercioId) {
  if (!comercioId) throw new Error("comercioId es requerido");
  return httpGet(`/publicaciones/comercios/${comercioId}`);
}

/**
 * getHistoriasDeComercio
 */
export async function getHistoriasDeComercio(comercioId) {
  if (!comercioId) throw new Error("comercioId es requerido");
  return httpGet(`/historias/comercios/${comercioId}`);
}

/**
 * listarComerciosActivos
 * ----------------------
 * ETAPA 48 — Explorar
 * ETAPA 50 — IA v1 (smart ranking)
 *
 * Endpoint:
 * GET /comercios/activos?q=&smart=&limit=&offset=
 *
 * - smart=false → comportamiento clásico
 * - smart=true → ranking inteligente (IA v1 backend)
 */
export async function listarComerciosActivos({
  q = null,
  smart = false,
  limit = 20,
  offset = 0,
} = {}) {
  if (limit === null || limit === undefined) throw new Error("limit es requerido");
  if (offset === null || offset === undefined) throw new Error("offset es requerido");

  const limitNumber = Number(limit);
  const offsetNumber = Number(offset);

  if (Number.isNaN(limitNumber) || limitNumber < 1) {
    throw new Error("limit debe ser un número >= 1");
  }

  if (Number.isNaN(offsetNumber) || offsetNumber < 0) {
    throw new Error("offset debe ser un número >= 0");
  }

  const params = new URLSearchParams();
  params.set("limit", String(limitNumber));
  params.set("offset", String(offsetNumber));

  // q (búsqueda)
  if (q !== null && q !== undefined) {
    const qNormalizada = String(q).trim();
    if (qNormalizada.length > 0) {
      params.set("q", qNormalizada);
    }
  }

  // ETAPA 50 — smart (IA v1)
  if (smart === true) {
    params.set("smart", "true");
  }

  const queryString = params.toString();
  return httpGet(`/comercios/activos?${queryString}`);
}

/**
 * getMisComercios
 */
export async function getMisComercios() {
  const token = localStorage.getItem("access_token");
  if (!token) throw new Error("No hay sesión activa.");

  return httpGet("/comercios/mis", token);
}

/**
 * crearComercio
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
 */
export async function desactivarComercio(comercioId) {
  const token = localStorage.getItem("access_token");
  if (!token) throw new Error("No hay sesión activa.");

  if (!comercioId) throw new Error("comercioId es requerido");

  return httpDelete(`/comercios/${comercioId}`, token);
}

/**
 * actualizarComercio
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
 */
export async function reactivarComercio(comercioId) {
  const token = localStorage.getItem("access_token");
  if (!token) throw new Error("No hay sesión activa.");

  if (!comercioId) throw new Error("comercioId es requerido");

  return httpPost(`/comercios/${comercioId}/reactivar`, null, token);
}
/**
 * seguidores_service.js
 *
 * ETAPA 60 — Seguidores
 */

import { httpGet, httpPost, httpDelete } from "@core";

function getToken() {
  return localStorage.getItem("access_token") || localStorage.getItem("token");
}

export async function seguirEspacio(comercioId) {
  return await httpPost(`/seguidores/espacios/${comercioId}`, null, getToken());
}

export async function dejarDeSeguirEspacio(comercioId) {
  return await httpDelete(`/seguidores/espacios/${comercioId}`, getToken());
}

export async function obtenerEstadoSeguimiento(comercioId) {
  return await httpGet(`/seguidores/espacios/${comercioId}/estado`, getToken());
}

export async function obtenerMisEspaciosSeguidos({
  lat = null,
  lng = null,
} = {}) {
  const params = new URLSearchParams();

  if (lat !== null && lat !== undefined) {
    params.set("lat", String(lat));
  }

  if (lng !== null && lng !== undefined) {
    params.set("lng", String(lng));
  }

  const queryString = params.toString();
  const url = queryString
    ? `/seguidores/mis-espacios?${queryString}`
    : "/seguidores/mis-espacios";

  return await httpGet(url, getToken());
}

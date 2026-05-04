/**
 * seguidores_service.js
 *
 * ETAPA 60 — Seguidores
 */

import { httpGet, httpPost, httpDelete } from "./http_service";

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

export async function obtenerMisEspaciosSeguidos() {
  return await httpGet("/seguidores/mis-espacios", getToken());
}
import { httpGet, httpPost } from "@core";

export function crearDenunciaContenido(payload, token) {
  return httpPost("/moderacion/denuncias", payload, token);
}

function buildDenunciasQuery(filters = {}, cursor = null) {
  const params = new URLSearchParams();
  params.set("limit", String(filters.limit ?? 20));
  if (cursor) params.set("cursor", cursor);

  for (const key of [
    "estado",
    "recurso_tipo",
    "recurso_id",
    "motivo",
    "desde",
    "hasta",
  ]) {
    const value = filters[key];
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  }

  return params.toString();
}

export function listarDenunciasAdministrativas({
  filters,
  cursor = null,
  token,
  signal,
}) {
  const query = buildDenunciasQuery(filters, cursor);
  return httpGet(`/moderacion/denuncias?${query}`, token, { signal });
}

export function obtenerDenunciaAdministrativa({ reportId, token, signal }) {
  return httpGet(`/moderacion/denuncias/${Number(reportId)}`, token, { signal });
}

export function listarDecisionesModeracion({ reportId, token, signal }) {
  return httpGet(`/moderacion/denuncias/${Number(reportId)}/decisiones`, token, { signal });
}

export function crearDecisionModeracion({ reportId, payload, token }) {
  return httpPost(`/moderacion/denuncias/${Number(reportId)}/decisiones`, payload, token);
}

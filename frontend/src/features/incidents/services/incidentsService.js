import { httpGet, httpPost } from "@core";

function buildQuery(filters = {}, cursor = null) {
  const params = new URLSearchParams({ limit: String(filters.limit ?? 20) });
  if (cursor) params.set("cursor", String(cursor));
  for (const key of ["status", "severity", "owner_usuario_id"]) {
    if (filters[key] !== undefined && filters[key] !== null && filters[key] !== "") {
      params.set(key, String(filters[key]));
    }
  }
  return params.toString();
}

export function listOperationalIncidents({ filters, cursor, token, signal }) {
  return httpGet(`/administracion/incidentes?${buildQuery(filters, cursor)}`, token, { signal });
}

export function getOperationalIncident({ publicId, token, signal }) {
  return httpGet(`/administracion/incidentes/${encodeURIComponent(publicId)}`, token, { signal });
}

export function getOperationalIncidentTimeline({ publicId, token, signal }) {
  return httpGet(`/administracion/incidentes/${encodeURIComponent(publicId)}/eventos`, token, { signal });
}

export function openOperationalIncident({ payload, token }) {
  return httpPost("/administracion/incidentes", payload, token);
}

export function actOnOperationalIncident({ publicId, payload, token }) {
  return httpPost(`/administracion/incidentes/${encodeURIComponent(publicId)}/acciones`, payload, token);
}

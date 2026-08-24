import { httpGet } from "@core";

export function getOperationalStatus({ token, signal }) {
  return httpGet("/administracion/operaciones/estado", token, { signal });
}

export function inspectOperationalResource({ resourceType, resourceId, token, signal }) {
  return httpGet(
    `/administracion/operaciones/recursos/${encodeURIComponent(resourceType)}/${encodeURIComponent(resourceId)}/integridad`,
    token,
    { signal },
  );
}

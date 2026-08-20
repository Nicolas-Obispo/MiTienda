import { httpGet } from "@core";

export async function fetchMyAdministrativeCapabilities(tokenJWT) {
  if (!tokenJWT) {
    throw new Error("Falta token para consultar capacidades administrativas");
  }

  return httpGet("/administracion/me/capacidades", tokenJWT);
}

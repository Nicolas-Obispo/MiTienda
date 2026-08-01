import { httpPost } from "@core";

export function crearDenunciaContenido(payload, token) {
  return httpPost("/moderacion/denuncias", payload, token);
}

import { httpGet } from "@core";

export async function listarRubros() {
  const data = await httpGet("/rubros/");

  return Array.isArray(data) ? data : [];
}

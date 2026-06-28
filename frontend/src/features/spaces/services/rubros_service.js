import { httpGet } from "@core";

export async function listarRubros() {
  const data = await httpGet("/rubros/");

  return Array.isArray(data) ? data : [];
}

export async function listarEspecialidadesPorRubro(rubroId) {
  const id = Number(rubroId);
  if (!id) return [];

  const data = await httpGet(`/rubros/${id}/especialidades`);

  return Array.isArray(data) ? data : [];
}

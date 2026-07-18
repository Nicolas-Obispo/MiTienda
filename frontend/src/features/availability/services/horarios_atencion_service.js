import { httpGet, httpPut } from "@core";

function getToken() {
  return (
    localStorage.getItem("access_token") ||
    localStorage.getItem("token") ||
    ""
  );
}

export async function obtenerHorariosAtencion(comercioId) {
  if (!comercioId) throw new Error("comercioId es requerido");

  const token = getToken();
  return httpGet(`/comercios/${comercioId}/horarios`, token || null);
}

export async function reemplazarHorariosAtencion({ comercioId, franjas }) {
  if (!comercioId) throw new Error("comercioId es requerido");
  if (!Array.isArray(franjas)) throw new Error("franjas debe ser una lista");

  const token = getToken();
  if (!token) throw new Error("No hay sesion activa.");

  return httpPut(
    `/comercios/${comercioId}/horarios`,
    { franjas },
    token
  );
}

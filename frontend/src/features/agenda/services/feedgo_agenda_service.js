import { httpGet, httpPatch, httpPost } from "@core";

function getToken() {
  return (
    localStorage.getItem("access_token") ||
    localStorage.getItem("token") ||
    ""
  );
}

function requireToken() {
  const token = getToken();
  if (!token) throw new Error("No hay sesion activa.");
  return token;
}

function requireComercioId(comercioId) {
  if (!comercioId || Number.isNaN(Number(comercioId))) {
    throw new Error("comercioId es requerido");
  }

  return Number(comercioId);
}

function agendaBasePath(comercioId) {
  return `/feedgo-agenda/comercios/${requireComercioId(comercioId)}`;
}

function buildElementosQuery({
  inicio = null,
  fin = null,
  estado = null,
  tipo = null,
  comercioId = null,
} = {}) {
  const params = new URLSearchParams();

  if (inicio) params.set("inicio", inicio);
  if (fin) params.set("fin", fin);
  if (estado) params.set("estado", estado);
  if (tipo) params.set("tipo", tipo);
  if (comercioId) params.set("comercio_id", Number(comercioId));

  const query = params.toString();
  return query ? `?${query}` : "";
}

export function obtenerHttpStatus(error) {
  const match = String(error?.message || "").match(/HTTP\s+(\d+)/);
  return match ? Number(match[1]) : null;
}

export async function obtenerContextoAgenda(comercioId) {
  return httpGet(`${agendaBasePath(comercioId)}/contexto`, requireToken());
}

export async function obtenerOCrearContextoAgenda(comercioId) {
  return httpPost(`${agendaBasePath(comercioId)}/contexto`, null, requireToken());
}

export async function listarElementosAgenda({
  comercioId,
  inicio = null,
  fin = null,
  estado = null,
  tipo = null,
}) {
  const query = buildElementosQuery({ inicio, fin, estado, tipo });
  return httpGet(`${agendaBasePath(comercioId)}/elementos${query}`, requireToken());
}

export async function listarElementosAgendaGeneral({
  inicio = null,
  fin = null,
  estado = null,
  tipo = null,
  comercioId = null,
} = {}) {
  const query = buildElementosQuery({
    inicio,
    fin,
    estado,
    tipo,
    comercioId,
  });
  return httpGet(`/feedgo-agenda/mis/elementos${query}`, requireToken());
}

export async function crearElementoAgenda({ comercioId, payload }) {
  if (!payload || typeof payload !== "object") {
    throw new Error("payload es requerido");
  }

  return httpPost(
    `${agendaBasePath(comercioId)}/elementos`,
    payload,
    requireToken()
  );
}

export async function actualizarElementoAgenda({ comercioId, elementoId, payload }) {
  if (!elementoId) throw new Error("elementoId es requerido");
  if (!payload || typeof payload !== "object") {
    throw new Error("payload es requerido");
  }

  return httpPatch(
    `${agendaBasePath(comercioId)}/elementos/${elementoId}`,
    payload,
    requireToken()
  );
}

export async function cambiarEstadoElementoAgenda({
  comercioId,
  elementoId,
  versionEsperada,
  estado,
}) {
  if (!elementoId) throw new Error("elementoId es requerido");
  if (!versionEsperada) throw new Error("versionEsperada es requerida");
  if (!estado) throw new Error("estado es requerido");

  return httpPatch(
    `${agendaBasePath(comercioId)}/elementos/${elementoId}/estado`,
    {
      version_esperada: Number(versionEsperada),
      estado,
    },
    requireToken()
  );
}

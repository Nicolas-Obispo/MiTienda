/**
 * historias_service.js
 * -------------------------------------------------------
 * Service de Historias (MiPlaza).
 *
 * Objetivo:
 * - Centralizar llamadas HTTP relacionadas a Historias.
 * - Asegurar Authorization en endpoints protegidos (vistas).
 *
 * Backend confirmado:
 * - GET  /historias/comercios/{comercio_id}
 * - POST /historias/comercios/{comercio_id}
 * - POST /historias/{historia_id}/vistas   (PROTEGIDO)
 */

// Base URL del backend (fallback seguro)
function getApiBaseUrl() {
  return (
    import.meta?.env?.VITE_API_BASE_URL ||
    import.meta?.env?.VITE_BACKEND_URL ||
    "http://127.0.0.1:8000"
  );
}

function getAccessToken() {
  return localStorage.getItem("access_token");
}

async function requestJson(path, { method = "GET", body = null, auth = false } = {}) {
  const url = `${getApiBaseUrl()}${path}`;

  const headers = {
    Accept: "application/json",
  };

  if (body !== null) {
    headers["Content-Type"] = "application/json";
  }

  if (auth) {
    const token = getAccessToken();
    if (!token) {
      // Si no hay token, es consistente tirar error antes del request
      throw new Error("No authenticated: falta access_token en localStorage.");
    }
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    method,
    headers,
    body: body !== null ? JSON.stringify(body) : undefined,
  });

  // Intentamos parsear JSON si existe
  let data = null;
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    data = await response.json().catch(() => null);
  }

  if (!response.ok) {
    const detail =
      data?.detail ||
      data?.message ||
      `HTTP ${response.status} ${response.statusText}`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  return data;
}

/**
 * fetchHistoriasPorComercio
 * Trae historias activas y no expiradas de un comercio.
 *
 * Backend:
 * - GET /historias/comercios/{comercio_id}
 */
export async function fetchHistoriasPorComercio(comercioId) {
  if (!comercioId) {
    throw new Error("fetchHistoriasPorComercio: comercioId es requerido");
  }

  return requestJson(`/historias/comercios/${comercioId}`, { method: "GET" });
}

/**
 * crearHistoria
 * Crea una historia para un comercio.
 *
 * Backend:
 * - POST /historias/comercios/{comercio_id}
 *
 * Nota:
 * - Si tu backend exige auth para crear historias, poné auth:true.
 *   (si hoy no lo exige, queda en false para no romper)
 */
export async function crearHistoria(comercioId, historiaPayload) {
  if (!comercioId) {
    throw new Error("crearHistoria: comercioId es requerido");
  }
  if (!historiaPayload?.media_url) {
    throw new Error("crearHistoria: media_url es requerido");
  }
  if (!historiaPayload?.expira_en) {
    throw new Error("crearHistoria: expira_en es requerido");
  }

  return requestJson(`/historias/comercios/${comercioId}`, {
    method: "POST",
    body: {
      media_url: historiaPayload.media_url,
      expira_en: historiaPayload.expira_en,
      publicacion_id: historiaPayload.publicacion_id ?? null,
      is_activa: historiaPayload.is_activa ?? true,
    },
    auth: false, // <- si tu POST de crear historia es protegido, cambiá a true
  });
}

/**
 * marcarHistoriaVista
 * Marca una historia como vista por el usuario autenticado.
 *
 * Backend:
 * - POST /historias/{historia_id}/vistas
 *
 * ESTE ENDPOINT ES PROTEGIDO → auth: true
 */
export async function marcarHistoriaVista(historiaId) {
  if (!historiaId) {
    throw new Error("marcarHistoriaVista: historiaId es requerido");
  }

  // endpoint sin body
  return requestJson(`/historias/${historiaId}/vistas`, {
    method: "POST",
    body: {}, // mandamos {} para evitar problemas con algunos servidores
    auth: true,
  });
}

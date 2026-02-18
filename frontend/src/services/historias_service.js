/**
 * historias_service.js
 * -------------------------------------------------------
 * Service de Historias (MiPlaza).
 *
 * Objetivo:
 * - Centralizar llamadas HTTP relacionadas a Historias.
 * - Asegurar Authorization en endpoints protegidos (vistas).
 * - En GET públicos, mandar token SI EXISTE (para vista_by_me real).
 *
 * Backend confirmado:
 * - GET  /historias/comercios/{comercio_id}  (PÚBLICO + token opcional)
 * - POST /historias/comercios/{comercio_id}
 * - POST /historias/{historia_id}/vistas   (PROTEGIDO, idempotente)
 *
 * ETAPA 47:
 * - GET /historias/bar (PÚBLICO + token opcional) -> items listos para HistoriasBar
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

/**
 * requestJson
 * Helper genérico para requests al backend.
 *
 * auth:
 * - false  -> no manda Authorization
 * - true   -> exige token (si no hay, tira error)
 * - "optional" -> manda token SOLO si existe (no falla si no hay)
 *
 * - Si body=null → NO setea Content-Type y NO manda body
 */
async function requestJson(
  path,
  { method = "GET", body = null, auth = false } = {}
) {
  const url = `${getApiBaseUrl()}${path}`;

  const headers = {
    Accept: "application/json",
  };

  // Solo seteamos Content-Type si realmente vamos a enviar body
  if (body !== null) {
    headers["Content-Type"] = "application/json";
  }

  // Authorization según modo
  if (auth === true) {
    const token = getAccessToken();
    if (!token) {
      throw new Error("No authenticated: falta access_token en localStorage.");
    }
    headers.Authorization = `Bearer ${token}`;
  }

  if (auth === "optional") {
    const token = getAccessToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }

  const response = await fetch(url, {
    method,
    headers,
    // Si body es null, NO mandamos body
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

    throw new Error(
      typeof detail === "string" ? detail : JSON.stringify(detail)
    );
  }

  return data;
}

/**
 * fetchHistoriasBarItems (ETAPA 47)
 * Trae items listos para renderizar en HistoriasBar.
 *
 * Backend:
 * - GET /historias/bar (PÚBLICO + token opcional)
 *
 * Importante:
 * - Si hay token, el backend devuelve pendientes reales por usuario.
 * - Si NO hay token, pendientes = cantidad (todo queda "no visto").
 */
export async function fetchHistoriasBarItems() {
  return requestJson("/historias/bar", {
    method: "GET",
    auth: "optional",
  });
}

/**
 * fetchHistoriasPorComercio
 * Trae historias activas y no expiradas de un comercio.
 *
 * Backend:
 * - GET /historias/comercios/{comercio_id}
 *
 * Importante (ETAPA 44):
 * - Es público, pero si hay token lo mandamos para obtener vista_by_me real.
 */
export async function fetchHistoriasPorComercio(comercioId) {
  if (!comercioId) {
    throw new Error("fetchHistoriasPorComercio: comercioId es requerido");
  }

  return requestJson(`/historias/comercios/${comercioId}`, {
    method: "GET",
    auth: "optional", // <- clave: si hay token, backend calcula vista_by_me
  });
}

/**
 * crearHistoria
 * Crea una historia para un comercio.
 *
 * Backend:
 * - POST /historias/comercios/{comercio_id}
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
 * PROTEGIDO → auth: true
 */
export async function marcarHistoriaVista(historiaId) {
  if (!historiaId) {
    throw new Error("marcarHistoriaVista: historiaId es requerido");
  }

  return requestJson(`/historias/${historiaId}/vistas`, {
    method: "POST",
    body: null, // POST vacío
    auth: true,
  });
}

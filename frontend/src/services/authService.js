/**
 * authService.js
 * Responsabilidad:
 * - Centralizar toda la comunicación de autenticación con el backend
 */

const API_BASE_URL = "http://127.0.0.1:8000";

export async function loginUsuario({ email, password }) {
  try {
    const response = await fetch(`${API_BASE_URL}/usuarios/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) throw new Error("Credenciales inválidas");

    const data = await response.json();
    const token = data.access_token || data.token;
    if (!token) throw new Error("El backend no devolvió token");
    return token;
  } catch (error) {
    throw new Error(error.message || "Error al iniciar sesión");
  }
}

export async function logoutUsuario(tokenJWT) {
  if (!tokenJWT) return;

  const response = await fetch(`${API_BASE_URL}/usuarios/logout`, {
    method: "POST",
    headers: { Authorization: `Bearer ${tokenJWT}` },
  });

  if (!response.ok) {
    throw new Error("Error al cerrar sesión");
  }
}

/**
 * getMe
 * ✅ Endpoint real según Swagger: GET /usuarios/me
 * Devuelve el usuario logueado (id, email, etc.)
 */
export async function getMe(tokenJWT) {
  if (!tokenJWT) throw new Error("Falta token para getMe");

  const response = await fetch(`${API_BASE_URL}/usuarios/me`, {
    headers: { Authorization: `Bearer ${tokenJWT}` },
  });

  if (!response.ok) {
    let detail = "";
    try {
      const data = await response.json();
      detail = data?.detail ? String(data.detail) : "";
    } catch {
      // ignore
    }
    throw new Error(detail || "No se pudo obtener mi perfil (/usuarios/me)");
  }

  return response.json();
}

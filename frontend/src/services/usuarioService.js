/**
 * usuarioService.js
 * Responsabilidad:
 * - Obtener información del usuario autenticado
 * - Comunicarse con endpoints protegidos del backend
 */

const API_BASE_URL = "http://127.0.0.1:8000";

/**
 * obtenerUsuarioActual
 * Consulta el endpoint /usuarios/me usando el token JWT.
 *
 * @param {string} tokenJWT
 * @returns {Promise<Object>} datos del usuario
 */
export async function obtenerUsuarioActual(tokenJWT) {
  const response = await fetch(`${API_BASE_URL}/usuarios/me`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${tokenJWT}`,
    },
  });

  if (!response.ok) {
    throw new Error("Token inválido o sesión expirada");
  }

  return response.json();
}

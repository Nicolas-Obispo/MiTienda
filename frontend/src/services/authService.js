/**
 * authService.js
 * Responsabilidad:
 * - Centralizar toda la comunicación de autenticación con el backend
 * - Exponer funciones claras y reutilizables (login, logout, etc.)
 *
 * NOTA:
 * - Este archivo NO maneja UI
 * - Solo se encarga de llamadas HTTP y manejo de datos
 */

// URL base del backend (en desarrollo)
const API_BASE_URL = "http://127.0.0.1:8000";

/**
 * loginUsuario
 * Envía credenciales al backend y obtiene un JWT si son válidas.
 *
 * @param {Object} credenciales
 * @param {string} credenciales.email - Email del usuario
 * @param {string} credenciales.password - Password del usuario
 *
 * @returns {Promise<string>} token JWT
 * @throws Error si las credenciales son inválidas o hay error de red
 */
export async function loginUsuario({ email, password }) {
  try {
    const response = await fetch(`${API_BASE_URL}/usuarios/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        password,
      }),
    });

    // Si el backend responde con error (401, 400, etc.)
    if (!response.ok) {
      throw new Error("Credenciales inválidas");
    }

    const data = await response.json();

        // El backend devuelve { access_token: "..." }
        const token = data.access_token || data.token;
    if (!token) throw new Error("El backend no devolvió token");
    return token;

  } catch (error) {
    // Normalizamos el error para la UI
    throw new Error(error.message || "Error al iniciar sesión");
  }
}

/**
 * logoutUsuario
 * Informa al backend que el token actual debe ser revocado.
 *
 * @param {string} tokenJWT
 * @returns {Promise<void>}
 */
export async function logoutUsuario(tokenJWT) {
  if (!tokenJWT) return;

  const response = await fetch("http://127.0.0.1:8000/usuarios/logout", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${tokenJWT}`,
    },
  });

  if (!response.ok) {
    throw new Error("Error al cerrar sesión");
  }
}

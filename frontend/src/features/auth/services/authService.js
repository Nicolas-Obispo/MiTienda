/**
 * authService.js
 * Responsabilidad:
 * - Centralizar toda la comunicación de autenticación con el backend.
 * - Usar http_service como única capa HTTP de infraestructura.
 */

import { httpGet, httpPost } from "@core";

export async function loginUsuario({ email, password }) {
  try {
    const data = await httpPost("/usuarios/login", {
      email,
      password,
    });

    const token = data.access_token || data.token;

    if (!token) {
      throw new Error("El backend no devolvió token");
    }

    return token;
  } catch (error) {
    throw new Error(error.message || "Error al iniciar sesión");
  }
}

export async function logoutUsuario(tokenJWT) {
  if (!tokenJWT) return;

  await httpPost(
    "/usuarios/logout",
    null,
    tokenJWT
  );
}

/**
 * getMe
 * Endpoint real: GET /usuarios/me
 * Devuelve el usuario logueado.
 */
export async function getMe(tokenJWT) {
  if (!tokenJWT) {
    throw new Error("Falta token para getMe");
  }

  return httpGet("/usuarios/me", tokenJWT);
}

/**
 * registrarUsuario
 * Crea un nuevo usuario usando /usuarios/registrar.
 */
export async function registrarUsuario({ email, password }) {
  try {
    return await httpPost("/usuarios/registrar", {
      email,
      password,
    });
  } catch (error) {
    throw new Error(error.message || "Error al registrar usuario");
  }
}
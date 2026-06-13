/**
 * usuarioService.js
 * Responsabilidad:
 * - Obtener información del usuario autenticado.
 * - Cambiar modo activo del usuario.
 * - Comunicarse con endpoints protegidos usando http_service.
 */

import { httpGet, httpPost } from "@core";

export async function obtenerUsuarioActual(tokenJWT) {
  if (!tokenJWT) {
    throw new Error("Falta token para obtener usuario actual");
  }

  return httpGet("/usuarios/me", tokenJWT);
}

export async function cambiarModoUsuario(tokenJWT, modo) {
  if (!tokenJWT) {
    throw new Error("Falta token para cambiar modo de usuario");
  }

  return httpPost(
    "/usuarios/modo",
    { modo },
    tokenJWT
  );
}

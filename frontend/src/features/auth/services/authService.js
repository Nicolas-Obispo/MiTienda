/**
 * authService.js
 * Responsabilidad:
 * - Centralizar toda la comunicación de autenticación con el backend.
 * - Usar http_service como única capa HTTP de infraestructura.
 */

import { httpGet, httpPatch, httpPost } from "@core";

export const REGISTRATION_EMAIL_UNAVAILABLE = "registration_email_unavailable";
export const EMAIL_VERIFICATION_INVALID = "email_verification_invalid";
export const EMAIL_VERIFICATION_RATE_LIMITED = "email_verification_rate_limited";
export const PASSWORD_RESET_INVALID = "password_reset_invalid";
export const CURRENT_PASSWORD_INCORRECT = "current_password_incorrect";
export const CURRENT_PASSWORD_RATE_LIMITED = "current_password_rate_limited";
export const PHONE_VERIFICATION_INVALID = "phone_verification_invalid";
export const PHONE_VERIFICATION_RATE_LIMITED = "phone_verification_rate_limited";

export async function comprobarDisponibilidadEmail(email, options = {}) {
  return httpPost(
    "/usuarios/email-disponibilidad",
    { email },
    null,
    { signal: options.signal }
  );
}

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
 * actualizarPerfilUsuario
 * Edita campos basicos permitidos del usuario autenticado.
 */
export async function actualizarPerfilUsuario(tokenJWT, payload) {
  if (!tokenJWT) {
    throw new Error("Falta token para actualizar perfil");
  }

  return httpPatch("/usuarios/me", payload, tokenJWT);
}

export async function solicitarVerificacionTelefono(tokenJWT) {
  try {
    return await httpPost(
      "/usuarios/me/telefono-verificacion/reenvio",
      null,
      tokenJWT
    );
  } catch (error) {
    const safeError = new Error("No podés pedir otro código todavía.");
    safeError.code = error?.status === 400
      ? PHONE_VERIFICATION_RATE_LIMITED
      : "phone_verification_technical_error";
    throw safeError;
  }
}

export async function confirmarVerificacionTelefono(tokenJWT, { challengeId, code }) {
  try {
    return await httpPost(
      "/usuarios/me/telefono-verificacion/confirmar",
      { challenge_id: challengeId, code },
      tokenJWT
    );
  } catch (error) {
    const safeError = new Error(
      "Este código no es válido o venció. Pedí uno nuevo para continuar."
    );
    safeError.code = error?.status === 400
      ? PHONE_VERIFICATION_INVALID
      : "phone_verification_technical_error";
    throw safeError;
  }
}

/**
 * registrarUsuario
 * Crea un nuevo usuario usando /usuarios/registrar.
 */
export async function registrarUsuario({
  email,
  password,
  aceptaTerminos,
  aceptaPrivacidad,
}) {
  try {
    return await httpPost("/usuarios/registrar", {
      email,
      password,
      acepta_terminos: aceptaTerminos,
      acepta_privacidad: aceptaPrivacidad,
    });
  } catch (error) {
    if (error?.status === 409) {
      const conflict = new Error("Este correo ya está registrado en FeedGo.");
      conflict.code = REGISTRATION_EMAIL_UNAVAILABLE;
      throw conflict;
    }
    throw new Error(error.message || "Error al registrar usuario");
  }
}

export async function confirmarEmail(token) {
  try {
    return await httpPost("/usuarios/email-verificacion/confirmar", { token });
  } catch (error) {
    const safeError = new Error("No pudimos verificar el enlace.");
    safeError.code = error?.status === 400
      ? EMAIL_VERIFICATION_INVALID
      : "email_verification_technical_error";
    throw safeError;
  }
}

export async function reenviarVerificacionEmail(tokenJWT) {
  try {
    return await httpPost(
      "/usuarios/me/email-verificacion/reenvio",
      null,
      tokenJWT
    );
  } catch (error) {
    const safeError = new Error("No pudimos enviar el enlace.");
    safeError.code = error?.status === 429
      ? EMAIL_VERIFICATION_RATE_LIMITED
      : "email_verification_delivery_failed";
    throw safeError;
  }
}

export function extraerTokenVerificacionDelFragmento(
  locationObject = window.location,
  historyObject = window.history
) {
  const fragment = locationObject.hash.startsWith("#")
    ? locationObject.hash.slice(1)
    : locationObject.hash;
  const token = new URLSearchParams(fragment).get("token");
  if (locationObject.hash) {
    historyObject.replaceState(
      historyObject.state,
      "",
      `${locationObject.pathname}${locationObject.search}`
    );
  }
  return token || null;
}

export async function solicitarRecuperacionPassword(email) {
  try {
    return await httpPost("/usuarios/password/recuperacion", { email });
  } catch {
    // La presentación pública permanece uniforme incluso ante degradación.
    return {
      message: "Si ese usuario está registrado, te vamos a enviar un enlace para crear una nueva contraseña.",
    };
  }
}

export async function restablecerPassword({ token, newPassword }) {
  try {
    return await httpPost("/usuarios/password/restablecer", {
      token,
      new_password: newPassword,
    });
  } catch (error) {
    const safeError = new Error("No pudimos actualizar la contraseña.");
    safeError.code = error?.status === 400
      ? PASSWORD_RESET_INVALID
      : "password_reset_technical_error";
    throw safeError;
  }
}

export async function cambiarPasswordAutenticado(
  tokenJWT,
  { currentPassword, newPassword }
) {
  try {
    return await httpPatch(
      "/usuarios/me/password",
      { current_password: currentPassword, new_password: newPassword },
      tokenJWT
    );
  } catch (error) {
    const safeError = new Error("No pudimos actualizar la contraseña.");
    safeError.code = error?.status === 429
      ? CURRENT_PASSWORD_RATE_LIMITED
      : error?.status === 400
        ? CURRENT_PASSWORD_INCORRECT
        : "current_password_technical_error";
    throw safeError;
  }
}

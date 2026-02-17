// frontend/src/context/AuthContext.jsx
import { createContext, useEffect, useMemo, useState } from "react";
import { getMe, logoutUsuario } from "../services/authService";

export const AuthContext = createContext(null);

/**
 * AuthProvider
 * - Hidratación SINCRÓNICA desde localStorage (evita rebote)
 * - Contrato intacto: accessToken + estaAutenticado + login(token) + logout()
 * - Trae usuario desde GET /usuarios/me
 *
 * MEJORA UX:
 * - Si /usuarios/me responde 401 (token inválido/expirado/revocado):
 *   limpiamos sesión local SIN ensuciar consola con "error".
 */
export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(() => {
    const token = localStorage.getItem("access_token");
    return token && token !== "null" && token !== "undefined" ? token : null;
  });

  const [estaAutenticado, setEstaAutenticado] = useState(() => {
    const token = localStorage.getItem("access_token");
    return Boolean(token && token !== "null" && token !== "undefined");
  });

  const [usuario, setUsuario] = useState(null);
  const [isCargandoUsuario, setIsCargandoUsuario] = useState(false);

  function limpiarSesionLocal() {
    // Centralizamos limpieza para evitar estados inconsistentes
    localStorage.removeItem("access_token");
    setAccessToken(null);
    setEstaAutenticado(false);
    setUsuario(null);
  }

  function login(token) {
    if (!token || typeof token !== "string") return;
    localStorage.setItem("access_token", token);
    setAccessToken(token);
    setEstaAutenticado(true);
    // usuario se carga por effect (abajo)
  }

  async function logout() {
    try {
      // Logout real en backend (revoca token) si hay token
      if (accessToken) {
        await logoutUsuario(accessToken);
      }
    } catch (error) {
      // Si falla el logout remoto, igual limpiamos local (no bloquea al usuario)
      console.warn("Logout remoto falló (se limpia sesión local igual):", error);
    } finally {
      limpiarSesionLocal();
    }
  }

  async function refrescarUsuario() {
    if (!accessToken) {
      setUsuario(null);
      return;
    }

    try {
      setIsCargandoUsuario(true);
      const me = await getMe(accessToken);
      setUsuario(me || null);
    } catch (error) {
      // Detectamos 401 de forma robusta (según cómo authService construya el error)
      const msg = String(error?.message || "");
      const is401 =
        msg.includes("HTTP 401") ||
        msg.includes("401") ||
        msg.toLowerCase().includes("token inválido") ||
        msg.toLowerCase().includes("token invalido") ||
        msg.toLowerCase().includes("expirado") ||
        msg.toLowerCase().includes("unauthorized");

      if (is401) {
        // 401 no es “error”: es sesión vencida/revocada -> limpieza silenciosa
        limpiarSesionLocal();
        return;
      }

      // Otros errores sí interesan (backend caído, CORS, etc.)
      console.error("Error obteniendo /usuarios/me:", error);
    } finally {
      setIsCargandoUsuario(false);
    }
  }

  useEffect(() => {
    if (!accessToken) {
      setUsuario(null);
      return;
    }
    refrescarUsuario();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  const value = useMemo(
    () => ({
      accessToken,
      estaAutenticado,
      usuario,
      isCargandoUsuario,
      login,
      logout,
      refrescarUsuario,
    }),
    [accessToken, estaAutenticado, usuario, isCargandoUsuario]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

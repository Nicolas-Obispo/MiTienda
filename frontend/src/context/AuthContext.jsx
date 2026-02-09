// frontend/src/context/AuthContext.jsx
import { createContext, useEffect, useMemo, useState } from "react";
import { getMe, logoutUsuario } from "../services/authService";

export const AuthContext = createContext(null);

/**
 * AuthProvider
 * - Hidratación SINCRÓNICA desde localStorage (evita rebote)
 * - Contrato intacto: accessToken + estaAutenticado + login(token) + logout()
 * - ✅ Definitivo: trae usuario desde GET /usuarios/me (según Swagger)
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

  function login(token) {
    if (!token || typeof token !== "string") return;
    localStorage.setItem("access_token", token);
    setAccessToken(token);
    setEstaAutenticado(true);
    // usuario se carga por effect (abajo)
  }

  async function logout() {
    try {
      await logoutUsuario(accessToken);
    } catch (error) {
      console.error("Error al cerrar sesión:", error);
    } finally {
      localStorage.removeItem("access_token");
      setAccessToken(null);
      setEstaAutenticado(false);
      setUsuario(null);
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
      console.error("Error obteniendo /usuarios/me:", error);

      // ✅ Definitivo: token inválido => limpiamos sesión local
      localStorage.removeItem("access_token");
      setAccessToken(null);
      setEstaAutenticado(false);
      setUsuario(null);
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

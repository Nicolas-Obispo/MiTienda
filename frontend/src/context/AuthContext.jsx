// frontend/src/context/AuthContext.jsx
import { createContext, useMemo, useState } from "react";
import { logoutUsuario } from "../services/authService";

export const AuthContext = createContext(null);

/**
 * AuthProvider
 * - Hidratación SINCRÓNICA desde localStorage (evita rebote /login -> /feed en pestaña nueva)
 * - Mantiene tu contrato actual: accessToken + estaAutenticado
 */
export function AuthProvider({ children }) {
  // ✅ Hidratar token en el primer render (clave para que no rebote)
  const [accessToken, setAccessToken] = useState(() => {
    const token = localStorage.getItem("access_token");
    return token && token !== "null" && token !== "undefined" ? token : null;
  });

  const [estaAutenticado, setEstaAutenticado] = useState(() => {
    const token = localStorage.getItem("access_token");
    return Boolean(token && token !== "null" && token !== "undefined");
  });

  function login(token) {
    if (!token || typeof token !== "string") return;
    localStorage.setItem("access_token", token);
    setAccessToken(token);
    setEstaAutenticado(true);
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
    }
  }

  const value = useMemo(
    () => ({ accessToken, estaAutenticado, login, logout }),
    [accessToken, estaAutenticado]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

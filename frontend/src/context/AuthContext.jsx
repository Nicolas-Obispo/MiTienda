import { createContext, useEffect, useMemo, useState } from "react";
import { logoutUsuario } from "../services/authService";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(null);
  const [estaAutenticado, setEstaAutenticado] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      setAccessToken(token);
      setEstaAutenticado(true);
    }
  }, []);

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

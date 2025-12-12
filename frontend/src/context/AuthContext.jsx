import { createContext, useContext, useEffect, useState } from "react";
import { obtenerUsuarioActual } from "../services/usuarioService";
import { logoutUsuario } from "../services/authService";

/**
 * AuthContext
 * Contexto global de autenticación
 */
const AuthContext = createContext(null);

/**
 * AuthProvider
 * Provee el estado de autenticación a toda la app
 */
export function AuthProvider({ children }) {
  const [authToken, setAuthToken] = useState(null);
  const [usuarioActual, setUsuarioActual] = useState(null);
  const [authInicializado, setAuthInicializado] = useState(false);

  /**
   * Inicializa la sesión al cargar la app
   */
  useEffect(() => {
    async function inicializarAuth() {
      const tokenGuardado = localStorage.getItem("authToken");

      if (!tokenGuardado) {
        setAuthInicializado(true);
        return;
      }

      try {
        const usuario = await obtenerUsuarioActual(tokenGuardado);
        setAuthToken(tokenGuardado);
        setUsuarioActual(usuario);
      } catch (error) {
        localStorage.removeItem("authToken");
        setAuthToken(null);
        setUsuarioActual(null);
      } finally {
        setAuthInicializado(true);
      }
    }

    inicializarAuth();
  }, []);

  /**
   * login
   */
  function login(tokenJWT) {
    localStorage.setItem("authToken", tokenJWT);
    setAuthToken(tokenJWT);
    setUsuarioActual(null);
  }

  /**
   * logout
   */
  async function logout() {
    try {
      if (authToken) {
        await logoutUsuario(authToken);
      }
    } catch (error) {
      console.warn("Logout backend falló:", error.message);
    } finally {
      localStorage.removeItem("authToken");
      setAuthToken(null);
      setUsuarioActual(null);
    }
  }

  const authContextValue = {
    authToken,
    usuarioActual,
    estaAutenticado: Boolean(authToken),
    authInicializado,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={authContextValue}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * useAuth
 * Hook para consumir el contexto
 */
export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth debe usarse dentro de AuthProvider");
  }

  return context;
}

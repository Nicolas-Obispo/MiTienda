// frontend/src/context/AuthContext.jsx
import { useCallback, useEffect, useMemo, useState } from "react";
import { queryKeys } from "@core/constants/queryKeys";
import { queryClient } from "@core/query/queryClient";
import { logoutUsuario } from "@features/auth/services/authService";
import { AuthContext } from "@features/auth/context/AuthContextCore";
import { useCurrentUser } from "@features/auth/hooks/useCurrentUser";

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

  const [postAuthDestination, setPostAuthDestination] = useState(null);
  const currentUserQuery = useCurrentUser(accessToken);
  const {
    data: currentUser,
    error: currentUserError,
    isFetching: isFetchingCurrentUser,
    refetch: refetchCurrentUser,
  } = currentUserQuery;
  const clearPostAuthDestination = useCallback(
    () => setPostAuthDestination(null),
    []
  );

  const limpiarSesionLocal = useCallback(() => {
    // Centralizamos limpieza para evitar estados inconsistentes.
    localStorage.removeItem("access_token");
    setAccessToken(null);
    setEstaAutenticado(false);
    setPostAuthDestination(null);

    // Limpiamos cache TanStack Query al cerrar o invalidar sesión.
    // Evita que el modo exploración herede liked_by_me / guardada_by_me
    // de un usuario anterior.
    queryClient.clear();
  }, []);

  const login = useCallback((token, options = {}) => {
    if (!token || typeof token !== "string") return;

    // Limpiamos cache anterior antes de iniciar una nueva sesión.
    // Evita mezclar datos personales entre usuarios distintos.
    queryClient.clear();

    localStorage.setItem("access_token", token);
    setAccessToken(token);
    setEstaAutenticado(true);
    setPostAuthDestination(options.postAuthDestination || null);
    // La query habilitada por accessToken carga /usuarios/me.
  }, []);

  const logout = useCallback(async () => {
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
  }, [accessToken, limpiarSesionLocal]);

  const refrescarUsuario = useCallback(async () => {
    if (!accessToken) {
      queryClient.removeQueries({ queryKey: queryKeys.users.me() });
      return null;
    }

    try {
      const result = await refetchCurrentUser({ throwOnError: false });
      if (!result.error) return result.data || null;

      throw result.error;
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
        return null;
      }

      // Otros errores sí interesan (backend caído, CORS, etc.)
      console.error("Error obteniendo /usuarios/me:", error);
      return null;
    }
  }, [accessToken, limpiarSesionLocal, refetchCurrentUser]);

  useEffect(() => {
    if (!accessToken || !currentUserError) return;

    const msg = String(currentUserError?.message || "");
    const is401 =
      msg.includes("HTTP 401") ||
      msg.includes("401") ||
      msg.toLowerCase().includes("token invÃ¡lido") ||
      msg.toLowerCase().includes("token invalido") ||
      msg.toLowerCase().includes("expirado") ||
      msg.toLowerCase().includes("unauthorized");

    if (is401) {
      limpiarSesionLocal();
      return;
    }

    console.error("Error obteniendo /usuarios/me:", currentUserError);
  }, [accessToken, currentUserError, limpiarSesionLocal]);

  const value = useMemo(
    () => ({
      accessToken,
      estaAutenticado,
      usuario: currentUser || null,
      isCargandoUsuario: Boolean(accessToken) && isFetchingCurrentUser,
      login,
      logout,
      refrescarUsuario,
      postAuthDestination,
      clearPostAuthDestination,
    }),
    [
      accessToken,
      estaAutenticado,
      currentUser,
      isFetchingCurrentUser,
      postAuthDestination,
      clearPostAuthDestination,
      login,
      logout,
      refrescarUsuario,
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

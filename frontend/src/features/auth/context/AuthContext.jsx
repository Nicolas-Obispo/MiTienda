// frontend/src/context/AuthContext.jsx
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { queryKeys } from "@core/constants/queryKeys";
import { queryClient } from "@core/query/queryClient";
import { logoutUsuario } from "@features/auth/services/authService";
import { AuthContext } from "@features/auth/context/AuthContextCore";
import {
  AUTH_TOKEN_STORAGE_KEY,
  getTokenFromStorageEvent,
  normalizeAuthToken,
  removeStoredAuthTokenIfCurrent,
  shouldClearAuthSession,
} from "@features/auth/context/authSessionTransition";
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
    return normalizeAuthToken(localStorage.getItem(AUTH_TOKEN_STORAGE_KEY));
  });

  const [estaAutenticado, setEstaAutenticado] = useState(() => {
    return Boolean(normalizeAuthToken(localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)));
  });

  const [postAuthDestination, setPostAuthDestination] = useState(null);
  const [sessionGeneration, setSessionGeneration] = useState(0);
  const activeAccessTokenRef = useRef(accessToken);
  const sessionGenerationRef = useRef(0);
  const currentUserQuery = useCurrentUser(accessToken, sessionGeneration);
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

  const advanceSessionGeneration = useCallback(() => {
    const nextGeneration = sessionGenerationRef.current + 1;
    sessionGenerationRef.current = nextGeneration;
    setSessionGeneration(nextGeneration);
  }, []);

  const limpiarSesionLocal = useCallback((
    failedToken = null,
    failedGeneration = null,
  ) => {
    // Una respuesta tardía de una sesión anterior nunca puede invalidar la
    // sesión que se instaló después de iniciar sesión nuevamente.
    if (!shouldClearAuthSession(
      activeAccessTokenRef.current,
      failedToken,
      sessionGenerationRef.current,
      failedGeneration
    )) {
      return false;
    }

    // Compare-and-remove: otro cliente puede haber instalado una sesión nueva
    // en el storage compartido aunque este cliente todavía conserve la vieja.
    if (!removeStoredAuthTokenIfCurrent(localStorage, failedToken)) {
      return false;
    }

    // Centralizamos limpieza para evitar estados inconsistentes.
    activeAccessTokenRef.current = null;
    advanceSessionGeneration();
    setAccessToken(null);
    setEstaAutenticado(false);
    setPostAuthDestination(null);

    // Limpiamos cache TanStack Query al cerrar o invalidar sesión.
    // Evita que el modo exploración herede liked_by_me / guardada_by_me
    // de un usuario anterior.
    queryClient.clear();
    return true;
  }, [advanceSessionGeneration]);

  const login = useCallback((token, options = {}) => {
    if (!token || typeof token !== "string") return;

    // Limpiamos cache anterior antes de iniciar una nueva sesión.
    // Evita mezclar datos personales entre usuarios distintos.
    queryClient.clear();

    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
    // La referencia activa y su generación se actualizan antes de habilitar
    // cualquier query de la nueva sesión.
    activeAccessTokenRef.current = token;
    advanceSessionGeneration();
    setAccessToken(token);
    setEstaAutenticado(true);
    setPostAuthDestination(options.postAuthDestination || null);
    // La query habilitada por accessToken carga /usuarios/me.
  }, [advanceSessionGeneration]);

  const logout = useCallback(async () => {
    const tokenBeingLoggedOut = accessToken;
    const generationBeingLoggedOut = sessionGeneration;
    try {
      // Logout real en backend (revoca token) si hay token
      if (accessToken) {
        await logoutUsuario(accessToken);
      }
    } catch (error) {
      // Si falla el logout remoto, igual limpiamos local (no bloquea al usuario)
      console.warn("Logout remoto falló (se limpia sesión local igual):", error);
    } finally {
      limpiarSesionLocal(tokenBeingLoggedOut, generationBeingLoggedOut);
    }
  }, [accessToken, limpiarSesionLocal, sessionGeneration]);

  const refrescarUsuario = useCallback(async () => {
    if (!accessToken) {
      queryClient.removeQueries({ queryKey: queryKeys.users.me() });
      return null;
    }

    const requestToken = accessToken;
    const requestGeneration = sessionGeneration;

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
        limpiarSesionLocal(requestToken, requestGeneration);
        return null;
      }

      // Otros errores sí interesan (backend caído, CORS, etc.)
      console.error("Error obteniendo /usuarios/me:", error);
      return null;
    }
  }, [accessToken, limpiarSesionLocal, refetchCurrentUser, sessionGeneration]);

  useEffect(() => {
    function handleStorage(event) {
      const nextToken = getTokenFromStorageEvent(event, localStorage);
      if (nextToken === undefined || nextToken === activeAccessTokenRef.current) return;

      // El evento storage no escribe nuevamente: adopta el estado compartido
      // y por eso no puede generar un loop entre clientes.
      queryClient.clear();
      activeAccessTokenRef.current = nextToken;
      advanceSessionGeneration();
      setAccessToken(nextToken);
      setEstaAutenticado(Boolean(nextToken));
      setPostAuthDestination(null);
    }

    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, [advanceSessionGeneration]);

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
      limpiarSesionLocal(accessToken, sessionGeneration);
      return;
    }

    console.error("Error obteniendo /usuarios/me:", currentUserError);
  }, [accessToken, currentUserError, limpiarSesionLocal, sessionGeneration]);

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

import { useCallback } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "@features/auth";

export function useProtectedActionRedirect() {
  const { estaAutenticado } = useAuth();
  const navigate = useNavigate();

  const requireAuthentication = useCallback((message = "Para interactuar con FeedGo, registrate o iniciá sesión.") => {
    if (estaAutenticado) return false;
    navigate("/registro", { state: { message } });
    return true;
  }, [estaAutenticado, navigate]);

  return { estaAutenticado, requireAuthentication };
}

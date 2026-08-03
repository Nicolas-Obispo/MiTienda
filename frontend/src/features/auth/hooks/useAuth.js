import { useContext } from "react";
import { AuthContext } from "@features/auth/context/AuthContextCore";

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth debe usarse dentro de <AuthProvider>.");
  }
  return ctx;
}

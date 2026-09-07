import { useContext } from "react";

import { ProtectedActionContext } from "@core/access/ProtectedActionContext";

export function useProtectedAction() {
  const context = useContext(ProtectedActionContext);
  if (!context) {
    throw new Error("useProtectedAction debe usarse dentro de ProtectedActionProvider");
  }
  return context;
}

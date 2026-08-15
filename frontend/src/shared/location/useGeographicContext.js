import { useContext } from "react";

import { GeographicContext } from "@shared/location/GeographicContextCore";

export function useGeographicContext() {
  const value = useContext(GeographicContext);
  if (!value) throw new Error("useGeographicContext requiere GeographicContextProvider.");
  return value;
}

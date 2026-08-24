import { useEffect, useRef } from "react";

export function useFocusOnAdministrativeError(isError) {
  const errorRef = useRef(null);

  useEffect(() => {
    if (isError) errorRef.current?.focus();
  }, [isError]);

  return errorRef;
}

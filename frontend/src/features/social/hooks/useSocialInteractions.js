/**
 * useSocialInteractions.js
 *
 * ETAPA 67 — SOCIAL ENTERPRISE
 *
 * Hook reusable para centralizar locks sociales.
 * Más adelante también va a centralizar rollback,
 * cache, errores y sincronización.
 */

import { useMemo, useState } from "react";

/**
 * useSocialInteractions
 *
 * Responsabilidad inicial:
 * - Manejar locks de likes.
 * - Manejar locks de guardados.
 * - Evitar doble click por publicación.
 */
export function useSocialInteractions() {
  const [likeLocks, setLikeLocks] = useState({});
  const [saveLocks, setSaveLocks] = useState({});

  const likeLocksMemo = useMemo(() => likeLocks, [likeLocks]);
  const saveLocksMemo = useMemo(() => saveLocks, [saveLocks]);

  function setLock(setter, publicacionId, value) {
    setter((prev) => ({
      ...prev,
      [publicacionId]: value,
    }));
  }

  function setLikeLock(publicacionId, value) {
    setLock(setLikeLocks, publicacionId, value);
  }

  function setSaveLock(publicacionId, value) {
    setLock(setSaveLocks, publicacionId, value);
  }

  function isLikeLocked(publicacionId) {
    return Boolean(likeLocksMemo[publicacionId]);
  }

  function isSaveLocked(publicacionId) {
    return Boolean(saveLocksMemo[publicacionId]);
  }

  return {
    likeLocks: likeLocksMemo,
    saveLocks: saveLocksMemo,
    setLikeLock,
    setSaveLock,
    isLikeLocked,
    isSaveLocked,
  };
}

export function resolveStoryMediaFailure({
  historias,
  indexActual,
  failedIds,
  puedeAdministrar,
}) {
  const list = Array.isArray(historias) ? historias : [];
  const failed = new Set(failedIds || []);
  const historiaActual = list[indexActual];

  if (historiaActual?.id != null) failed.add(historiaActual.id);

  if (puedeAdministrar) {
    return {
      failedIds: failed,
      shouldStay: true,
      shouldClose: false,
      nextIndex: indexActual,
    };
  }

  const nextIndex = list.findIndex(
    (historia, index) => index > indexActual && !failed.has(historia?.id)
  );

  return {
    failedIds: failed,
    shouldStay: false,
    shouldClose: nextIndex === -1,
    nextIndex,
  };
}

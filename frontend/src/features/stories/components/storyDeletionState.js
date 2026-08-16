export function reconcileStoryDeletion(historias, indexActual, historiaId) {
  const list = Array.isArray(historias) ? historias : [];
  const historiasRestantes = list.filter((historia) => historia.id !== historiaId);

  return {
    historiasRestantes,
    nextIndex:
      historiasRestantes.length === 0
        ? 0
        : Math.min(indexActual, historiasRestantes.length - 1),
    shouldClose: historiasRestantes.length === 0,
  };
}

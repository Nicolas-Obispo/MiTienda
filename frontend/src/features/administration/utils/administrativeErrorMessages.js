const STATUS_MESSAGES = Object.freeze({
  401: "La sesión venció. Iniciá sesión nuevamente.",
  403: "No tenés permiso para realizar esta operación.",
  404: "El recurso administrativo ya no existe.",
  409: "El recurso cambió. Actualizá la información antes de continuar.",
  422: "Los datos enviados no son válidos.",
});

export function administrativeErrorMessage(error, fallback) {
  return STATUS_MESSAGES[error?.status] ?? fallback;
}

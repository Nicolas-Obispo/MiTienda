const LABELS = Object.freeze({
  recibida: "Recibida", resuelta: "Resuelta", comercio: "Comercio", publicacion: "Publicación", historia: "Historia",
  resolver_sin_accion: "Resolver sin acción", ocultar_recurso: "Ocultar recurso", restaurar_recurso: "Restaurar recurso",
  sin_incumplimiento: "Sin incumplimiento", incumplimiento_confirmado: "Incumplimiento confirmado", contenido_no_disponible: "Contenido no disponible", correccion_operativa: "Corrección operativa", otro: "Otro",
  contenido_inapropiado: "Contenido inapropiado", fraude_engano: "Fraude o engaño", suplantacion: "Suplantación", datos_personales: "Exposición de datos personales", propiedad_intelectual: "Propiedad intelectual", producto_servicio_restringido: "Producto o servicio restringido", spam: "Contenido no solicitado",
  ocultado: "Ocultado", restaurado: "Restaurado", sin_cambio: "Sin cambios sobre el recurso",
  open: "Abierto", investigating: "En investigación", contained: "Contenido", resolved: "Resuelto", reviewed: "Revisado",
  sev1_critical: "SEV1 · Crítico", sev2_high: "SEV2 · Alto", sev3_medium: "SEV3 · Medio", sev4_low: "SEV4 · Bajo",
  low: "Bajo", medium: "Medio", high: "Alto", critical: "Crítico",
  opened: "Incidente abierto", start_investigation: "Iniciar investigación", record_finding: "Registrar hallazgo", contain: "Registrar contención", resolve: "Resolver incidente", review: "Completar revisión", reopen: "Reabrir incidente",
  record_legal_assessment: "Registrar evaluación legal", change_severity: "Cambiar severidad", assign_owner: "Cambiar responsable",
  pending: "Pendiente", not_required: "No requerida", required: "Requerida", completed: "Completada", unknown: "Sin determinar", none: "Ninguno", suspected: "Posible", confirmed: "Confirmado", no: "No", yes: "Sí",
  availability: "Disponibilidad", security: "Seguridad", privacy: "Privacidad", data_integrity: "Integridad de datos", dependency: "Dependencia", storage_media: "Archivos multimedia", configuration: "Configuración",
  healthy: "Saludable", degraded: "Degradado", unhealthy: "No saludable", unavailable: "No disponible",
  api: "API", database: "Base de datos", database_schema: "Esquema de base de datos", uploads_storage: "Almacenamiento de archivos", embeddings: "Representaciones de búsqueda", backup_evidence: "Evidencia de copias de seguridad", restore_evidence: "Evidencia de restauración",
  backup: "Copia de seguridad", restore: "Restauración", valid: "Válida", invalid: "Inválida", missing: "Ausente", valid_evidence_available: "Evidencia válida disponible", evidence_unavailable_or_invalid: "Evidencia ausente o inválida", evidence_check_unavailable: "Comprobación de evidencia no disponible",
  info: "Información", warning: "Advertencia", error: "Error", triggered: "Detectada", recovered: "Recuperada", active_alert: "Activa", suppressed: "Silenciada",
  readiness_unhealthy: "Sistema no disponible", http_5xx_repeated: "Errores internos repetidos", backup_failed: "Falló la copia de seguridad", backup_evidence_not_healthy: "Evidencia de copia degradada", restore_failed: "Falló la restauración", uploads_rejected_repeated: "Archivos rechazados repetidamente",
  local_health_requests_total: "Consultas locales de salud", local_health_errors_total: "Errores locales de salud", local_alert_events_total: "Eventos locales de alerta", local_upload_checks_total: "Comprobaciones locales de archivos",
  active: "Activo", paused: "Pausado", sold: "Vendido", deleted: "Eliminado", visible: "Visible", hidden: "Oculto",
  stopped: "Detenido", disabled: "Deshabilitado",
  local: "Archivo local", external: "Archivo externo", invalid_reference: "Referencia inválida", present: "Disponible", not_verified: "No verificado", not_applicable: "No corresponde",
  local_asset_missing: "El archivo local asociado no está disponible", invalid_asset_reference: "La referencia del archivo es inválida", asset_missing: "El archivo asociado no está disponible", asset_reference_missing: "El recurso no tiene un archivo asociado",
});

export function administrativeLabel(value, fallback = "Dato no disponible") {
  if (value === null || value === undefined || value === "") return fallback;
  return LABELS[value] ?? fallback;
}

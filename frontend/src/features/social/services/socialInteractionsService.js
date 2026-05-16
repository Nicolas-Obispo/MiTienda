/**
 * socialInteractionsService.js
 *
 * ETAPA 67 — SOCIAL ENTERPRISE
 *
 * Responsabilidad:
 * Centralizar acciones sociales reutilizables.
 *
 * Esta capa desacopla:
 * - páginas
 * - hooks
 * - UI
 *
 * de:
 * - servicios reales
 * - requests
 * - lógica social backend
 */

import {
  toggleLikePublicacion,
  guardarPublicacion,
  quitarPublicacionGuardada,
} from "@features/posts";

import {
  seguirEspacio,
  dejarDeSeguirEspacio,
} from "@features/spaces";

/**
 * toggleLike
 *
 * Alterna like de publicación.
 */
export async function toggleLike(publicacionId) {
  return toggleLikePublicacion(publicacionId);
}

/**
 * toggleGuardado
 *
 * Alterna guardado de publicación.
 */
export async function toggleGuardado({
  publicacionId,
  estabaGuardada,
}) {
  if (estabaGuardada) {
    return quitarPublicacionGuardada(publicacionId);
  }

  return guardarPublicacion(publicacionId);
}

/**
 * toggleSeguimientoEspacio
 *
 * Alterna seguimiento de espacio.
 */
export async function toggleSeguimientoEspacio({
  comercioId,
  siguiendo,
}) {
  if (siguiendo) {
    return dejarDeSeguirEspacio(comercioId);
  }

  return seguirEspacio(comercioId);
}

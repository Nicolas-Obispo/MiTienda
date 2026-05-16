/*
comercios_metricas_sociales_service.js
--------------------------------------
Service frontend para consultar métricas sociales
reales de un espacio/comercio.

El backend sigue siendo la fuente de verdad.
*/

import { httpGet } from "@core";

// =======================================================
// Obtener métricas sociales de un espacio
// =======================================================

export async function obtenerMetricasSocialesEspacio(comercioId) {
  /*
  Consulta las métricas sociales reales del espacio.

  Requiere usuario autenticado porque el endpoint backend
  usa JWT para proteger la información de analytics.
  */

  const token = localStorage.getItem("access_token");

  return httpGet(
    `/comercios-metricas-sociales/espacios/${comercioId}`,
    token
  );
}

// =======================================================
// Obtener comparación de métricas sociales de un espacio
// =======================================================

export async function obtenerComparacionMetricasSocialesEspacio(comercioId) {
  /*
  Consulta comparación real:
  snapshot actual vs snapshot anterior.
  */

  const token = localStorage.getItem("access_token");

  return httpGet(
    `/comercios-metricas-sociales/espacios/${comercioId}/comparacion`,
    token
  );
}

/*
comercios_analytics_service.js
------------------------------
Service frontend para consumir Analytics Engine
de espacios MiPlaza.
*/

import { httpGet } from "./http_service";

// =======================================================
// Obtener analytics completo de un espacio
// =======================================================

export async function obtenerAnalyticsEspacio(comercioId) {
  /*
  Consulta:
  - métricas
  - métricas derivadas
  - comparación
  - insights
  */

  const token = localStorage.getItem("access_token");

  return httpGet(
    `/comercios-analytics/espacios/${comercioId}`,
    token
  );
}

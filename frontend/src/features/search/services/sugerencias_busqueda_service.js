/**
 * sugerencias_busqueda_service.js
 * --------------------------------
 * Cliente HTTP para sugerencias predictivas del buscador.
 */

import { httpGet } from "@core";

export async function getBuscarSugerencias({
  q = null,
  limit = 5,
} = {}) {
  const query = String(q || "").trim();
  const limitNumber = Number(limit);

  if (!query || query.length < 2) {
    return {
      query,
      suggestions: [],
    };
  }

  const params = new URLSearchParams();
  params.set("q", query);
  params.set(
    "limit",
    String(Number.isNaN(limitNumber) ? 5 : Math.min(Math.max(limitNumber, 1), 10))
  );

  return httpGet(`/buscar/sugerencias?${params.toString()}`);
}

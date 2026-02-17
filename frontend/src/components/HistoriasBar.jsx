/**
 * HistoriasBar.jsx
 * -------------------------------------------------------
 * Componente UI: Barra horizontal de Historias (tipo Instagram).
 *
 * Responsabilidad:
 * - Renderizar una lista horizontal de "burbujas" de historias.
 * - NO hace requests.
 * - Recibe todo por props (data + handlers).
 *
 * UX ETAPA 44:
 * - Si el usuario NO vio historias de un comercio → aro VERDE + contador (pendientes)
 * - Si el usuario ya vio todo → aro GRIS + sin contador
 * - Orden: primero las burbujas con pendientes, al final las vistas
 */

import React from "react";

/**
 * @typedef {Object} HistoriaComercioItem
 * @property {number} comercioId
 * @property {string} nombre
 * @property {string|null} thumbnailUrl
 * @property {number} cantidad - Total de historias del comercio (informativo)
 *
 * NUEVO (ETAPA 44):
 * @property {number} [pendientes] - Cantidad de historias NO vistas por el usuario (para contador y aro)
 */

export default function HistoriasBar({ items = [], onClickComercio }) {
  /**
   * Orden UI:
   * - Primero comercios con historias pendientes (>0)
   * - Luego los que ya están “vistos” (0 pendientes)
   * - Mantiene el orden relativo dentro de cada grupo.
   */
  const itemsOrdenados = Array.isArray(items)
    ? [...items].sort((a, b) => {
        const aPend = Number(a?.pendientes ?? 0);
        const bPend = Number(b?.pendientes ?? 0);

        const aTienePend = aPend > 0 ? 1 : 0;
        const bTienePend = bPend > 0 ? 1 : 0;

        // Queremos pendientes primero → bTienePend - aTienePend
        return bTienePend - aTienePend;
      })
    : [];

  return (
    <section className="w-full" aria-label="Historias">
      <div className="flex gap-3 overflow-x-auto px-3 py-3">
        {itemsOrdenados.length === 0 ? (
          <div className="text-sm opacity-70">No hay historias para mostrar.</div>
        ) : (
          itemsOrdenados.map((item) => {
            // pendientes: si no viene, fallback a "cantidad" para no romper UI
            const pendientes = Number(
              item?.pendientes ?? item?.cantidad ?? 0
            );

            const tienePendientes = pendientes > 0;

            // UX:
            // - aro verde si tiene pendientes
            // - aro gris si ya está visto
            const aroClass = tienePendientes
              ? "ring-2 ring-green-500"
              : "ring-2 ring-white/30";

            return (
              <button
                key={item.comercioId}
                type="button"
                className="flex w-[70px] shrink-0 flex-col items-center gap-2"
                onClick={() => {
                  if (typeof onClickComercio === "function") {
                    onClickComercio(item.comercioId);
                  }
                }}
                aria-label={`Ver historias de ${item.nombre}`}
                title={`Ver historias de ${item.nombre}`}
              >
                <div className="relative">
                  <div className={`rounded-full p-[2px] ${aroClass}`}>
                    <div className="h-14 w-14 overflow-hidden rounded-full bg-white/10">
                      {item.thumbnailUrl ? (
                        <img
                          src={item.thumbnailUrl}
                          alt={item.nombre}
                          className="h-full w-full object-cover"
                          loading="lazy"
                        />
                      ) : (
                        <div className="flex h-full w-full items-center justify-center text-xs opacity-70">
                          {item.nombre?.slice(0, 2)?.toUpperCase() || "HP"}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Contador: SOLO si hay pendientes */}
                  {tienePendientes ? (
                    <div className="absolute -right-1 -top-1 rounded-full bg-white px-1.5 py-0.5 text-[10px] text-black">
                      {pendientes}
                    </div>
                  ) : null}
                </div>

                <div className="w-full truncate text-center text-[12px] opacity-90">
                  {item.nombre}
                </div>
              </button>
            );
          })
        )}
      </div>
    </section>
  );
}

/**
 * HistoriasBar.jsx
 * -------------------------------------------------------
 * Componente UI: Barra horizontal de Historias (tipo Instagram).
 *
 * Responsabilidad:
 * - Renderizar una lista horizontal de "burbujas" de historias.
 * - NO hace requests.
 * - NO maneja lógica de negocio.
 * - Recibe todo por props (data + handlers).
 *
 * Naming (Regla de Oro):
 * - Dominio del negocio en español: HistoriasBar, historia, comercio.
 */

import React from "react";

/**
 * @typedef {Object} HistoriaComercioItem
 * @property {number} comercioId - ID del comercio dueño de las historias
 * @property {string} nombre - Nombre a mostrar debajo de la burbuja
 * @property {string|null} thumbnailUrl - Imagen a mostrar (logo/foto). Si no hay, muestra placeholder.
 * @property {number} cantidad - Cantidad de historias (sirve para UI/indicador)
 */

/**
 * HistoriasBar
 * -------------------------------------------------------
 * Qué hace:
 * - Muestra un carrusel horizontal con burbujas de historias por comercio.
 *
 * Por qué existe:
 * - Es la pieza UI base para ETAPA 41 (Historias).
 * - Luego se integra en FeedPage arriba del feed.
 *
 * @param {Object} props
 * @param {HistoriaComercioItem[]} props.items - Lista de comercios con historias para renderizar
 * @param {(comercioId:number)=>void} props.onClickComercio - Callback al tocar una burbuja
 * @returns {JSX.Element}
 */
export default function HistoriasBar({ items = [], onClickComercio }) {
  return (
    <section
      className="w-full"
      aria-label="Historias"
    >
      {/* Contenedor scrolleable horizontal (tipo Instagram) */}
      <div className="flex gap-3 overflow-x-auto px-3 py-3">
        {items.length === 0 ? (
          /**
           * Estado vacío:
           * - No mostramos placeholders "hardcodeados" para no mentir data.
           * - Solo mostramos un texto discreto.
           */
          <div className="text-sm opacity-70">
            No hay historias para mostrar.
          </div>
        ) : (
          items.map((item) => (
            <button
              key={item.comercioId}
              type="button"
              className="flex w-[70px] shrink-0 flex-col items-center gap-2"
              onClick={() => {
                /**
                 * Delegamos el click al padre.
                 * - El padre decide si abre viewer, modal, etc.
                 */
                if (typeof onClickComercio === "function") {
                  onClickComercio(item.comercioId);
                }
              }}
              aria-label={`Ver historias de ${item.nombre}`}
              title={`Ver historias de ${item.nombre}`}
            >
              {/* Burbuja circular */}
              <div className="relative">
                {/* Borde “activo” (simula el aro de historias) */}
                <div className="rounded-full p-[2px] ring-2 ring-white/30">
                  {/* Imagen / placeholder */}
                  <div className="h-14 w-14 overflow-hidden rounded-full bg-white/10">
                    {item.thumbnailUrl ? (
                      <img
                        src={item.thumbnailUrl}
                        alt={item.nombre}
                        className="h-full w-full object-cover"
                        loading="lazy"
                      />
                    ) : (
                      /**
                       * Placeholder simple:
                       * - No usamos íconos externos para mantenerlo liviano.
                       */
                      <div className="flex h-full w-full items-center justify-center text-xs opacity-70">
                        {item.nombre?.slice(0, 2)?.toUpperCase() || "HP"}
                      </div>
                    )}
                  </div>
                </div>

                {/* Indicador de cantidad (opcional) */}
                {typeof item.cantidad === "number" && item.cantidad > 0 ? (
                  <div className="absolute -right-1 -top-1 rounded-full bg-white px-1.5 py-0.5 text-[10px] text-black">
                    {item.cantidad}
                  </div>
                ) : null}
              </div>

              {/* Nombre debajo (corte a 1 línea) */}
              <div className="w-full truncate text-center text-[12px] opacity-90">
                {item.nombre}
              </div>
            </button>
          ))
        )}
      </div>
    </section>
  );
}

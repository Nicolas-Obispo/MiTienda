// frontend/src/components/PublicacionCard.jsx
import React from "react";

/**
 * MetricBadge
 * - Espaciado correcto entre icono, texto y valor
 * - Mejor legibilidad
 */
function MetricBadge({ label, value, icon }) {
  return (
    <div className="inline-flex items-center rounded-full border border-gray-800 bg-gray-900 px-3 py-1 text-xs text-gray-200">
      <span className="mr-1" aria-hidden="true">
        {icon}
      </span>

      <span className="mr-1 text-gray-400">{label}</span>

      <span className="font-semibold text-white">{value}</span>
    </div>
  );
}

/**
 * ActionButton
 * Botón chico y consistente para acciones (like/guardar)
 */
function ActionButton({
  children,
  onClick,
  disabled,
  variant = "neutral",
  title,
}) {
  const base =
    "inline-flex items-center justify-center rounded-xl px-3 py-2 text-xs sm:text-sm font-semibold border transition select-none";
  const styles = {
    neutral: "bg-gray-900 text-gray-200 border-gray-800 hover:bg-gray-800",
    active:
      "bg-green-950/40 text-green-300 border-green-800 hover:bg-green-950/60",
    danger: "bg-red-950/40 text-red-200 border-red-900 hover:bg-red-950/60",
  };

  return (
    <button
      type="button"
      className={[
        base,
        styles[variant],
        disabled ? "opacity-50 cursor-not-allowed" : "",
      ].join(" ")}
      onClick={onClick}
      disabled={disabled}
      title={title}
    >
      {children}
    </button>
  );
}

/**
 * PublicacionCard (componente reutilizable)
 *
 * Props:
 * - pub: publicación (id, titulo, descripcion, liked_by_me, guardada_by_me, likes_count, guardados_count, interacciones_count?)
 * - isActingLike: boolean (lock UI like)
 * - isActingSave: boolean (lock UI guardado)
 * - onToggleLike: () => void
 * - onToggleSave: () => void
 *
 * Extras (opcional, para Ranking):
 * - rankIndex?: number (0-based) -> muestra badge #{rankIndex+1}
 * - headerRightBadgeText?: string -> texto en el badge derecho ("Ranking", etc.)
 *
 * Nota:
 * - No contiene lógica de negocio (optimistic, services, etc.). Eso queda en Pages.
 */
export default function PublicacionCard({
  pub,
  isActingLike,
  isActingSave,
  onToggleLike,
  onToggleSave,
  rankIndex = null,
  headerRightBadgeText = null,
}) {
  const likeVariant = pub?.liked_by_me ? "active" : "neutral";
  const saveVariant = pub?.guardada_by_me ? "active" : "neutral";

  const showRank = Number.isInteger(rankIndex);
  const showInteracciones =
    typeof pub?.interacciones_count === "number" && pub.interacciones_count >= 0;

  return (
    <article className="rounded-2xl border border-gray-800 bg-gray-950 p-5">
      <header className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            {showRank ? (
              <span className="inline-flex items-center justify-center rounded-xl border border-gray-800 bg-gray-900 px-2 py-1 text-xs font-semibold text-gray-200">
                #{rankIndex + 1}
              </span>
            ) : null}

            <h2 className="text-base sm:text-lg font-semibold text-white leading-snug">
              {pub?.titulo}
            </h2>
          </div>

          <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
            <span className="rounded-md border border-gray-800 bg-gray-900 px-2 py-0.5">
              ID #{pub?.id}
            </span>
            <span className="hidden sm:inline">•</span>
            <span className="hidden sm:inline">MiPlaza</span>
          </div>
        </div>

        {/* Badge derecho:
            - Si viene headerRightBadgeText (Ranking), lo mostramos.
            - Si no viene, mantenemos el badge de estado Like del Feed.
        */}
        {headerRightBadgeText ? (
          <div className="shrink-0 rounded-full px-3 py-1 text-xs font-semibold border bg-gray-900 text-gray-300 border-gray-800">
            {headerRightBadgeText}
          </div>
        ) : (
          <div
            className={[
              "shrink-0 rounded-full px-3 py-1 text-xs font-semibold border",
              pub?.liked_by_me
                ? "bg-green-950/40 text-green-300 border-green-800"
                : "bg-gray-900 text-gray-300 border-gray-800",
            ].join(" ")}
            title="Estado de Like del usuario"
          >
            {pub?.liked_by_me ? "Te gustó" : "No te gustó"}
          </div>
        )}
      </header>

      <div className="mt-4">
        {pub?.descripcion ? (
          <p className="text-sm sm:text-base text-gray-200 leading-relaxed">
            {pub.descripcion}
          </p>
        ) : (
          <p className="text-sm text-gray-500 italic">Sin descripción.</p>
        )}
      </div>

      {/* Acciones */}
      <div className="mt-5 flex flex-wrap items-center gap-2">
        <ActionButton
          variant={likeVariant}
          disabled={Boolean(isActingLike)}
          onClick={onToggleLike}
          title="Dar/Quitar like"
        >
          {isActingLike
            ? "Procesando..."
            : pub?.liked_by_me
            ? "👍 Te gustó"
            : "👍 Like"}
        </ActionButton>

        <ActionButton
          variant={saveVariant}
          disabled={Boolean(isActingSave)}
          onClick={onToggleSave}
          title="Guardar/Quitar de guardados"
        >
          {isActingSave
            ? "Procesando..."
            : pub?.guardada_by_me
            ? "⭐ Guardada"
            : "⭐ Guardar"}
        </ActionButton>
      </div>

      {/* Métricas */}
      <footer className="mt-5 flex flex-wrap items-center gap-2">
        <MetricBadge label="Likes" value={pub?.likes_count} icon="👍" />
        <MetricBadge label="Guardados" value={pub?.guardados_count} icon="⭐" />
        {showInteracciones ? (
          <MetricBadge
            label="Interacciones"
            value={pub?.interacciones_count}
            icon="🔥"
          />
        ) : null}
        <MetricBadge
          label="Liked"
          value={pub?.liked_by_me ? "Sí" : "No"}
          icon="📌"
        />
        <MetricBadge
          label="Guardada"
          value={pub?.guardada_by_me ? "Sí" : "No"}
          icon="💾"
        />
      </footer>
    </article>
  );
}

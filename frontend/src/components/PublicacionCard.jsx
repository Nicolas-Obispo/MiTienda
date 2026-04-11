// frontend/src/components/PublicacionCard.jsx
import React from "react";
import { Link, useNavigate } from "react-router-dom";

function MetricBadge({ label, value, icon }) {
  return (
    <div className="inline-flex items-center rounded-full border border-gray-800 bg-gray-900 px-3 py-1 text-xs text-gray-200">
      <span className="mr-1" aria-hidden="true">
        {icon}
      </span>
      <span className="mr-1 text-gray-400">{label}</span>
      <span className="font-semibold text-white">{value ?? 0}</span>
    </div>
  );
}

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

function getNombreComercio(pub) {
  return (
    pub?.comercio_nombre ||
    pub?.nombre_comercio ||
    pub?.comercio?.nombre ||
    (typeof pub?.comercio_id === "number" ? `Comercio #${pub.comercio_id}` : "Comercio")
  );
}

function getMediaUrl(pub) {
  return (
    pub?.imagen_url ||
    pub?.media_url ||
    pub?.foto_url ||
    pub?.portada_url ||
    pub?.thumbnail_url ||
    ""
  );
}

function esVideo(url) {
  if (!url || typeof url !== "string") return false;
  return [".mp4", ".webm", ".ogg", ".mov"].some((ext) =>
    url.toLowerCase().includes(ext)
  );
}

export default function PublicacionCard({
  pub,
  isActingLike,
  isActingSave,
  onToggleLike,
  onToggleSave,
  rankIndex = null,
  headerRightBadgeText = null,
  compact = false,
}) {
  const navigate = useNavigate();

  const likeVariant = pub?.liked_by_me ? "active" : "neutral";
  const saveVariant = pub?.guardada_by_me ? "active" : "neutral";

  const showRank = Number.isInteger(rankIndex);
  const showInteracciones =
    typeof pub?.interacciones_count === "number" && pub.interacciones_count >= 0;

  const comercioId =
    typeof pub?.comercio_id === "number" && pub.comercio_id > 0
      ? pub.comercio_id
      : null;

  const nombreComercio = getNombreComercio(pub);
  const mediaUrl = getMediaUrl(pub);
  const mediaEsVideo = esVideo(mediaUrl);

  function irADetallePublicacion() {
    if (!pub?.id) return;
    navigate(`/publicaciones/${pub.id}`);
  }

  function handleLikeClick(e) {
    e.stopPropagation();
    onToggleLike?.();
  }

  function handleSaveClick(e) {
    e.stopPropagation();
    onToggleSave?.();
  }

  // =====================================================
  // MODO COMPACTO — para Feed / Ranking en grid
  // =====================================================
  if (compact) {
    return (
      <article
        onClick={irADetallePublicacion}
        className="overflow-hidden rounded-2xl border border-gray-800 bg-gray-950 cursor-pointer"
        title="Ver publicación"
      >
        <div className="relative aspect-square bg-black">
          {mediaUrl ? (
            mediaEsVideo ? (
              <video
                src={mediaUrl}
                muted
                playsInline
                className="h-full w-full object-cover"
              />
            ) : (
              <img
                src={mediaUrl}
                alt={pub?.titulo || nombreComercio}
                className="h-full w-full object-cover"
              />
            )
          ) : (
            <div className="flex h-full w-full items-center justify-center bg-gray-900 text-sm text-gray-500">
              Sin imagen
            </div>
          )}

          <div className="pointer-events-none absolute left-2 top-2 flex items-center gap-2">
            {showRank ? (
              <span className="rounded-full border border-black/30 bg-black/60 px-2 py-1 text-[11px] font-semibold text-white backdrop-blur-sm">
                #{rankIndex + 1}
              </span>
            ) : null}

            {headerRightBadgeText ? (
              <span className="rounded-full border border-black/30 bg-black/60 px-2 py-1 text-[11px] font-semibold text-white backdrop-blur-sm">
                {headerRightBadgeText}
              </span>
            ) : null}
          </div>

          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-black/80 via-black/35 to-transparent" />

          <div className="absolute inset-x-0 bottom-0 p-3">
            <div className="flex items-end justify-between gap-2">
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-white">
                  {nombreComercio}
                </p>

                {pub?.descripcion ? (
                  <p className="mt-1 line-clamp-2 text-xs text-white/80">
                    {pub.descripcion}
                  </p>
                ) : pub?.titulo ? (
                  <p className="mt-1 line-clamp-2 text-xs text-white/80">
                    {pub.titulo}
                  </p>
                ) : null}
              </div>

              <div className="flex shrink-0 flex-col gap-2">
                <button
                  type="button"
                  onClick={handleLikeClick}
                  disabled={Boolean(isActingLike)}
                  className={[
                    "rounded-full border px-2.5 py-1 text-[11px] font-semibold backdrop-blur-sm transition",
                    pub?.liked_by_me
                      ? "border-green-700 bg-green-950/70 text-green-300"
                      : "border-white/20 bg-black/50 text-white",
                    isActingLike ? "opacity-50 cursor-not-allowed" : "",
                  ].join(" ")}
                  title="Dar/Quitar like"
                >
                  {pub?.liked_by_me ? "👍" : "🤍"}
                </button>

                <button
                  type="button"
                  onClick={handleSaveClick}
                  disabled={Boolean(isActingSave)}
                  className={[
                    "rounded-full border px-2.5 py-1 text-[11px] font-semibold backdrop-blur-sm transition",
                    pub?.guardada_by_me
                      ? "border-green-700 bg-green-950/70 text-green-300"
                      : "border-white/20 bg-black/50 text-white",
                    isActingSave ? "opacity-50 cursor-not-allowed" : "",
                  ].join(" ")}
                  title="Guardar/Quitar de guardados"
                >
                  {pub?.guardada_by_me ? "⭐" : "☆"}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between gap-2 px-3 py-2">
          <div className="flex items-center gap-2 text-[11px] text-gray-400">
            <span>👍 {pub?.likes_count ?? 0}</span>
            <span>⭐ {pub?.guardados_count ?? 0}</span>
          </div>

          {comercioId ? (
            <Link
              to={`/comercios/${comercioId}`}
              onClick={(e) => e.stopPropagation()}
              className="text-[11px] text-gray-300 hover:text-white"
            >
              Ver mas
            </Link>
          ) : null}
        </div>
      </article>
    );
  }

  // =====================================================
  // MODO COMPLETO — para detalle / otras pantallas
  // =====================================================
  return (
    <article className="overflow-hidden rounded-2xl border border-gray-800 bg-gray-950">
      <header className="flex items-center justify-between gap-3 p-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            {showRank ? (
              <span className="inline-flex items-center justify-center rounded-xl border border-gray-800 bg-gray-900 px-2 py-1 text-xs font-semibold text-gray-200">
                #{rankIndex + 1}
              </span>
            ) : null}

            <h2 className="truncate text-sm sm:text-base font-semibold text-white">
              {nombreComercio}
            </h2>
          </div>

          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-gray-400">
            {comercioId ? (
              <Link
                to={`/comercios/${comercioId}`}
                className="inline-flex items-center rounded-md border border-gray-800 bg-gray-900 px-2 py-0.5 text-gray-300 hover:bg-gray-800 hover:text-white"
              >
                Ver comercio
              </Link>
            ) : null}

            {pub?.titulo ? (
              <span className="truncate text-gray-500">{pub.titulo}</span>
            ) : null}
          </div>
        </div>

        {headerRightBadgeText ? (
          <div className="shrink-0 rounded-full border border-gray-800 bg-gray-900 px-3 py-1 text-xs font-semibold text-gray-300">
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
          >
            {pub?.liked_by_me ? "Te gustó" : "Publicación"}
          </div>
        )}
      </header>

      <div className="border-y border-gray-800 bg-black">
        {mediaUrl ? (
          mediaEsVideo ? (
            <video
              src={mediaUrl}
              controls
              playsInline
              className="h-auto max-h-[70vh] w-full object-cover"
            />
          ) : (
            <img
              src={mediaUrl}
              alt={pub?.titulo || nombreComercio}
              className="h-auto max-h-[70vh] w-full object-cover"
            />
          )
        ) : (
          <div className="flex aspect-square w-full items-center justify-center bg-gray-900 text-sm text-gray-500">
            Sin imagen
          </div>
        )}
      </div>

      <div className="p-4">
        {pub?.descripcion ? (
          <p className="text-sm text-gray-200 leading-relaxed">
            {pub.descripcion}
          </p>
        ) : (
          <p className="text-sm italic text-gray-500">Sin descripción.</p>
        )}

        <div className="mt-4 flex flex-wrap items-center gap-2">
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
              : "👍 Me gusta"}
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

        <footer className="mt-4 flex flex-wrap items-center gap-2">
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
      </div>
    </article>
  );
}
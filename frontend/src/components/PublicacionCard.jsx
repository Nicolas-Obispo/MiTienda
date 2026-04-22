// frontend/src/components/PublicacionCard.jsx
import React from "react";
import { Link, useNavigate } from "react-router-dom";
import InteraccionButton from "./InteraccionButton";

/*
====================================================
BADGE DE MÉTRICA
- Se usa para mostrar métricas resumidas
====================================================
*/
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

/*
====================================================
HELPERS DE NORMALIZACIÓN
====================================================
*/
function getNombreComercio(pub) {
  return (
    pub?.comercio_nombre ||
    pub?.nombre_comercio ||
    pub?.comercio?.nombre ||
    (typeof pub?.comercio_id === "number"
      ? `Comercio #${pub.comercio_id}`
      : "Comercio")
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

  /*
  ====================================================
  NAVEGACIÓN A DETALLE
  ====================================================
  */
  function irADetallePublicacion() {
    if (!pub?.id) return;
    navigate(`/publicaciones/${pub.id}`);
  }

  /*
  ====================================================
  HANDLERS DE BOTONES
  - Frenan propagación para no abrir el detalle
  ====================================================
  */
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
        className="cursor-pointer overflow-hidden rounded-2xl border border-gray-800 bg-gray-950"
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

          {/* BADGES SUPERIORES */}
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

          {/* DEGRADÉ INFERIOR */}
          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-black/80 via-black/35 to-transparent" />

          {/* INFO + ACCIONES */}
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

              {/* 
              ============================================
              ACCIONES COMPACTAS
              - Círculo perfecto
              - Solo icono
              ============================================
              */}
              <div
                className="flex shrink-0 flex-col gap-2"
                onClick={(e) => e.stopPropagation()}
              >
                <InteraccionButton
                  type="like"
                  active={Boolean(pub?.liked_by_me)}
                  onClick={handleLikeClick}
                  disabled={Boolean(isActingLike)}
                  label=""
                  iconOnly={true}
                />

                <InteraccionButton
                  type="guardar"
                  active={Boolean(pub?.guardada_by_me)}
                  onClick={handleSaveClick}
                  disabled={Boolean(isActingSave)}
                  label=""
                  iconOnly={true}
                />
              </div>
            </div>
          </div>
        </div>

        {/* MÉTRICAS INFERIORES */}
        <div className="flex items-center justify-between gap-2 px-3 py-2">
          <div className="flex items-center gap-2 text-[11px] text-gray-400">
            <span>❤️ {pub?.likes_count ?? 0}</span>
            <span>⭐ {pub?.guardados_count ?? 0}</span>
          </div>

          {comercioId ? (
            <Link
              to={`/comercios/${comercioId}`}
              onClick={(e) => e.stopPropagation()}
              className="text-[11px] text-gray-300 hover:text-white"
            >
              Ver más
            </Link>
          ) : null}
        </div>
      </article>
    );
  }

  // =====================================================
  // MODO COMPLETO — para perfil / otras pantallas
  // =====================================================
  return (
    <article className="overflow-hidden rounded-2xl border border-gray-800 bg-gray-950">
      {/* HEADER */}
      <header className="flex items-center justify-between gap-3 p-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            {showRank ? (
              <span className="inline-flex items-center justify-center rounded-xl border border-gray-800 bg-gray-900 px-2 py-1 text-xs font-semibold text-gray-200">
                #{rankIndex + 1}
              </span>
            ) : null}

            <h2 className="truncate text-sm font-semibold text-white sm:text-base">
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
          <div className="shrink-0 rounded-full border border-gray-800 bg-gray-900 px-3 py-1 text-xs font-semibold text-gray-300">
            Publicación
          </div>
        )}
      </header>

      {/* MEDIA */}
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

      {/* INFO */}
      <div className="p-4">
        {pub?.descripcion ? (
          <p className="text-sm leading-relaxed text-gray-200">
            {pub.descripcion}
          </p>
        ) : (
          <p className="text-sm italic text-gray-500">Sin descripción.</p>
        )}

        {/* ACCIONES */}
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <InteraccionButton
            type="like"
            active={Boolean(pub?.liked_by_me)}
            onClick={onToggleLike}
            disabled={Boolean(isActingLike)}
            label={
              isActingLike
                ? "Procesando..."
                : pub?.liked_by_me
                ? "Te gusta"
                : "Me gusta"
            }
          />

          <InteraccionButton
            type="guardar"
            active={Boolean(pub?.guardada_by_me)}
            onClick={onToggleSave}
            disabled={Boolean(isActingSave)}
            label={
              isActingSave
                ? "Procesando..."
                : pub?.guardada_by_me
                ? "Guardada"
                : "Guardar"
            }
          />
        </div>

        {/* MÉTRICAS */}
        <footer className="mt-4 flex flex-wrap items-center gap-2">
          <MetricBadge label="Likes" value={pub?.likes_count} icon="❤️" />
          <MetricBadge label="Guardados" value={pub?.guardados_count} icon="⭐" />

          {showInteracciones ? (
            <MetricBadge
              label="Interacciones"
              value={pub?.interacciones_count}
              icon="🔥"
            />
          ) : null}
        </footer>
      </div>
    </article>
  );
}
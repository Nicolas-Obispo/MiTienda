// frontend/src/components/PublicacionCard.jsx
import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { InteraccionButton, PublicationVideo } from "@shared";
import { getMediaUrlFromAny } from "@shared";
import { SOCIAL_ICONS } from "@shared/constants/socialIcons";
import InteractiveLiquidLayers from "@shared/components/InteractiveLiquidLayers";
import PublicacionReportControl from "@features/moderation/components/PublicacionReportControl";

function RankingBadge({ rankIndex, compact = false }) {
  const position = rankIndex + 1;

  return (
    <span
      className={`interactive-bubble interactive-bubble--flush interactive-bubble--liquid pointer-events-none inline-flex shrink-0 items-center justify-center rounded-full font-semibold text-primary ${
        compact ? "h-6 w-6 text-[11px]" : "h-7 w-7 text-xs"
      }`}
    >
      <span>#{position}</span>
      <InteractiveLiquidLayers />
    </span>
  );
}

function MetricBadge({ label, value, icon }) {
  return (
    <div className="inline-flex items-center px-3 py-1 text-xs text-primary">
      <span className="mr-1" aria-hidden="true">{icon}</span>
      <span className="mr-1 text-secondary">{label}</span>
      <span className="font-semibold">{value ?? 0}</span>
    </div>
  );
}

function getNombreComercio(pub) {
  return (
    pub?.comercio_nombre ||
    pub?.nombre_comercio ||
    pub?.comercio?.nombre ||
    "Perfil"
  );
}

function getMediaUrl(pub) {
  return getMediaUrlFromAny(pub);
}

function getInicialesComercio(nombre) {
  return String(nombre || "Perfil").slice(0, 2).toUpperCase();
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
  compactActions = false,
  compactWholeCardLink = false,
  showReportTrigger = false,
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

  if (compact) {
    const wholeCardLinkEnabled = compactWholeCardLink && !compactActions;
    const compactCardClassName = wholeCardLinkEnabled
      ? "group block w-full cursor-pointer overflow-hidden rounded-2xl border border-border bg-surface transition-[border-color,box-shadow] duration-200 ease-out hover:border-border-strong hover:shadow-[inset_0_0_0_1px_var(--fg-color-border-strong)] focus-visible:border-border-strong focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring focus-visible:shadow-[inset_0_0_0_1px_var(--fg-color-border-strong)] active:shadow-[inset_0_0_0_1px_var(--fg-color-border-strong)] motion-reduce:transition-none"
      : "cursor-pointer overflow-hidden rounded-2xl border border-border bg-surface";
    const accessiblePublicationName =
      pub?.titulo || pub?.descripcion || "Publicación";

    const compactContent = (
      <>
        <div className="relative aspect-square bg-black">
          {mediaUrl ? (
            mediaEsVideo ? (
              <PublicationVideo
                src={mediaUrl}
                preload="metadata"
                className="h-full w-full object-cover"
              />
            ) : (
              <img
                src={mediaUrl}
                alt={pub?.titulo || pub?.descripcion || "Publicación"}
                loading="lazy"
                decoding="async"
                className={
                  wholeCardLinkEnabled
                    ? "h-full w-full object-cover transition-transform duration-200 ease-out group-hover:scale-[1.015] group-focus-visible:scale-[1.015] group-active:scale-[1.005] motion-reduce:transform-none motion-reduce:transition-none"
                    : "h-full w-full object-cover"
                }
              />
            )
          ) : (
            <div className="flex h-full w-full items-center justify-center bg-surface-subtle text-sm text-muted">
              Sin imagen
            </div>
          )}

          {showRank ? (
            <div className="pointer-events-none absolute left-2 top-2">
              <RankingBadge rankIndex={rankIndex} compact />
            </div>
          ) : null}

          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-black/80 via-black/35 to-transparent" />

          <div className="absolute inset-x-0 bottom-0 p-3">
            <div className="flex items-end justify-between gap-2">
              <div className="min-w-0">
                {pub?.descripcion ? (
                  <p className="line-clamp-2 text-xs font-medium text-white/90">
                    {pub.descripcion}
                  </p>
                ) : pub?.titulo ? (
                  <p className="line-clamp-2 text-xs font-medium text-white/90">
                    {pub.titulo}
                  </p>
                ) : null}
              </div>

              {compactActions ? (
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
                    iconOnly
                  />

                  <InteraccionButton
                    type="guardar"
                    active={Boolean(pub?.guardada_by_me)}
                    onClick={handleSaveClick}
                    disabled={Boolean(isActingSave)}
                    label=""
                    iconOnly
                  />
                </div>
              ) : null}
            </div>
          </div>
        </div>

        <div
          className={
            wholeCardLinkEnabled
              ? "flex items-center px-3 py-2"
              : "flex items-center justify-between gap-2 px-3 py-2"
          }
        >
          <div className="flex items-center gap-2 text-[11px] text-secondary">
            <span>❤️ {pub?.likes_count ?? 0}</span>
            <span>⭐ {pub?.guardados_count ?? 0}</span>
          </div>

          {!wholeCardLinkEnabled ? (
            <Link
              to={`/publicaciones/${pub.id}`}
              onClick={(event) => event.stopPropagation()}
              className="rounded-sm text-[11px] text-interactive-primary underline underline-offset-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
            >
              Ver publicación
            </Link>
          ) : null}
        </div>
      </>
    );

    if (wholeCardLinkEnabled) {
      return (
        <Link
          to={`/publicaciones/${pub.id}`}
          aria-label={`Ver publicación: ${accessiblePublicationName}`}
          className={compactCardClassName}
        >
          {compactContent}
        </Link>
      );
    }

    return (
      <article
        onClick={irADetallePublicacion}
        className={compactCardClassName}
        title="Ver publicación"
      >
        {compactContent}
      </article>
    );
  }

  return (
    <article className="overflow-hidden rounded-3xl border border-border bg-surface">
      <header className="space-y-2 p-4">
        <div className="flex min-w-0 items-center gap-2">
          {showRank ? <RankingBadge rankIndex={rankIndex} /> : null}

          <div className="flex h-8 w-8 shrink-0 items-center justify-center overflow-hidden rounded-full bg-surface-subtle text-xs font-semibold text-muted">
            {pub?.comercio_portada_url ? (
              <img
                src={pub.comercio_portada_url}
                alt=""
                loading="lazy"
                decoding="async"
                className="h-full w-full object-cover"
              />
            ) : (
              <span aria-hidden="true">
                {getInicialesComercio(nombreComercio)}
              </span>
            )}
          </div>

          <span className="min-w-0 truncate text-sm font-medium text-secondary">
            {nombreComercio}
          </span>

          <div className="ml-auto flex min-w-0 shrink-0 items-center gap-2">
            {comercioId ? (
              <Link
                to={`/comercios/${comercioId}`}
                className="interactive-bubble interactive-bubble--liquid interactive-bubble--secondary text-xs shrink-0"
              >
                <span>Ver espacio</span>
                <InteractiveLiquidLayers />
              </Link>
            ) : null}

            {headerRightBadgeText ? (
              <div className="max-w-32 truncate rounded-full border border-border bg-surface-subtle px-3 py-1 text-xs font-semibold text-secondary sm:max-w-48">
                {headerRightBadgeText}
              </div>
            ) : null}
          </div>
        </div>

        <h2 className="truncate text-lg font-semibold sm:text-xl">
          <Link
            to={`/publicaciones/${pub.id}`}
            className="rounded-sm text-primary focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
          >
            {pub?.titulo || nombreComercio}
          </Link>
        </h2>
      </header>

      <div
        className="cursor-pointer border-y border-border bg-black"
        onClick={irADetallePublicacion}
      >
        {mediaUrl ? (
          mediaEsVideo ? (
            <PublicationVideo
              src={mediaUrl}
              controls
              preload="metadata"
              className="max-h-[78vh] w-full object-contain"
/>
          ) : (
            <img
              src={mediaUrl}
              alt={pub?.titulo || pub?.descripcion || "Publicación"}
              loading="lazy"
              decoding="async"
              className="max-h-[78vh] w-full object-contain"
            />
          )
        ) : (
          <div className="flex aspect-square w-full items-center justify-center bg-surface-subtle text-sm text-muted">
            Sin imagen
          </div>
        )}
      </div>

      <div className="p-4">
        {pub?.descripcion ? (
          <p className="text-base leading-relaxed text-primary">
            {pub.descripcion}
          </p>
        ) : (
          <p className="text-sm italic text-muted">Sin descripción.</p>
        )}

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <InteraccionButton
            type="like"
            active={Boolean(pub?.liked_by_me)}
            onClick={onToggleLike}
            disabled={Boolean(isActingLike)}
            label={
              pub?.liked_by_me
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
              pub?.guardada_by_me
                ? "Guardada"
                : "Guardar"
              }
          />

          {showReportTrigger ? (
            <PublicacionReportControl publicacionId={pub?.id} />
          ) : null}
        </div>

        <footer className="mt-4 flex flex-wrap items-center gap-2">
          <MetricBadge label="Likes" value={pub?.likes_count} icon={SOCIAL_ICONS.like} />
          <MetricBadge label="Guardados" value={pub?.guardados_count} icon={SOCIAL_ICONS.guardado} />

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

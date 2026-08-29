/**
 * InteraccionButton.jsx
 * ----------------------
 * Componente reutilizable para:
 * - Like (corazon) -> animacion latido
 * - Guardar (estrella) -> animacion bounce
 */

import { useState } from "react";
import { Heart, Star } from "lucide-react";
import InteractiveLiquidLayers from "@shared/components/InteractiveLiquidLayers";
import { SOCIAL_ICONS } from "@shared/constants/socialIcons";

export default function InteraccionButton({
  active = false,
  onClick,
  disabled = false,
  label = "",
  type = "like", // "like" | "guardar"
  iconOnly = false,
}) {
  /*
  ====================================================
  CONFIGURACION SEGUN TIPO
  ====================================================
  */
  const config = {
    like: {
      Icon: Heart,
      activeIcon: SOCIAL_ICONS.like,
      activeBubbleClass: "interactive-bubble--danger",
      borderActive: "border-danger-border",
      animation: "animate-like",
    },
    guardar: {
      Icon: Star,
      activeIcon: SOCIAL_ICONS.guardado,
      activeBubbleClass: "interactive-bubble--warning",
      borderActive: "border-warning-border",
      animation: "animate-save",
    },
  };

  const cfg = config[type];
  const Icon = cfg.Icon;

  /*
  ====================================================
  ESTADO DE ANIMACION
  ====================================================
  */
  const [isAnimating, setIsAnimating] = useState(false);

  function handleClick(e) {
    if (disabled) return;

    // Ejecuta accion original
    onClick?.(e);

    // Dispara animacion
    setIsAnimating(true);

    setTimeout(() => {
      setIsAnimating(false);
    }, 300);
  }

  /*
  ====================================================
  ESTILO BASE
  ====================================================
  */
  const baseClass = iconOnly
    ? `
      interactive-bubble inline-flex h-11 w-11 shrink-0 items-center justify-center
      rounded-full border transition
    `
    : `
      interactive-bubble gap-1
    `;

  const bubbleVariantClass =
    active ? cfg.activeBubbleClass : "interactive-bubble--secondary";
  const accessibleLabel =
    label ||
    (type === "guardar"
      ? active
        ? "Quitar de guardados"
        : "Guardar"
      : active
        ? "Quitar Me gusta"
        : "Me gusta");

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled}
      aria-label={iconOnly ? accessibleLabel : undefined}
      className={`
        ${baseClass}
        interactive-bubble--liquid
        ${bubbleVariantClass}
        ${iconOnly ? (active ? cfg.borderActive : "border-border") : ""}
        ${disabled ? "cursor-not-allowed opacity-60" : iconOnly ? "hover:bg-surface-subtle" : ""}
      `}
    >
      {/* ICONO */}
      {active ? (
        <span
          aria-hidden="true"
          className={`
            inline-flex shrink-0 items-center justify-center text-base leading-none transition
            ${iconOnly ? "h-[1.125rem] w-[1.125rem]" : "h-5 w-5"}
            ${isAnimating ? cfg.animation : ""}
          `}
        >
          {cfg.activeIcon}
        </span>
      ) : (
        <Icon
          aria-hidden="true"
          className={`
            shrink-0 fill-none stroke-current leading-none text-interactive-on-primary transition
            ${iconOnly ? "h-[1.125rem] w-[1.125rem]" : "h-5 w-5"}
            ${isAnimating ? cfg.animation : ""}
          `}
        />
      )}

      {/* TEXTO SOLO SI NO ES iconOnly */}
      {!iconOnly && <span className="text-interactive-on-primary">{label}</span>}
      <InteractiveLiquidLayers />
    </button>
  );
}

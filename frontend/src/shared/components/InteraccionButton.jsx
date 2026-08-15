/**
 * InteraccionButton.jsx
 * ----------------------
 * Componente reutilizable para:
 * - Like (corazon) -> animacion latido
 * - Guardar (estrella) -> animacion bounce
 */

import { useState } from "react";

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
      icon: "♥",
      activeColor: "text-danger-text",
      inactiveColor: "text-secondary",
      activeBubbleClass: "interactive-bubble--danger",
      borderActive: "border-danger-border",
      animation: "animate-like",
    },
    guardar: {
      icon: "★",
      activeColor: "text-warning-text",
      inactiveColor: "text-secondary",
      activeBubbleClass: "interactive-bubble--warning",
      borderActive: "border-warning-border",
      animation: "animate-save",
    },
  };

  const cfg = config[type];

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
        ${bubbleVariantClass}
        ${iconOnly ? (active ? cfg.borderActive : "border-border") : ""}
        ${disabled ? "cursor-not-allowed opacity-60" : iconOnly ? "hover:bg-surface-subtle" : ""}
      `}
    >
      {/* ICONO */}
      <span
        className={`
          leading-none transition
          ${iconOnly ? "text-lg" : "text-xl"}
          ${active ? cfg.activeColor : cfg.inactiveColor}
          ${isAnimating ? cfg.animation : ""}
        `}
      >
        {cfg.icon}
      </span>

      {/* TEXTO SOLO SI NO ES iconOnly */}
      {!iconOnly && <span>{label}</span>}
    </button>
  );
}

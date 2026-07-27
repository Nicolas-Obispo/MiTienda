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
      activeColor: "text-red-500",
      inactiveColor: "text-gray-300",
      activeBubbleVars: {
        "--bubble-border": "rgba(239, 68, 68, 0.28)",
        "--bubble-border-hover": "rgba(239, 68, 68, 0.42)",
      },
      borderActive: "border-red-500",
      animation: "animate-like",
    },
    guardar: {
      icon: "★",
      activeColor: "text-yellow-400",
      inactiveColor: "text-gray-300",
      activeBubbleVars: {
        "--bubble-border": "rgba(234, 179, 8, 0.3)",
        "--bubble-border-hover": "rgba(234, 179, 8, 0.46)",
      },
      borderActive: "border-yellow-500",
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
      inline-flex h-11 w-11 shrink-0 items-center justify-center
      rounded-full border transition
    `
    : `
      interactive-bubble gap-1
    `;

  const bubbleStyle =
    !iconOnly && active ? cfg.activeBubbleVars : undefined;

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled}
      style={bubbleStyle}
      className={`
        ${baseClass}
        ${iconOnly ? (active ? cfg.borderActive : "border-gray-700") : ""}
        ${disabled ? "cursor-not-allowed opacity-60" : iconOnly ? "hover:bg-gray-800" : ""}
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
      {!iconOnly && <span className="text-white">{label}</span>}
    </button>
  );
}

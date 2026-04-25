/**
 * InteraccionButton.jsx
 * ----------------------
 * Componente reutilizable para:
 * - Like (corazón) → animación latido
 * - Guardar (estrella) → animación bounce
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
  CONFIGURACIÓN SEGÚN TIPO
  ====================================================
  */
  const config = {
    like: {
      icon: "♥",
      activeColor: "text-red-500",
      inactiveColor: "text-gray-300",
      borderActive: "border-red-500",
      animation: "animate-like",
    },
    guardar: {
      icon: "★",
      activeColor: "text-yellow-400",
      inactiveColor: "text-gray-300",
      borderActive: "border-yellow-500",
      animation: "animate-save",
    },
  };

  const cfg = config[type];

  /*
  ====================================================
  ESTADO DE ANIMACIÓN
  ====================================================
  */
  const [isAnimating, setIsAnimating] = useState(false);

  function handleClick(e) {
    if (disabled) return;

    // Ejecuta acción original
    onClick?.(e);

    // Dispara animación
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
      inline-flex items-center gap-2 rounded-full border px-4 py-2 transition
    `;

  return (
    <>
      {/* ESTILOS DE ANIMACIÓN INLINE */}
      <style>
        {`
          @keyframes likePop {
            0% { transform: scale(1); }
            50% { transform: scale(1.3); }
            100% { transform: scale(1); }
          }

          @keyframes saveBounce {
            0% { transform: translateY(0); }
            40% { transform: translateY(-6px); }
            100% { transform: translateY(0); }
          }

          .animate-like {
            animation: likePop 0.3s ease;
          }

          .animate-save {
            animation: saveBounce 0.3s ease;
          }
        `}
      </style>

      <button
        type="button"
        onClick={handleClick}
        disabled={disabled}
        className={`
          ${baseClass}
          ${active ? cfg.borderActive : "border-gray-700"}
          ${disabled ? "cursor-not-allowed opacity-60" : "hover:bg-gray-800"}
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
    </>
  );
}
/**
 * InteraccionButton.jsx
 * ----------------------
 * Componente reutilizable para:
 * - Like (corazón)
 * - Guardar (estrella)
 *
 * OBJETIVO:
 * - Unificar UI en toda la app
 * - Permitir modo normal y modo iconOnly
 * - En modo iconOnly, el botón debe ser perfectamente circular
 */

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
    },
    guardar: {
      icon: "★",
      activeColor: "text-yellow-400",
      inactiveColor: "text-gray-300",
      borderActive: "border-yellow-500",
    },
  };

  const cfg = config[type];

  /*
  ====================================================
  ESTILO BASE
  - iconOnly: círculo perfecto
  - normal: botón con texto
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
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`
        ${baseClass}
        ${active ? cfg.borderActive : "border-gray-700"}
        ${disabled ? "cursor-not-allowed opacity-60" : "hover:bg-gray-800"}
      `}
    >
      {/* ICONO */}
      <span
        className={`leading-none transition ${
          iconOnly ? "text-lg" : "text-xl"
        } ${active ? cfg.activeColor : cfg.inactiveColor}`}
      >
        {cfg.icon}
      </span>

      {/* TEXTO SOLO SI NO ES iconOnly */}
      {!iconOnly && <span className="text-white">{label}</span>}
    </button>
  );
}
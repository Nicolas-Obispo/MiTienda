const ESTADO_CONFIG = {
  abierto: {
    dotClassName: "bg-green-400",
    className: "border-green-500/40 bg-green-950/60 text-green-200",
    inlineClassName: "text-green-300",
    fallbackText: "Abierto",
  },
  cerrado: {
    dotClassName: "bg-red-400",
    className: "border-red-500/40 bg-red-950/60 text-red-200",
    inlineClassName: "text-red-300",
    fallbackText: "Cerrado",
  },
  sin_horarios: {
    dotClassName: "bg-gray-400",
    className: "border-gray-600 bg-gray-950/70 text-gray-300",
    inlineClassName: "text-gray-400",
    fallbackText: "No hay horarios declarados",
  },
};

export default function EstadoHorarioBadge({
  horarioAtencion,
  compact = false,
  variant = "pill",
  className = "",
}) {
  if (!horarioAtencion) return null;

  const config =
    ESTADO_CONFIG[horarioAtencion.estado] || ESTADO_CONFIG.sin_horarios;
  const texto = horarioAtencion.texto || config.fallbackText;
  const isInline = variant === "inline";

  return (
    <span
      className={[
        "inline-flex max-w-full items-center gap-1.5 font-medium",
        isInline
          ? "min-h-9 py-1 text-xs"
          : [
              "rounded-full border",
              compact ? "px-2 py-0.5 text-[10px]" : "px-3 py-1 text-xs",
              config.className,
            ].join(" "),
        isInline ? config.inlineClassName : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      title={texto}
    >
      <span
        className={[
          "shrink-0 rounded-full",
          compact ? "h-1.5 w-1.5" : "h-2 w-2",
          config.dotClassName,
        ].join(" ")}
      />
      <span className="min-w-0 truncate">{texto}</span>
    </span>
  );
}

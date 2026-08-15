const ESTADO_CONFIG = {
  abierto: {
    dotClassName: "bg-success-text",
    className: "border-success-border bg-success-surface text-success-text",
    inlineClassName: "text-success-text",
    fallbackText: "Abierto",
  },
  cerrado: {
    dotClassName: "bg-danger-text",
    className: "border-danger-border bg-danger-surface text-danger-text",
    inlineClassName: "text-danger-text",
    fallbackText: "Cerrado",
  },
  sin_horarios: {
    dotClassName: "bg-disabled-text",
    className: "border-disabled-border bg-disabled-surface text-disabled-text",
    inlineClassName: "text-muted",
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

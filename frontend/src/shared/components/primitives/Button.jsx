import { forwardRef } from "react";

import { classNames } from "./classNames";

const VARIANT_CLASSES = {
  primary:
    "interactive-bubble--primary-action bg-interactive-primary text-interactive-on-primary hover:bg-interactive-primary-hover active:bg-interactive-primary-active",
  secondary:
    "interactive-bubble--secondary bg-surface-subtle text-primary hover:bg-surface",
  danger:
    "interactive-bubble--danger bg-danger-surface text-danger-text",
  success:
    "interactive-bubble--success bg-success-surface text-success-text",
  warning:
    "interactive-bubble--warning bg-warning-surface text-warning-text",
  ghost: "bg-transparent text-secondary",
};

const Button = forwardRef(function Button(
  {
    "aria-label": ariaLabel,
    "aria-labelledby": ariaLabelledBy,
    children,
    className = "",
    disabled = false,
    iconOnly = false,
    type = "button",
    variant = "secondary",
    ...props
  },
  ref
) {
  if (iconOnly && !ariaLabel && !ariaLabelledBy) {
    throw new Error(
      "Button iconOnly requiere aria-label o aria-labelledby para tener nombre accesible."
    );
  }

  const variantClass = VARIANT_CLASSES[variant] || VARIANT_CLASSES.secondary;

  return (
    <button
      {...props}
      ref={ref}
      type={type}
      disabled={disabled}
      aria-disabled={disabled || undefined}
      aria-label={ariaLabel}
      aria-labelledby={ariaLabelledBy}
      className={classNames(
        "interactive-bubble max-w-full whitespace-normal break-words text-center font-semibold",
        variantClass,
        iconOnly && "h-10 w-10 shrink-0 rounded-full p-0",
        disabled &&
          "cursor-not-allowed border-disabled-border bg-disabled-surface text-disabled-text",
        className
      )}
    >
      {children}
    </button>
  );
});

export default Button;

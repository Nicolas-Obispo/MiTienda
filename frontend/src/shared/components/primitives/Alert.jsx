import { forwardRef } from "react";

import { classNames } from "./classNames";

const VARIANT_CLASSES = {
  success: "border-success-border bg-success-surface text-success-text",
  warning: "border-warning-border bg-warning-surface text-warning-text",
  danger: "border-danger-border bg-danger-surface text-danger-text",
};

const Alert = forwardRef(function Alert(
  { children, className = "", variant = "danger", ...props },
  ref
) {
  return (
    <div
      {...props}
      ref={ref}
      className={classNames(
        "min-w-0 break-words rounded-xl border p-4 text-sm",
        VARIANT_CLASSES[variant] || VARIANT_CLASSES.danger,
        className
      )}
    >
      {children}
    </div>
  );
});

export default Alert;

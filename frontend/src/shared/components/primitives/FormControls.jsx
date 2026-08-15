import { forwardRef } from "react";

import { classNames } from "./classNames";

const BASE_CONTROL_CLASSES =
  "min-w-0 w-full rounded-xl border bg-surface px-3 py-2 text-primary outline-none placeholder:text-muted focus-visible:border-border-strong focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring disabled:cursor-not-allowed disabled:border-disabled-border disabled:bg-disabled-surface disabled:text-disabled-text";

function controlClasses(invalid, className) {
  return classNames(
    BASE_CONTROL_CLASSES,
    invalid ? "border-danger-border" : "border-border",
    className
  );
}

export const Input = forwardRef(function Input(
  { className = "", invalid = false, trailingAction = null, ...props },
  ref
) {
  const input = (
    <input
      {...props}
      ref={ref}
      aria-invalid={invalid || undefined}
      className={controlClasses(
        invalid,
        classNames(trailingAction && "pr-12", className)
      )}
    />
  );

  if (!trailingAction) return input;

  return (
    <div className="relative min-w-0 w-full">
      {input}
      <div className="pointer-events-none absolute inset-y-0 right-1 flex items-center [&>.interactive-bubble]:pointer-events-auto [&>.interactive-bubble]:!h-8 [&>.interactive-bubble]:!min-h-8 [&>.interactive-bubble]:!w-8">
        {trailingAction}
      </div>
    </div>
  );
});

export const Select = forwardRef(function Select(
  { children, className = "", invalid = false, ...props },
  ref
) {
  return (
    <select
      {...props}
      ref={ref}
      aria-invalid={invalid || undefined}
      className={controlClasses(invalid, className)}
    >
      {children}
    </select>
  );
});

export const Textarea = forwardRef(function Textarea(
  { className = "", invalid = false, ...props },
  ref
) {
  return (
    <textarea
      {...props}
      ref={ref}
      aria-invalid={invalid || undefined}
      className={controlClasses(invalid, className)}
    />
  );
});

export function FormControl({
  children,
  className = "",
  error,
  errorId,
  help,
  helpId,
  label,
  labelFor,
}) {
  return (
    <div className={classNames("space-y-1.5", className)}>
      {label ? (
        <label htmlFor={labelFor} className="block text-sm font-medium text-secondary">
          {label}
        </label>
      ) : null}
      {children}
      {error ? (
        <p id={errorId} className="text-sm text-danger-text">
          {error}
        </p>
      ) : help ? (
        <p id={helpId} className="text-sm text-muted">
          {help}
        </p>
      ) : null}
    </div>
  );
}

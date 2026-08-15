import { createElement, forwardRef } from "react";

import { classNames } from "./classNames";

const VARIANT_CLASSES = {
  base: "border-border bg-surface text-primary",
  subtle: "border-border-subtle bg-surface-subtle text-primary",
  elevated:
    "border-border bg-surface-elevated text-primary shadow-elevation",
};

const Surface = forwardRef(function Surface(
  {
    as: Component = "div",
    children,
    className = "",
    variant = "base",
    ...props
  },
  ref
) {
  return createElement(
    Component,
    {
      ...props,
      ref,
      className: classNames(
        "min-w-0 rounded-2xl border",
        VARIANT_CLASSES[variant] || VARIANT_CLASSES.base,
        className
      ),
    },
    children
  );
});

export default Surface;

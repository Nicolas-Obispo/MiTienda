import { createElement, forwardRef } from "react";

import { classNames } from "./classNames";

const Skeleton = forwardRef(function Skeleton(
  { as: Component = "div", className = "", ...props },
  ref
) {
  return createElement(Component, {
    ...props,
    ref,
    "aria-hidden": "true",
    className: classNames(
      "animate-pulse bg-skeleton-base motion-reduce:animate-none",
      className
    ),
  });
});

export default Skeleton;

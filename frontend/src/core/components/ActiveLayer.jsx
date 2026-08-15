import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";

let activeLayerCount = 0;
let savedBodyStyles = null;
let savedScrollY = 0;

function lockBodyScroll() {
  if (typeof window === "undefined" || typeof document === "undefined") return;

  if (activeLayerCount === 0) {
    savedScrollY = window.scrollY || window.pageYOffset || 0;
    savedBodyStyles = {
      position: document.body.style.position,
      top: document.body.style.top,
      left: document.body.style.left,
      right: document.body.style.right,
      width: document.body.style.width,
      overflow: document.body.style.overflow,
    };

    document.body.style.position = "fixed";
    document.body.style.top = `-${savedScrollY}px`;
    document.body.style.left = "0";
    document.body.style.right = "0";
    document.body.style.width = "100%";
    document.body.style.overflow = "hidden";
  }

  activeLayerCount += 1;
}

function unlockBodyScroll() {
  if (typeof window === "undefined" || typeof document === "undefined") return;

  activeLayerCount = Math.max(0, activeLayerCount - 1);

  if (activeLayerCount > 0 || !savedBodyStyles) return;

  document.body.style.position = savedBodyStyles.position;
  document.body.style.top = savedBodyStyles.top;
  document.body.style.left = savedBodyStyles.left;
  document.body.style.right = savedBodyStyles.right;
  document.body.style.width = savedBodyStyles.width;
  document.body.style.overflow = savedBodyStyles.overflow;

  window.scrollTo(0, savedScrollY);
  savedBodyStyles = null;
  savedScrollY = 0;
}

function getFocusableElements(container) {
  if (!container) return [];

  return Array.from(
    container.querySelectorAll(
      [
        "a[href]",
        "button:not([disabled])",
        "textarea:not([disabled])",
        "input:not([disabled])",
        "select:not([disabled])",
        "[tabindex]:not([tabindex='-1'])",
      ].join(",")
    )
  ).filter((element) => {
    const style = window.getComputedStyle(element);
    return style.display !== "none" && style.visibility !== "hidden";
  });
}

export default function ActiveLayer({
  children,
  onClose,
  labelledBy,
  describedBy,
  initialFocusRef,
  closeOnBackdrop = true,
  closeOnEscape = true,
  className = "",
  backdropClassName = "bg-overlay-backdrop",
  contentClassName = "",
  zIndex = 50,
}) {
  const contentRef = useRef(null);
  const previousFocusRef = useRef(null);
  const initialFocusTimerRef = useRef(null);
  const restoreFocusTimerRef = useRef(null);

  useEffect(() => {
    previousFocusRef.current = document.activeElement;
    lockBodyScroll();

    const focusTarget =
      initialFocusRef?.current ||
      getFocusableElements(contentRef.current)[0] ||
      contentRef.current;

    initialFocusTimerRef.current = window.setTimeout(() => {
      focusTarget?.focus?.();
      initialFocusTimerRef.current = null;
    }, 0);

    return () => {
      if (initialFocusTimerRef.current !== null) {
        window.clearTimeout(initialFocusTimerRef.current);
        initialFocusTimerRef.current = null;
      }

      unlockBodyScroll();

      const previousFocus = previousFocusRef.current;
      if (
        previousFocus?.isConnected &&
        typeof previousFocus.focus === "function"
      ) {
        restoreFocusTimerRef.current = window.setTimeout(() => {
          if (previousFocus.isConnected) previousFocus.focus();
          restoreFocusTimerRef.current = null;
        }, 0);
      }
    };
  }, [initialFocusRef]);

  function handleKeyDown(event) {
    if (event.key === "Escape" && closeOnEscape) {
      event.stopPropagation();
      onClose?.();
      return;
    }

    if (event.key !== "Tab") return;

    const focusableElements = getFocusableElements(contentRef.current);
    if (focusableElements.length === 0) {
      event.preventDefault();
      contentRef.current?.focus();
      return;
    }

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    if (event.shiftKey && document.activeElement === firstElement) {
      event.preventDefault();
      lastElement.focus();
    } else if (!event.shiftKey && document.activeElement === lastElement) {
      event.preventDefault();
      firstElement.focus();
    }
  }

  const layer = (
    <div
      className={`fixed inset-0 flex items-start justify-center overflow-y-auto overscroll-contain ${className}`}
      style={{ zIndex }}
      onKeyDown={handleKeyDown}
    >
      {closeOnBackdrop ? (
        <button
          type="button"
          aria-label="Cerrar capa activa"
          tabIndex={-1}
          className={`absolute inset-0 h-full w-full cursor-default ${backdropClassName}`}
          onClick={() => onClose?.()}
        />
      ) : (
        <div
          aria-hidden="true"
          className={`absolute inset-0 h-full w-full ${backdropClassName}`}
        />
      )}

      <div
        ref={contentRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy}
        aria-describedby={describedBy}
        tabIndex={-1}
        className={`relative z-10 my-auto outline-none ${contentClassName}`}
      >
        {children}
      </div>
    </div>
  );

  return createPortal(layer, document.body);
}

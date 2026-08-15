import { useEffect, useRef, useState } from "react";
import { ActiveLayer } from "@core";
import { useAuth } from "@features/auth";
import { Button, Surface } from "@shared";

const INACTIVITY_LIMIT_MS = 15 * 60 * 1000;
const ACTIVITY_EVENTS = ["click", "keydown", "scroll", "touchstart", "pointerdown"];

export default function SessionInactivityGuard() {
  const { estaAutenticado, logout } = useAuth();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const lastActivityAtRef = useRef(null);
  const timerRef = useRef(null);
  const continueButtonRef = useRef(null);

  useEffect(() => {
    function clearCurrentTimer() {
      if (timerRef.current) {
        window.clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    }

    if (!estaAutenticado) {
      lastActivityAtRef.current = Date.now();
      clearCurrentTimer();

      if (isModalOpen) {
        const resetModalTimer = window.setTimeout(() => {
          setIsModalOpen(false);
        }, 0);

        return () => {
          window.clearTimeout(resetModalTimer);
        };
      }

      return;
    }

    if (isModalOpen) {
      clearCurrentTimer();
      return;
    }

    function showInactivityModal() {
      clearCurrentTimer();
      setIsModalOpen(true);
    }

    function scheduleTimer() {
      clearCurrentTimer();

      const elapsed = Date.now() - lastActivityAtRef.current;
      const remaining = Math.max(INACTIVITY_LIMIT_MS - elapsed, 0);

      timerRef.current = window.setTimeout(() => {
        showInactivityModal();
      }, remaining);
    }

    function registerActivity() {
      lastActivityAtRef.current = Date.now();
      scheduleTimer();
    }

    function handleVisibilityChange() {
      if (document.visibilityState !== "visible") return;

      const elapsed = Date.now() - lastActivityAtRef.current;
      if (elapsed >= INACTIVITY_LIMIT_MS) {
        showInactivityModal();
        return;
      }

      scheduleTimer();
    }

    lastActivityAtRef.current = Date.now();
    scheduleTimer();

    ACTIVITY_EVENTS.forEach((eventName) => {
      const options = eventName === "keydown" ? undefined : { passive: true };
      window.addEventListener(eventName, registerActivity, options);
    });
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      clearCurrentTimer();
      ACTIVITY_EVENTS.forEach((eventName) => {
        window.removeEventListener(eventName, registerActivity);
      });
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [estaAutenticado, isModalOpen]);

  function handleContinue() {
    lastActivityAtRef.current = Date.now();
    setIsModalOpen(false);
  }

  async function handleLogout() {
    await logout();
  }

  if (!estaAutenticado || !isModalOpen) return null;

  return (
    <ActiveLayer
      onClose={handleContinue}
      labelledBy="session-inactivity-title"
      initialFocusRef={continueButtonRef}
      className="px-4 py-6"
      backdropClassName="bg-overlay-backdrop backdrop-blur-sm"
      contentClassName="w-full max-w-sm"
      zIndex={300}
    >
      <Surface variant="elevated" className="p-5">
        <h2 id="session-inactivity-title" className="text-center text-lg font-semibold text-primary">
          ¿Deseás cerrar sesión?
        </h2>

        <div className="mt-5 grid grid-cols-2 gap-3">
          <Button
            ref={continueButtonRef}
            type="button"
            onClick={handleLogout}
            variant="danger"
            className="px-3 py-2 text-sm"
          >
            Cerrar sesión
          </Button>

          <Button
            type="button"
            onClick={handleContinue}
            variant="secondary"
            className="px-3 py-2 text-sm"
          >
            Continuar
          </Button>
        </div>
      </Surface>
    </ActiveLayer>
  );
}

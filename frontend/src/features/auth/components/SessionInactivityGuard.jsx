import { useEffect, useRef, useState } from "react";
import { useAuth } from "@features/auth";

const INACTIVITY_LIMIT_MS = 15 * 60 * 1000;
const ACTIVITY_EVENTS = ["click", "keydown", "scroll", "touchstart", "pointerdown"];

export default function SessionInactivityGuard() {
  const { estaAutenticado, logout } = useAuth();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const lastActivityAtRef = useRef(Date.now());
  const timerRef = useRef(null);

  useEffect(() => {
    function clearCurrentTimer() {
      if (timerRef.current) {
        window.clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    }

    if (!estaAutenticado) {
      setIsModalOpen(false);
      lastActivityAtRef.current = Date.now();
      clearCurrentTimer();
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
    <div className="fixed inset-0 z-[300] flex items-center justify-center bg-black/75 px-4 py-6 backdrop-blur-sm">
      <div className="w-full max-w-sm rounded-2xl border border-gray-800 bg-gray-950 p-5 shadow-2xl">
        <p className="text-center text-lg font-semibold text-white">
          ¿Deseás cerrar sesión?
        </p>

        <div className="mt-5 grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={handleLogout}
            className="rounded-xl border border-red-800 bg-red-950 px-3 py-2 text-sm font-semibold text-red-100 hover:bg-red-900"
          >
            Cerrar sesión
          </button>

          <button
            type="button"
            onClick={handleContinue}
            className="rounded-xl bg-white px-3 py-2 text-sm font-semibold text-gray-950 hover:bg-gray-100"
          >
            Continuar
          </button>
        </div>
      </div>
    </div>
  );
}

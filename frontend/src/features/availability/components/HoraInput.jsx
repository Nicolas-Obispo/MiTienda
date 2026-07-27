import { useEffect, useId, useRef, useState } from "react";

const HORAS_OPCIONES = Array.from({ length: 48 }, (_, index) => {
  const horas = String(Math.floor(index / 2)).padStart(2, "0");
  const minutos = index % 2 === 0 ? "00" : "30";
  return `${horas}:${minutos}`;
});

function normalizarEntradaHora(valor) {
  const texto = String(valor || "");

  if (texto.includes(":")) {
    return texto.replace(/[^\d:]/g, "").slice(0, 5);
  }

  const digitos = texto.replace(/\D/g, "").slice(0, 4);

  if (digitos.length <= 2) {
    return digitos;
  }

  return `${digitos.slice(0, 2)}:${digitos.slice(2)}`;
}

function obtenerIndiceActivo(valor) {
  const index = HORAS_OPCIONES.indexOf(valor);
  return index >= 0 ? index : 0;
}

export default function HoraInput({
  id,
  label,
  value,
  onChange,
  isOpen,
  onOpenChange,
  disabled = false,
}) {
  const generatedId = useId();
  const inputId = id || generatedId;
  const listboxId = `${inputId}-opciones`;
  const rootRef = useRef(null);
  const [activeIndex, setActiveIndex] = useState(() =>
    obtenerIndiceActivo(value)
  );

  useEffect(() => {
    if (!isOpen) return undefined;

    function handlePointerDown(event) {
      if (!rootRef.current?.contains(event.target)) {
        onOpenChange(false);
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("touchstart", handlePointerDown);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("touchstart", handlePointerDown);
    };
  }, [isOpen, onOpenChange]);

  function seleccionarHora(hora) {
    onChange(hora);
    onOpenChange(false);
  }

  function abrirOpciones() {
    setActiveIndex(obtenerIndiceActivo(value));
    onOpenChange(true);
  }

  function handleKeyDown(event) {
    if (event.key === "Escape") {
      if (isOpen) {
        event.stopPropagation();
      }
      onOpenChange(false);
      return;
    }

    if (event.key === "Tab") {
      onOpenChange(false);
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      if (!isOpen) {
        abrirOpciones();
        return;
      }
      setActiveIndex((index) => Math.min(index + 1, HORAS_OPCIONES.length - 1));
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      if (!isOpen) {
        abrirOpciones();
        return;
      }
      setActiveIndex((index) => Math.max(index - 1, 0));
      return;
    }

    if (event.key === "Enter" && isOpen) {
      event.preventDefault();
      seleccionarHora(HORAS_OPCIONES[activeIndex]);
    }
  }

  return (
    <div ref={rootRef} className="relative">
      <label htmlFor={inputId} className="text-xs text-gray-400">
        {label}
      </label>
      <input
        id={inputId}
        type="text"
        inputMode="numeric"
        autoComplete="off"
        value={value}
        disabled={disabled}
        role="combobox"
        aria-expanded={isOpen}
        aria-controls={listboxId}
        aria-activedescendant={
          isOpen ? `${listboxId}-${activeIndex}` : undefined
        }
        onFocus={abrirOpciones}
        onClick={abrirOpciones}
        onChange={(event) => onChange(normalizarEntradaHora(event.target.value))}
        onKeyDown={handleKeyDown}
        placeholder="HH:mm"
        className="mt-1 w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white outline-none transition focus:border-gray-500 focus:ring-2 focus:ring-white/10 disabled:opacity-60"
      />

      {isOpen ? (
        <div
          id={listboxId}
          role="listbox"
          className="absolute left-0 right-0 z-[60] mt-1 max-h-56 overflow-y-auto rounded-lg border border-gray-700 bg-gray-950 py-1 shadow-xl"
        >
          {HORAS_OPCIONES.map((hora, index) => (
            <button
              key={hora}
              id={`${listboxId}-${index}`}
              type="button"
              role="option"
              aria-selected={value === hora}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => seleccionarHora(hora)}
              className={`block w-full px-3 py-2 text-left text-sm transition ${
                index === activeIndex
                  ? "bg-gray-800 text-white"
                  : "text-gray-200 hover:bg-gray-900"
              }`}
            >
              {hora}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

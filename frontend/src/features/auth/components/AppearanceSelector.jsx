import { useTheme } from "@core";

const APPEARANCE_OPTIONS = [
  {
    value: "dark",
    label: "Fondo oscuro",
    description: "Conserva la apariencia oscura de FeedGo.",
  },
  {
    value: "light",
    label: "Fondo claro",
    description: "Usa superficies claras y texto oscuro.",
  },
  {
    value: "system",
    label: "Usar configuración del sistema",
    description: "Acompaña automáticamente la apariencia de tu dispositivo.",
  },
];

export default function AppearanceSelector() {
  const { preference, setPreference } = useTheme();

  return (
    <fieldset className="space-y-2" aria-describedby="appearance-help">
      <legend className="text-sm font-semibold text-primary">Apariencia</legend>
      <p id="appearance-help" className="text-xs text-secondary">
        Elegí cómo querés ver FeedGo en este dispositivo.
      </p>

      <div className="grid gap-2 sm:grid-cols-3">
        {APPEARANCE_OPTIONS.map((option) => {
          const isSelected = preference === option.value;

          return (
            <label
              key={option.value}
              className={[
                "interactive-bubble interactive-bubble--secondary flex cursor-pointer items-start justify-start gap-3 rounded-xl p-3 text-left",
                "focus-within:outline focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-focus-ring",
                isSelected
                  ? "border-border-strong bg-surface text-primary shadow-elevation"
                  : "border-border bg-surface-subtle text-primary hover:bg-surface",
              ].join(" ")}
            >
              <input
                type="radio"
                name="theme-preference"
                value={option.value}
                checked={isSelected}
                onChange={() => setPreference(option.value)}
                className="mt-0.5 h-4 w-4 shrink-0 accent-brand"
              />
              <span className="min-w-0">
                <span className="block text-sm font-semibold">
                  {option.label}
                </span>
                <span className="mt-1 block text-xs text-secondary">
                  {option.description}
                </span>
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

import { useState } from "react";

import { useGeographicContext } from "@shared/location/useGeographicContext";
import { Alert, Button, FormControl, Input, Surface } from "@shared/components/primitives";

export default function GeographicContextControls() {
  const {
    context,
    browserPermission,
    error,
    permissionState,
    hasTerritory,
    requestDeviceLocation,
    selectManualTerritory,
  } = useGeographicContext();
  const [manualOpen, setManualOpen] = useState(false);
  const [city, setCity] = useState("");
  const [province, setProvince] = useState("");

  const requesting = permissionState === "requesting";
  const needsAttention = !hasTerritory || Boolean(error);

  function submitManual(event) {
    event.preventDefault();
    selectManualTerritory({ city, province, source: "manual" });
    setManualOpen(false);
  }

  return (
    <Surface as="section" variant="subtle" className="p-2" aria-labelledby="geographic-context-title">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p id="geographic-context-title" className="text-sm font-semibold">
            {hasTerritory ? context.city : "Ubicación no disponible"}
          </p>
          {hasTerritory && (
            <p className="text-xs text-secondary">
              {context.source === "device"
                ? "Ubicación actual detectada"
                : context.source === "profile_fallback"
                  ? "Ciudad de tu perfil (seleccionada como referencia)"
                  : "Ubicación seleccionada manualmente"}
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {(context.source !== "device" || browserPermission === "denied" || needsAttention) && <Button
            type="button"
            disabled={requesting}
            onClick={() => requestDeviceLocation({ needDistance: true, force: hasTerritory })}
            variant="secondary"
            className="px-3 py-2 text-xs"
          >
            {requesting ? "Obteniendo ubicación…" : "Habilitar ubicación exacta"}
          </Button>
          }
          <Button
            type="button"
            onClick={() => setManualOpen((value) => !value)}
            variant="secondary"
            className="px-3 py-2 text-xs"
          >
            Cambiar ciudad
          </Button>
        </div>
      </div>

      {!hasTerritory && (
        <p className="mt-2 text-xs text-secondary">
          Elegí una ciudad para explorar. La distancia exacta requiere habilitar ubicación.
        </p>
      )}

      {error && (
        <Alert className="mt-2 p-3 text-xs" role="status" variant="warning">
          {error}
        </Alert>
      )}

      {context.attribution?.url && context.attribution?.label && (
        <a
          href={context.attribution.url}
          target="_blank"
          rel="noreferrer"
          className="mt-2 inline-block text-xs text-brand underline decoration-current underline-offset-2 hover:text-brand-strong focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
        >
          {context.attribution.label}
        </a>
      )}

      {manualOpen && (
        <form onSubmit={submitManual} className="mt-3 grid gap-2 sm:grid-cols-3">
          <FormControl label="Provincia" labelFor="territorio-provincia">
            <Input
              id="territorio-provincia"
              required
              value={province}
              onChange={(event) => setProvince(event.target.value)}
              className="text-sm"
            />
          </FormControl>
          <FormControl label="Ciudad" labelFor="territorio-ciudad">
            <Input
              id="territorio-ciudad"
              required
              value={city}
              onChange={(event) => setCity(event.target.value)}
              className="text-sm"
            />
          </FormControl>
          <Button type="submit" variant="primary" className="self-end px-3 py-2 text-xs">
            Buscar en esta ciudad
          </Button>
        </form>
      )}
    </Surface>
  );
}

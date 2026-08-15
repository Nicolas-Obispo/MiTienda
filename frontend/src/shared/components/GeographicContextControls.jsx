import { useState } from "react";

import { useAuth } from "@features/auth/hooks/useAuth";
import { useGeographicContext } from "@shared/location/useGeographicContext";
import { Alert, Button, FormControl, Input, Surface } from "@shared/components/primitives";

export default function GeographicContextControls() {
  const { usuario } = useAuth();
  const {
    context,
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
  const profileAvailable = Boolean(usuario?.ciudad && usuario?.provincia);

  function submitManual(event) {
    event.preventDefault();
    selectManualTerritory({ city, province, source: "manual" });
    setManualOpen(false);
  }

  return (
    <Surface as="section" variant="subtle" className="p-3" aria-labelledby="geographic-context-title">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p id="geographic-context-title" className="text-sm font-semibold">
            {hasTerritory ? `Resultados cerca de ${context.city}` : "Elegí dónde buscar"}
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
          <Button
            type="button"
            disabled={requesting}
            onClick={() => requestDeviceLocation({ needDistance: true, force: hasTerritory })}
            variant="secondary"
            className="px-3 py-2 text-xs"
          >
            {requesting ? "Obteniendo ubicación…" : hasTerritory ? "Actualizar ubicación" : "Usar mi ubicación"}
          </Button>
          <Button
            type="button"
            onClick={() => setManualOpen((value) => !value)}
            variant="secondary"
            className="px-3 py-2 text-xs"
          >
            Elegir ciudad
          </Button>
        </div>
      </div>

      {context.source !== "device" && (
        <p className="mt-2 text-xs text-secondary">
          FeedGo usa tu ubicación mientras utilizás la app para determinar tu zona,
          mostrarte resultados cercanos y calcular distancias. No guardamos un
          historial de tus desplazamientos.
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
          {profileAvailable && (
            <Button
              type="button"
              onClick={() => {
                selectManualTerritory({
                  city: usuario.ciudad,
                  province: usuario.provincia,
                  source: "profile_fallback",
                });
                setManualOpen(false);
              }}
              variant="ghost"
              className="justify-start text-left text-xs underline sm:col-span-3"
            >
              Usar {usuario.ciudad}, {usuario.provincia} desde mi perfil
            </Button>
          )}
        </form>
      )}
    </Surface>
  );
}

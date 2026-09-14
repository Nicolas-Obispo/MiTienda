import { useState } from "react";

import { solicitarRecuperacionPassword } from "@features/auth";
import { Button, FormControl, Input, Surface } from "@shared";

const UNIFORM_MESSAGE = "Si ese usuario está registrado, te vamos a enviar un enlace para crear una nueva contraseña.";

export default function RecuperarPassword() {
  const [email, setEmail] = useState("");
  const [sending, setSending] = useState(false);
  const [done, setDone] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setSending(true);
    await solicitarRecuperacionPassword(email);
    setDone(true);
    setSending(false);
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-canvas px-4 text-primary">
      <Surface variant="elevated" className="w-full max-w-md p-6">
        <h1 className="text-2xl font-semibold">Crear una nueva contraseña</h1>
        {!done ? (
          <form onSubmit={submit} className="mt-5 space-y-4">
            <FormControl label="Usuario" labelFor="recuperacion-email">
              <Input
                id="recuperacion-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="nombre@correo.com"
                required
              />
              <p className="mt-2 text-sm text-secondary">Ingresá el correo que usás en FeedGo.</p>
            </FormControl>
            <Button type="submit" disabled={sending} className="w-full">
              {sending ? "Enviando..." : "Enviar enlace"}
            </Button>
          </form>
        ) : (
          <p className="mt-5 text-sm text-secondary" role="status">{UNIFORM_MESSAGE}</p>
        )}
      </Surface>
    </main>
  );
}

import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import {
  EMAIL_VERIFICATION_INVALID,
  EMAIL_VERIFICATION_RATE_LIMITED,
  confirmarEmail,
  extraerTokenVerificacionDelFragmento,
  reenviarVerificacionEmail,
  useAuth,
} from "@features/auth";
import { Button, Surface } from "@shared";
import { getInternalReturnTo } from "@core/navigation/internalReturnTo";

async function tokenFingerprint(secret) {
  const bytes = new TextEncoder().encode(secret);
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0")
  ).join("");
}

export default function VerificarEmail() {
  const location = useLocation();
  const {
    accessToken,
    estaAutenticado,
    usuario,
    isCargandoUsuario,
    refrescarUsuario,
    clearPostAuthDestination,
  } = useAuth();
  const pendingSecretRef = useRef(null);
  const operationsByNavigationRef = useRef(new Map());
  const operationsByDigestRef = useRef(new Map());
  const processedDigestsRef = useRef(new Set());
  const [tokenNavigation, setTokenNavigation] = useState(0);
  const [tokenReady, setTokenReady] = useState(false);
  const initialDelivery = location.state?.registrationEmailStatus;
  const returnTo = getInternalReturnTo(location.state?.returnTo, "/feed");
  const [status, setStatus] = useState(
    initialDelivery === "sent"
      ? "sent"
      : initialDelivery === "delivery_failed"
        ? "delivery_failed"
        : "processing"
  );
  const [sending, setSending] = useState(false);
  const [isProcessingToken, setIsProcessingToken] = useState(false);
  const emailVerificado = Boolean(usuario?.email_verified_at);

  const captureTokenFromFragment = useCallback(() => {
    const extracted = extraerTokenVerificacionDelFragmento();
    if (extracted) {
      pendingSecretRef.current = extracted;
      setIsProcessingToken(true);
      setStatus("processing");
      setTokenNavigation((current) => current + 1);
    }
  }, []);

  useLayoutEffect(() => {
    clearPostAuthDestination();
  }, [clearPostAuthDestination]);

  useLayoutEffect(() => {
    captureTokenFromFragment();
    setTokenReady(true);
  }, [captureTokenFromFragment, location.hash, location.key]);

  useLayoutEffect(() => {
    window.addEventListener("hashchange", captureTokenFromFragment);
    return () => window.removeEventListener("hashchange", captureTokenFromFragment);
  }, [captureTokenFromFragment]);

  useEffect(() => {
    if (!tokenNavigation) return undefined;

    let operation = operationsByNavigationRef.current.get(tokenNavigation);
    if (!operation) {
      const secret = pendingSecretRef.current;
      pendingSecretRef.current = null;
      if (!secret) return undefined;

      operation = (async () => {
        const digest = await tokenFingerprint(secret);
        if (processedDigestsRef.current.has(digest)) {
          return { status: "already_processed" };
        }

        let confirmation = operationsByDigestRef.current.get(digest);
        if (!confirmation) {
          confirmation = (async () => {
            try {
              await confirmarEmail(secret);
              processedDigestsRef.current.add(digest);
              if (!estaAutenticado) return { status: "verified" };
              const me = await refrescarUsuario();
              return {
                status: me?.email_verified_at ? "verified" : "technical_error",
              };
            } catch (error) {
              processedDigestsRef.current.add(digest);
              return {
                status: error.code === EMAIL_VERIFICATION_INVALID
                  ? "invalid"
                  : "technical_error",
              };
            } finally {
              operationsByDigestRef.current.delete(digest);
            }
          })();
          operationsByDigestRef.current.set(digest, confirmation);
        }
        return confirmation;
      })();
      operationsByNavigationRef.current.set(tokenNavigation, operation);
      void operation.finally(() => {
        operationsByNavigationRef.current.delete(tokenNavigation);
      });
    }

    let active = true;
    operation.then((result) => {
      if (!active) return;
      if (result.status !== "already_processed") setStatus(result.status);
      setIsProcessingToken(false);
    });

    return () => {
      active = false;
    };
  }, [estaAutenticado, refrescarUsuario, tokenNavigation]);

  useEffect(() => {
    if (
      tokenReady &&
      !isProcessingToken &&
      !tokenNavigation &&
      !initialDelivery &&
      !estaAutenticado
    ) {
      setStatus("invalid");
    }
  }, [estaAutenticado, initialDelivery, isProcessingToken, tokenNavigation, tokenReady]);

  useEffect(() => {
    if (!tokenReady || isProcessingToken || !estaAutenticado || isCargandoUsuario) return;
    if (emailVerificado) {
      setStatus("verified");
    } else if (!initialDelivery) {
      setStatus("unverified");
    }
  }, [emailVerificado, estaAutenticado, initialDelivery, isCargandoUsuario, isProcessingToken, tokenReady]);

  async function resend() {
    if (!accessToken || sending) return;
    setSending(true);
    try {
      const result = await reenviarVerificacionEmail(accessToken);
      const me = await refrescarUsuario();
      setStatus(
        result.status === "already_verified" && me?.email_verified_at
          ? "verified"
          : "sent"
      );
    } catch (error) {
      setStatus(error.code === EMAIL_VERIFICATION_RATE_LIMITED ? "cooldown" : "delivery_failed");
    } finally {
      setSending(false);
    }
  }

  const messages = {
    processing: "Estamos verificando tu cuenta...",
    verified: "Listo, tu cuenta ya está verificada.",
    sent: "Te enviamos un enlace para verificar tu cuenta.",
    unverified: "Verificá tu cuenta para continuar.",
    delivery_failed: "No pudimos enviar el enlace ahora. Podés pedir otro en un momento.",
    cooldown: "Podés pedir otro enlace en unos segundos.",
    invalid: "Este enlace ya no es válido. Pedí uno nuevo para continuar.",
    technical_error: "No pudimos completar esto ahora. Intentá nuevamente en un momento.",
  };

  const canResend = ["sent", "unverified", "delivery_failed", "cooldown", "invalid"].includes(status);
  const showAuthenticatedResend = canResend && estaAutenticado && !emailVerificado;

  return (
    <main className="flex min-h-screen items-center justify-center bg-canvas px-4 text-primary">
      <Surface variant="elevated" className="w-full max-w-md p-6 text-center">
        <img src="/logo_Feedgo.png" alt="FeedGo" className="mx-auto h-24 w-24 object-contain" />
        <h1 className="mt-3 text-2xl font-semibold">Verificar cuenta</h1>
        <p className="mt-3 text-sm text-secondary" role="status" aria-live="polite">
          {messages[status]}
        </p>
        {showAuthenticatedResend && (
          <Button type="button" onClick={resend} disabled={sending} className="mt-5">
            {sending ? "Enviando..." : "Enviar otro enlace"}
          </Button>
        )}
        {canResend && !estaAutenticado && (
          <Link className="mt-5 inline-block font-medium text-brand underline" to="/login">
            Iniciar sesión para pedir otro enlace
          </Link>
        )}
        {status === "verified" && (
          <Link className="mt-5 inline-block font-medium text-brand underline" to={returnTo}>
            Continuar
          </Link>
        )}
      </Surface>
    </main>
  );
}

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { QueryClient } from "@tanstack/react-query";

import { queryKeys } from "../src/core/constants/queryKeys.js";
import {
  aplicarSeguimientoEnCache,
  crearEstadoSeguimientoOptimista,
  restaurarSeguimientoCaches,
  snapshotSeguimientoCaches,
} from "../src/features/spaces/utils/seguimientoCache.js";

const [profile, hook, service, feed, ranking, explore, auth] = await Promise.all([
  readFile(new URL("../src/features/spaces/pages/PerfilComercioPage.jsx", import.meta.url), "utf8"),
  readFile(new URL("../src/features/spaces/hooks/useSeguimientoEspacio.js", import.meta.url), "utf8"),
  readFile(new URL("../src/features/spaces/services/seguidores_service.js", import.meta.url), "utf8"),
  readFile(new URL("../src/features/feed/pages/FeedPage.jsx", import.meta.url), "utf8"),
  readFile(new URL("../src/features/posts/pages/RankingPage.jsx", import.meta.url), "utf8"),
  readFile(new URL("../src/features/explore/pages/ExplorarPage.jsx", import.meta.url), "utf8"),
  readFile(new URL("../src/features/auth/context/AuthContext.jsx", import.meta.url), "utf8"),
]);

function createClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

test("true y false confirmados permanecen estados semanticos distintos", () => {
  assert.equal(crearEstadoSeguimientoOptimista({ siguiendo: false }).siguiendo, true);
  assert.equal(crearEstadoSeguimientoOptimista({ siguiendo: true }).siguiendo, false);
  assert.equal(crearEstadoSeguimientoOptimista(undefined), undefined);
});

test("unknown y error sin cache no inventan false", async () => {
  const client = createClient();
  const key = queryKeys.spaces.followingStatus(5);
  assert.equal(client.getQueryData(key), undefined);
  await assert.rejects(
    client.fetchQuery({ queryKey: key, queryFn: async () => { throw new Error("offline"); } }),
    /offline/
  );
  assert.equal(client.getQueryData(key), undefined);
  assert.match(profile, /seguimientoDesconocido[\s\S]*"Comprobando\.\.\."/);
  assert.match(profile, /disabled=\{[\s\S]*seguimientoDesconocido/);
  assert.doesNotMatch(profile, /seguimientoPerfilComercioCache|seguimientoHydratado/);
});

test("cache confirmada se conserva durante refresh fallido", async () => {
  const client = createClient();
  const key = queryKeys.spaces.followingStatus(5);
  const refresh = deferred();
  client.setQueryData(key, { siguiendo: true, seguidores_count: 3 });
  const request = client.fetchQuery({ queryKey: key, queryFn: () => refresh.promise, staleTime: 0 });
  assert.equal(client.getQueryData(key).siguiendo, true);
  refresh.reject(new Error("offline"));
  await assert.rejects(request, /offline/);
  assert.equal(client.getQueryData(key).siguiendo, true);
});

test("A lenta y B rapida nunca comparten cache ni sobrescriben IDs", async () => {
  const client = createClient();
  const slowA = deferred();
  const fastB = deferred();
  const requestA = client.fetchQuery({
    queryKey: queryKeys.spaces.followingStatus(1),
    queryFn: () => slowA.promise,
  });
  const requestB = client.fetchQuery({
    queryKey: queryKeys.spaces.followingStatus(2),
    queryFn: () => fastB.promise,
  });
  fastB.resolve({ siguiendo: true, seguidores_count: 8 });
  await requestB;
  slowA.resolve({ siguiendo: false, seguidores_count: 2 });
  await requestA;
  assert.equal(client.getQueryData(queryKeys.spaces.followingStatus(2)).siguiendo, true);
  assert.equal(client.getQueryData(queryKeys.spaces.followingStatus(1)).siguiendo, false);
});

test("cambio de usuario limpia el estado junto con TanStack", () => {
  const client = createClient();
  client.setQueryData(queryKeys.spaces.followingStatus(5), { siguiendo: true });
  client.clear();
  assert.equal(client.getQueryData(queryKeys.spaces.followingStatus(5)), undefined);
  assert.match(auth, /queryClient\.clear\(\)/);
});

test("follow y unfollow reconcilian status y todas las listas Seguidos", () => {
  const client = createClient();
  const statusKey = queryKeys.spaces.followingStatus(5);
  const listA = queryKeys.spaces.seguidos({ positionRevision: 0 });
  const listB = queryKeys.spaces.seguidos({ positionRevision: 3 });
  const comercio = { id: 5, nombre: "Espacio" };
  client.setQueryData(statusKey, { siguiendo: false, seguidores_count: 2 });
  client.setQueryData(listA, []);
  client.setQueryData(listB, []);
  aplicarSeguimientoEnCache({
    queryClient: client,
    comercioId: 5,
    comercio,
    estado: { siguiendo: true, seguidores_count: 3 },
  });
  assert.equal(client.getQueryData(statusKey).siguiendo, true);
  assert.deepEqual(client.getQueryData(listA), [comercio]);
  assert.deepEqual(client.getQueryData(listB), [comercio]);
  aplicarSeguimientoEnCache({
    queryClient: client,
    comercioId: 5,
    comercio,
    estado: { siguiendo: false, seguidores_count: 2 },
  });
  assert.deepEqual(client.getQueryData(listA), []);
  assert.deepEqual(client.getQueryData(listB), []);
});

test("rollback restaura status y listas Seguidos", () => {
  const client = createClient();
  const statusKey = queryKeys.spaces.followingStatus(5);
  const listKey = queryKeys.spaces.seguidos();
  client.setQueryData(statusKey, { siguiendo: false, seguidores_count: 2 });
  client.setQueryData(listKey, []);
  const snapshot = snapshotSeguimientoCaches(client, 5);
  aplicarSeguimientoEnCache({
    queryClient: client,
    comercioId: 5,
    comercio: { id: 5 },
    estado: { siguiendo: true, seguidores_count: 3 },
  });
  restaurarSeguimientoCaches(client, 5, snapshot);
  assert.equal(client.getQueryData(statusKey).siguiendo, false);
  assert.deepEqual(client.getQueryData(listKey), []);
});

test("hook usa key estructural, cancelacion, respuesta final y bloquea unknown", () => {
  assert.match(hook, /queryKeys\.spaces\.followingStatus\(id\)/);
  assert.match(hook, /queryFn: \(\{ signal \}\)[\s\S]*\{ signal \}/);
  assert.match(hook, /enabled: enabled && comercioIdValido\(id\)/);
  assert.match(hook, /typeof siguiendoActual !== "boolean"/);
  assert.match(hook, /onSuccess: \(estadoConfirmado\)/);
  assert.doesNotMatch(hook, /onSuccess[\s\S]*obtenerEstadoSeguimiento/);
  assert.match(service, /obtenerEstadoSeguimiento\(comercioId, \{ signal \} = \{\}\)/);
});

test("Feed, Ranking y Explorar no consultan seguimiento por card e invitado conserva gate", () => {
  for (const source of [feed, ranking, explore]) {
    assert.doesNotMatch(source, /obtenerEstadoSeguimiento|followingStatus|seguidores\/espacios/);
  }
  assert.match(profile, /if \(usuarioDebeLoguearse\(\)\) return/);
  assert.match(profile, /estaAutenticado && typeof siguiendoConfirmado !== "boolean"/);
});

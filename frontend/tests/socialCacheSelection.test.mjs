import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { QueryClient, QueryObserver } from "@tanstack/react-query";

import { queryKeys } from "../src/core/constants/queryKeys.js";
import {
  actualizarGuardadasOptimistaEnCache,
  aplicarGuardadoOptimistaEnCache,
  aplicarLikeOptimistaEnCache,
  guardadoQueryFilters,
  invalidarGuardadoQueries,
  invalidarLikeQueries,
  likeQueryFilters,
  restaurarSnapshotCache,
  snapshotPublicacionesCache,
} from "../src/features/social/utils/socialCacheUtils.js";

const socialCacheSource = await readFile(
  new URL("../src/features/social/utils/socialCacheUtils.js", import.meta.url),
  "utf8"
);
const likeMutationSource = await readFile(
  new URL("../src/features/social/mutations/useToggleLikePublicacionMutation.js", import.meta.url),
  "utf8"
);
const savedMutationSource = await readFile(
  new URL("../src/features/social/mutations/useToggleGuardadoPublicacionMutation.js", import.meta.url),
  "utf8"
);

const publication = {
  id: 20,
  liked_by_me: false,
  guardada_by_me: false,
  likes_count: 2,
  guardados_count: 3,
  interacciones_count: 5,
};

const keys = {
  feed: queryKeys.feed.publicaciones(),
  ranking: queryKeys.ranking.publicaciones(),
  detail: queryKeys.posts.detalle(20),
  saved: queryKeys.posts.guardadas(),
  space: queryKeys.spaces.publicaciones(10),
  explore: queryKeys.explore.posts({ q: null, limit: 20, offset: 0 }),
  unrelated: queryKeys.agenda.contexto(10),
  substringOnly: ["future", "posts-archive"],
};

function createClient() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  client.setQueryData(keys.feed, [publication]);
  client.setQueryData(keys.ranking, [publication]);
  client.setQueryData(keys.detail, publication);
  client.setQueryData(keys.saved, []);
  client.setQueryData(keys.space, [publication]);
  client.setQueryData(keys.explore, [publication]);
  client.setQueryData(keys.unrelated, { id: 20, value: "agenda" });
  client.setQueryData(keys.substringOnly, [publication]);
  return client;
}

test("like actualiza solamente familias explicitas de publicaciones", () => {
  const client = createClient();

  aplicarLikeOptimistaEnCache(client, 20);

  for (const key of [keys.feed, keys.ranking, keys.detail, keys.space, keys.explore]) {
    const data = client.getQueryData(key);
    const item = Array.isArray(data) ? data[0] : data;
    assert.equal(item.liked_by_me, true);
    assert.equal(item.likes_count, 3);
  }
  assert.deepEqual(client.getQueryData(keys.saved), []);
  assert.deepEqual(client.getQueryData(keys.unrelated), { id: 20, value: "agenda" });
  assert.equal(client.getQueryData(keys.substringOnly)[0].liked_by_me, false);
});

test("guardado actualiza familias y mantiene la coleccion de guardadas", () => {
  const client = createClient();

  aplicarGuardadoOptimistaEnCache(client, 20);
  actualizarGuardadasOptimistaEnCache({
    queryClient: client,
    publicacionId: 20,
    estabaGuardada: false,
  });

  assert.equal(client.getQueryData(keys.feed)[0].guardada_by_me, true);
  assert.equal(client.getQueryData(keys.detail).guardada_by_me, true);
  assert.equal(client.getQueryData(keys.space)[0].guardados_count, 4);
  assert.equal(client.getQueryData(keys.saved)[0].id, 20);
  assert.equal(client.getQueryData(keys.substringOnly)[0].guardada_by_me, false);

  aplicarGuardadoOptimistaEnCache(client, 20);
  actualizarGuardadasOptimistaEnCache({
    queryClient: client,
    publicacionId: 20,
    estabaGuardada: true,
  });
  assert.deepEqual(client.getQueryData(keys.saved), []);
});

test("rollback restaura solo caches seleccionadas", () => {
  const client = createClient();
  const snapshot = snapshotPublicacionesCache(client, likeQueryFilters());

  aplicarLikeOptimistaEnCache(client, 20);
  client.setQueryData(keys.unrelated, { id: 20, value: "changed" });
  restaurarSnapshotCache(client, snapshot);

  assert.equal(client.getQueryData(keys.feed)[0].liked_by_me, false);
  assert.equal(client.getQueryData(keys.detail).liked_by_me, false);
  assert.deepEqual(client.getQueryData(keys.unrelated), {
    id: 20,
    value: "changed",
  });
});

test("reconciliacion marca listas stale sin refetch inmediato", async () => {
  for (const invalidate of [invalidarLikeQueries, invalidarGuardadoQueries]) {
    const client = createClient();
    const requests = { feed: 0, ranking: 0 };
    const observers = [
      new QueryObserver(client, {
        queryKey: keys.feed,
        queryFn: async () => {
          requests.feed += 1;
          return [publication];
        },
        staleTime: Infinity,
      }),
      new QueryObserver(client, {
        queryKey: keys.ranking,
        queryFn: async () => {
          requests.ranking += 1;
          return [publication];
        },
        staleTime: Infinity,
      }),
    ];
    const unsubscribes = observers.map((observer) =>
      observer.subscribe(() => {})
    );

    await invalidate(client);
    await new Promise((resolve) => setTimeout(resolve, 0));

    for (const key of [keys.feed, keys.ranking, keys.space, keys.explore]) {
      assert.equal(client.getQueryState(key).isInvalidated, true);
    }
    assert.equal(client.getQueryState(keys.detail).isInvalidated, false);
    assert.equal(client.getQueryState(keys.saved).isInvalidated, false);
    assert.equal(client.getQueryState(keys.unrelated).isInvalidated, false);
    assert.equal(client.getQueryState(keys.substringOnly).isInvalidated, false);
    assert.deepEqual(requests, { feed: 0, ranking: 0 });
    unsubscribes.forEach((unsubscribe) => unsubscribe());
  }
});

test("like y guardado conservan orden durante optimistic update", () => {
  for (const update of [
    aplicarLikeOptimistaEnCache,
    aplicarGuardadoOptimistaEnCache,
  ]) {
    const client = createClient();
    client.setQueryData(keys.feed, [
      { ...publication, id: 30 },
      publication,
      { ...publication, id: 10 },
    ]);
    const before = client.getQueryData(keys.feed).map(({ id }) => id);

    update(client, 20);

    assert.deepEqual(
      client.getQueryData(keys.feed).map(({ id }) => id),
      before
    );
  }
});

test("rollback restaura estado y orden sin refetch inmediato", async () => {
  const client = createClient();
  client.setQueryData(keys.feed, [
    { ...publication, id: 30 },
    publication,
    { ...publication, id: 10 },
  ]);
  const snapshot = snapshotPublicacionesCache(client, likeQueryFilters());

  aplicarLikeOptimistaEnCache(client, 20);
  restaurarSnapshotCache(client, snapshot);
  await invalidarLikeQueries(client);

  assert.deepEqual(
    client.getQueryData(keys.feed).map(({ id, liked_by_me }) => ({
      id,
      liked_by_me,
    })),
    [
      { id: 30, liked_by_me: false },
      { id: 20, liked_by_me: false },
      { id: 10, liked_by_me: false },
    ]
  );
});

test("refresh normal posterior puede adoptar el orden del backend", async () => {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  client.setQueryDefaults(keys.feed, {
    queryFn: async () => [
      { ...publication, id: 10 },
      publication,
      { ...publication, id: 30 },
    ],
  });
  client.setQueryData(keys.feed, [
    { ...publication, id: 30 },
    publication,
    { ...publication, id: 10 },
  ]);

  await invalidarLikeQueries(client);
  assert.deepEqual(
    client.getQueryData(keys.feed).map(({ id }) => id),
    [30, 20, 10]
  );

  await client.refetchQueries({ queryKey: keys.feed, exact: true });
  assert.deepEqual(
    client.getQueryData(keys.feed).map(({ id }) => id),
    [10, 20, 30]
  );
});

test("detalle activo no se refetchea por invalidacion social", async () => {
  for (const invalidate of [invalidarLikeQueries, invalidarGuardadoQueries]) {
    const client = createClient();
    let detailRequests = 0;
    const observer = new QueryObserver(client, {
      queryKey: keys.detail,
      queryFn: async () => {
        detailRequests += 1;
        return publication;
      },
      staleTime: Infinity,
    });
    const unsubscribe = observer.subscribe(() => {});

    await invalidate(client);
    await new Promise((resolve) => setTimeout(resolve, 0));

    assert.equal(detailRequests, 0);
    assert.equal(client.getQueryState(keys.detail).isInvalidated, false);
    unsubscribe();
  }
});

test("mutaciones usan filtros diferenciados sin seleccion textual", () => {
  assert.doesNotMatch(socialCacheSource, /JSON\.stringify|\.includes\(/);
  assert.match(socialCacheSource, /prefix\.every\(\(segment, index\) => queryKey\[index\] === segment\)/);
  assert.match(socialCacheSource, /refetchType: "none"/);
  assert.match(likeMutationSource, /const queryFilters = likeQueryFilters\(\)/);
  assert.match(likeMutationSource, /invalidarLikeQueries\(queryClient\)/);
  assert.match(savedMutationSource, /const queryFilters = guardadoQueryFilters\(\)/);
  assert.match(savedMutationSource, /invalidarGuardadoQueries\(queryClient\)/);
  assert.doesNotMatch(`${likeMutationSource}\n${savedMutationSource}`, /invalidarPublicacionesQueries|publicacionesQueryFilters/);
  assert.equal(typeof guardadoQueryFilters().predicate, "function");
});

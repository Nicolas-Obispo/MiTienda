/*
|--------------------------------------------------------------------------
| Query Keys globales de FeedGo!
|--------------------------------------------------------------------------
|
| Responsabilidad:
| - centralizar nombres de cache
| - evitar strings sueltos
| - preparar invalidaciones limpias
| - preparar realtime/cache sync futuro
|
*/

export const queryKeys = {
  feed: {
    all: ["feed"],
    publicaciones: () => ["feed", "publicaciones"],
  },

  ranking: {
    all: ["ranking"],
    publicaciones: () => ["ranking", "publicaciones"],
  },

  posts: {
    all: ["posts"],
    detalle: (publicacionId) => ["posts", "detalle", publicacionId],
    guardadas: () => ["posts", "guardadas"],
  },

  spaces: {
    all: ["spaces"],
    detalle: (espacioId) => ["spaces", "detalle", espacioId],
    publicaciones: (espacioId) => ["spaces", "publicaciones", espacioId],
    mis: () => ["spaces", "mis"],
  },

  stories: {
    all: ["stories"],
    bar: () => ["stories", "bar"],
    bySpace: (espacioId) => ["stories", "space", espacioId],
  },

  social: {
    all: ["social"],
  },

  analytics: {
    all: ["analytics"],
    espacio: (espacioId) => ["analytics", "espacio", espacioId],
  },
};

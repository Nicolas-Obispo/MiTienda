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
    rubros: () => ["spaces", "rubros"],
    mis: () => ["spaces", "mis"],
    seguidos: ({ lat = null, lng = null } = {}) => [
      "spaces",
      "seguidos",
      { lat, lng },
    ],
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

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
    rubroEspecialidades: (rubroId) => [
      "spaces",
      "rubros",
      rubroId,
      "especialidades",
    ],
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

  agenda: {
    all: ["agenda"],
    contexto: (comercioId) => ["agenda", "contexto", Number(comercioId)],
    elementos: ({
      comercioId,
      inicio = null,
      fin = null,
      estado = null,
      tipo = null,
    } = {}) => [
      "agenda",
      "elementos",
      Number(comercioId),
      {
        inicio,
        fin,
        estado,
        tipo,
      },
    ],
    general: ({
      inicio = null,
      fin = null,
      estado = null,
      tipo = null,
      comercioId = null,
    } = {}) => [
      "agenda",
      "general",
      {
        inicio,
        fin,
        estado,
        tipo,
        comercioId,
      },
    ],
  },

  search: {
    all: ["search"],
    suggestions: ({ q = null, limit = 5 } = {}) => [
      "search",
      "suggestions",
      { q, limit },
    ],
  },

  explore: {
    all: ["explore"],
    posts: ({ q = null, limit = 20, offset = 0 } = {}) => [
      "explore",
      "posts",
      {
        q,
        limit,
        offset,
      },
    ],
    spaces: ({
      q = null,
      smart = false,
      smart_semantic = false,
      lat = null,
      lng = null,
      radio_km = null,
      limit = 20,
    } = {}) => [
      "explore",
      "spaces",
      {
        q,
        smart,
        smart_semantic,
        lat,
        lng,
        radio_km,
        limit,
      },
    ],
  },
};

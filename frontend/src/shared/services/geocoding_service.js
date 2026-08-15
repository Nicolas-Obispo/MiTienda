import { httpPost } from "@core";


function getToken() {
  const token = localStorage.getItem("access_token");
  if (!token) throw new Error("No hay sesion activa.");
  return token;
}


export function buscarDirecciones(
  { query, ciudad = null, provincia = null, limit = 5 },
  { signal } = {}
) {
  return httpPost(
    "/geocoding/forward",
    { query, ciudad, provincia, pais: "Argentina", limit },
    getToken(),
    { signal }
  );
}


export function proponerDireccion(
  { latitud, longitud },
  { signal } = {}
) {
  return httpPost(
    "/geocoding/reverse",
    { latitud, longitud },
    getToken(),
    { signal }
  );
}


export function resolverTerritorio({ latitud, longitud }, { signal } = {}) {
  return httpPost(
    "/geocoding/territory",
    { latitud, longitud },
    null,
    { signal }
  );
}

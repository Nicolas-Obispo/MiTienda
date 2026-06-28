"""
knowledge_legacy_intent_services.py
-----------------------------------
Logica legacy de intencion para Knowledge Core.

Mantiene los terminos actuales sin normalizaciones nuevas ni correcciones de
encoding para conservar compatibilidad exacta durante la migracion.
"""


def _normalizar_texto(valor: str | None) -> str:
    if not valor:
        return ""
    return valor.strip().lower()


def _tokenizar(texto: str) -> list[str]:
    """
    Tokenizacion simple (MVP).
    - Split por espacios
    - Filtra tokens vacios
    """
    if not texto:
        return []
    return [t for t in texto.split(" ") if t]


_INTENCIONES_BUSQUEDA_V2 = {
    "pizza": [
        "pizza",
        "pizzeria",
        "pizzería",
        "comida",
        "gastronomia",
        "gastronomía",
        "restaurante",
        "delivery",
        "cena",
        "kiosco",
    ],
    "hamburguesa": [
        "hamburguesa",
        "comida",
        "gastronomia",
        "gastronomía",
        "restaurante",
        "fast food",
        "cena",
    ],
    "ropa": [
        "ropa",
        "indumentaria",
        "moda",
        "boutique",
        "calzado",
        "tienda de ropa",
    ],
    "zapatos": [
        "zapatos",
        "zapato",
        "zapatillas",
        "zapatilla",
        "calzado",
        "zapateria",
        "zapatería",
        "tienda de ropa",
        "deportes",
    ],
    "zapatillas": [
        "zapatillas",
        "zapatilla",
        "zapatos",
        "calzado",
        "zapateria",
        "zapatería",
        "deportes",
    ],
    "calzado": [
        "calzado",
        "zapatos",
        "zapatillas",
        "zapateria",
        "zapatería",
        "tienda de ropa",
        "deportes",
    ],
    "deportes": [
        "deportes",
        "deportivo",
        "deportiva",
        "deportivas",
        "zapatillas deportivas",
    ],
    "deportivo": [
        "deportes",
        "deportivo",
        "deportiva",
        "deportivas",
        "zapatillas deportivas",
    ],
    "revestimientos": [
        "revestimientos",
        "revestimiento",
        "construccion",
        "construcción",
        "obra",
        "materiales",
        "hogar y construccion",
        "hogar y construcción",
        "servicios de construccion",
        "servicios de construcción",
    ],
    "construccion": [
        "construccion",
        "construcción",
        "obra",
        "materiales",
        "revestimientos",
        "hogar y construccion",
        "hogar y construcción",
        "servicios de construccion",
        "servicios de construcción",
    ],
    "construcción": [
        "construccion",
        "construcción",
        "obra",
        "materiales",
        "revestimientos",
        "hogar y construccion",
        "hogar y construcción",
        "servicios de construccion",
        "servicios de construcción",
    ],
    "obra": [
        "obra",
        "construccion",
        "construcción",
        "materiales",
        "revestimientos",
        "servicios de construccion",
        "servicios de construcción",
    ],
    "materiales": [
        "materiales",
        "construccion",
        "construcción",
        "obra",
        "revestimientos",
        "servicios de construccion",
        "servicios de construcción",
    ],
    "cafe": [
        "cafe",
        "café",
        "cafeteria",
        "cafetería",
        "desayuno",
        "merienda",
        "gastronomia",
        "gastronomía",
    ],
    "café": [
        "cafe",
        "café",
        "cafeteria",
        "cafetería",
        "desayuno",
        "merienda",
        "gastronomia",
        "gastronomía",
    ],
    "cerveza": [
        "cerveza",
        "bar",
        "bebida",
        "salida",
        "gastronomia",
        "gastronomía",
    ],
    "helado": [
        "helado",
        "heladeria",
        "heladería",
        "postre",
        "gastronomia",
        "gastronomía",
    ],
}


_INTENCION_A_FAMILIA_V2 = {
    "pizza": "gastronomia",
    "hamburguesa": "gastronomia",
    "cafe": "gastronomia",
    "café": "gastronomia",
    "cerveza": "gastronomia",
    "helado": "gastronomia",
    "ropa": "moda",
    "zapatos": "moda_calzado",
    "zapatillas": "moda_calzado",
    "calzado": "moda_calzado",
    "deportes": "deportes",
    "deportivo": "deportes",
    "revestimientos": "construccion",
    "construccion": "construccion",
    "construcción": "construccion",
    "obra": "construccion",
    "materiales": "construccion",
}


_FAMILIAS_INTENCION_V2 = {
    "gastronomia": [
        "gastronomia",
        "gastronomía",
        "kiosco",
        "comida",
        "bebida",
        "bar",
        "restaurante",
        "pizzeria",
        "pizzería",
        "cafeteria",
        "cafetería",
        "heladeria",
        "heladería",
    ],
    "moda": [
        "ropa",
        "tienda de ropa",
        "indumentaria",
        "moda",
        "boutique",
        "calzado",
        "zapateria",
        "zapatería",
    ],
    "moda_calzado": [
        "ropa",
        "tienda de ropa",
        "indumentaria",
        "moda",
        "boutique",
        "calzado",
        "zapatos",
        "zapato",
        "zapatillas",
        "zapatilla",
        "zapateria",
        "zapatería",
        "deportes",
    ],
    "deportes": [
        "deportes",
        "deportivo",
        "deportiva",
        "deportivas",
        "zapatillas deportivas",
    ],
    "construccion": [
        "construccion",
        "construcción",
        "hogar y construccion",
        "hogar y construcción",
        "servicios de construccion",
        "servicios de construcción",
        "revestimientos",
        "revestimiento",
        "obra",
        "materiales",
    ],
}


def _normalizar_lista_terminos(terminos: list[str]) -> list[str]:
    resultado: list[str] = []
    vistos: set[str] = set()

    for termino in terminos:
        termino_normalizado = _normalizar_texto(termino)

        if termino_normalizado and termino_normalizado not in vistos:
            resultado.append(termino_normalizado)
            vistos.add(termino_normalizado)

    return resultado


def _obtener_familia_intencion(q: str) -> str | None:
    q_normalizada = _normalizar_texto(q)

    if not q_normalizada:
        return None

    if q_normalizada in _INTENCION_A_FAMILIA_V2:
        return _INTENCION_A_FAMILIA_V2[q_normalizada]

    for token in _tokenizar(q_normalizada):
        if token in _INTENCION_A_FAMILIA_V2:
            return _INTENCION_A_FAMILIA_V2[token]

    return None


def _terminos_familia_intencion(q: str) -> list[str]:
    familia = _obtener_familia_intencion(q)

    if not familia:
        return []

    return _normalizar_lista_terminos(_FAMILIAS_INTENCION_V2.get(familia, []))


def _expandir_intencion_busqueda(q: str) -> list[str]:
    """
    Expande consultas cortas a terminos de intencion controlados.

    La expansion vive en backend para mantener React como capa de UI/cache.
    Si no hay match, conserva la busqueda original.
    """
    q_normalizada = _normalizar_texto(q)

    if not q_normalizada:
        return []

    terminos: list[str] = [q_normalizada]

    for token in _tokenizar(q_normalizada):
        terminos.extend(_INTENCIONES_BUSQUEDA_V2.get(token, []))

    if q_normalizada in _INTENCIONES_BUSQUEDA_V2:
        terminos.extend(_INTENCIONES_BUSQUEDA_V2[q_normalizada])

    resultado = _normalizar_lista_terminos(terminos)
    return resultado or [q_normalizada]


def _tiene_intencion_conocida(q: str) -> bool:
    return _obtener_familia_intencion(q) is not None

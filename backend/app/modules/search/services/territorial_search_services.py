from dataclasses import dataclass
import re
import unicodedata

from app.modules.spaces.models.comercios_models import Comercio


ARGENTINA_COUNTRY_CODE = "AR"

_PROVINCES = {
    "A": "Salta",
    "B": "Buenos Aires",
    "C": "Ciudad Autónoma de Buenos Aires",
    "D": "San Luis",
    "E": "Entre Ríos",
    "F": "La Rioja",
    "G": "Santiago del Estero",
    "H": "Chaco",
    "J": "San Juan",
    "K": "Catamarca",
    "L": "La Pampa",
    "M": "Mendoza",
    "N": "Misiones",
    "P": "Formosa",
    "Q": "Neuquén",
    "R": "Río Negro",
    "S": "Santa Fe",
    "T": "Tucumán",
    "U": "Chubut",
    "V": "Tierra del Fuego",
    "W": "Corrientes",
    "X": "Córdoba",
    "Y": "Jujuy",
    "Z": "Santa Cruz",
}


def normalize_territorial_text(value: str | None) -> str:
    decomposed = unicodedata.normalize("NFKD", value or "")
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", plain.casefold()).split())


def normalize_city_key(value: str | None) -> str:
    normalized = normalize_territorial_text(value)
    for prefix in ("municipio de ", "municipalidad de ", "ciudad de "):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
            break
    return normalized


def normalize_country_code(value: str | None) -> str:
    normalized = normalize_territorial_text(value)
    if normalized in {"ar", "arg", "argentina"}:
        return ARGENTINA_COUNTRY_CODE
    raise ValueError("country_code debe identificar Argentina")


def normalize_province_code(value: str | None) -> str:
    normalized = normalize_territorial_text(value)
    if normalized.startswith("ar "):
        normalized = normalized[3:]
    if len(normalized) == 1 and normalized.upper() in _PROVINCES:
        return f"AR-{normalized.upper()}"

    aliases = {
        "caba": "C",
        "capital federal": "C",
        "ciudad de buenos aires": "C",
        "tierra del fuego antartida e islas del atlantico sur": "V",
    }
    if normalized in aliases:
        return f"AR-{aliases[normalized]}"

    for code, province_name in _PROVINCES.items():
        if normalized == normalize_territorial_text(province_name):
            return f"AR-{code}"
    raise ValueError("province_code argentino invalido")


@dataclass(frozen=True)
class TerritorialContext:
    city_key: str
    province_code: str
    country_code: str = ARGENTINA_COUNTRY_CODE

    @classmethod
    def build(cls, *, city_key: str, province_code: str, country_code: str):
        normalized_city = normalize_city_key(city_key)
        if not normalized_city:
            raise ValueError("city_key es requerido")
        return cls(
            city_key=normalized_city,
            province_code=normalize_province_code(province_code),
            country_code=normalize_country_code(country_code),
        )


def commerce_matches_territory(comercio: Comercio, context: TerritorialContext) -> bool:
    try:
        commerce_province = normalize_province_code(getattr(comercio, "provincia", None))
    except ValueError:
        return False
    return (
        context.country_code == ARGENTINA_COUNTRY_CODE
        and commerce_province == context.province_code
        and normalize_city_key(getattr(comercio, "ciudad", None)) == context.city_key
    )


def filter_territorial_candidates(
    comercios: list[Comercio],
    context: TerritorialContext | None,
) -> list[Comercio]:
    if context is None:
        return comercios
    return [item for item in comercios if commerce_matches_territory(item, context)]

"""
knowledge_legacy_adapter_services.py
------------------------------------
Adaptador temporal para encapsular la logica legacy de intencion.
"""

from dataclasses import dataclass

from app.modules.knowledge.services.knowledge_legacy_intent_services import (
    _expandir_intencion_busqueda,
    _obtener_familia_intencion,
    _terminos_familia_intencion,
    _tiene_intencion_conocida,
)


_LEGACY_SOURCE = "legacy_spaces_comercios_intent_v2"


@dataclass(frozen=True)
class LegacyIntentInterpretation:
    terminos_expandidos: list[str]
    familia_intencion: str | None
    terminos_familia: list[str]
    tiene_intencion_conocida: bool
    source: str
    fallback_usado: bool


def interpretar_intencion_legacy(query_normalizada: str) -> LegacyIntentInterpretation:
    """
    Interpreta una query usando los helpers legacy alojados en Knowledge.
    """
    if not query_normalizada:
        return LegacyIntentInterpretation(
            terminos_expandidos=[],
            familia_intencion=None,
            terminos_familia=[],
            tiene_intencion_conocida=False,
            source=_LEGACY_SOURCE,
            fallback_usado=True,
        )

    familia_intencion = _obtener_familia_intencion(query_normalizada)
    terminos_expandidos = _expandir_intencion_busqueda(query_normalizada)
    terminos_familia = _terminos_familia_intencion(query_normalizada)
    tiene_intencion_conocida = _tiene_intencion_conocida(query_normalizada)

    return LegacyIntentInterpretation(
        terminos_expandidos=terminos_expandidos,
        familia_intencion=familia_intencion,
        terminos_familia=terminos_familia,
        tiene_intencion_conocida=tiene_intencion_conocida,
        source=_LEGACY_SOURCE,
        fallback_usado=True,
    )

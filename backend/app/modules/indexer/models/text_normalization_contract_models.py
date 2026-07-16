"""Contrato compartido de normalizacion de texto."""

from typing import Protocol


class TextNormalizationContract(Protocol):
    """Interfaz conceptual de normalizacion consumida por busqueda."""

    def normalize(self, text: str | None) -> str:
        """Normaliza texto."""

    def tokenize(self, text: str | None) -> list[str]:
        """Tokeniza texto."""

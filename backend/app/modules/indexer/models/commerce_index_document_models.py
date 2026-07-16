"""Contrato de dominio del Commerce Index Document."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.indexer.models.index_block_models import CommerceIndexBlocks


class CommerceIndexDocument(BaseModel):
    """Documento derivado y regenerable para un comercio."""

    document_id: str
    entity_type: Literal["commerce"] = "commerce"
    entity_id: int = Field(ge=1)
    document_version: str
    indexing_process_version: str
    generated_at: datetime
    is_indexable: bool
    non_indexable_reasons: list[str] = Field(default_factory=list)
    blocks: CommerceIndexBlocks

    @field_validator("document_id", "document_version", "indexing_process_version")
    @classmethod
    def _texto_no_vacio(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("los campos de texto no pueden estar vacios")
        return text

    @model_validator(mode="after")
    def _validar_indexabilidad(self) -> "CommerceIndexDocument":
        if not self.is_indexable and not self.non_indexable_reasons:
            raise ValueError("un documento no indexable debe indicar motivos")
        return self

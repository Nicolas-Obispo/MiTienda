"""Builder del bloque Contexto Derivado."""

from datetime import datetime

from app.modules.indexer.models.index_block_models import DerivedContextBlock
from app.modules.indexer.models.source_snapshot_models import ContentSourceSnapshot


class DerivedContextBuilder:
    """Construye el bloque Contexto Derivado desde snapshot de contenido."""

    def build(self, *, content: ContentSourceSnapshot) -> DerivedContextBlock:
        """Construye contexto derivado sin modificar contenido."""

        publication_ids = [publication.id for publication in content.publications]
        story_ids = [story.id for story in content.stories]

        return DerivedContextBlock(
            active_publication_refs=publication_ids,
            active_story_refs=story_ids,
            recent_activity_summary=self._recent_activity_summary(content),
            content_coverage_terms=self._content_coverage_terms(content),
        )

    @staticmethod
    def _recent_activity_summary(
        content: ContentSourceSnapshot,
    ) -> dict[str, int | str | None]:
        publication_dates = [
            publication.created_at
            for publication in content.publications
            if publication.created_at is not None
        ]
        story_dates = [
            story.created_at for story in content.stories if story.created_at is not None
        ]
        latest_activity_at = DerivedContextBuilder._latest_datetime(
            [*publication_dates, *story_dates]
        )

        return {
            "active_publication_count": len(content.publications),
            "active_story_count": len(content.stories),
            "latest_publication_at": DerivedContextBuilder._latest_iso(
                publication_dates
            ),
            "latest_story_at": DerivedContextBuilder._latest_iso(story_dates),
            "latest_activity_at": (
                latest_activity_at.isoformat() if latest_activity_at else None
            ),
        }

    @staticmethod
    def _content_coverage_terms(content: ContentSourceSnapshot) -> list[str]:
        terms: list[str] = []
        seen: set[str] = set()

        for publication in content.publications:
            for value in (publication.titulo, publication.descripcion):
                term = (value or "").strip()
                dedupe_key = term.lower()
                if term and dedupe_key not in seen:
                    terms.append(term)
                    seen.add(dedupe_key)

        return terms

    @staticmethod
    def _latest_datetime(values: list[datetime]) -> datetime | None:
        if not values:
            return None
        return max(values)

    @staticmethod
    def _latest_iso(values: list[datetime]) -> str | None:
        latest = DerivedContextBuilder._latest_datetime(values)
        if latest is None:
            return None
        return latest.isoformat()

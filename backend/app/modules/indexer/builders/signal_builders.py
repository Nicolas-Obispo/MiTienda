"""Builder del bloque Senales."""

from app.modules.indexer.models.index_block_models import (
    DerivedContextBlock,
    SignalsBlock,
)
from app.modules.indexer.models.source_snapshot_models import SignalSourceSnapshot


class SignalBuilder:
    """Construye senales agregadas aptas para indexacion."""

    def build(
        self,
        *,
        signals: SignalSourceSnapshot,
        derived_context: DerivedContextBlock,
    ) -> SignalsBlock:
        """Construye el bloque Senales sin ranking ni personalizacion."""

        return SignalsBlock(
            activity_signals={
                **signals.activity,
                "active_publication_count": len(
                    derived_context.active_publication_refs
                ),
                "active_story_count": len(derived_context.active_story_refs),
            },
            engagement_signals=dict(signals.metrics),
            freshness_signals={
                "latest_publication_at": derived_context.recent_activity_summary.get(
                    "latest_publication_at"
                ),
                "latest_story_at": derived_context.recent_activity_summary.get(
                    "latest_story_at"
                ),
                "latest_activity_at": derived_context.recent_activity_summary.get(
                    "latest_activity_at"
                ),
            },
            quality_signals={
                "has_active_publications": bool(
                    derived_context.active_publication_refs
                ),
                "has_active_stories": bool(derived_context.active_story_refs),
            },
        )

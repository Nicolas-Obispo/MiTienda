"""
Registro central de modelos SQLAlchemy.

Importar este modulo registra todos los modelos en Base.metadata sin ejecutar
operaciones sobre la base de datos.
"""


def import_all_models() -> None:
    """
    Importa todos los modelos ORM para registrar metadata.

    No debe ejecutar create_all, drop_all ni consultas.
    """

    # USERS
    from app.modules.users.models.usuarios_models import Usuario  # noqa: F401
    from app.modules.users.models.tokens_models import TokenRevocado  # noqa: F401
    from app.modules.users.models.usuarios_documentos_aceptaciones_models import (  # noqa: F401
        UsuarioDocumentoAceptacion,
    )

    # SPACES
    from app.modules.spaces.models.comercios_models import Comercio  # noqa: F401

    # AVAILABILITY
    from app.modules.availability.models.horarios_atencion_models import (  # noqa: F401
        ComercioHorarioAtencion,
    )

    # AGENDA
    from app.modules.agenda.models.agenda_models import (  # noqa: F401
        ContextoAgendable,
        ElementoAgenda,
    )

    # FEEDGO AGENDA
    from app.modules.feedgo_agenda.models.feedgo_agenda_contextos_models import (  # noqa: F401
        FeedGoAgendaContexto,
    )

    # PRODUCTS
    from app.modules.products.models.productos_models import Producto  # noqa: F401
    from app.modules.products.models.rubros_models import Rubro  # noqa: F401
    from app.modules.products.models.secciones_models import Seccion  # noqa: F401

    # DISCOVERY
    from app.modules.discovery.models.taxonomy_models import (  # noqa: F401
        TaxonomyAssignment,
        TaxonomyNode,
    )

    # SEARCH
    from app.modules.search.models.search_event_models import SearchEvent  # noqa: F401

    # KNOWLEDGE
    from app.modules.knowledge.models.knowledge_proposal_models import (  # noqa: F401
        KnowledgeProposal,
    )

    # POSTS
    from app.modules.posts.models.publicaciones_models import Publicacion  # noqa: F401

    # SOCIAL
    from app.modules.social.models.publicaciones_guardadas_models import (  # noqa: F401
        PublicacionGuardada,
    )
    from app.modules.social.models.likes_publicaciones_models import (  # noqa: F401
        LikePublicacion,
    )
    from app.modules.social.models.seguidores_models import Seguidores  # noqa: F401

    # STORIES
    from app.modules.stories.models.historias_models import Historia  # noqa: F401
    from app.modules.stories.models.historias_vistas_models import (  # noqa: F401
        HistoriaVista,
    )
    from app.modules.stories.models.historias_likes_models import (  # noqa: F401
        HistoriaLike,
    )

    # MODERATION
    from app.modules.moderation.models.contenido_denuncias_models import (  # noqa: F401
        ContenidoDenuncia,
    )

    # AI
    from app.modules.ai.models.comercios_embeddings_models import (  # noqa: F401
        ComercioEmbedding,
    )
    from app.modules.ai.models.usuarios_embeddings_models import (  # noqa: F401
        UsuarioEmbedding,
    )

    # ANALYTICS
    from app.modules.analytics.models.comercios_metricas_sociales_models import (  # noqa: F401
        ComercioMetricasSociales,
    )
    from app.modules.analytics.models.comercios_metricas_snapshots_models import (  # noqa: F401
        ComercioMetricasSnapshot,
    )

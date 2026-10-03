"""Escenarios logicos puros aprobados para ET100.3.

Este modulo declara filas y relaciones; no conoce SQLAlchemy, conexiones,
materializacion, reset ni medios fisicos. ``functional`` reutiliza exactamente
la declaracion ``smoke`` y ``representative`` extiende ambas declaraciones sin
agregar volumen fuera de la matriz aprobada.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.modules.ai.providers.simulated_provider import SimulatedEmbeddingProvider

from .blueprint import (
    BlueprintBuilder,
    BlueprintContext,
    BlueprintContractError,
    ClockPolicy,
    LogicalBlueprint,
)
from .fingerprint import (
    NonDeterministicKind,
    NormalizedNonDeterministicValue,
    OwnerDerivedValue,
)


SMOKE_PROFILE = "smoke"
FUNCTIONAL_PROFILE = "functional"
REPRESENTATIVE_PROFILE = "representative"
SUPPORTED_PROFILES = frozenset(
    {SMOKE_PROFILE, FUNCTIONAL_PROFILE, REPRESENTATIVE_PROFILE}
)
_SIMULATED_EMBEDDINGS = SimulatedEmbeddingProvider()
_REPORT_CREATED = "moderation.report.created"
_LEGAL_DOCUMENTS = (
    ("terminos_condiciones", "v1", "terminos_condiciones:v1"),
    ("politica_privacidad", "v1", "politica_privacidad:v1"),
)
_TAXONOMY_CONTRACTS: dict[str, dict[str, Any]] = {
    "servicios": {
        "nombre": "Servicios", "type": "sector",
        "descripcion": "Prestadores de servicios profesionales, tecnicos, obra y mantenimiento.",
        "orden": 20, "metadata_json": None,
    },
    "consumo": {
        "nombre": "Consumo", "type": "sector",
        "descripcion": "Comida, compras diarias, kioscos, supermercados y consumo frecuente.",
        "orden": 30, "metadata_json": None,
    },
    "gastronomia-categoria": {
        "nombre": "Gastronomia", "type": "categoria",
        "descripcion": "Comida, restaurantes, bares, cafeterias, pizzerias y delivery.",
        "orden": 10, "metadata_json": None,
    },
    "comida-preparada": {
        "nombre": "Comida preparada", "type": "subcategoria",
        "descripcion": "Restaurantes, pizzerias, cafeterias, heladerias, bares, almuerzo y cena.",
        "orden": 10, "metadata_json": None,
    },
    "gastronomia": {
        "nombre": "Gastronomia", "type": "rubro",
        "descripcion": "Locales gastronomicos, bares, restaurantes, pizzerias, cafeterias y delivery.",
        "orden": 10, "metadata_json": None,
    },
    "pizzerias-rotiserias-delivery": {
        "nombre": "Pizzerías, rotiserías y delivery", "type": "especialidad",
        "descripcion": "Pizzerías, rotiserías, delivery, comida para llevar y comidas rápidas.",
        "orden": 60,
        "metadata_json": {
            "search_terms": ["pizza", "pizzas", "pizzeria", "pizzerias", "rotiseria", "rotiserias", "delivery", "lomito", "lomitos"],
            "synonyms": ["pizzería", "pizzeria", "rotisería", "rotiseria"],
            "related_terms": ["delivery", "cena", "almuerzo", "comida para llevar", "combo"],
        },
    },
    "servicios-profesionales": {
        "nombre": "Servicios Profesionales", "type": "categoria",
        "descripcion": "Servicios profesionales, legales, contables, administrativos y consultoria.",
        "orden": 10, "metadata_json": None,
    },
    "marketing-digital": {
        "nombre": "Marketing Digital", "type": "especialidad",
        "descripcion": "Marketing Digital, redes sociales, campañas, publicidad online y estrategia digital.",
        "orden": 60,
        "metadata_json": {
            "search_terms": ["marketing digital", "redes sociales", "publicidad online", "campañas"],
            "synonyms": ["marketing online", "publicidad digital"],
            "related_terms": ["seo", "contenido", "estrategia digital"],
        },
    },
}


def _opaque(
    kind: NonDeterministicKind,
    **invariants: Any,
) -> NormalizedNonDeterministicValue:
    """Describe material criptografico que pertenecera al materializador."""

    return NormalizedNonDeterministicValue(
        kind=kind,
        invariants={"materializer_owned": True, **invariants},
        opaque_value=None,
    )


def _row(
    builder: BlueprintBuilder,
    alias: str,
    table: str,
    **attributes: Any,
) -> None:
    builder.add_entity(alias=alias, entity_type=table, attributes=attributes)


def _link(
    builder: BlueprintBuilder,
    alias: str,
    relation_type: str,
    source_alias: str,
    target_alias: str,
    **attributes: Any,
) -> None:
    builder.add_relation(
        alias=alias,
        relation_type=relation_type,
        source_alias=source_alias,
        target_alias=target_alias,
        attributes=attributes,
    )


def _at(builder: BlueprintBuilder, seconds: int):
    return builder.context.clock_policy.at(seconds=seconds)


def _password_contract() -> NormalizedNonDeterministicValue:
    return _opaque(
        NonDeterministicKind.BCRYPT_HASH,
        algorithm="bcrypt",
        hash_version="bcrypt",
        owner="app.core.auth.hash_password",
        verifies_fixture_secret=True,
    )


def _digest_contract(*, purpose: str, owner: str, algorithm: str) -> NormalizedNonDeterministicValue:
    return _opaque(
        NonDeterministicKind.TOKEN_DIGEST,
        algorithm=algorithm,
        owner=owner,
        purpose=purpose,
    )


def _nonce_contract(*, purpose: str, owner: str, format: str) -> NormalizedNonDeterministicValue:
    return _opaque(
        NonDeterministicKind.CRYPTOGRAPHIC_NONCE,
        owner=owner,
        purpose=purpose,
        format=format,
        minimum_entropy_bits=128,
    )


def _owner_derived(owner: str, **inputs: Any) -> OwnerDerivedValue:
    return OwnerDerivedValue(owner=owner, inputs=inputs)


def _physical_id(alias: str) -> OwnerDerivedValue:
    return _owner_derived(
        "feedgo.synthetic.materializer.alias_to_database_id",
        alias=alias,
    )


def _owner_attribute(alias: str, attribute: str) -> OwnerDerivedValue:
    return _owner_derived(
        "feedgo.synthetic.materializer.materialized_owner_attribute",
        alias=alias,
        attribute=attribute,
    )


def _owner_generated_incident_id() -> NormalizedNonDeterministicValue:
    return _opaque(
        NonDeterministicKind.OWNER_GENERATED_IDENTIFIER,
        owner="app.modules.incidents.services.operational_incidents_services.create_incident",
        format="INC-{UUID4_HEX_UPPER}",
        unique=True,
    )


def _taxonomy_attributes(slug: str) -> dict[str, Any]:
    contract = _TAXONOMY_CONTRACTS[slug]
    return {
        "slug": slug,
        "type": contract["type"],
        "nombre": contract["nombre"],
        "descripcion": contract["descripcion"],
        "activo": True,
        "orden": contract["orden"],
        "metadata_json": contract["metadata_json"],
    }


def _commerce_embedding(commerce_alias: str) -> OwnerDerivedValue:
    return _owner_derived(
        "app.modules.ai.services.comercios_embeddings_services.upsert_embedding_comercio",
        commerce_alias=commerce_alias,
        provider="SimulatedEmbeddingProvider",
        dimensions=_SIMULATED_EMBEDDINGS.dim,
        model_version=1,
    )


def _user_embedding(user_alias: str) -> OwnerDerivedValue:
    return _owner_derived(
        "app.modules.ai.services.usuarios_embeddings_services.generar_embedding_usuario",
        user_alias=user_alias,
        provider="SimulatedEmbeddingProvider",
        dimensions=_SIMULATED_EMBEDDINGS.dim,
        model_version=1,
    )


def _add_smoke(builder: BlueprintBuilder) -> None:
    """Agrega las 20 filas minimas del escenario smoke aprobado."""

    _row(
        builder,
        "user.owner",
        "usuarios",
        email="owner.synthetic@example.com",
        email_canonical="owner.synthetic@example.com",
        email_verified_at=_at(builder, 10),
        email_verification_source="email_link",
        modo_activo="publicador",
        onboarding_completo=True,
        provincia="Buenos Aires",
        ciudad="Tandil",
        telefono_e164="+12025550123",
        telefono_verified_at=_at(builder, 20),
        telefono_verification_source="phone_otp",
    )
    _row(
        builder,
        "credential.owner",
        "password_credentials",
        password_hash=_password_contract(),
        hash_version="bcrypt",
        created_at=_at(builder, 30),
        updated_at=_at(builder, 30),
    )
    for suffix, document in zip(
        ("terms", "privacy"), _LEGAL_DOCUMENTS, strict=True
    ):
        document_type, document_version, document_reference = document
        _row(
            builder,
            f"legal.owner.{suffix}",
            "usuarios_documentos_aceptaciones",
            documento_tipo=document_type,
            documento_version=document_version,
            aceptado_en=_at(builder, 40),
            canal="web",
            metodo="checkbox_explicito",
            estado="aceptado",
            documento_referencia=document_reference,
        )
    _row(
        builder,
        "session.owner.active",
        "feedgo_sessions",
        id=_nonce_contract(
            purpose="feedgo_session_id",
            owner="app.modules.users.services.feedgo_session_services.generate_session_id",
            format="token_urlsafe_32",
        ),
        authentication_method="password",
        issued_at=_at(builder, 60),
        expires_at=_at(builder, 86460),
        revoked_at=None,
        contract_version=1,
    )

    _row(
        builder,
        "rubro.gastronomia",
        "rubros",
        nombre="Gastronomia",
        descripcion="Comida preparada y servicios gastronomicos sinteticos.",
        activo=True,
    )
    taxonomy_rows = (
        ("taxonomy.consumo", "consumo", "sector", None, "Consumo"),
        (
            "taxonomy.gastronomia_categoria",
            "gastronomia-categoria",
            "categoria",
            "taxonomy.consumo",
            "Gastronomia",
        ),
        (
            "taxonomy.comida_preparada",
            "comida-preparada",
            "subcategoria",
            "taxonomy.gastronomia_categoria",
            "Comida preparada",
        ),
        (
            "taxonomy.gastronomia",
            "gastronomia",
            "rubro",
            "taxonomy.comida_preparada",
            "Gastronomia",
        ),
        (
            "taxonomy.pizzerias",
            "pizzerias-rotiserias-delivery",
            "especialidad",
            "taxonomy.gastronomia",
            "Pizzerias, rotiserias y delivery",
        ),
    )
    for alias, slug, _node_type, parent, _name in taxonomy_rows:
        _row(
            builder,
            alias,
            "taxonomy_nodes",
            **_taxonomy_attributes(slug),
        )
        if parent is not None:
            _link(
                builder,
                f"hierarchy.{alias}",
                "taxonomy_parent",
                alias,
                parent,
                source_field="parent_id",
            )

    _row(
        builder,
        "assignment.rubro.gastronomia",
        "taxonomy_assignments",
        entity_type="rubro",
        source="sistema",
        confidence=1.0,
        principal=True,
    )
    _row(
        builder,
        "commerce.primary",
        "comercios",
        nombre="Pizzeria Sintetica Central",
        descripcion="Comercio sintetico para validacion smoke.",
        portada_url="synthetic-media://commerce/primary/cover-v1",
        provincia="Buenos Aires",
        ciudad="Tandil",
        direccion="Calle Sintetica 100",
        whatsapp="+12025550123",
        latitud=-37.3217,
        longitud=-59.1332,
        mostrar_direccion_publicamente=True,
        activo=True,
        moderation_hidden=False,
        moderation_revision=0,
        created_at=_at(builder, 120),
        updated_at=_at(builder, 120),
    )
    _row(
        builder,
        "assignment.commerce.primary",
        "taxonomy_assignments",
        entity_type="comercio",
        source="rubro_sync",
        confidence=1.0,
        principal=True,
    )
    _row(
        builder,
        "assignment.commerce.primary.pizzerias",
        "taxonomy_assignments",
        entity_type="comercio",
        source="manual",
        confidence=1.0,
        principal=False,
    )
    _row(
        builder,
        "schedule.primary.monday",
        "comercios_horarios_atencion",
        dia_semana=0,
        hora_apertura="09:00:00",
        hora_cierre="18:00:00",
        created_at=_at(builder, 130),
        updated_at=_at(builder, 130),
    )
    _row(
        builder,
        "section.primary.menu",
        "secciones",
        nombre="Menu sintetico",
        descripcion="Seccion activa de validacion.",
        orden=10,
        activo=True,
        created_at=_at(builder, 140),
        updated_at=_at(builder, 140),
    )
    _row(
        builder,
        "post.primary.active",
        "publicaciones",
        titulo="Pizza sintetica destacada",
        descripcion="Contenido sintetico activo para lectura publica.",
        imagen_url="synthetic-media://post/primary-active/image-v1",
        is_activa=True,
        moderation_hidden=False,
        moderation_revision=0,
        views_count=0,
        created_at=_at(builder, 150),
        updated_at=_at(builder, 150),
    )
    _row(
        builder,
        "story.primary.active",
        "historias",
        media_url="synthetic-media://story/primary-active/video-v1",
        is_activa=True,
        moderation_hidden=False,
        moderation_revision=0,
        expira_en=_at(builder, 43200),
        created_at=_at(builder, 160),
        updated_at=_at(builder, 160),
    )
    _row(
        builder,
        "embedding.commerce.primary",
        "comercios_embeddings",
        vector=_commerce_embedding("commerce.primary"),
        model_version=1,
        created_at=_at(builder, 170),
        updated_at=_at(builder, 170),
    )

    for alias, source, target, relation_type, field in (
        ("link.credential.owner", "credential.owner", "user.owner", "credential_of", "usuario_id"),
        ("link.legal.owner.terms", "legal.owner.terms", "user.owner", "accepted_by", "usuario_id"),
        ("link.legal.owner.privacy", "legal.owner.privacy", "user.owner", "accepted_by", "usuario_id"),
        ("link.session.owner.active", "session.owner.active", "user.owner", "session_of", "usuario_id"),
        (
            "link.rubro.taxonomy.gastronomia",
            "assignment.rubro.gastronomia",
            "taxonomy.gastronomia",
            "assigned_node",
            "taxonomy_node_id",
        ),
        (
            "link.rubro.assignment.gastronomia",
            "assignment.rubro.gastronomia",
            "rubro.gastronomia",
            "assigned_entity",
            "entity_id",
        ),
        ("link.commerce.primary.owner", "commerce.primary", "user.owner", "owned_by", "usuario_id"),
        ("link.commerce.primary.rubro", "commerce.primary", "rubro.gastronomia", "classified_by", "rubro_id"),
        (
            "link.assignment.commerce.primary.node",
            "assignment.commerce.primary",
            "taxonomy.gastronomia",
            "assigned_node",
            "taxonomy_node_id",
        ),
        (
            "link.assignment.commerce.primary.entity",
            "assignment.commerce.primary",
            "commerce.primary",
            "assigned_entity",
            "entity_id",
        ),
        (
            "link.assignment.commerce.primary.pizzerias.node",
            "assignment.commerce.primary.pizzerias",
            "taxonomy.pizzerias",
            "assigned_node",
            "taxonomy_node_id",
        ),
        (
            "link.assignment.commerce.primary.pizzerias.entity",
            "assignment.commerce.primary.pizzerias",
            "commerce.primary",
            "assigned_entity",
            "entity_id",
        ),
        ("link.schedule.primary", "schedule.primary.monday", "commerce.primary", "schedule_of", "comercio_id"),
        ("link.section.primary", "section.primary.menu", "commerce.primary", "section_of", "comercio_id"),
        ("link.post.primary.commerce", "post.primary.active", "commerce.primary", "post_of", "comercio_id"),
        ("link.post.primary.section", "post.primary.active", "section.primary.menu", "post_section", "seccion_id"),
        ("link.story.primary.commerce", "story.primary.active", "commerce.primary", "story_of", "comercio_id"),
        ("link.story.primary.post", "story.primary.active", "post.primary.active", "story_post", "publicacion_id"),
        (
            "link.embedding.commerce.primary",
            "embedding.commerce.primary",
            "commerce.primary",
            "embedding_of",
            "comercio_id",
        ),
    ):
        _link(builder, alias, relation_type, source, target, source_field=field)


def _add_functional_identity(builder: BlueprintBuilder) -> None:
    _row(
        builder,
        "user.operator",
        "usuarios",
        email="operator.synthetic@example.com",
        email_canonical="operator.synthetic@example.com",
        email_verified_at=_at(builder, 200),
        email_verification_source="email_link",
        modo_activo="usuario",
        onboarding_completo=True,
        provincia="Buenos Aires",
        ciudad="Tandil",
    )
    _row(
        builder,
        "credential.operator",
        "password_credentials",
        password_hash=_password_contract(),
        hash_version="bcrypt",
        created_at=_at(builder, 210),
        updated_at=_at(builder, 210),
    )
    for suffix, document in zip(
        ("terms", "privacy"), _LEGAL_DOCUMENTS, strict=True
    ):
        document_type, document_version, document_reference = document
        _row(
            builder,
            f"legal.operator.{suffix}",
            "usuarios_documentos_aceptaciones",
            documento_tipo=document_type,
            documento_version=document_version,
            aceptado_en=_at(builder, 220),
            canal="web",
            metodo="checkbox_explicito",
            estado="aceptado",
            documento_referencia=document_reference,
        )
    capabilities = (
        "moderation.reports.read",
        "moderation.decisions.write",
        "operations.status.read",
        "operations.incidents.manage",
    )
    for index, capability in enumerate(capabilities, 1):
        suffix = capability.replace(".", "_")
        _row(
            builder,
            f"admin.capability.{suffix}",
            "administrative_capability_events",
            capability=capability,
            action="grant",
            source="synthetic_fixture",
            reason="Functional profile minimum administrative coverage.",
            created_at=_at(builder, 220 + index),
        )
        _link(
            builder,
            f"link.admin.capability.{suffix}.subject",
            "capability_subject",
            f"admin.capability.{suffix}",
            "user.operator",
            source_field="usuario_id",
        )
        _link(
            builder,
            f"link.admin.capability.{suffix}.actor",
            "capability_actor",
            f"admin.capability.{suffix}",
            "user.operator",
            source_field="actor_usuario_id",
        )

    _row(
        builder,
        "user.incomplete",
        "usuarios",
        email="incomplete.synthetic@example.com",
        email_canonical="incomplete.synthetic@example.com",
        email_verified_at=None,
        email_verification_source=None,
        modo_activo="usuario",
        onboarding_completo=False,
        provincia=None,
        ciudad=None,
    )
    _row(
        builder,
        "credential.incomplete",
        "password_credentials",
        password_hash=_password_contract(),
        hash_version="bcrypt",
        created_at=_at(builder, 230),
        updated_at=_at(builder, 230),
    )
    for alias, expires_offset, revoked_offset in (
        ("session.owner.expired", -60, None),
        ("session.owner.revoked", 7200, 300),
    ):
        _row(
            builder,
            alias,
            "feedgo_sessions",
                id=_nonce_contract(
                purpose="feedgo_session_id",
                owner="app.modules.users.services.feedgo_session_services.generate_session_id",
                format="token_urlsafe_32",
            ),
            authentication_method="password",
            issued_at=_at(builder, -3600),
            expires_at=_at(builder, expires_offset),
            revoked_at=None if revoked_offset is None else _at(builder, revoked_offset),
            contract_version=1,
        )

    token_specs = (
        ("token.password_reset.active", "password_reset", 3600, None, None, None),
        ("token.email_verification.consumed", "email_verification", 3600, 300, None, None),
        ("token.password_reset.expired", "password_reset", -60, None, None, None),
        ("token.password_reset.invalidated", "password_reset", 3600, None, 240, "password_changed"),
    )
    for alias, purpose, expiry, consumed, invalidated, reason in token_specs:
        _row(
            builder,
            alias,
            "account_action_tokens",
            purpose=purpose,
            token_digest=_digest_contract(
                purpose=purpose,
                owner="app.modules.users.services.account_action_token_services.digest_token_secret",
                algorithm="sha256",
            ),
            email_canonical_snapshot="owner.synthetic@example.com",
            created_at=_at(builder, -600),
            expires_at=_at(builder, expiry),
            consumed_at=None if consumed is None else _at(builder, consumed),
            invalidated_at=None if invalidated is None else _at(builder, invalidated),
            invalidation_reason=reason,
            issuance_id=_nonce_contract(
                purpose=f"{purpose}_issuance",
                owner="app.modules.users.services.account_action_token_services._new_issuance_id",
                format="uuid4_hex",
            ),
        )
    for alias, action, attempts, blocked in (
        ("rate.password_login.open", "password_login", 1, None),
        ("rate.password_reset.blocked", "password_reset", 5, 900),
    ):
        _row(
            builder,
            alias,
            "account_action_rate_limits",
            action=action,
            subject_digest=_digest_contract(
                purpose=f"rate_limit_{action}",
                owner="app.modules.users.services.account_action_rate_limit_services.subject_digest",
                algorithm="hmac-sha256",
            ),
            window_started_at=_at(builder, -300),
            attempt_count=attempts,
            blocked_until=None if blocked is None else _at(builder, blocked),
            updated_at=_at(builder, -30),
        )
    challenge_specs = (
        ("phone.challenge.active", 3600, None, None, None),
        ("phone.challenge.consumed", 3600, 120, None, None),
        ("phone.challenge.revoked", 3600, None, 180, "superseded"),
    )
    for alias, expiry, consumed, revoked, reason in challenge_specs:
        _row(
            builder,
            alias,
            "phone_verification_challenges",
            id=_nonce_contract(
                purpose="phone_challenge_id",
                owner="app.modules.users.services.phone_verification_services.issue_phone_challenge",
                format="token_urlsafe_32",
            ),
            phone_e164_snapshot="+12025550123",
            code_digest=_digest_contract(
                purpose="phone_verification",
                owner="app.modules.users.services.phone_verification_services.digest_code",
                algorithm="hmac-sha256",
            ),
            issuance_id=_nonce_contract(
                purpose="phone_verification_issuance",
                owner="app.modules.users.services.phone_verification_services.issue_phone_challenge",
                format="uuid4_hex",
            ),
            created_at=_at(builder, -300),
            expires_at=_at(builder, expiry),
            consumed_at=None if consumed is None else _at(builder, consumed),
            revoked_at=None if revoked is None else _at(builder, revoked),
            invalidation_reason=reason,
            failed_attempts=0,
        )

    for alias, source, target, relation_type, field in (
        ("link.credential.operator", "credential.operator", "user.operator", "credential_of", "usuario_id"),
        ("link.legal.operator.terms", "legal.operator.terms", "user.operator", "accepted_by", "usuario_id"),
        ("link.legal.operator.privacy", "legal.operator.privacy", "user.operator", "accepted_by", "usuario_id"),
        ("link.credential.incomplete", "credential.incomplete", "user.incomplete", "credential_of", "usuario_id"),
        ("link.session.owner.expired", "session.owner.expired", "user.owner", "session_of", "usuario_id"),
        ("link.session.owner.revoked", "session.owner.revoked", "user.owner", "session_of", "usuario_id"),
        ("link.token.password_reset.active", "token.password_reset.active", "user.owner", "token_of", "usuario_id"),
        (
            "link.token.email_verification.consumed",
            "token.email_verification.consumed",
            "user.owner",
            "token_of",
            "usuario_id",
        ),
        ("link.token.password_reset.expired", "token.password_reset.expired", "user.owner", "token_of", "usuario_id"),
        (
            "link.token.password_reset.invalidated",
            "token.password_reset.invalidated",
            "user.owner",
            "token_of",
            "usuario_id",
        ),
        ("link.phone.challenge.active", "phone.challenge.active", "user.incomplete", "challenge_of", "usuario_id"),
        ("link.phone.challenge.consumed", "phone.challenge.consumed", "user.owner", "challenge_of", "usuario_id"),
        ("link.phone.challenge.revoked", "phone.challenge.revoked", "user.incomplete", "challenge_of", "usuario_id"),
    ):
        _link(builder, alias, relation_type, source, target, source_field=field)


def _add_functional_discovery_content(builder: BlueprintBuilder) -> None:
    _row(
        builder,
        "rubro.services",
        "rubros",
        nombre="Servicios profesionales",
        descripcion="Servicios profesionales sinteticos.",
        activo=True,
    )
    for alias, slug, _node_type, parent, _name in (
        ("taxonomy.services", "servicios", "sector", None, "Servicios"),
        (
            "taxonomy.professional_services",
            "servicios-profesionales",
            "categoria",
            "taxonomy.services",
            "Servicios Profesionales",
        ),
        (
            "taxonomy.digital_marketing",
            "marketing-digital",
            "especialidad",
            "taxonomy.professional_services",
            "Marketing Digital",
        ),
    ):
        _row(
            builder,
            alias,
            "taxonomy_nodes",
            **_taxonomy_attributes(slug),
        )
        if parent:
            _link(builder, f"hierarchy.{alias}", "taxonomy_parent", alias, parent, source_field="parent_id")

    _row(
        builder,
        "assignment.rubro.services",
        "taxonomy_assignments",
        entity_type="rubro",
        source="sistema",
        confidence=1.0,
        principal=True,
    )
    _row(
        builder,
        "commerce.secondary",
        "comercios",
        nombre="Estudio Sintetico Digital",
        descripcion="Servicio sintetico activo.",
        portada_url="synthetic-media://commerce/secondary/cover-v1",
        provincia="Cordoba",
        ciudad="Cordoba",
        direccion="Avenida Sintetica 200",
        mostrar_direccion_publicamente=False,
        activo=True,
        moderation_hidden=False,
        moderation_revision=0,
        created_at=_at(builder, 300),
        updated_at=_at(builder, 300),
    )
    _row(
        builder,
        "assignment.commerce.secondary",
        "taxonomy_assignments",
        entity_type="comercio",
        source="rubro_sync",
        confidence=1.0,
        principal=True,
    )
    _row(
        builder,
        "assignment.commerce.secondary.marketing",
        "taxonomy_assignments",
        entity_type="comercio",
        source="manual",
        confidence=1.0,
        principal=False,
    )
    _row(
        builder,
        "commerce.inactive",
        "comercios",
        nombre="Comercio Sintetico Inactivo",
        descripcion="Estado terminal valido para filtros.",
        portada_url="synthetic-media://commerce/inactive/cover-v1",
        provincia="Buenos Aires",
        ciudad="Tandil",
        direccion=None,
        mostrar_direccion_publicamente=False,
        activo=False,
        moderation_hidden=False,
        moderation_revision=0,
        created_at=_at(builder, 310),
        updated_at=_at(builder, 310),
    )
    _row(
        builder,
        "section.primary.inactive",
        "secciones",
        nombre="Seccion sintetica inactiva",
        descripcion=None,
        orden=20,
        activo=False,
        created_at=_at(builder, 320),
        updated_at=_at(builder, 320),
    )
    _row(
        builder,
        "embedding.commerce.secondary",
        "comercios_embeddings",
        vector=_commerce_embedding("commerce.secondary"),
        model_version=1,
        created_at=_at(builder, 330),
        updated_at=_at(builder, 330),
    )

    discovery_links = (
        (
            "link.rubro.services.node",
            "assignment.rubro.services",
            "taxonomy.professional_services",
            "assigned_node",
            "taxonomy_node_id",
        ),
        ("link.rubro.services.entity", "assignment.rubro.services", "rubro.services", "assigned_entity", "entity_id"),
        ("link.commerce.secondary.owner", "commerce.secondary", "user.owner", "owned_by", "usuario_id"),
        ("link.commerce.secondary.rubro", "commerce.secondary", "rubro.services", "classified_by", "rubro_id"),
        (
            "link.assignment.commerce.secondary.node",
            "assignment.commerce.secondary",
            "taxonomy.professional_services",
            "assigned_node",
            "taxonomy_node_id",
        ),
        (
            "link.assignment.commerce.secondary.entity",
            "assignment.commerce.secondary",
            "commerce.secondary",
            "assigned_entity",
            "entity_id",
        ),
        (
            "link.assignment.commerce.secondary.marketing.node",
            "assignment.commerce.secondary.marketing",
            "taxonomy.digital_marketing",
            "assigned_node",
            "taxonomy_node_id",
        ),
        (
            "link.assignment.commerce.secondary.marketing.entity",
            "assignment.commerce.secondary.marketing",
            "commerce.secondary",
            "assigned_entity",
            "entity_id",
        ),
        ("link.commerce.inactive.owner", "commerce.inactive", "user.owner", "owned_by", "usuario_id"),
        ("link.commerce.inactive.rubro", "commerce.inactive", "rubro.gastronomia", "classified_by", "rubro_id"),
        ("link.section.primary.inactive", "section.primary.inactive", "commerce.primary", "section_of", "comercio_id"),
        (
            "link.embedding.commerce.secondary",
            "embedding.commerce.secondary",
            "commerce.secondary",
            "embedding_of",
            "comercio_id",
        ),
    )
    for alias, source, target, relation_type, field in discovery_links:
        _link(builder, alias, relation_type, source, target, source_field=field)

    post_specs = (
        ("post.secondary.active_unsectioned", "commerce.secondary", True, False, 0),
        ("post.primary.inactive", "commerce.primary", False, False, 0),
        ("post.primary.hidden", "commerce.primary", True, True, 1),
    )
    for index, (alias, commerce, active, hidden, revision) in enumerate(post_specs, 1):
        _row(
            builder,
            alias,
            "publicaciones",
            titulo=f"Publicacion sintetica funcional {index}",
            descripcion="Estado funcional valido.",
            imagen_url=f"synthetic-media://{alias.replace('.', '/')}/image-v1",
            is_activa=active,
            moderation_hidden=hidden,
            moderation_revision=revision,
            views_count=0,
            created_at=_at(builder, 340 + index),
            updated_at=_at(builder, 340 + index),
        )
        _link(builder, f"link.{alias}.commerce", "post_of", alias, commerce, source_field="comercio_id")

    story_specs = (
        ("story.primary.expired_active", True, False, -60, "post.primary.active"),
        ("story.primary.inactive", False, False, 7200, "post.primary.inactive"),
        ("story.primary.hidden", True, True, 7200, "post.primary.hidden"),
    )
    for index, (alias, active, hidden, expiry, post) in enumerate(story_specs, 1):
        _row(
            builder,
            alias,
            "historias",
            media_url=f"synthetic-media://{alias.replace('.', '/')}/video-v1",
            is_activa=active,
            moderation_hidden=hidden,
            moderation_revision=1 if hidden else 0,
            expira_en=_at(builder, expiry),
            created_at=_at(builder, 350 + index),
            updated_at=_at(builder, 350 + index),
        )
        _link(builder, f"link.{alias}.commerce", "story_of", alias, "commerce.primary", source_field="comercio_id")
        _link(builder, f"link.{alias}.post", "story_post", alias, post, source_field="publicacion_id")

    social_specs = (
        ("social.follow.primary", "seguidores", "user.operator", "commerce.primary", "follows"),
        ("social.like.post.primary", "likes_publicaciones", "user.operator", "post.primary.active", "likes_post"),
        ("social.save.post.primary", "publicaciones_guardadas", "user.operator", "post.primary.active", "saves_post"),
        ("social.view.story.primary", "historias_vistas", "user.operator", "story.primary.active", "views_story"),
        ("social.like.story.primary", "historias_likes", "user.operator", "story.primary.active", "likes_story"),
    )
    for index, (alias, table, user, resource, relation_type) in enumerate(social_specs, 1):
        _row(builder, alias, table, created_at=_at(builder, 360 + index))
        _link(builder, f"link.{alias}.user", "interaction_user", alias, user, source_field="usuario_id")
        resource_field = (
            "comercio_id"
            if table == "seguidores"
            else ("publicacion_id" if "publicacion" in table else "historia_id")
        )
        _link(builder, f"link.{alias}.resource", relation_type, alias, resource, source_field=resource_field)
    _row(
        builder,
        "embedding.user.operator",
        "usuarios_embeddings",
        vector=_user_embedding("user.operator"),
        model_version=1,
        created_at=_at(builder, 370),
        updated_at=_at(builder, 370),
    )
    _link(
        builder,
        "link.embedding.user.operator",
        "embedding_of",
        "embedding.user.operator",
        "user.operator",
        source_field="usuario_id",
    )


def _add_functional_moderation_metrics(builder: BlueprintBuilder) -> None:
    report_specs = (
        ("report.post.received", "user.operator", "publicacion", "post.primary.active", "spam", "recibida", 1),
        (
            "report.post.hidden.resolved",
            "user.operator",
            "publicacion",
            "post.primary.hidden",
            "contenido_inapropiado",
            "resuelta",
            2,
        ),
        (
            "report.story.hidden.resolved",
            "user.owner",
            "historia",
            "story.primary.hidden",
            "datos_personales",
            "resuelta",
            2,
        ),
    )
    report_contracts = {
        alias: (resource_type, resource, reason)
        for alias, _reporter, resource_type, resource, reason, _status, _version in report_specs
    }
    for index, (alias, reporter, resource_type, resource, reason, status, version) in enumerate(report_specs, 1):
        _row(
            builder,
            alias,
            "contenido_denuncias",
            recurso_tipo=resource_type,
            motivo=reason,
            detalle="Detalle sintetico sin PII.",
            estado=status,
            version=version,
            resuelta_en=None if status == "recibida" else _at(builder, 410 + index),
            creado_en=_at(builder, 380 + index),
        )
        _link(builder, f"link.{alias}.reporter", "reported_by", alias, reporter, source_field="usuario_id")
        _link(builder, f"link.{alias}.resource", "reports_resource", alias, resource, source_field="recurso_id")

    decision_specs = (
        ("decision.post.hidden", "report.post.hidden.resolved", "post.primary.hidden", "publicacion"),
        ("decision.story.hidden", "report.story.hidden.resolved", "story.primary.hidden", "historia"),
    )
    for index, (alias, report, resource, resource_type) in enumerate(decision_specs, 1):
        decision_payload = {
            "accion": "ocultar_recurso",
            "motivo_codigo": "incumplimiento_confirmado",
            "fundamento": "Fundamento sintetico seguro.",
            "evidencia_resumen": "Referencia sintetica sin contenido sensible.",
            "evidencia_referencia": f"synthetic-evidence-{index}",
            "expected_denuncia_version": 1,
            "expected_resource_revision": 0,
            "reverses_decision_id": None,
            "idempotency_key": f"synthetic-moderation-{index}",
        }
        _row(
            builder,
            alias,
            "moderation_decisions",
            accion=decision_payload["accion"],
            motivo_codigo=decision_payload["motivo_codigo"],
            fundamento=decision_payload["fundamento"],
            evidencia_resumen=decision_payload["evidencia_resumen"],
            evidencia_referencia=decision_payload["evidencia_referencia"],
            resultado="aplicado",
            recurso_tipo=resource_type,
            estado_recurso_anterior="visible",
            estado_recurso_resultante="oculto",
            expected_denuncia_version=decision_payload["expected_denuncia_version"],
            denuncia_version_resultante=2,
            expected_resource_revision=decision_payload["expected_resource_revision"],
            resource_revision_anterior=0,
            resource_revision_resultante=1,
            idempotency_key=decision_payload["idempotency_key"],
            request_fingerprint=_owner_derived(
                "app.modules.moderation.services.moderation_decisions_services._fingerprint",
                denuncia_id=_physical_id(report),
                payload=decision_payload,
            ),
            creado_en=_at(builder, 420 + index),
        )
        _link(builder, f"link.{alias}.report", "decision_for_report", alias, report, source_field="denuncia_id")
        _link(
            builder,
            f"link.{alias}.operator",
            "decided_by",
            alias,
            "user.operator",
            source_field="operador_usuario_id",
        )
        _link(
            builder,
            f"link.{alias}.resource",
            "decides_resource",
            alias,
            resource,
            source_field="recurso_id",
            target_field="moderation_hidden_by_decision_id",
        )

    reports = (
        "report.post.received",
        "report.post.hidden.resolved",
        "report.story.hidden.resolved",
    )
    for index, report in enumerate(reports, 1):
        alias = f"outbox.moderation.{index}"
        resource_type, resource_alias, reason_code = report_contracts[report]
        report_contract = {
            "report_id": _physical_id(report),
            "resource_type": resource_type,
            "resource_id": _physical_id(resource_alias),
            "reason_code": reason_code,
        }
        _row(
            builder,
            alias,
            "operational_notification_outbox",
            event_type=_REPORT_CREATED,
            aggregate_type="moderation_report",
            aggregate_id=_owner_derived(
                "app.modules.notifications.services.operational_notification_services.enqueue_report_created",
                output="aggregate_id",
                **report_contract,
            ),
            deduplication_key=_owner_derived(
                "app.modules.notifications.services.operational_notification_services.enqueue_report_created",
                output="deduplication_key",
                **report_contract,
            ),
            payload_json=_owner_derived(
                "app.modules.notifications.services.operational_notification_services.enqueue_report_created",
                output="payload_json",
                **report_contract,
            ),
            payload_fingerprint=_owner_derived(
                "app.modules.notifications.services.operational_notification_services.enqueue_report_created",
                output="payload_fingerprint",
                **report_contract,
            ),
            status="suppressed",
            attempt_count=0,
            suppressed_at=_at(builder, 430 + index),
            suppressed_by="et100.3-functional",
            suppression_reason="pre_activation_synthetic",
            created_at=_at(builder, 400 + index),
        )
        _link(builder, f"link.{alias}.report", "outbox_for_report", alias, report, source_field="aggregate_id")

    for index, commerce in enumerate(("commerce.primary", "commerce.secondary"), 1):
        metric_alias = f"metrics.commerce.{index}"
        snapshot_alias = f"snapshot.commerce.{index}"
        values = {
            "total_seguidores": 1 if index == 1 else 0,
            "total_publicaciones": 3 if index == 1 else 1,
            "total_likes_publicaciones": 1 if index == 1 else 0,
            "total_guardados_publicaciones": 1 if index == 1 else 0,
            "total_historias": 4 if index == 1 else 0,
            "total_vistas_historias": 1 if index == 1 else 0,
            "total_likes_historias": 1 if index == 1 else 0,
        }
        _row(builder, metric_alias, "comercios_metricas_sociales", **values, updated_at=_at(builder, 450 + index))
        _row(
            builder,
            snapshot_alias,
            "comercios_metricas_snapshots",
            fecha=date(2026, 1, 14),
            **values,
            created_at=_at(builder, 440 + index),
            updated_at=_at(builder, 440 + index),
        )
        _link(builder, f"link.{metric_alias}", "metrics_of", metric_alias, commerce, source_field="comercio_id")
        _link(builder, f"link.{snapshot_alias}", "snapshot_of", snapshot_alias, commerce, source_field="comercio_id")


def _add_functional_agenda_operations_knowledge(builder: BlueprintBuilder) -> None:
    for index, (context_alias, commerce, status) in enumerate(
        (
            ("agenda.context.primary", "commerce.primary", "activo"),
            ("agenda.context.secondary", "commerce.secondary", "archivado"),
        ),
        1,
    ):
        _row(
            builder,
            context_alias,
            "agenda_contextos_agendables",
            estado=status,
            created_at=_at(builder, 500 + index),
            updated_at=_at(builder, 500 + index),
        )
        link_alias = f"agenda.feedgo.{index}"
        _row(
            builder,
            link_alias,
            "feedgo_agenda_contextos",
            created_at=_at(builder, 510 + index),
            updated_at=_at(builder, 510 + index),
        )
        _link(
            builder,
            f"link.{link_alias}.commerce",
            "agenda_for_commerce",
            link_alias,
            commerce,
            source_field="comercio_id",
        )
        _link(
            builder,
            f"link.{link_alias}.context",
            "agenda_context",
            link_alias,
            context_alias,
            source_field="agenda_contexto_id",
        )

    agenda_elements = (
        ("agenda.element.active", "agenda.context.primary", "evento", "activo", 600, 1800),
        ("agenda.element.completed", "agenda.context.primary", "tarea", "completado", 2400, 3000),
        ("agenda.element.cancelled", "agenda.context.secondary", "recordatorio", "cancelado", 3600, None),
    )
    for index, (alias, context, kind, status, start, end) in enumerate(agenda_elements, 1):
        _row(
            builder,
            alias,
            "agenda_elementos",
            tipo=kind,
            estado=status,
            version=1,
            titulo=f"Elemento sintetico {index}",
            descripcion="Agenda funcional sintetica.",
            inicio=_at(builder, start),
            fin=None if end is None else _at(builder, end),
            todo_el_dia=False,
            created_at=_at(builder, 520 + index),
            updated_at=_at(builder, 520 + index),
        )
        _link(builder, f"link.{alias}.context", "agenda_element_of", alias, context, source_field="contexto_id")

    incident_specs = (
        ("incident.open", "open", 1, None, None, None),
        ("incident.reviewed", "reviewed", 5, 560, 570, 580),
    )
    incident_create_payloads: dict[str, dict[str, Any]] = {}
    for index, (alias, status, version, contained, resolved, reviewed) in enumerate(incident_specs, 1):
        create_payload = {
            "title": f"Incidente sintetico {index}",
            "summary": "Resumen sintetico sin PII ni secretos.",
            "incident_type": "availability" if index == 1 else "data_integrity",
            "severity": "sev3_medium",
            "owner_usuario_id": _physical_id("user.operator"),
            "operational_deadline_at": _at(builder, 7200),
            "source": None,
            "idempotency_key": f"synthetic-incident-{index}",
        }
        incident_create_payloads[alias] = create_payload
        _row(
            builder,
            alias,
            "operational_incidents",
            public_id=_owner_generated_incident_id(),
            title=create_payload["title"],
            summary_sanitized=create_payload["summary"],
            incident_type=create_payload["incident_type"],
            severity=create_payload["severity"],
            status=status,
            version=version,
            operational_deadline_at=create_payload["operational_deadline_at"],
            contained_at=None if contained is None else _at(builder, contained),
            resolved_at=None if resolved is None else _at(builder, resolved),
            reviewed_at=None if reviewed is None else _at(builder, reviewed),
            residual_risk_level=None if reviewed is None else "low",
            residual_risk_summary=None if reviewed is None else "Riesgo sintetico aceptado.",
            residual_risk_review_at=None,
            legal_assessment_status="pending",
            personal_data_impact="unknown",
            user_communication_status="pending",
            authority_communication_status="pending",
            idempotency_key=create_payload["idempotency_key"],
            request_fingerprint=_owner_derived(
                "app.modules.incidents.services.operational_incidents_services._fingerprint",
                operation="create_incident",
                payload=create_payload,
            ),
            opened_at=_at(builder, 540 + index),
            updated_at=_at(builder, 580 if reviewed else 540 + index),
        )
        _link(
            builder,
            f"link.{alias}.owner",
            "incident_owner",
            alias,
            "user.operator",
            source_field="owner_usuario_id",
        )
        _link(
            builder,
            f"link.{alias}.opened_by",
            "incident_opener",
            alias,
            "user.operator",
            source_field="opened_by_usuario_id",
        )

    event_specs = (
        ("incident.event.open.created", "incident.open", "opened", None, "open", 0, 1),
        ("incident.event.reviewed.created", "incident.reviewed", "opened", None, "open", 0, 1),
        (
            "incident.event.reviewed.investigating",
            "incident.reviewed",
            "start_investigation",
            "open",
            "investigating",
            1,
            2,
        ),
        ("incident.event.reviewed.contained", "incident.reviewed", "contain", "investigating", "contained", 2, 3),
        ("incident.event.reviewed.resolved", "incident.reviewed", "resolve", "contained", "resolved", 3, 4),
        ("incident.event.reviewed.reviewed", "incident.reviewed", "review", "resolved", "reviewed", 4, 5),
    )
    for index, (alias, incident, event_type, before, after, expected, resulting) in enumerate(event_specs, 1):
        if event_type == "opened":
            event_idempotency_key = incident_create_payloads[incident]["idempotency_key"]
            event_summary = incident_create_payloads[incident]["summary"]
            event_fingerprint = _owner_derived(
                "app.modules.incidents.services.operational_incidents_services._fingerprint",
                operation="create_incident",
                payload=incident_create_payloads[incident],
            )
            safe_details = None
        else:
            event_idempotency_key = f"synthetic-incident-event-{index}"
            event_summary = "Evento sintetico sin datos sensibles."
            action_payload = {
                "action": event_type,
                "expected_version": expected,
                "idempotency_key": event_idempotency_key,
                "summary": event_summary,
                "severity": None,
                "owner_usuario_id": None,
                "operational_deadline_at": None,
                "residual_risk_level": "low" if event_type == "resolve" else None,
                "residual_risk_summary": (
                    "Riesgo sintetico aceptado." if event_type == "resolve" else None
                ),
                "residual_risk_owner_usuario_id": None,
                "residual_risk_review_at": None,
                "legal_assessment_status": None,
                "personal_data_impact": None,
                "legal_owner_usuario_id": None,
                "user_communication_status": None,
                "authority_communication_status": None,
                "legal_deadline_at": None,
                "source": None,
            }
            event_fingerprint = _owner_derived(
                "app.modules.incidents.services.operational_incidents_services._fingerprint",
                operation="apply_incident_action",
                public_id=_owner_attribute(incident, "public_id"),
                payload=action_payload,
            )
            safe_details = _owner_derived(
                "app.modules.incidents.services.operational_incidents_services.apply_incident_action",
                output="safe_details_json",
                incident_alias=incident,
                payload=action_payload,
            )
        _row(
            builder,
            alias,
            "operational_incident_events",
            event_type=event_type,
            status_before=before,
            status_after=after,
            severity_before=None if before is None else "sev3_medium",
            severity_after="sev3_medium",
            safe_summary=event_summary,
            safe_details_json=safe_details,
            expected_incident_version=expected,
            resulting_incident_version=resulting,
            idempotency_key=event_idempotency_key,
            request_fingerprint=event_fingerprint,
            occurred_at=_at(builder, 540 + index * 10),
        )
        _link(builder, f"link.{alias}.incident", "incident_event_of", alias, incident, source_field="incident_id")
        _link(
            builder,
            f"link.{alias}.actor",
            "incident_event_actor",
            alias,
            "user.operator",
            source_field="actor_usuario_id",
        )
        _link(
            builder,
            f"link.{alias}.owner_after",
            "incident_event_owner",
            alias,
            "user.operator",
            source_field="owner_after_usuario_id",
            owner_before_source_field=(
                None if event_type == "opened" else "owner_before_usuario_id"
            ),
        )

    proposal_specs = (
        ("knowledge.proposal.pending", "pending", None, None),
        ("knowledge.proposal.rejected", "rejected", "Cobertura sintetica insuficiente.", "user.operator"),
    )
    for index, (alias, status, reason, reviewer) in enumerate(proposal_specs, 1):
        query = f"consulta sintetica {index}"
        confidence = 0.75 if status == "pending" else 0.25
        evidence_json = {
            "evidence_type": "synonym",
            "query": query,
            "confidence": confidence,
            "strength": "candidate",
            "reason": "Cobertura funcional sintetica.",
            "metrics": {"synthetic_count": index},
            "source": "synthetic_functional",
            "generated_at": _at(builder, 610 + index).isoformat(),
        }
        _row(
            builder,
            alias,
            "knowledge_proposals",
            proposal_type="add_synonym",
            status=status,
            query=query,
            term=query,
            target_payload_json={"term": query, "evidence_type": "synonym"},
            evidence_json=evidence_json,
            confidence=confidence,
            source="synthetic_functional",
            dedupe_key=f"add_synonym:none:{query}",
            rejected_reason=reason,
            created_at=_at(builder, 620 + index),
            reviewed_at=None if reviewer is None else _at(builder, 630 + index),
        )
        _link(
            builder,
            f"link.{alias}.taxonomy",
            "proposal_for_node",
            alias,
            "taxonomy.digital_marketing",
            source_field="taxonomy_node_id",
        )
        if reviewer:
            _link(
                builder,
                f"link.{alias}.reviewer",
                "proposal_reviewed_by",
                alias,
                reviewer,
                source_field="reviewed_by_usuario_id",
            )


def _add_representative(builder: BlueprintBuilder) -> None:
    """Agrega las 36 filas de diversidad aprobadas sobre functional."""

    secondary_owner = "user.representative.owner_secondary"
    _row(
        builder,
        secondary_owner,
        "usuarios",
        email="secondary.owner.synthetic@example.com",
        email_canonical="secondary.owner.synthetic@example.com",
        email_verified_at=_at(builder, 700),
        email_verification_source="email_link",
        modo_activo="publicador",
        onboarding_completo=True,
        provincia="Buenos Aires",
        ciudad="Tandil",
    )
    _row(
        builder,
        "credential.representative.owner_secondary",
        "password_credentials",
        password_hash=_password_contract(),
        hash_version="bcrypt",
        created_at=_at(builder, 701),
        updated_at=_at(builder, 701),
    )
    for suffix, document in zip(
        ("terms", "privacy"), _LEGAL_DOCUMENTS, strict=True
    ):
        document_type, document_version, document_reference = document
        _row(
            builder,
            f"legal.representative.owner_secondary.{suffix}",
            "usuarios_documentos_aceptaciones",
            documento_tipo=document_type,
            documento_version=document_version,
            aceptado_en=_at(builder, 702),
            canal="web",
            metodo="checkbox_explicito",
            estado="aceptado",
            documento_referencia=document_reference,
        )
    _row(
        builder,
        "session.representative.owner_secondary.active",
        "feedgo_sessions",
        id=_nonce_contract(
            purpose="feedgo_session_id",
            owner="app.modules.users.services.feedgo_session_services.generate_session_id",
            format="token_urlsafe_32",
        ),
        authentication_method="password",
        issued_at=_at(builder, 703),
        expires_at=_at(builder, 87103),
        revoked_at=None,
        contract_version=1,
    )
    _row(
        builder,
        "embedding.user.representative.owner_secondary",
        "usuarios_embeddings",
        vector=_user_embedding(secondary_owner),
        model_version=1,
        created_at=_at(builder, 704),
        updated_at=_at(builder, 704),
    )
    for alias, source, field in (
        (
            "link.credential.representative.owner_secondary",
            "credential.representative.owner_secondary",
            "usuario_id",
        ),
        (
            "link.legal.representative.owner_secondary.terms",
            "legal.representative.owner_secondary.terms",
            "usuario_id",
        ),
        (
            "link.legal.representative.owner_secondary.privacy",
            "legal.representative.owner_secondary.privacy",
            "usuario_id",
        ),
        (
            "link.session.representative.owner_secondary",
            "session.representative.owner_secondary.active",
            "usuario_id",
        ),
        (
            "link.embedding.user.representative.owner_secondary",
            "embedding.user.representative.owner_secondary",
            "usuario_id",
        ),
    ):
        _link(builder, alias, "representative_identity", source, secondary_owner, source_field=field)

    commerce_specs = (
        (
            "commerce.representative.local_peer",
            "Comercio Sintetico Local Comparable",
            "user.owner",
            "rubro.gastronomia",
            "taxonomy.gastronomia",
            "Buenos Aires",
            "Tandil",
            "Calle Sintetica 220",
            -37.3221,
            -59.1328,
        ),
        (
            "commerce.representative.distant_peer",
            "Comercio Sintetico Distante",
            "user.owner",
            "rubro.gastronomia",
            "taxonomy.gastronomia",
            "Buenos Aires",
            "Mar del Plata",
            "Avenida Sintetica 330",
            -38.0055,
            -57.5426,
        ),
        (
            "commerce.representative.no_location_secondary_owner",
            "Servicio Sintetico Sin Geolocalizacion",
            secondary_owner,
            "rubro.services",
            "taxonomy.professional_services",
            "Buenos Aires",
            "Tandil",
            None,
            None,
            None,
        ),
    )
    for index, (
        alias,
        name,
        owner,
        rubro,
        taxonomy,
        province,
        city,
        address,
        latitude,
        longitude,
    ) in enumerate(commerce_specs, 1):
        _row(
            builder,
            alias,
            "comercios",
            nombre=name,
            descripcion="Comercio de diversidad representative sintetica.",
            portada_url=f"synthetic-media://{alias.replace('.', '/')}/cover-v1",
            provincia=province,
            ciudad=city,
            direccion=address,
            latitud=latitude,
            longitud=longitude,
            mostrar_direccion_publicamente=address is not None,
            activo=True,
            moderation_hidden=False,
            moderation_revision=0,
            created_at=_at(builder, 720 + index),
            updated_at=_at(builder, 720 + index),
        )
        assignment = f"assignment.{alias}"
        embedding = f"embedding.{alias}"
        _row(
            builder,
            assignment,
            "taxonomy_assignments",
            entity_type="comercio",
            source="manual",
            confidence=1.0,
            principal=True,
        )
        _row(
            builder,
            embedding,
            "comercios_embeddings",
            vector=_commerce_embedding(alias),
            model_version=1,
            created_at=_at(builder, 730 + index),
            updated_at=_at(builder, 730 + index),
        )
        _link(builder, f"link.{alias}.owner", "owned_by", alias, owner, source_field="usuario_id")
        _link(builder, f"link.{alias}.rubro", "classified_by", alias, rubro, source_field="rubro_id")
        _link(builder, f"link.{assignment}.node", "assigned_node", assignment, taxonomy, source_field="taxonomy_node_id")
        _link(builder, f"link.{assignment}.entity", "assigned_entity", assignment, alias, source_field="entity_id")
        _link(builder, f"link.{embedding}", "embedding_of", embedding, alias, source_field="comercio_id")

    for suffix, opening, closing in (
        ("morning", "09:00:00", "12:00:00"),
        ("afternoon", "14:00:00", "18:00:00"),
    ):
        alias = f"schedule.representative.local_peer.{suffix}"
        _row(
            builder,
            alias,
            "comercios_horarios_atencion",
            dia_semana=0,
            hora_apertura=opening,
            hora_cierre=closing,
            created_at=_at(builder, 740),
            updated_at=_at(builder, 740),
        )
        _link(
            builder,
            f"link.{alias}",
            "schedule_of",
            alias,
            "commerce.representative.local_peer",
            source_field="comercio_id",
        )

    post_specs = (
        ("post.representative.local.tie", "commerce.representative.local_peer", 750, True),
        ("post.representative.local.secondary", "commerce.representative.local_peer", 751, False),
        ("post.representative.distant.tie", "commerce.representative.distant_peer", 750, True),
        (
            "post.representative.secondary_owner",
            "commerce.representative.no_location_secondary_owner",
            752,
            False,
        ),
    )
    for index, (alias, commerce, timestamp, with_media) in enumerate(post_specs, 1):
        _row(
            builder,
            alias,
            "publicaciones",
            titulo=f"Publicacion representative sintetica {index}",
            descripcion="Contenido representative activo y visible.",
            imagen_url=(
                f"synthetic-media://{alias.replace('.', '/')}/image-v1"
                if with_media
                else None
            ),
            is_activa=True,
            moderation_hidden=False,
            moderation_revision=0,
            views_count=0,
            created_at=_at(builder, timestamp),
            updated_at=_at(builder, timestamp),
        )
        _link(builder, f"link.{alias}.commerce", "post_of", alias, commerce, source_field="comercio_id")

    story_specs = (
        (
            "story.representative.local.linked",
            "commerce.representative.local_peer",
            "post.representative.local.tie",
        ),
        (
            "story.representative.secondary_owner.independent",
            "commerce.representative.no_location_secondary_owner",
            None,
        ),
    )
    for index, (alias, commerce, post) in enumerate(story_specs, 1):
        _row(
            builder,
            alias,
            "historias",
            media_url=f"synthetic-media://{alias.replace('.', '/')}/video-v1",
            is_activa=True,
            moderation_hidden=False,
            moderation_revision=0,
            expira_en=_at(builder, 44000 + index),
            created_at=_at(builder, 760 + index),
            updated_at=_at(builder, 760 + index),
        )
        _link(builder, f"link.{alias}.commerce", "story_of", alias, commerce, source_field="comercio_id")
        if post:
            _link(builder, f"link.{alias}.post", "story_post", alias, post, source_field="publicacion_id")

    interaction_specs = (
        ("social.representative.follow.local", "seguidores", "commerce.representative.local_peer"),
        ("social.representative.like.post", "likes_publicaciones", "post.representative.local.tie"),
        ("social.representative.save.post", "publicaciones_guardadas", "post.representative.local.tie"),
        ("social.representative.view.story", "historias_vistas", "story.representative.local.linked"),
        ("social.representative.like.story", "historias_likes", "story.representative.local.linked"),
    )
    for index, (alias, table, resource) in enumerate(interaction_specs, 1):
        _row(builder, alias, table, created_at=_at(builder, 770 + index))
        _link(builder, f"link.{alias}.user", "interaction_user", alias, secondary_owner, source_field="usuario_id")
        resource_field = (
            "comercio_id"
            if table == "seguidores"
            else ("publicacion_id" if "publicacion" in table else "historia_id")
        )
        _link(builder, f"link.{alias}.resource", "representative_interaction", alias, resource, source_field=resource_field)

    metric_values = {
        "total_seguidores": 1,
        "total_publicaciones": 2,
        "total_likes_publicaciones": 1,
        "total_guardados_publicaciones": 1,
        "total_historias": 1,
        "total_vistas_historias": 1,
        "total_likes_historias": 1,
    }
    _row(
        builder,
        "metrics.representative.local_peer",
        "comercios_metricas_sociales",
        **metric_values,
        updated_at=_at(builder, 790),
    )
    for index, values in enumerate(
        (
            {key: 0 for key in metric_values},
            metric_values,
        ),
        1,
    ):
        alias = f"snapshot.representative.local_peer.{index}"
        _row(
            builder,
            alias,
            "comercios_metricas_snapshots",
            fecha=date(2026, 1, 10 + index),
            **values,
            created_at=_at(builder, 780 + index),
            updated_at=_at(builder, 780 + index),
        )
        _link(builder, f"link.{alias}", "snapshot_of", alias, "commerce.representative.local_peer", source_field="comercio_id")
    _link(
        builder,
        "link.metrics.representative.local_peer",
        "metrics_of",
        "metrics.representative.local_peer",
        "commerce.representative.local_peer",
        source_field="comercio_id",
    )

    search_specs = (
        ("search.representative.keyword", "pizza sintetica", True, False, False, 2),
        ("search.representative.semantic_geo", "comida cercana", False, True, True, 1),
        ("search.representative.no_results", "consulta sin coincidencias", False, False, False, 0),
    )
    for index, (alias, query, smart, semantic, located, count) in enumerate(search_specs, 1):
        mode = "smart_semantic" if semantic else ("smart" if smart else "classic")
        _row(
            builder,
            alias,
            "search_events",
            endpoint="/comercios/activos",
            query_original=query,
            query_normalizada=query,
            modo_busqueda=mode,
            smart=smart,
            smart_semantic=semantic,
            limit=20,
            offset=0,
            radio_km=5.0 if located else None,
            has_location=located,
            result_count=count,
            no_results=count == 0,
            taxonomy_node_ids_json=[],
            rubro_ids_json=[],
            comercio_result_ids_json=[],
            metadata_json={"source": "synthetic_representative", "scenario": index},
        )

    incident_alias = "incident.open"
    incident_outbox_owner = (
        "app.modules.notifications.services.operational_notification_services."
        "enqueue_incident_opened"
    )
    _row(
        builder,
        "outbox.representative.incident.pending",
        "operational_notification_outbox",
        event_type="operations.incident.opened",
        aggregate_type="operational_incident",
        aggregate_id=_owner_derived(
            incident_outbox_owner,
            output="aggregate_id",
            incident_alias=incident_alias,
        ),
        deduplication_key=_owner_derived(
            incident_outbox_owner,
            output="deduplication_key",
            incident_alias=incident_alias,
        ),
        payload_json=_owner_derived(
            incident_outbox_owner,
            output="payload_json",
            incident_alias=incident_alias,
        ),
        payload_fingerprint=_owner_derived(
            incident_outbox_owner,
            output="payload_fingerprint",
            incident_alias=incident_alias,
        ),
        status="pending",
        attempt_count=0,
        created_at=_at(builder, 820),
    )

    query = "consulta sintetica aprobada"
    _row(
        builder,
        "knowledge.proposal.representative.approved",
        "knowledge_proposals",
        proposal_type="add_synonym",
        status="approved",
        query=query,
        term=query,
        target_payload_json={"term": query, "evidence_type": "synonym"},
        evidence_json={
            "evidence_type": "synonym",
            "query": query,
            "confidence": 0.9,
            "strength": "candidate",
            "reason": "Cobertura representative sintetica.",
            "metrics": {"synthetic_count": 3},
            "source": "synthetic_representative",
            "generated_at": _at(builder, 830).isoformat(),
        },
        confidence=0.9,
        source="synthetic_representative",
        dedupe_key=f"add_synonym:none:{query}",
        rejected_reason=None,
        created_at=_at(builder, 831),
        reviewed_at=_at(builder, 832),
        applied_at=None,
    )
    _link(
        builder,
        "link.knowledge.proposal.representative.approved.taxonomy",
        "proposal_for_node",
        "knowledge.proposal.representative.approved",
        "taxonomy.digital_marketing",
        source_field="taxonomy_node_id",
    )
    _link(
        builder,
        "link.knowledge.proposal.representative.approved.reviewer",
        "proposal_reviewed_by",
        "knowledge.proposal.representative.approved",
        "user.operator",
        source_field="reviewed_by_usuario_id",
    )


def compile_scenario(
    *,
    dataset_version: str,
    profile: str,
    seed: str,
    clock_policy: ClockPolicy,
) -> LogicalBlueprint:
    """Compila un profile aprobado sin I/O ni valores del reloj real."""

    if profile not in SUPPORTED_PROFILES:
        raise BlueprintContractError(f"profile sintetico no soportado: {profile}")
    context = BlueprintContext(
        dataset_version=dataset_version,
        profile=profile,
        seed=seed,
        clock_policy=clock_policy,
    )
    builder = BlueprintBuilder(context)
    _add_smoke(builder)
    if profile in {FUNCTIONAL_PROFILE, REPRESENTATIVE_PROFILE}:
        _add_functional_identity(builder)
        _add_functional_discovery_content(builder)
        _add_functional_moderation_metrics(builder)
        _add_functional_agenda_operations_knowledge(builder)
    if profile == REPRESENTATIVE_PROFILE:
        _add_representative(builder)
    return builder.build()


def compile_smoke(
    *, dataset_version: str, seed: str, clock_policy: ClockPolicy
) -> LogicalBlueprint:
    return compile_scenario(
        dataset_version=dataset_version,
        profile=SMOKE_PROFILE,
        seed=seed,
        clock_policy=clock_policy,
    )


def compile_functional(
    *, dataset_version: str, seed: str, clock_policy: ClockPolicy
) -> LogicalBlueprint:
    return compile_scenario(
        dataset_version=dataset_version,
        profile=FUNCTIONAL_PROFILE,
        seed=seed,
        clock_policy=clock_policy,
    )


def compile_representative(
    *, dataset_version: str, seed: str, clock_policy: ClockPolicy
) -> LogicalBlueprint:
    return compile_scenario(
        dataset_version=dataset_version,
        profile=REPRESENTATIVE_PROFILE,
        seed=seed,
        clock_policy=clock_policy,
    )

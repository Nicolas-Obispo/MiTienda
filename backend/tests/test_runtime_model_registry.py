import subprocess
import sys
import textwrap
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]


RUNTIME_PROBE = textwrap.dedent(
    r"""
    import sys

    assert "app.modules.moderation.models.moderation_decisions_models" not in sys.modules

    import main

    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.core.auth import crear_token_jwt
    from app.core.database import Base, get_db
    from app.core.model_registry import import_all_models
    from app.modules.posts.models.publicaciones_models import Publicacion
    from app.modules.products.models.rubros_models import Rubro
    from app.modules.social.models.likes_publicaciones_models import LikePublicacion
    from app.modules.social.models.publicaciones_guardadas_models import PublicacionGuardada
    from app.modules.spaces.models.comercios_models import Comercio
    from app.modules.users.models.usuarios_models import Usuario

    assert "moderation_decisions" in Base.metadata.tables
    for table in Base.metadata.tables.values():
        for foreign_key in table.foreign_keys:
            assert foreign_key.column.table.name in Base.metadata.tables

    tables_before = tuple(sorted(Base.metadata.tables))
    import_all_models()
    import_all_models()
    assert tuple(sorted(Base.metadata.tables)) == tables_before

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[get_db] = override_get_db

    db = Session()
    db.add(Rubro(id=1, nombre="Gastronomia", activo=True))
    db.add(Usuario(
        id=1,
        email="runtime-registry@example.com",
        hashed_password="hash",
        modo_activo="usuario",
        onboarding_completo=True,
    ))
    db.add(Comercio(
        id=10,
        usuario_id=1,
        nombre="Comercio runtime",
        descripcion="Prueba",
        portada_url="/uploads/portada.jpg",
        rubro_id=1,
        provincia="Buenos Aires",
        ciudad="La Plata",
        direccion="Calle 1",
        latitud=-34.92,
        longitud=-57.95,
        maps_url="https://maps.example/runtime",
        mostrar_direccion_publicamente=True,
        activo=True,
    ))
    db.add(Publicacion(
        id=20,
        comercio_id=10,
        titulo="Publicacion runtime",
        descripcion="Visible",
        imagen_url="/uploads/publicacion.jpg",
        is_activa=True,
        views_count=0,
    ))
    db.commit()
    db.close()

    token = crear_token_jwt({"sub": "1"})
    headers = {"Authorization": f"Bearer {token}"}
    client = TestClient(main.app, raise_server_exceptions=False)

    detail = client.get("/publicaciones/20")
    assert detail.status_code == 200, detail.text
    db = Session()
    assert db.get(Publicacion, 20).views_count == 1
    db.close()

    like_created = client.post("/likes/publicaciones/20", headers=headers)
    assert like_created.status_code == 200, like_created.text
    assert like_created.json() == {"liked": True}
    like_removed = client.post("/likes/publicaciones/20", headers=headers)
    assert like_removed.status_code == 200, like_removed.text
    assert like_removed.json() == {"liked": False}

    saved = client.post(
        "/publicaciones/guardadas",
        json={"publicacion_id": 20},
        headers=headers,
    )
    assert saved.status_code == 201, saved.text
    removed = client.delete("/publicaciones/guardadas/20", headers=headers)
    assert removed.status_code == 204, removed.text

    db = Session()
    assert db.query(LikePublicacion).count() == 0
    assert db.query(PublicacionGuardada).count() == 0
    assert db.get(Publicacion, 20).views_count == 1
    db.close()
    """
)


class RuntimeModelRegistryTests(unittest.TestCase):
    def test_real_application_initialization_registers_complete_metadata(self):
        result = subprocess.run(
            [sys.executable, "-c", RUNTIME_PROBE],
            cwd=BACKEND_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )

    def test_registry_runs_before_router_imports(self):
        source = (BACKEND_ROOT / "main.py").read_text(encoding="utf-8")

        self.assertLess(
            source.index("import_all_models()"),
            source.index("# Routers"),
        )


if __name__ == "__main__":
    unittest.main()

import unittest
from datetime import datetime
from pathlib import Path

from app.modules.posts.schemas.publicaciones_schemas import PublicacionRead


REPO_ROOT = Path(__file__).resolve().parents[2]


class PublicacionComercioIdentityContractTests(unittest.TestCase):
    def test_publicacion_read_expone_portada_del_comercio(self):
        publicacion = PublicacionRead(
            id=1,
            comercio_id=2,
            comercio_nombre="Espacio",
            comercio_portada_url="/uploads/espacio.jpg",
            titulo="Publicacion",
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
        )

        self.assertEqual(
            publicacion.comercio_portada_url,
            "/uploads/espacio.jpg",
        )

    def test_feed_proyecta_identidad_desde_su_join_sin_query_por_card(self):
        source = (
            REPO_ROOT
            / "backend/app/modules/posts/services/feed_publicaciones_services.py"
        ).read_text(encoding="utf-8")

        self.assertIn(
            ".join(Comercio, Publicacion.comercio_id == Comercio.id)",
            source,
        )
        self.assertIn('Comercio.nombre.label("comercio_nombre")', source)
        self.assertIn(
            'Comercio.portada_url.label("comercio_portada_url")',
            source,
        )
        self.assertNotIn("db.query(Comercio)", source)


if __name__ == "__main__":
    unittest.main()

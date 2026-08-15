import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.products.models.rubros_models import Rubro
from app.modules.search.services.territorial_search_services import (
    TerritorialContext,
    commerce_matches_territory,
    normalize_city_key,
    normalize_province_code,
)
from app.modules.spaces.models.comercios_models import Comercio
from app.modules.spaces.schemas.comercios_schemas import ComercioPublicResponse
from app.modules.spaces.services.comercios_services import listar_comercios_activos
from app.modules.users.models.usuarios_models import Usuario


import_all_models()

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TerritorialNormalizationTests(unittest.TestCase):
    def test_identidad_incluye_ciudad_provincia_y_pais(self):
        santa_fe = TerritorialContext.build(
            city_key="San Martín", province_code="AR-S", country_code="AR"
        )
        buenos_aires = TerritorialContext.build(
            city_key="San Martin", province_code="AR-B", country_code="Argentina"
        )
        self.assertEqual(santa_fe.city_key, buenos_aires.city_key)
        self.assertNotEqual(santa_fe.province_code, buenos_aires.province_code)
        self.assertEqual(santa_fe.country_code, "AR")

    def test_normaliza_aliases_sin_hardcodear_ciudad(self):
        self.assertEqual(normalize_city_key("Municipio de Sunchales"), "sunchales")
        self.assertEqual(normalize_city_key("Río Cuarto"), "rio cuarto")
        self.assertEqual(normalize_province_code("Córdoba"), "AR-X")
        self.assertEqual(normalize_province_code("Santa Fe"), "AR-S")


class TerritorialSearchTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        self.db.add(Usuario(id=1, email="owner@example.com", hashed_password="hash"))
        self.db.add(Rubro(id=1, nombre="Servicios", activo=True))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=engine)

    def _commerce(
        self,
        comercio_id,
        *,
        city="Rafaela",
        province="Santa Fe",
        name="Plomero",
        description="Servicio de plomeria",
        latitude=-31.25,
        longitude=-61.49,
        public=True,
    ):
        item = Comercio(
            id=comercio_id,
            usuario_id=1,
            nombre=name,
            descripcion=description,
            portada_url="/uploads/test.jpg",
            rubro_id=1,
            provincia=province,
            ciudad=city,
            direccion="Direccion publica" if public else "Domicilio privado",
            latitud=latitude,
            longitud=longitude,
            mostrar_direccion_publicamente=public,
            activo=True,
        )
        self.db.add(item)
        self.db.commit()
        return item

    def _search(self, **overrides):
        params = {
            "q": "Plomero",
            "city_key": "rafaela",
            "province_code": "AR-S",
            "country_code": "AR",
            "scope": "local",
            "limit": 20,
            "offset": 0,
        }
        params.update(overrides)
        with patch(
            "app.modules.spaces.services.comercios_services.registrar_search_event_best_effort"
        ):
            return listar_comercios_activos(self.db, **params)

    def test_rafaela_excluye_otra_ciudad_y_viceversa(self):
        self._commerce(1, city="Rafaela")
        self._commerce(2, city="Sunchales")

        rafaela = self._search()
        sunchales = self._search(city_key="sunchales")

        self.assertEqual([item.id for item in rafaela], [1])
        self.assertEqual([item.id for item in sunchales], [2])

    def test_ciudades_homonimas_no_cruzan_provincias(self):
        santa_fe = self._commerce(1, city="San Martin", province="Santa Fe")
        buenos_aires = self._commerce(2, city="San Martín", province="Buenos Aires")
        context = TerritorialContext.build(
            city_key="san martin", province_code="AR-S", country_code="AR"
        )
        self.assertTrue(commerce_matches_territory(santa_fe, context))
        self.assertFalse(commerce_matches_territory(buenos_aires, context))

    def test_frontera_ocurre_antes_de_paginacion_clasica(self):
        self._commerce(1, city="Rafaela")
        for comercio_id in range(2, 8):
            self._commerce(comercio_id, city="Sunchales")

        page = self._search(limit=1)
        self.assertEqual([item.id for item in page], [1])

    def test_keyword_filtra_territorio_y_prioriza_relevancia(self):
        self._commerce(
            1,
            name="Plomero especialista",
            description="Servicio",
            latitude=-31.35,
        )
        self._commerce(
            2,
            name="Servicios del hogar",
            description="Plomero",
            latitude=-31.2501,
        )
        self._commerce(3, city="Sunchales", name="Plomero Sunchales")

        results = self._search(smart=True, lat=-31.25, lng=-61.49)
        self.assertEqual([item.id for item in results], [1, 2])

    def test_semantico_hidrata_solo_territorio_activo(self):
        self._commerce(1, name="Plomero Rafaela")
        self._commerce(2, city="Sunchales", name="Plomero Sunchales")

        results = self._search(smart_semantic=True)
        self.assertEqual([item.id for item in results], [1])

    def test_publico_conserva_distancia_y_privado_no_la_expone(self):
        public = self._commerce(1, public=True, latitude=-31.251)
        private = self._commerce(2, public=False, latitude=-31.252)

        results = self._search(lat=-31.25, lng=-61.49)
        by_id = {item.id: item for item in results}
        self.assertIsNotNone(by_id[public.id].distancia_km)
        self.assertIsNone(by_id[private.id].distancia_km)
        self.assertIsNotNone(private._distancia_interna_km)
        payload = ComercioPublicResponse.model_validate(private).model_dump(exclude_none=True)
        self.assertNotIn("distancia_km", payload)
        self.assertNotIn("_distancia_orden_km", payload)

    def test_banda_privada_de_un_km_es_estable_y_no_publica(self):
        self._commerce(1, public=False, latitude=-31.253)
        self._commerce(2, public=False, latitude=-31.254)

        results = self._search(lat=-31.25, lng=-61.49)
        self.assertEqual([item.id for item in results], [2, 1])
        self.assertEqual(results[0]._distancia_orden_km, results[1]._distancia_orden_km)
        self.assertTrue(all(item.distancia_km is None for item in results))

    def test_expansion_50_y_100_km_es_explicita(self):
        self._commerce(1, latitude=-31.25)
        self._commerce(2, city="Sunchales", latitude=-31.60)
        self._commerce(3, city="Otra", latitude=-32.0)

        local = self._search(lat=-31.25, lng=-61.49)
        expanded_50 = self._search(
            scope="expanded", expansion_km=50, lat=-31.25, lng=-61.49
        )
        expanded_100 = self._search(
            scope="expanded", expansion_km=100, lat=-31.25, lng=-61.49
        )

        self.assertEqual([item.id for item in local], [1])
        self.assertEqual({item.id for item in expanded_50}, {1, 2})
        self.assertEqual({item.id for item in expanded_100}, {1, 2, 3})

    def test_historico_sin_coordenadas_participa_territorialmente(self):
        historic = self._commerce(1, latitude=None, longitude=None)
        results = self._search(lat=-31.25, lng=-61.49)
        self.assertEqual([item.id for item in results], [historic.id])
        self.assertIsNone(results[0].distancia_km)

    def test_search_event_registra_territorio_scope_y_no_coordenadas(self):
        self._commerce(1)
        captured = []
        with patch(
            "app.modules.spaces.services.comercios_services.registrar_search_event_best_effort",
            side_effect=lambda _db, payload: captured.append(payload),
        ):
            listar_comercios_activos(
                self.db,
                q="Plomero",
                city_key="Rafaela",
                province_code="Santa Fe",
                country_code="Argentina",
                scope="local",
                lat=-31.25,
                lng=-61.49,
            )

        metadata = captured[0]["metadata_json"]
        self.assertEqual(metadata["city_key"], "rafaela")
        self.assertEqual(metadata["province_code"], "AR-S")
        self.assertEqual(metadata["country_code"], "AR")
        self.assertEqual(metadata["scope"], "local")
        self.assertNotIn("lat", metadata)
        self.assertNotIn("lng", metadata)


if __name__ == "__main__":
    unittest.main()

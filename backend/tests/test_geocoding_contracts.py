import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth import obtener_usuario_actual
from app.modules.geocoding.routes.geocoding_routers import router
from app.modules.geocoding.services.geocoding_services import (
    GeocodingProviderError,
    GeocodingProviderTimeoutError,
    GeocodingService,
    ProviderLocation,
    UnavailableGeocodingProvider,
    get_geocoding_service,
)


class FakeProvider:
    def __init__(self):
        self.forward_calls = []
        self.reverse_calls = []

    def forward(self, **kwargs):
        self.forward_calls.append(kwargs)
        return [
            ProviderLocation(
                label="  Sgto.   Cabral 159, Rafaela  ",
                latitude=-31.2503,
                longitude=-61.4867,
                city=" Rafaela ",
                province="Santa Fe",
                country="Argentina",
            ),
            ProviderLocation(
                label="Sgto. Cabral 245, Rafaela",
                latitude=-31.251,
                longitude=-61.487,
            ),
        ]

    def reverse(self, **kwargs):
        self.reverse_calls.append(kwargs)
        return ProviderLocation(
            label="Sgto. Cabral 245, Rafaela",
            latitude=kwargs["latitude"],
            longitude=kwargs["longitude"],
            city="Rafaela",
            province="Santa Fe",
            country="Argentina",
        )


class TimeoutProvider(FakeProvider):
    def forward(self, **kwargs):
        raise GeocodingProviderTimeoutError("private_provider_timeout")


class ErrorProvider(FakeProvider):
    def reverse(self, **kwargs):
        raise GeocodingProviderError("raw_provider_payload_secret")


app = FastAPI()
app.include_router(router)
app.dependency_overrides[obtener_usuario_actual] = lambda: object()
client = TestClient(app)


class GeocodingContractsTests(unittest.TestCase):
    def setUp(self):
        self.provider = FakeProvider()
        self.service = GeocodingService(self.provider)
        app.dependency_overrides[get_geocoding_service] = lambda: self.service

    def tearDown(self):
        app.dependency_overrides.pop(get_geocoding_service, None)

    def test_forward_valido_devuelve_multiples_alternativas_normalizadas(self):
        response = client.post(
            "/geocoding/forward",
            json={
                "query": "  Sgto.  Cabral 159 ",
                "ciudad": "Rafaela",
                "provincia": "Santa Fe",
                "pais": "argentina",
                "limit": 5,
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["alternativas"]), 2)
        self.assertEqual(data["alternativas"][0]["label"], "Sgto. Cabral 159, Rafaela")
        self.assertEqual(data["alternativas"][0]["ciudad"], "Rafaela")
        self.assertEqual(self.provider.forward_calls[0]["country"], "Argentina")
        self.assertNotIn("raw", data["alternativas"][0])
        self.assertNotIn("place_id", data["alternativas"][0])

    def test_forward_invalido_es_rechazado_sin_consultar_proveedor(self):
        response = client.post(
            "/geocoding/forward",
            json={"query": "x", "pais": "Argentina", "limit": 6},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.provider.forward_calls, [])

    def test_reverse_valido_devuelve_propuesta_feedgo(self):
        response = client.post(
            "/geocoding/reverse",
            json={"latitud": -31.251, "longitud": -61.487},
        )

        self.assertEqual(response.status_code, 200)
        proposal = response.json()["propuesta"]
        self.assertEqual(proposal["label"], "Sgto. Cabral 245, Rafaela")
        self.assertEqual(proposal["latitud"], -31.251)
        self.assertEqual(len(self.provider.reverse_calls), 1)

    def test_reverse_invalido_es_rechazado_sin_consultar_proveedor(self):
        for payload in (
            {"latitud": 91, "longitud": -61.487},
            {"latitud": -31.251, "longitud": -181},
        ):
            response = client.post("/geocoding/reverse", json=payload)
            self.assertEqual(response.status_code, 422)
        self.assertEqual(self.provider.reverse_calls, [])

    def test_territory_es_publico_y_no_expone_domicilio_ni_coordenadas(self):
        app.dependency_overrides.pop(obtener_usuario_actual, None)
        try:
            response = client.post(
                "/geocoding/territory",
                json={"latitud": -31.251, "longitud": -61.487},
            )
        finally:
            app.dependency_overrides[obtener_usuario_actual] = lambda: object()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "city_key": "rafaela",
                "province_code": "AR-S",
                "country_code": "AR",
                "city": "Rafaela",
                "province": "Santa Fe",
                "country": "Argentina",
                "attribution": None,
            },
        )
        self.assertNotIn("Sgto.", response.text)
        self.assertNotIn("latitud", response.json())
        self.assertNotIn("longitud", response.json())

    def test_provider_no_disponible_es_503_sin_detalles_sensibles(self):
        app.dependency_overrides[get_geocoding_service] = lambda: GeocodingService(
            UnavailableGeocodingProvider()
        )
        response = client.post(
            "/geocoding/forward",
            json={"query": "Domicilio privado", "pais": "Argentina"},
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "Servicio geografico no disponible."})
        self.assertNotIn("Domicilio privado", response.text)

    def test_timeout_es_504_sin_payload_del_proveedor(self):
        app.dependency_overrides[get_geocoding_service] = lambda: GeocodingService(
            TimeoutProvider()
        )
        response = client.post(
            "/geocoding/forward",
            json={"query": "Sgto. Cabral 159", "pais": "Argentina"},
        )

        self.assertEqual(response.status_code, 504)
        self.assertEqual(
            response.json(),
            {"detail": "El servicio geografico no respondio a tiempo."},
        )
        self.assertNotIn("private_provider_timeout", response.text)

    def test_error_del_proveedor_es_502_y_no_expone_payload_crudo(self):
        app.dependency_overrides[get_geocoding_service] = lambda: GeocodingService(
            ErrorProvider()
        )
        response = client.post(
            "/geocoding/reverse",
            json={"latitud": -31.251, "longitud": -61.487},
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json(),
            {"detail": "El servicio geografico no pudo procesar la solicitud."},
        )
        self.assertNotIn("raw_provider_payload_secret", response.text)


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from app.core.config import settings
from app.modules.geocoding.providers.geoapify_provider import (
    GeoapifyProvider,
    RequestRateLimiter,
)
from app.modules.geocoding.services.geocoding_services import (
    GeocodingProviderError,
    GeocodingProviderRateLimitError,
    GeocodingProviderTimeoutError,
    UnavailableGeocodingProvider,
    get_geocoding_service,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        if isinstance(self.payload, bytes):
            return self.payload
        return json.dumps(self.payload).encode("utf-8")


def result(label="Sgto. Cabral 159, Rafaela, Argentina", **overrides):
    payload = {
        "formatted": label,
        "lat": -31.2503,
        "lon": -61.4867,
        "city": "Rafaela",
        "state": "Santa Fe",
        "country": "Argentina",
        "result_type": "building",
        "rank": {"confidence": 0.91},
        "provider_only": "no debe salir del adapter",
    }
    payload.update(overrides)
    return payload


class GeoapifyProviderTests(unittest.TestCase):
    def _provider(self, opener, *, limiter=None):
        return GeoapifyProvider(
            api_key="test-secret-key",
            timeout_seconds=3,
            rate_limit_rps=5,
            opener=opener,
            rate_limiter=limiter,
        )

    def test_forward_construye_contexto_argentina_y_normaliza_multiples(self):
        captured = {}

        def opener(request, timeout):
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            return FakeResponse({"results": [result(), result("Sgto. Cabral, Rafaela", result_type="street")]})

        results = self._provider(opener).forward(
            query="Sgto. Cabral 159",
            city="Rafaela",
            province="Santa Fe",
            country="Argentina",
            limit=5,
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].precision, "address")
        self.assertEqual(results[0].confidence, 0.91)
        self.assertEqual(results[1].precision, "street")
        self.assertEqual(self._provider(opener).attribution.label, "Powered by Geoapify")
        self.assertIn("filter=countrycode%3Aar", captured["url"])
        self.assertIn("Sgto.+Cabral+159%2C+Rafaela%2C+Santa+Fe%2C+Argentina", captured["url"])
        self.assertEqual(captured["timeout"], 3)

    def test_forward_respeta_limite_maximo_del_contrato(self):
        captured = {}

        def opener(request, timeout):
            captured["url"] = request.full_url
            return FakeResponse({"results": [result()] * 8})

        results = self._provider(opener).forward(
            query="Municipalidad",
            city="Rafaela",
            province="Santa Fe",
            country="Argentina",
            limit=5,
        )
        self.assertEqual(len(results), 5)
        self.assertIn("limit=5", captured["url"])

    def test_forward_descarta_confianza_cero_y_otras_ciudades(self):
        payload = {
            "results": [
                result("Sunchales, Santa Fe, Argentina", city="Sunchales", rank={"confidence": 0.25}),
                result("Municipalidad de Funes", city="Funes", rank={"confidence": 0.8}),
                result("Palacio Municipal, Sunchales", city="Sunchales", rank={"confidence": 0.0}),
            ]
        }
        provider = self._provider(lambda request, timeout: FakeResponse(payload))

        results = provider.forward(
            query="Belgranno 103",
            city="Sunchales",
            province="Santa Fe",
            country="Argentina",
            limit=5,
        )

        self.assertEqual([item.label for item in results], ["Sunchales, Santa Fe, Argentina"])

    def test_reverse_normaliza_propuesta_y_precision(self):
        captured = {}

        def opener(request, timeout):
            captured["url"] = request.full_url
            return FakeResponse({"results": [result(result_type="street", rank={"confidence": 0.65})]})

        proposal = self._provider(opener).reverse(latitude=-31.2503, longitude=-61.4867)
        self.assertEqual(proposal.city, "Rafaela")
        self.assertEqual(proposal.precision, "street")
        self.assertEqual(proposal.confidence, 0.65)
        self.assertIn("lat=-31.2503", captured["url"])
        self.assertIn("lon=-61.4867", captured["url"])

    def test_key_ausente_mantiene_provider_indisponible(self):
        get_geocoding_service.cache_clear()
        with patch.object(settings, "GEOCODING_PROVIDER", "geoapify"), patch.object(
            settings, "GEOAPIFY_API_KEY", None
        ):
            service = get_geocoding_service()
        self.assertIsInstance(service.provider, UnavailableGeocodingProvider)
        get_geocoding_service.cache_clear()

    def test_timeout_no_expone_api_key(self):
        def opener(_request, timeout):
            raise URLError(TimeoutError("test-secret-key"))

        with self.assertRaises(GeocodingProviderTimeoutError) as raised:
            self._provider(opener).reverse(latitude=-31.25, longitude=-61.48)
        self.assertNotIn("test-secret-key", str(raised.exception))

    def test_http_4xx_5xx_y_429_se_sanitizan(self):
        for status, expected in (
            (400, GeocodingProviderError),
            (500, GeocodingProviderError),
            (429, GeocodingProviderRateLimitError),
        ):
            def opener(request, timeout, code=status):
                raise HTTPError(request.full_url, code, "test-secret-key", {}, None)

            with self.assertRaises(expected) as raised:
                self._provider(opener).forward(
                    query="Direccion",
                    city="Rafaela",
                    province="Santa Fe",
                    country="Argentina",
                    limit=5,
                )
            self.assertNotIn("test-secret-key", str(raised.exception))

    def test_respuesta_invalida_se_rechaza(self):
        for payload in ({"features": []}, b"not-json", {"results": [{"formatted": "sin coordenadas"}]}):
            with self.assertRaises(GeocodingProviderError):
                self._provider(lambda request, timeout, value=payload: FakeResponse(value)).forward(
                    query="Direccion",
                    city="Rafaela",
                    province="Santa Fe",
                    country="Argentina",
                    limit=5,
                )

    def test_rate_limit_local_es_conservador_y_determinista(self):
        clock_values = iter([0.0, 0.1, 0.2, 1.1])
        limiter = RequestRateLimiter(2, clock=lambda: next(clock_values))
        limiter.acquire()
        limiter.acquire()
        with self.assertRaises(GeocodingProviderRateLimitError):
            limiter.acquire()
        limiter.acquire()


if __name__ == "__main__":
    unittest.main()

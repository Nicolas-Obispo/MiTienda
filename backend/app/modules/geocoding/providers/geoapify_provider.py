import json
import math
import threading
import time
import unicodedata
from collections import deque
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.modules.geocoding.services.geocoding_services import (
    GeocodingProviderError,
    GeocodingProviderRateLimitError,
    GeocodingProviderTimeoutError,
    ProviderAttribution,
    ProviderLocation,
)


GEOAPIFY_BASE_URL = "https://api-eu.geoapify.com/v1/geocode"


class RequestRateLimiter:
    def __init__(self, requests_per_second: int, clock=time.monotonic):
        if requests_per_second < 1:
            raise ValueError("requests_per_second debe ser positivo")
        self.requests_per_second = requests_per_second
        self.clock = clock
        self._timestamps = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        now = self.clock()
        with self._lock:
            while self._timestamps and now - self._timestamps[0] >= 1:
                self._timestamps.popleft()
            if len(self._timestamps) >= self.requests_per_second:
                raise GeocodingProviderRateLimitError("geoapify_local_rate_limit")
            self._timestamps.append(now)


def _precision_for(result_type: str | None) -> str:
    if result_type in {"building", "amenity"}:
        return "address"
    if result_type == "street":
        return "street"
    if result_type in {"suburb", "district", "postcode", "city"}:
        return "locality"
    if result_type in {"county", "state", "country"}:
        return "region"
    return "unknown"


def _finite_float(value):
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise GeocodingProviderError("geoapify_invalid_response") from exc
    if not math.isfinite(number):
        raise GeocodingProviderError("geoapify_invalid_response")
    return number


def _normalize_result(raw: dict) -> ProviderLocation:
    rank = raw.get("rank") if isinstance(raw.get("rank"), dict) else {}
    confidence = rank.get("confidence")
    if confidence is not None:
        confidence = _finite_float(confidence)
        if not 0 <= confidence <= 1:
            confidence = None

    return ProviderLocation(
        label=str(raw.get("formatted") or "").strip(),
        latitude=_finite_float(raw.get("lat")),
        longitude=_finite_float(raw.get("lon")),
        city=raw.get("city") or raw.get("town") or raw.get("village"),
        province=raw.get("state"),
        country=raw.get("country"),
        precision=_precision_for(raw.get("result_type")),
        confidence=confidence,
    )


def _territory_text(value: str | None) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return " ".join(
        "".join(character for character in normalized if not unicodedata.combining(character))
        .casefold()
        .split()
    )


def _is_useful_forward_result(location: ProviderLocation, expected_city: str | None) -> bool:
    if location.confidence == 0:
        return False
    if not expected_city:
        return True

    expected = _territory_text(expected_city)
    provider_city = _territory_text(location.city)
    label = _territory_text(location.label)
    return expected in provider_city or expected in label


class GeoapifyProvider:
    attribution = ProviderAttribution(
        label="Powered by Geoapify",
        url="https://www.geoapify.com/",
    )

    def __init__(
        self,
        *,
        api_key: str,
        timeout_seconds: float = 5,
        rate_limit_rps: int = 5,
        opener=urlopen,
        rate_limiter: RequestRateLimiter | None = None,
    ):
        if not api_key.strip():
            raise ValueError("Geoapify requiere API key")
        self._api_key = api_key.strip()
        self._timeout_seconds = timeout_seconds
        self._opener = opener
        self._rate_limiter = rate_limiter or RequestRateLimiter(rate_limit_rps)

    def _request(self, endpoint: str, params: dict) -> list[dict]:
        self._rate_limiter.acquire()
        query = urlencode({**params, "format": "json", "apiKey": self._api_key})
        request = Request(
            f"{GEOAPIFY_BASE_URL}/{endpoint}?{query}",
            headers={"Accept": "application/json", "User-Agent": "FeedGo-geocoding/1.0"},
        )
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 429:
                raise GeocodingProviderRateLimitError("geoapify_rate_limit") from None
            raise GeocodingProviderError("geoapify_http_error") from None
        except TimeoutError:
            raise GeocodingProviderTimeoutError("geoapify_timeout") from None
        except URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise GeocodingProviderTimeoutError("geoapify_timeout") from None
            raise GeocodingProviderError("geoapify_network_error") from None
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            raise GeocodingProviderError("geoapify_invalid_response") from None

        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, list):
            raise GeocodingProviderError("geoapify_invalid_response")
        return results

    def forward(self, *, query, city, province, country, limit):
        text = ", ".join(part for part in (query, city, province, country) if part)
        results = self._request(
            "search",
            {
                "text": text,
                "filter": "countrycode:ar",
                "lang": "es",
                "limit": min(limit, 5),
            },
        )
        normalized = [_normalize_result(result) for result in results]
        return [
            location
            for location in normalized
            if _is_useful_forward_result(location, city)
        ][:limit]

    def reverse(self, *, latitude, longitude):
        results = self._request(
            "reverse",
            {"lat": latitude, "lon": longitude, "lang": "es", "limit": 1},
        )
        return _normalize_result(results[0]) if results else None

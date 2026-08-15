from dataclasses import dataclass
from functools import lru_cache
from typing import Literal, Protocol

from app.modules.geocoding.schemas.geocoding_schemas import (
    ForwardGeocodingRequest,
    ForwardGeocodingResponse,
    GeocodingAttribution,
    GeocodingLocation,
    ReverseGeocodingRequest,
    ReverseGeocodingResponse,
)


class GeocodingUnavailableError(RuntimeError):
    pass


class GeocodingProviderError(RuntimeError):
    pass


class GeocodingProviderTimeoutError(GeocodingProviderError):
    pass


class GeocodingProviderRateLimitError(GeocodingProviderError):
    pass


@dataclass(frozen=True)
class ProviderLocation:
    label: str
    latitude: float
    longitude: float
    city: str | None = None
    province: str | None = None
    country: str | None = None
    precision: Literal["address", "street", "locality", "region", "unknown"] = "unknown"
    confidence: float | None = None


@dataclass(frozen=True)
class ProviderAttribution:
    label: str
    url: str


class GeocodingProvider(Protocol):
    attribution: ProviderAttribution | None

    def forward(
        self,
        *,
        query: str,
        city: str | None,
        province: str | None,
        country: str,
        limit: int,
    ) -> list[ProviderLocation]: ...

    def reverse(self, *, latitude: float, longitude: float) -> ProviderLocation | None: ...


class UnavailableGeocodingProvider:
    """Default seguro hasta configurar un proveedor compatible con el gate."""

    attribution = None

    def forward(self, **_kwargs) -> list[ProviderLocation]:
        raise GeocodingUnavailableError("geocoding_provider_unavailable")

    def reverse(self, **_kwargs) -> ProviderLocation | None:
        raise GeocodingUnavailableError("geocoding_provider_unavailable")


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.split())
    return normalized or None


def _normalize_location(location: ProviderLocation) -> GeocodingLocation:
    label = " ".join(location.label.split())
    if not label:
        raise GeocodingProviderError("geocoding_provider_invalid_response")

    try:
        return GeocodingLocation(
            label=label,
            latitud=location.latitude,
            longitud=location.longitude,
            ciudad=_normalize_optional(location.city),
            provincia=_normalize_optional(location.province),
            pais=_normalize_optional(location.country),
            precision=location.precision,
            confidence=location.confidence,
        )
    except (TypeError, ValueError) as exc:
        raise GeocodingProviderError("geocoding_provider_invalid_response") from exc


class GeocodingService:
    def __init__(self, provider: GeocodingProvider):
        self.provider = provider

    def forward(self, request: ForwardGeocodingRequest) -> ForwardGeocodingResponse:
        raw_results = self.provider.forward(
            query=request.query,
            city=request.ciudad,
            province=request.provincia,
            country=request.pais,
            limit=request.limit,
        )
        alternatives = [_normalize_location(item) for item in raw_results[: request.limit]]
        return ForwardGeocodingResponse(
            alternativas=alternatives,
            attribution=self._attribution(),
        )

    def reverse(self, request: ReverseGeocodingRequest) -> ReverseGeocodingResponse:
        raw_result = self.provider.reverse(
            latitude=request.latitud,
            longitude=request.longitud,
        )
        proposal = _normalize_location(raw_result) if raw_result else None
        return ReverseGeocodingResponse(
            propuesta=proposal,
            attribution=self._attribution(),
        )

    def _attribution(self) -> GeocodingAttribution | None:
        attribution = getattr(self.provider, "attribution", None)
        if attribution is None:
            return None
        return GeocodingAttribution(label=attribution.label, url=attribution.url)


@lru_cache(maxsize=1)
def get_geocoding_service() -> GeocodingService:
    from app.core.config import settings

    provider_name = (settings.GEOCODING_PROVIDER or "geoapify").strip().lower()
    api_key = (settings.GEOAPIFY_API_KEY or "").strip()
    if provider_name != "geoapify" or not api_key:
        return GeocodingService(UnavailableGeocodingProvider())

    from app.modules.geocoding.providers.geoapify_provider import GeoapifyProvider

    return GeocodingService(
        GeoapifyProvider(
            api_key=api_key,
            timeout_seconds=settings.GEOAPIFY_TIMEOUT_SECONDS,
            rate_limit_rps=settings.GEOAPIFY_RATE_LIMIT_RPS,
        )
    )
